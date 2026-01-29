import logging
import warnings

# Suppress all deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Configure logging to be cleaner
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
# Reduce noise from specific libraries
logging.getLogger("livekit").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("vyaas_get_weather").setLevel(logging.WARNING)
logging.getLogger("livekit.plugins.google").setLevel(logging.WARNING)
logging.getLogger("livekit.agents").setLevel(logging.WARNING)

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext, ChatMessage
from livekit.plugins import google
try:
    from livekit.plugins import noise_cancellation
except ImportError:
    noise_cancellation = None  # Optional on cloud
import asyncio
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import json

import json
import termux_compatibility as termux

# Import your custom modules
from vyaas_prompts import instructions_prompt, Reply_prompts
from vyaas_google_search import google_search, get_current_datetime
from vyaas_get_weather import get_weather
from vyaas_system_control import (
    system_shutdown,
    system_restart,
    cancel_shutdown,
    open_chrome,
    open_application,
    open_file,
    open_folder,
    lock_computer,
    set_volume,
    mute_unmute,
    take_screenshot,
    search_web,
    play_youtube
)
from vyaas_system_info import (
    get_system_info,
    get_cpu_usage,
    get_ram_usage,
    get_battery_status,
    get_disk_usage,
    get_running_processes,
    get_network_info
)
from vyaas_clipboard import (
    copy_to_clipboard,
    get_clipboard_content,
    clear_clipboard,
    clipboard_word_count
)
from vyaas_music import (
    play_spotify,
    play_youtube_music,
    play_pause_media,
    next_track,
    previous_track,
    stop_media,
    open_music_app,
    search_song
)
from vyaas_automation import (
    type_text,
    type_text_unicode,
    press_key,
    open_notepad_and_write,
    play_youtube_video,
    send_email_gmail,
    click_screen,
    scroll,
    wait_seconds,
    get_screen_size,
    focus_window,
    send_whatsapp_to_phone,
    send_whatsapp_message,
    send_instagram_message,
    send_whatsapp_file
)
from vyaas_file_tools import (
    create_html_file,
    create_text_file,
    create_excel_file,
    create_word_document,
    create_powerpoint,
    create_pdf_document,
    create_python_file,
    list_desktop_files
)
from vyaas_android import (
    pair_android_device,
    connect_android_device,
    open_android_app,
    send_android_whatsapp,
    search_and_send_android_whatsapp,
    make_android_call,
    search_android_youtube
)
from vyaas_memory import (
    remember_fact,
    get_fact,
    search_memory,
    list_all_memories,
    list_all_memories,
    delete_fact
)
import vyaas_iot
from vyaas_whatsapp_listener import (
    start_whatsapp_listener,
    check_whatsapp_messages,
    reply_to_whatsapp,
    get_whatsapp_status
)
from vyaas_maps import map_manager, show_google_map

# Local Commands (for remote execution on user's PC)
import vyaas_local_commands

from memory_loop import MemoryExtractor


load_dotenv()


class Assistant(Agent):
    def __init__(self, chat_ctx) -> None:
        super().__init__(chat_ctx = chat_ctx,
                        instructions=instructions_prompt,
                        llm=google.beta.realtime.RealtimeModel(
                            voice="Charon",
                            model="gemini-2.5-flash-native-audio-preview-12-2025",
                        ),
                        tools=[
                                google_search,
                                get_current_datetime,
                                get_weather,
                                # System Control Tools
                                system_shutdown,
                                system_restart,
                                cancel_shutdown,
                                open_chrome,
                                open_application,
                                open_file,
                                open_folder,
                                lock_computer,
                                set_volume,
                                mute_unmute,
                                take_screenshot,
                                search_web,
                                play_youtube,
                                # System Info Tools
                                get_system_info,
                                get_cpu_usage,
                                get_ram_usage,
                                get_battery_status,
                                get_disk_usage,
                                get_running_processes,
                                get_network_info,
                                # Clipboard Tools
                                copy_to_clipboard,
                                get_clipboard_content,
                                clear_clipboard,
                                clipboard_word_count,
                                # Music Tools
                                play_spotify,
                                play_youtube_music,
                                play_pause_media,
                                next_track,
                                previous_track,
                                stop_media,
                                open_music_app,
                                search_song,
                                # Automation Tools
                                type_text,
                                type_text_unicode,
                                press_key,
                                open_notepad_and_write,
                                play_youtube_video,
                                send_email_gmail,
                                click_screen,
                                scroll,
                                wait_seconds,
                                get_screen_size,
                                focus_window,
                                send_whatsapp_to_phone,
                                send_whatsapp_message,
                                send_instagram_message,
                                # File Creation Tools
                                create_html_file,
                                create_text_file,
                                create_excel_file,
                                create_word_document,
                                create_powerpoint,
                                create_pdf_document,
                                create_python_file,
                                list_desktop_files,
                                send_whatsapp_file,
                                # Android Tools
                                pair_android_device,
                                connect_android_device,
                                open_android_app,
                                send_android_whatsapp,
                                search_and_send_android_whatsapp,
                                make_android_call,
                                search_android_youtube,
                                # Memory Tools
                                remember_fact,
                                get_fact,
                                search_memory,
                                list_all_memories,
                                delete_fact,
                                # IoT Tools
                                vyaas_iot.scan_iot_devices,
                                vyaas_iot.control_iot_device,
                                vyaas_iot.set_iot_brightness,
                                # WhatsApp Listener Tools
                                start_whatsapp_listener,
                                check_whatsapp_messages,
                                reply_to_whatsapp,
                                get_whatsapp_status,
                                # Map Tools
                                show_google_map,
                                # LOCAL COMMAND TOOLS (execute on user's PC via Desktop Bridge)
                                vyaas_local_commands.open_whatsapp_local,
                                vyaas_local_commands.open_maps_local,
                                vyaas_local_commands.open_notes_local,
                                vyaas_local_commands.open_app_local,
                                vyaas_local_commands.send_whatsapp_local,
                                vyaas_local_commands.send_whatsapp_contact_local,
                                vyaas_local_commands.type_text_local,
                                vyaas_local_commands.press_key_local,
                                vyaas_local_commands.open_url_local,
                                vyaas_local_commands.play_youtube_local,
                                vyaas_local_commands.take_screenshot_local,
                                vyaas_local_commands.set_volume_local,
                                vyaas_local_commands.lock_pc_local,
                                vyaas_local_commands.shutdown_pc_local,
                                vyaas_local_commands.cancel_shutdown_local,
                        ]
                                )

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        preemptive_generation=False
    )
    
    # getting the current memory chat
    current_ctx = session.history.items
    
    # Wait for participant to connect
    await ctx.connect()

    # Start system monitoring task immediately
    asyncio.create_task(monitor_system(ctx.room, session))
    
    # Initialize Map Manager with current room
    map_manager.set_room(ctx.room)
    
    # Note: Local commands use HTTP bridge, no room initialization needed
    
    # Auto-Connect to Android (User Preference)
    async def auto_connect_android():
        if termux.is_android():
             print("Running on Android Device: connecting to local ADB...")
             # On Termux, connect to localhost
             res = await connect_android_device("localhost", "5555")
             print(f"Local Android Connect Result: {res}")
        else:
             print("Initiating Auto-Connection to Android Phone...")
             res = await connect_android_device("192.168.31.220", "36165")
             print(f"Android Auto-Connect Result: {res}")

    asyncio.create_task(auto_connect_android())

    # --- Face Intelligence Handler ---
    last_face_event = 0
    FACE_COOLDOWN = 10 # Seconds between reactions

    @ctx.room.on("data_received")
    def on_data_received(packet):
        nonlocal last_face_event
        try:
            payload = packet.data.decode('utf-8')
            data = json.loads(payload)
            
            if data.get("type") == "face_event":
                current_time = asyncio.get_event_loop().time()
                if current_time - last_face_event < FACE_COOLDOWN:
                    return

                identity = data.get("identity", "Unknown")
                emotion = data.get("emotion", "neutral")
                
                # Logic: Intruder Alert
                if identity == "Unknown":
                    print(f"⚠️ INTRUDER DETECTED! Emotion: {emotion}")
                    last_face_event = current_time
                    asyncio.create_task(session.generate_reply(
                        instructions=f"WARNING: An unknown face is detected! User is not 'Bhaiya'. Ask 'Kaun ho tum?'. Be suspicious. Current emotion: {emotion}"
                    ))
                
                # Logic: Empathy (Only for Bhaiya)
                elif identity == "Bhaiya":
                    if emotion == "sad":
                        print(f"💙 Empathy Trigger: Bhaiya is sad.")
                        last_face_event = current_time
                        asyncio.create_task(session.generate_reply(
                            instructions="Bhaiya looks sad. Stop everything. Speak in a very soft, comforting, 'Chhota Bhai' voice. Ask 'Kya hua Bhaiya? Aap pareshan lag rahe ho?'. Offer to play music."
                        ))
                    elif emotion == "happy":
                         # Maybe just a log or rare compliment
                         pass

        except Exception as e:
            print(f"Data processing error: {e}")

    # Load recent history logic
    try:
        from memory_store import ConversationMemory
        # Get participant identity
        participant = ctx.room.participants.values().__iter__().__next__()
        identity = participant.identity
        
        # Load last 10 messages for context
        memory = ConversationMemory(identity)
        recent_messages = memory.get_recent_context(max_messages=10)
        
        if recent_messages:
            # Convert dictionary messages back to ChatMessage objects if needed
            # Or simpler: Append to initial context string
            history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages if 'content' in msg])
            
            # Inject history as system context
            initial_ctx = ChatMessage(
                role="system",
                content=f"Previous conversation context:\n{history_text}"
            )
            current_ctx.append(initial_ctx)
            print(f"Loaded {len(recent_messages)} messages from history for {identity}")
            
    except Exception as e:
        print(f"Error loading history: {e}")

    await session.start(
        room=ctx.room,
        agent=Assistant(chat_ctx=current_ctx), #sending currenet chat to llm in realtime
        room_input_options=RoomInputOptions(
            audio_enabled=True,
            video_enabled=True,  # 🎥 Enable screen share vision!
        ),
    )

    # Wait for session to be ready
    await asyncio.sleep(3)

    try:
        await session.generate_reply(
            instructions=Reply_prompts
        )
    except RuntimeError as e:
        print(f"Session not ready yet: {e}")
    
    # Get user identity from room participants
    user_identity = "anonymous"
    for participant in ctx.room.remote_participants.values():
        if participant.identity:
            user_identity = participant.identity
            break
    
    conv_ctx = MemoryExtractor()
    await conv_ctx.run(current_ctx, user_identity)

async def monitor_system(room, session):
    """
    Background task to broadcast system metrics to the room
    And trigger alerts if thresholds are exceeded.
    """
    import psutil
    import json
    import time
    
    print("Starting system monitoring task...")
    
    # Thresholds
    CPU_THRESHOLD = 90
    RAM_THRESHOLD = 90
    DISK_THRESHOLD = 90
    
    # State tracking
    last_alert_time = 0
    ALERT_COOLDOWN = 60  # seconds
    
    while True:
        try:
            # CPU & RAM
            cpu_percent = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()

            if termux.is_android():
                # Check internal storage on Android
                disk = psutil.disk_usage('/data/data/com.termux/files/home')
            else:
                disk = psutil.disk_usage('C:/')
            
            # Top Processes
            processes = []
            high_usage_app = None
            cpu_count = psutil.cpu_count() or 1
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    # Normalize CPU usage by core count to keep it under 100%
                    raw_cpu = pinfo['cpu_percent'] or 0
                    normalized_cpu = raw_cpu / cpu_count
                    pinfo['cpu_percent'] = round(normalized_cpu, 1)
                    
                    processes.append(pinfo)
                    
                    # Check for individual app high usage (>80%) - INCREASED LIMIT
                    if normalized_cpu > 80 and pinfo['name'].lower() != "python.exe" and pinfo['name'] != "System Idle Process":
                         if high_usage_app is None or normalized_cpu > (high_usage_app['cpu_percent']):
                             high_usage_app = pinfo
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                     pass
            
            # Sort by CPU and top 5
            top_processes = sorted(processes, key=lambda x: (x['cpu_percent'] or 0), reverse=True)[:5]
            
            payload = {
                "type": "system_metrics",
                "cpu": cpu_percent,
                "memory": ram.percent,
                "disk": disk.percent,
                "processes": top_processes
            }
            
            # Broadcast metrics
            try:
                await room.local_participant.publish_data(
                    json.dumps(payload),
                    topic="system_metrics"
                )
            except Exception:
                pass

            # --- ALERT LOGIC ---
            current_time = time.time()
            if current_time - last_alert_time > ALERT_COOLDOWN:
                alert_msg = ""
                
                if cpu_percent > CPU_THRESHOLD:
                    alert_msg += f"Arre Bhaiya! CPU {cpu_percent}% pahunch gaya hai! PC garam ho raha hai! "
                if ram.percent > RAM_THRESHOLD:
                    alert_msg += f"Bhaiya, RAM {ram.percent}% full ho gayi hai! Thoda load kam kigiye na. "
                if disk.percent > DISK_THRESHOLD:
                    alert_msg += f"Bhaiya, Disk almost full hai ({disk.percent}%)! Kuch delete karna padega. "
                if high_usage_app:
                    alert_msg += f"Dekho Bhaiya! Ye {high_usage_app['name']} {high_usage_app['cpu_percent']}% CPU kha raha hai! Isko band karoon kya? "
                
                if alert_msg:
                    print(f"TRIGGERING ALERT: {alert_msg}")
                    last_alert_time = current_time
                    
                    # 1. Send Visual Alert to Frontend
                    try:
                        alert_payload = {
                            "type": "system_alert",
                            "message": alert_msg
                        }
                        await room.local_participant.publish_data(
                            json.dumps(alert_payload),
                            topic="system_alert" # Dedicated topic
                        )
                    except Exception:
                        pass
                        
                    # 2. Trigger AI Speech
                    # We inject a system instruction telling the AI to speak the warning
                    try:
                        # Force the AI to speak this warning immediately
                        # IMPORTANT: Explicitly forbid greeting here
                        await session.generate_reply(
                            instructions=f"URGENT: Speak this system warning to the user immediately in Hinglish. Do NOT say hello or introduce yourself. Just say the warning: {alert_msg}"
                        )
                    except Exception as e:
                        print(f"Failed to trigger voice alert: {e}")

        except Exception as e:
            print(f"Error in monitor_system: {e}")
            
        await asyncio.sleep(2) # Update every 2 seconds
    

# Health Check Server for Render
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "ok", "service": "VYAAS AI Agent"}')
    
    def log_message(self, format, *args):
        pass  # Suppress logs

def start_health_server():
    port = int(os.getenv('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    print(f"Health server running on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    # Fix for Python 3.10+ asyncio event loop compatibility
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    
    # Start health check server in background thread
    health_thread = Thread(target=start_health_server, daemon=True)
    health_thread.start()
    

    # Start LiveKit agent
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))


    