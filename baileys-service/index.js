import makeWASocket, {
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
} from '@whiskeysockets/baileys'
import { Boom } from '@hapi/boom'
import express from 'express'
import QRCode from 'qrcode'
import pino from 'pino'
import https from 'https'
import http from 'http'

const logger = pino({ level: 'silent' })
const app = express()
app.use(express.json())

const PORT = process.env.PORT || 3000
const BOT_WEBHOOK_URL = process.env.BOT_WEBHOOK_URL || 'http://localhost:8000/webhook/whatsapp'

let currentQR = null
let sock = null
let isConnected = false
let isReconnecting = false
let reconnectAttempts = 0
const MAX_RECONNECT_DELAY = 60000 // 60 segundos

async function forwardToBotWebhook(msg) {
  const text =
    msg.message?.conversation ||
    msg.message?.extendedTextMessage?.text ||
    null

  if (!text) return

  const payload = JSON.stringify({
    event: 'messages.upsert',
    instance: 'baileys',
    data: {
      key: {
        remoteJid: msg.key.remoteJid,
        fromMe: msg.key.fromMe ?? false,
        id: msg.key.id,
      },
      message: {
        conversation: msg.message?.conversation ?? null,
        extendedTextMessage: msg.message?.extendedTextMessage ?? null,
      },
      messageType: msg.message?.conversation ? 'conversation' : 'extendedTextMessage',
      pushName: msg.pushName ?? null,
    },
  })

  const url = new URL(BOT_WEBHOOK_URL)
  const transport = url.protocol === 'https:' ? https : http

  const options = {
    hostname: url.hostname,
    port: url.port || (url.protocol === 'https:' ? 443 : 80),
    path: url.pathname,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(payload),
    },
  }

  return new Promise((resolve) => {
    const req = transport.request(options, (res) => {
      console.log(`[webhook] forwarded msg → bot responded ${res.statusCode}`)
      resolve()
    })
    req.on('error', (e) => console.error('[webhook] forward error:', e.message))
    req.write(payload)
    req.end()
  })
}

async function startSocket() {
  const { state, saveCreds } = await useMultiFileAuthState('./auth_info')
  const { version } = await fetchLatestBaileysVersion()

  sock = makeWASocket({
    version,
    logger,
    auth: state,
    printQRInTerminal: true,
    markOnlineOnConnect: false,
    getMessage: async () => undefined,
  })

  sock.ev.on('connection.update', ({ connection, lastDisconnect, qr }) => {
    if (qr) {
      currentQR = qr
      console.log('[baileys] QR atualizado — acesse GET /qrcode')
    }

    if (connection === 'close') {
      isConnected = false
      currentQR = null
      const code = (lastDisconnect?.error)?.output?.statusCode
      const shouldReconnect = code !== DisconnectReason.loggedOut
      console.log(`[baileys] conexão fechada (código ${code}), reconectando: ${shouldReconnect}`)
      if (shouldReconnect && !isReconnecting) {
        isReconnecting = true
        reconnectAttempts++
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts - 1), MAX_RECONNECT_DELAY)
        console.log(`[baileys] tentativa ${reconnectAttempts} de reconexão em ${delay}ms`)
        setTimeout(() => {
          startSocket()
        }, delay)
      }
    }

    if (connection === 'open') {
      isConnected = true
      isReconnecting = false
      reconnectAttempts = 0
      currentQR = null
      console.log('[baileys] conectado ao WhatsApp!')
    }
  })

  sock.ev.on('creds.update', saveCreds)

  sock.ev.on('messages.upsert', async ({ messages, type }) => {
    if (type !== 'notify') return
    for (const msg of messages) {
await forwardToBotWebhook(msg)
    }
  })
}

// GET /qrcode — retorna QR como imagem PNG
app.get('/qrcode', async (req, res) => {
  if (isConnected) {
    return res.status(200).json({ status: 'connected' })
  }
  if (!currentQR) {
    return res.status(503).json({ status: 'waiting_qr', message: 'QR ainda não gerado, aguarde...' })
  }
  try {
    const png = await QRCode.toBuffer(currentQR, { type: 'png', width: 300 })
    res.setHeader('Content-Type', 'image/png')
    res.send(png)
  } catch (e) {
    res.status(500).json({ error: 'Falha ao gerar QR' })
  }
})

// POST /send — envia mensagem via WhatsApp
// Body: { "number": "5511999999999@g.us", "text": "Olá!" }
app.post('/send', async (req, res) => {
  const { number, text } = req.body
  if (!number || !text) {
    return res.status(400).json({ error: 'number e text são obrigatórios' })
  }
  if (!isConnected || !sock) {
    return res.status(503).json({ error: 'WhatsApp não conectado' })
  }
  try {
    await sock.sendMessage(number, { text })
    res.json({ status: 'sent' })
  } catch (e) {
    console.error('[send] erro:', e.message)
    res.status(500).json({ error: e.message })
  }
})

// GET /health
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', connected: isConnected })
})

app.listen(PORT, () => {
  console.log(`[baileys-service] rodando na porta ${PORT}`)
  startSocket()
})
