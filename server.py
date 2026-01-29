import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from datetime import timedelta
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from livekit import api
from supabase import create_client, Client

# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "https://vyaas-backend.onrender.com",
        "https://vyaas-ai.vercel.app",
        "capacitor://localhost",
        "http://192.168.1.1",
        "*" # Fallback for now, but explicit is better
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variables
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
HF_TOKEN = os.getenv("HF_TOKEN")

# Initialize Supabase
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Pydantic Models ---

class ConnectionDetailsRequest(BaseModel):
    username: Optional[str] = None
    room_config: Optional[Dict[str, Any]] = None

class EmailRequest(BaseModel):
    type: str
    email: str
    data: Dict[str, Any]

class BroadcastRequest(BaseModel):
    title: str
    message: str
    targetUserId: Optional[str] = None
    type: Optional[str] = "info"
    adminEmail: str

class ImageRequest(BaseModel):
    prompt: str

# --- Helper Functions ---

def send_email_sync(to_email: str, subject: str, html_content: str):
    if not GMAIL_USER or not GMAIL_PASSWORD:
        print("❌ Gmail credentials not set")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = f"VYAAS AI Team <{GMAIL_USER}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        return False

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"status": "ok", "message": "VYAAS AI Backend is running"}

@app.post("/api/connection-details")
async def get_connection_details(request: ConnectionDetailsRequest):
    if not LIVEKIT_URL or not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(status_code=500, detail="Missing LiveKit environment variables")

    try:
        agent_name = None
        if request.room_config and "agents" in request.room_config:
            agents = request.room_config["agents"]
            if agents and len(agents) > 0:
                agent_name = agents[0].get("agent_name")

        participant_name = request.username or "user"
        participant_identity = request.username or f"voice_assistant_user_{os.urandom(4).hex()}"
        
        # Use fixed room name from env or default to ensures bridge connects to same room
        room_name = os.getenv("VYAAS_ROOM_NAME", "vyaas_assist_room")

        token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
            .with_identity(participant_identity) \
            .with_name(participant_name) \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_publish_data=True,
                can_subscribe=True,
            )) \
            .with_ttl(timedelta(seconds=3600)) # 1 hour

        # Note: roomConfig is not directly supported in the python sdk AccessToken builder in the same way as JS
        # But we can add attributes or metadata if needed. For now, we'll skip specific roomConfig 
        # as it's often used for SIP or other features. 
        # If agent dispatch is needed, it's usually handled by the agent listening to the room.

        jwt_token = token.to_jwt()

        return {
            "serverUrl": LIVEKIT_URL,
            "roomName": room_name,
            "participantName": participant_name,
            "participantToken": jwt_token,
        }

    except Exception as e:
        print(f"❌ Error creating LiveKit token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/send-email")
async def send_email_endpoint(request: EmailRequest, background_tasks: BackgroundTasks):
    if request.type == "approval":
        subject = "Payment Approved - VYAAS AI"
        html = f"""
        <div style="font-family: sans-serif; padding: 20px;">
            <h2>Payment Approved! ✅</h2>
            <p>Your payment of <b>₹{request.data.get('amount', 0)}</b> has been approved.</p>
            <p>{request.data.get('credits', 0)} credits have been added to your account.</p>
            <p>Thank you for choosing VYAAS AI!</p>
        </div>
        """
    elif request.type == "rejection":
        subject = "Payment Request Update - VYAAS AI"
        html = f"""
        <div style="font-family: sans-serif; padding: 20px;">
            <h2>Payment Request Update</h2>
            <p>Hi {request.data.get('customerName', 'User')},</p>
            <p>Your payment request for ₹{request.data.get('amount', 0)} was not approved.</p>
            <p><b>Reason:</b> {request.data.get('reason', 'Verification failed')}</p>
            <p>Please contact support if you think this is a mistake.</p>
        </div>
        """
    else:
        raise HTTPException(status_code=400, detail="Invalid email type")

    background_tasks.add_task(send_email_sync, request.email, subject, html)
    return {"success": True}

@app.post("/api/admin/broadcast")
async def broadcast_endpoint(request: BroadcastRequest, background_tasks: BackgroundTasks):
    if request.adminEmail != 'maheshwarkibehan@gmail.com':
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not initialized")

    try:
        recipients = []
        if request.targetUserId:
            # Fetch specific user
            response = supabase.table("users").select("id, email").eq("id", request.targetUserId).single().execute()
            if response.data:
                recipients.append(response.data)
        else:
            # Fetch all users
            response = supabase.table("users").select("id, email").execute()
            if response.data:
                recipients = response.data

        if not recipients:
            return {"message": "No recipients found"}

        # 1. Insert Notifications
        notifications = []
        for r in recipients:
            notifications.append({
                "user_id": r['id'],
                "title": f"📢 {request.title}",
                "message": f"✨ {request.message}",
                "type": request.type or "info",
                "is_read": False
            })
        
        supabase.table("user_notifications").insert(notifications).execute()

        # 2. Send Emails
        html_template = f"""
          <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background-color: #f4f4f5; color: #333;">
            <div style="background-color: #ffffff; padding: 40px; border-radius: 16px; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
              <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #7c3aed; margin: 0; font-size: 28px;">VYAAS AI</h1>
              </div>
              
              <h2 style="color: #1f2937; margin-top: 0;">{request.title}</h2>
              
              <div style="font-size: 16px; line-height: 1.6; color: #4b5563; margin: 20px 0;">
                {request.message.replace('\n', '<br>')}
              </div>
              
              <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 30px 0;">
              
              <div style="text-align: center; font-size: 12px; color: #9ca3af;">
                <p>&copy; 2025 VYAAS AI. All rights reserved.</p>
                <p>This is an automated message. Please do not reply.</p>
              </div>
            </div>
          </div>
        """

        for r in recipients:
            if r.get('email'):
                background_tasks.add_task(send_email_sync, r['email'], f"📢 {request.title}", html_template)

        return {"success": True, "count": len(recipients)}

    except Exception as e:
        print(f"❌ Broadcast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-image")
async def generate_image_endpoint(request: ImageRequest):
    if not request.prompt:
        raise HTTPException(status_code=400, detail="Missing prompt")
    
    if not HF_TOKEN:
        raise HTTPException(status_code=500, detail="Missing HF_TOKEN")

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2",
            headers={
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"inputs": request.prompt}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"API Error: {response.reason}")

        import base64
        base64_image = base64.b64encode(response.content).decode('utf-8')
        
        return {"imageUrl": f"data:image/png;base64,{base64_image}"}

    except Exception as e:
        print(f"❌ Image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
