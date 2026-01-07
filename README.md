# Kavro

A secure messaging API with end-to-end encryption. Messages are encrypted on your device before they ever leave - the server never sees what you're sending.

Built with FastAPI, PostgreSQL, and Redis.

## What's This?

Kavro is a backend for encrypted messaging apps. Think of it like the server part of Signal or WhatsApp, but simpler and open source.

```
Your app encrypts message → sends to Kavro → recipient fetches → their app decrypts
```

The server just stores encrypted blobs. It can't read your messages even if it wanted to.

## Is This Real E2EE?

**Yes.** This is a real end-to-end encryption implementation, not a mock or demo.

**How it works:**
1. Each user generates a keypair (public + private) on their device
2. User uploads their public key to Kavro
3. When Alice wants to message Bob, she fetches Bob's public key
4. Alice encrypts the message with Bob's public key (using NaCl/libsodium)
5. Alice sends the encrypted blob to Kavro
6. Bob fetches the blob and decrypts it with his private key

**What the server sees:** Encrypted bytes. Nothing readable.

**What the server stores:**
- Public keys (meant to be public anyway)
- Encrypted message blobs
- User accounts and metadata

**What the server CANNOT do:**
- Read message content
- Decrypt messages
- Forge messages from users

The crypto is done client-side. The server is just a relay and storage layer.

---

## Connecting Your Frontend

Here's how to integrate Kavro with any frontend (React, Vue, mobile app, etc.):

### Step 1: Install a crypto library

```bash
# JavaScript/TypeScript
npm install tweetnacl tweetnacl-util

# Python
pip install pynacl

# React Native / Mobile
npm install react-native-nacl-jsi
```

### Step 2: Generate keypair on user signup

```javascript
// JavaScript example
import nacl from 'tweetnacl';
import { encodeBase64, decodeBase64 } from 'tweetnacl-util';

// Generate keypair (store private key securely on device!)
const keypair = nacl.box.keyPair();
const publicKey = encodeBase64(keypair.publicKey);
const privateKey = encodeBase64(keypair.secretKey); // NEVER send this to server
```

### Step 3: Register and publish public key

```javascript
// Register user
const response = await fetch('https://your-kavro-server.com/api/v1/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'alice', password: 'SecurePass123' })
});
const { access_token } = await response.json();

// Publish public key
await fetch('https://your-kavro-server.com/api/v1/keys/publish', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${access_token}`
  },
  body: JSON.stringify({ identity_pubkey: publicKey, device_name: 'iPhone' })
});
```

### Step 4: Send encrypted message

```javascript
import nacl from 'tweetnacl';

async function sendMessage(recipientId, messageText, token) {
  // 1. Get recipient's public key
  const keysRes = await fetch(`https://your-kavro-server.com/api/v1/keys/${recipientId}`);
  const { devices } = await keysRes.json();
  const recipientPubKey = decodeBase64(devices[0].identity_pubkey);

  // 2. Encrypt message
  const messageBytes = new TextEncoder().encode(messageText);
  const ephemeralKeypair = nacl.box.keyPair();
  const nonce = nacl.randomBytes(24);
  const encrypted = nacl.box(messageBytes, nonce, recipientPubKey, ephemeralKeypair.secretKey);

  // 3. Package and send
  const ciphertext = encodeBase64(new Uint8Array([...nonce, ...encrypted]));

  await fetch('https://your-kavro-server.com/api/v1/messages/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      recipient_id: recipientId,
      ciphertext: ciphertext,
      ephemeral_pubkey: encodeBase64(ephemeralKeypair.publicKey)
    })
  });
}
```

### Step 5: Receive and decrypt messages

```javascript
async function getMessages(token, myPrivateKey) {
  const res = await fetch('https://your-kavro-server.com/api/v1/messages/inbox', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const { messages } = await res.json();

  return messages.map(msg => {
    const data = decodeBase64(msg.ciphertext);
    const nonce = data.slice(0, 24);
    const encrypted = data.slice(24);
    const senderPubKey = decodeBase64(msg.ephemeral_pubkey);

    const decrypted = nacl.box.open(encrypted, nonce, senderPubKey, myPrivateKey);
    return new TextDecoder().decode(decrypted);
  });
}
```

### Demo Client

Check `client/demo_client.py` for a working Python implementation.

---

## Quick Start

### With Docker (easiest)

```bash
git clone https://github.com/ashishkrshaw/kavro.git
cd kavro

cp .env.docker.example .env
nano .env  # change the passwords!

docker-compose up -d

curl http://localhost:8000/health
```

### Without Docker

```bash
git clone https://github.com/ashishkrshaw/kavro.git
cd kavro

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
nano .env  # add your database URL

uvicorn app.main:app --reload
```

Open http://localhost:8000/docs to see the API.

## Environment Variables

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/kavro
SECRET_KEY=some-long-random-string
REDIS_URL=redis://localhost:6379
```

Generate a secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## API Overview

| Endpoint | What it does |
|----------|--------------|
| `POST /api/v1/auth/register` | Create account |
| `POST /api/v1/auth/login` | Get token |
| `GET /api/v1/auth/me` | Current user |
| `POST /api/v1/keys/publish` | Upload public key |
| `GET /api/v1/keys/{user_id}` | Get public key |
| `POST /api/v1/messages/` | Send encrypted message |
| `GET /api/v1/messages/inbox` | Get messages |
| `GET /health` | Health check |

Full docs at http://localhost:8000/docs

## Running Tests

```bash
pip install -r requirements-test.txt
pytest app/tests/ -v
```

All 25 tests pass.

## Security Features

- E2EE with NaCl (libsodium)
- Passwords hashed with bcrypt
- JWT tokens for auth
- Rate limiting
- Brute force protection
- OWASP security headers

## Deploying

See [docs/EC2_DEPLOYMENT.md](docs/EC2_DEPLOYMENT.md) for EC2 + HTTPS setup.

```bash
docker pull ashishkrshaw/kavro-api:latest
docker-compose up -d
```

## Tech Stack

- Python 3.10+, FastAPI
- PostgreSQL (async), Redis
- NaCl/libsodium for crypto
- Docker

## License

MIT

## Author

Ashish Kumar Shaw - [@ashishkrshaw](https://github.com/ashishkrshaw)
