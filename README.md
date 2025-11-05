# Kavro

A secure messaging API with end-to-end encryption. Messages are encrypted on your device before they ever leave - the server never sees what you're sending.

Built with FastAPI, PostgreSQL, and Redis.

## What's This?

Kavro is a backend for encrypted messaging apps. Think of it like the server part of Signal or WhatsApp, but simpler and open source.

Your app encrypts messages → sends to Kavro → recipient fetches → their app decrypts

The server just stores encrypted blobs. It can't read your messages even if it wanted to.

## Quick Start

### With Docker (easiest)

```bash
git clone https://github.com/ashishkrshaw/kavro.git
cd kavro

# Setup config
cp .env.docker.example .env
nano .env  # change the passwords!

# Run
docker-compose up -d

# Check it works
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

Create a `.env` file:

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

Everything lives under `/api/v1/`. Here's what you can do:

**Auth stuff:**
- `POST /api/v1/auth/register` - create account
- `POST /api/v1/auth/login` - get token
- `GET /api/v1/auth/me` - who am I?

**Keys:**
- `POST /api/v1/keys/publish` - upload your public key
- `GET /api/v1/keys/{user_id}` - get someone's public key

**Messages:**
- `POST /api/v1/messages/` - send encrypted message
- `GET /api/v1/messages/inbox` - get your messages
- `POST /api/v1/messages/{id}/ack` - mark as read

**Health:**
- `GET /health` - is server alive?

Full docs at http://localhost:8000/docs when running.

## Project Layout

```
kavro/
├── app/
│   ├── api/          # endpoints
│   ├── core/         # security, config
│   ├── db/           # database stuff
│   ├── tests/        # tests (25 of them)
│   ├── models.py     # database tables
│   ├── schemas.py    # request/response shapes
│   └── main.py       # app starts here
├── docs/             # deployment guides
├── .env.example      # config template
└── docker-compose.yml
```

## Running Tests

```bash
pip install -r requirements-test.txt
pytest app/tests/ -v
```

All 25 tests should pass.

## Security

- Passwords hashed with bcrypt
- JWT tokens for auth
- Rate limiting to prevent abuse
- Brute force protection (locks after failed attempts)
- Security headers (HSTS, CSP, etc.)
- Field encryption for sensitive data

## Deploying

See [docs/EC2_DEPLOYMENT.md](docs/EC2_DEPLOYMENT.md) for a step-by-step guide on deploying to AWS EC2 with HTTPS.

Short version:
```bash
docker pull ashishkrshaw/kavro-api:latest
docker-compose up -d
```

## Tech Stack

- Python 3.10+
- FastAPI
- PostgreSQL (async)
- Redis
- Docker

## Contributing

Found a bug? Want to add something? PRs welcome.

1. Fork it
2. Make changes
3. Run tests
4. Submit PR

## License

MIT - do whatever you want with it.

## Author

Ashish Kumar Shaw
- GitHub: [@ashishkrshaw](https://github.com/ashishkrshaw)
- LinkedIn: [asksaw](https://linkedin.com/in/asksaw)
