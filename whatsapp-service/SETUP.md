# WhatsApp Listener Setup Guide

## Prerequisites
1. **Node.js 18+** installed (check with `node --version`)
2. **WhatsApp Desktop** or phone with WhatsApp

## Installation Steps

### Step 1: Open Terminal in WhatsApp Service Folder
```powershell
cd C:\Users\mahes\OneDrive\Desktop\vyaasaiupdated\Backend\whatsapp-service
```

### Step 2: Install Dependencies
```powershell
# If normal install fails, try these alternatives:

# Option A: Skip Chromium download (use existing Chrome)
$env:PUPPETEER_SKIP_CHROMIUM_DOWNLOAD = "true"
npm install

# Option B: Use npm with specific registry
npm install --registry https://registry.npmjs.org/

# Option C: Install packages one by one
npm install express@4.18.2
npm install qrcode-terminal@0.12.0
npm install whatsapp-web.js@1.23.0
npm install puppeteer@21.0.0
```

### Step 3: Start the WhatsApp Service
```powershell
npm start
```

### Step 4: Scan QR Code
- A QR code will appear in the terminal
- Open WhatsApp on your phone
- Go to **Settings → Linked Devices → Link a Device**
- Scan the QR code

### Step 5: Test the Service
Once connected, you can test by visiting:
- Health check: http://localhost:3001/health
- Should show: `{"status":"ok","ready":true}`

---

## Using with VYAAS AI

Once the WhatsApp service is running, tell VYAAS:
- **"Start WhatsApp listener"** - Initializes the listener
- **"Check WhatsApp messages"** - Checks for new messages
- **"Reply to [phone number] saying [message]"** - Sends a reply
- **"WhatsApp status"** - Checks connection status

---

## Troubleshooting

### If npm install fails:
1. Try running PowerShell as Administrator
2. Clear npm cache: `npm cache clean --force`
3. Try installing puppeteer separately: `npm install puppeteer`

### If Chromium download fails:
Set environment variable to use your existing Chrome:
```powershell
$env:PUPPETEER_EXECUTABLE_PATH = "C:\Program Files\Google\Chrome\Application\chrome.exe"
npm start
```

### If QR code doesn't appear:
- Check if port 3001 is available
- Try restarting the service
