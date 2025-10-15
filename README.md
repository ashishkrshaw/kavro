# Kavro

End-to-End Encrypted Messaging Backend

---

## Overview

Kavro is a backend service that provides secure message exchange using public-key cryptography. Messages are encrypted on the client side before transmission, ensuring that the server cannot access message content at any point.

This implementation follows the same security principles used in production messaging applications such as WhatsApp and Signal.

---

## System Requirements

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.10+ | Runtime environment |
| PostgreSQL | 14+ | Primary data storage |
| Redis | 6+ | Rate limiting and caching |

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   Server    │────▶│  Database   │
│             │     │  (FastAPI)  │     │ (PostgreSQL)│
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       │                   ▼
       │            ┌─────────────┐
       │            │    Redis    │
       │            │ (Rate Limit)│
       │            └─────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────┐
│                  Message Flow                        │
├──────────────────────────────────────────────────────┤
│  1. Sender retrieves recipient's public key          │
│  2. Sender encrypts message using public key         │
│  3. Server stores encrypted message (ciphertext)    │
│  4. Recipient retrieves encrypted message           │
│  5. Recipient decrypts using their private key      │
└─────────────────────────────────────────────────────┘
```

---

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/ashishkrshaw/Kavro.git
cd Kavro
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
```

Activate the environment:

| Operating System | Command |
|------------------|---------|
| Windows | `venv\Scripts\activate` |
| Linux / macOS | `source venv/bin/activate` |

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/kavro
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=10080
REDIS_URL=redis://localhost:6379
```

| Variable | Description |
|----------|-------------|
| DATABASE_URL | PostgreSQL connection string |
| SECRET_KEY | JWT signing key |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token validity period |
| REDIS_URL | Redis connection string |

### Step 5: Start Server

```bash
uvicorn app.main:app --reload
```

Server will be available at `http://localhost:8000`

---

## API Reference

### Authentication

| Endpoint         | Method | Description |
|----------------- |--------|-------------|
| `/auth/register` | POST | Create new user account |
| `/auth/login`    | POST | Authenticate and receive JWT token |

### Key Management

| Endpoint         | Method | Description |
|----------------- |--------|-------------|
| `/keys/publish`  | POST | Upload user's public key |
| `/keys/{user_id}` | GET | Retrieve public key of specified user |

### Messaging

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/messages/` | POST | Send encrypted message |
| `/messages/inbox` | GET | Retrieve received messages |

---

## Project Structure

```
kavro/
├── app/
│   ├── main.py              # Application entry point
│   ├── models.py            # Database schema definitions
│   ├── schemas.py           # Request/Response models
│   │
│   ├── api/
│   │   ├── auth.py          # Authentication handlers
│   │   ├── keys.py          # Key exchange handlers
│   │   └── messages.py      # Message handlers
│   │
│   ├── core/
│   │   ├── config.py        # Configuration management
│   │   ├── security.py      # Cryptographic utilities
│   │   └── rate_limiter.py  # Request throttling
│   │
│   └── db/
│       ├── base.py          # Database metadata
│       └── session.py       # Connection management
│
├── requirements.txt         # Python dependencies
├── Procfile                 # Deployment configuration
└── .env                     # Environment variables
```

---

## Security Implementation

### Password Storage

User passwords are hashed using bcrypt algorithm before storage. Plain text passwords are never stored in the database.

### Token Authentication

JWT (JSON Web Token) is used for session management. Tokens are signed using HS256 algorithm and include expiration timestamps.

### Rate Limiting

Redis-based rate limiting is implemented to prevent brute force attacks and API abuse. Default limit: 60 requests per minute per user.

### Data Protection

The server stores only encrypted message content. Decryption keys are never transmitted to or stored on the server.

---

## Development

### Running Tests

```bash
pytest
```

### API Documentation

Interactive documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Demo Client

A Python client is included to demonstrate the complete E2EE flow.

### Prerequisites

```bash
pip install requests pynacl
```

### Usage

```bash
cd client
python demo_client.py
```

### What It Does

| Step | Action |
|------|--------|
| 1 | Registers/logs in two test users (Alice and Bob) |
| 2 | Generates NaCl key pairs for both users |
| 3 | Publishes public keys to the server |
| 4 | Alice encrypts a message for Bob |
| 5 | Sends encrypted message through server |
| 6 | Bob retrieves and decrypts the message |

### Client Structure

```
client/
├── demo_client.py       # Main demo script
└── keys/                # Generated key pairs (local storage)
    ├── alice_demo_priv.hex
    ├── alice_demo_pub.hex
    ├── bob_demo_priv.hex
    └── bob_demo_pub.hex
```

### Key Functions

| Function | Description |
|----------|-------------|
| `gen_identity_keypair()` | Generate Curve25519 key pair |
| `encrypt_for_recipient()` | Encrypt using NaCl Box |
| `decrypt_for_recipient()` | Decrypt using private key |
| `publish_key()` | Upload public key to server |
| `send_message()` | Send encrypted message |
| `fetch_inbox()` | Retrieve encrypted messages |

---

## Deployment

Refer to the deployment guide for production setup instructions including:

- EC2 instance configuration
- PostgreSQL installation
- Nginx reverse proxy setup
- SSL certificate installation

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Submit a pull request

Please ensure all tests pass before submitting.

---

## License

This project is licensed under the MIT License.

---

## Author

**Ashish Kumar Shaw**

- GitHub: https://github.com/ashishkrshaw
- LinkedIn: https://www.linkedin.com/in/asksaw/

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-10 | Initial release |
