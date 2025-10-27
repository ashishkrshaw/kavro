# Kavro

A production-ready End-to-End Encrypted (E2EE) messaging backend built with FastAPI.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Overview

Kavro implements secure message exchange using public-key cryptography. Messages are encrypted client-side before transmission, ensuring the server never has access to plaintext content.

This project demonstrates:
- RESTful API design with FastAPI
- Async database operations with SQLAlchemy + asyncpg
- JWT-based authentication
- OWASP security best practices
- Docker containerization

## Features

| Feature | Description |
|---------|-------------|
| E2EE Messaging | Public/private key encryption (NaCl) |
| Secure Auth | JWT tokens + bcrypt password hashing |
| Brute Force Protection | Account lockout after failed attempts |
| Rate Limiting | Redis-based request throttling |
| Field Encryption | Fernet encryption for sensitive data |
| Security Headers | HSTS, CSP, X-Frame-Options |
| Audit Logging | Security event tracking |
| Docker Support | Multi-container deployment |

## Tech Stack

- **Backend**: Python 3.10+, FastAPI
- **Database**: PostgreSQL (async with asyncpg)
- **Cache**: Redis
- **Auth**: JWT (python-jose), bcrypt (passlib)
- **Encryption**: PyNaCl, Fernet

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 6+

### Installation

```bash
git clone https://github.com/ashishkrshaw/kavro.git
cd kavro
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

Create `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/kavro
SECRET_KEY=your_secure_random_string
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REDIS_URL=redis://localhost:6379
```

### Run

```bash
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Create account |
| POST | /auth/login | Get JWT token |
| GET | /auth/me | Get current user |

### Keys

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /keys/publish | Upload public key |
| GET | /keys/{user_id} | Get user's public keys |

### Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /messages/ | Send encrypted message |
| GET | /messages/inbox | Get received messages |
| POST | /messages/{id}/ack | Mark as delivered |

## Project Structure

```
kavro/
├── app/
│   ├── api/           # Route handlers
│   ├── core/          # Security, config, middleware
│   ├── db/            # Database setup
│   ├── main.py        # App entry point
│   ├── models.py      # DB tables
│   └── schemas.py     # Pydantic models
├── client/            # Demo client
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Docker Deployment

```bash
docker-compose up --build
```

Services:
- API: http://localhost:8000
- PostgreSQL: Internal
- Redis: Internal

## Security

This project implements **OWASP Top 10** security best practices:

### SQL Injection Prevention

All database queries use **SQLAlchemy ORM with parameterized queries**:

```python
# Safe - parameterized query (used in this project)
q = sa.select(users).where(users.c.username == payload.username)

# Unsafe - raw SQL (NOT used)
# cursor.execute(f"SELECT * FROM users WHERE username = '{input}'")
```

**Protection**: User input is automatically escaped by SQLAlchemy, preventing injection attacks.

### Authentication & Session Security

| Protection | Implementation |
|------------|----------------|
| Password Hashing | bcrypt with salt rounds |
| Token Auth | JWT with expiration |
| Brute Force | Account lockout after 5 failed attempts |
| Session Timeout | Configurable token expiry |

### Input Validation

All inputs validated using **Pydantic** schemas:

```python
# Username: alphanumeric, 3-50 chars
# Password: 8+ chars, uppercase, lowercase, digit, special char
```

### Rate Limiting

Redis-based throttling per endpoint:

| Endpoint | Limit | Window |
|----------|-------|--------|
| /auth/register | 3 requests | 1 hour |
| /auth/login | 5 requests | 15 min |
| /messages/ | 30 requests | 1 min |

### Security Headers

Middleware adds OWASP-recommended headers:

| Header | Value |
|--------|-------|
| Strict-Transport-Security | max-age=31536000; includeSubDomains |
| Content-Security-Policy | default-src 'self' |
| X-Frame-Options | DENY |
| X-Content-Type-Options | nosniff |
| X-XSS-Protection | 1; mode=block |

### Data Encryption

| Layer | Method |
|-------|--------|
| Passwords | bcrypt (one-way hash) |
| Messages | Client-side NaCl (E2EE) |
| Sensitive Fields | Fernet symmetric encryption |
| Transport | HTTPS/TLS |

### Audit Logging

Security events logged in JSON format:

```json
{"timestamp": "...", "event": "login", "user": "john", "status": "success", "ip": "..."}
```

Events tracked: login, register, key_publish, message_send, message_fetch

## Demo Client

Located in `client/demo_client.py`. Demonstrates full E2EE flow:

```bash
cd client
pip install requests pynacl
python demo_client.py
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -m 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Open Pull Request

## License

MIT License - see [LICENSE](LICENSE)

## Author

**Ashish Kumar Shaw**

- GitHub: [@ashishkrshaw](https://github.com/ashishkrshaw)
- LinkedIn: [asksaw](https://www.linkedin.com/in/asksaw/)

---

*Built with security in mind.*
