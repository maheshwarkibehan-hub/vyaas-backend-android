/**
 * VYAAS WhatsApp Service
 * Secure WhatsApp message listener using whatsapp-web.js
 * 
 * Security Features:
 * - Binds to localhost only (not exposed to network)
 * - No external API calls with message content
 * - Session stored locally only
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');

const app = express();
app.use(express.json());

// Configuration
const PORT = process.env.WHATSAPP_SERVICE_PORT || 3001;
const HOST = '127.0.0.1'; // Localhost only - SECURITY

// Store for pending messages to be fetched by Python
let pendingMessages = [];
let isReady = false;
let qrCodeData = null;

// Initialize WhatsApp Client with Local Authentication
const client = new Client({
    authStrategy: new LocalAuth({
        dataPath: './.wwebjs_auth'
    }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ]
    }
});

// QR Code Event - Display in terminal for scanning
client.on('qr', (qr) => {
    console.log('\n📱 Scan this QR code with WhatsApp:\n');
    qrcode.generate(qr, { small: true });
    qrCodeData = qr;
});

// Ready Event - WhatsApp connected
client.on('ready', () => {
    console.log('\n✅ WhatsApp Client is ready!');
    console.log('🔒 Listening for messages securely on localhost...\n');
    isReady = true;
    qrCodeData = null;
});

// Authentication Success
client.on('authenticated', () => {
    console.log('🔐 WhatsApp authenticated successfully');
});

// Authentication Failure
client.on('auth_failure', (msg) => {
    console.error('❌ Authentication failed:', msg);
});

// Disconnected
client.on('disconnected', (reason) => {
    console.log('📴 WhatsApp disconnected:', reason);
    isReady = false;
});

// Message Event - New incoming message
client.on('message', async (message) => {
    try {
        // Get contact info
        const contact = await message.getContact();
        const chat = await message.getChat();

        // Create message object
        const msgData = {
            id: message.id._serialized,
            from: message.from,
            contactName: contact.pushname || contact.name || message.from,
            body: message.body,
            timestamp: message.timestamp,
            isGroup: chat.isGroup,
            groupName: chat.isGroup ? chat.name : null,
            hasMedia: message.hasMedia,
            type: message.type
        };

        // Add to pending messages queue
        pendingMessages.push(msgData);

        console.log(`📩 New message from ${msgData.contactName}: ${msgData.body.substring(0, 50)}...`);

        // Keep only last 50 messages in queue
        if (pendingMessages.length > 50) {
            pendingMessages = pendingMessages.slice(-50);
        }
    } catch (error) {
        console.error('Error processing message:', error);
    }
});

// ============== HTTP API Endpoints ==============

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        ready: isReady,
        hasQR: qrCodeData !== null,
        pendingMessages: pendingMessages.length
    });
});

// Get QR code for scanning (if needed)
app.get('/qr', (req, res) => {
    if (qrCodeData) {
        res.json({ qr: qrCodeData });
    } else if (isReady) {
        res.json({ message: 'Already authenticated', ready: true });
    } else {
        res.json({ message: 'Waiting for QR code...', ready: false });
    }
});

// Get pending messages (Python will poll this)
app.get('/messages', (req, res) => {
    const messages = [...pendingMessages];
    pendingMessages = []; // Clear after fetching
    res.json({ messages });
});

// Send a message
app.post('/send', async (req, res) => {
    try {
        const { to, message } = req.body;

        if (!to || !message) {
            return res.status(400).json({ error: 'Missing "to" or "message" field' });
        }

        if (!isReady) {
            return res.status(503).json({ error: 'WhatsApp not ready' });
        }

        // Format phone number (add @c.us if not present)
        let chatId = to;
        if (!chatId.includes('@')) {
            chatId = `${to.replace(/\D/g, '')}@c.us`;
        }

        await client.sendMessage(chatId, message);

        console.log(`📤 Sent message to ${to}`);
        res.json({ success: true, to, message });
    } catch (error) {
        console.error('Error sending message:', error);
        res.status(500).json({ error: error.message });
    }
});

// Reply to a specific message
app.post('/reply', async (req, res) => {
    try {
        const { messageId, reply } = req.body;

        if (!messageId || !reply) {
            return res.status(400).json({ error: 'Missing "messageId" or "reply" field' });
        }

        if (!isReady) {
            return res.status(503).json({ error: 'WhatsApp not ready' });
        }

        // Get the message and reply to it
        const msg = await client.getMessageById(messageId);
        if (msg) {
            await msg.reply(reply);
            console.log(`↩️ Replied to message`);
            res.json({ success: true });
        } else {
            res.status(404).json({ error: 'Message not found' });
        }
    } catch (error) {
        console.error('Error replying:', error);
        res.status(500).json({ error: error.message });
    }
});

// Get recent chats
app.get('/chats', async (req, res) => {
    try {
        if (!isReady) {
            return res.status(503).json({ error: 'WhatsApp not ready' });
        }

        const chats = await client.getChats();
        const chatList = chats.slice(0, 20).map(chat => ({
            id: chat.id._serialized,
            name: chat.name,
            isGroup: chat.isGroup,
            unreadCount: chat.unreadCount
        }));

        res.json({ chats: chatList });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// ============== Start Server ==============

app.listen(PORT, HOST, () => {
    console.log('╔═══════════════════════════════════════════════╗');
    console.log('║     VYAAS WhatsApp Service                     ║');
    console.log('╠═══════════════════════════════════════════════╣');
    console.log(`║ 🔒 Server running on http://${HOST}:${PORT}     ║`);
    console.log('║ 🛡️  Localhost only - Secure mode              ║');
    console.log('╚═══════════════════════════════════════════════╝');
    console.log('\n⏳ Initializing WhatsApp client...\n');
});

// Initialize WhatsApp client
client.initialize();

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down...');
    await client.destroy();
    process.exit(0);
});
