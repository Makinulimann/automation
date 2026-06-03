const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode-terminal');
const express = require('express');
const pino = require('pino');
require('dotenv').config();

const app = express();
app.use(express.json());

const PORT = process.env.WA_BOT_PORT || 3000;

let sock = null; // Global socket reference
let isConnected = false; // Track WA connection state
let currentQR = null; // Store current QR for GUI display

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys');

    sock = makeWASocket({
        auth: state,
        printQRInTerminal: false, // kita handle sendiri via qrcode-terminal
        logger: pino({ level: 'silent' }) // suppress verbose logs
    });

    // Event: Connection Update (QR Code, connected, disconnected)
    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            currentQR = qr;
            console.log('\n=========================================');
            console.log('SCAN QR CODE INI MENGGUNAKAN WHATSAPP ANDA');
            console.log('(Buka WhatsApp > Menu > Perangkat Tertaut > Tautkan Perangkat)');
            console.log('=========================================');
            qrcode.generate(qr, { small: true });
        }

        if (connection === 'close') {
            isConnected = false;
            currentQR = null;
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('[INFO] Koneksi terputus. Alasan:', lastDisconnect?.error?.message || 'Unknown');
            if (shouldReconnect) {
                console.log('[INFO] Mencoba reconnect...');
                connectToWhatsApp();
            } else {
                console.log('[INFO] Anda sudah logged out. Hapus folder auth_info_baileys dan jalankan ulang.');
            }
        } else if (connection === 'open') {
            isConnected = true;
            currentQR = null;
            console.log('\n[INFO] ✅ WhatsApp Bot TERHUBUNG dan SIAP menerima request!');
        }
    });

    // Event: Simpan credentials setiap kali ada update
    sock.ev.on('creds.update', saveCreds);
}

// Endpoint: Health check / status untuk GUI
app.get('/status', (req, res) => {
    res.json({
        connected: isConnected,
        qr: currentQR,
        uptime: process.uptime()
    });
});

// Endpoint untuk menerima HTTP POST Request dari Python
app.post('/send-message', async (req, res) => {
    const { number, message } = req.body;

    if (!number || !message) {
        return res.status(400).json({ error: 'Field "number" dan "message" wajib diisi.' });
    }

    if (!sock) {
        return res.status(503).json({ error: 'WhatsApp belum terhubung. Silakan scan QR terlebih dahulu.' });
    }

    try {
        // Format nomor: pastikan menggunakan format @s.whatsapp.net
        // Input bisa berupa "6285xxx@c.us" atau "6285xxx" atau "6285xxx@s.whatsapp.net"
        let jid = number;
        if (jid.endsWith('@c.us')) {
            jid = jid.replace('@c.us', '@s.whatsapp.net');
        } else if (!jid.includes('@')) {
            jid = jid + '@s.whatsapp.net';
        }

        console.log(`\n[INFO] Mengirim pesan ke ${jid}...`);
        await sock.sendMessage(jid, { text: message });
        console.log(`[BERHASIL] ✅ Pesan terkirim ke ${jid}`);
        res.status(200).json({ success: true, message: 'Pesan terkirim!' });
    } catch (error) {
        console.error(`[GAGAL] ❌ Mengirim pesan: ${error.message}`);
        res.status(500).json({ error: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`\n=========================================`);
    console.log(`Webhook Server berjalan di http://localhost:${PORT}`);
    console.log(`=========================================\n`);
    connectToWhatsApp();
});
