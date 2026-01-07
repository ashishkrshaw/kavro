# Kavro

I built this to learn how encrypted messaging actually works.

You know how Signal and WhatsApp say "end-to-end encrypted"? I always wondered what that actually means. Where does encryption happen? What does the server see? Can the company read my messages?

So I built Kavro to figure it out.

## What I learned

The server never sees your messages. Heres the flow:

1. You generate a keypair on your device
2. You upload only the public key to server
3. When you message someone, you encrypt it with their public key
4. Server just stores the encrypted blob
5. Recipient decrypts with their private key

Server literally cant read messages even if it wanted to. Thats the whole point.

## Running it

```
git clone https://github.com/ashishkrshaw/kavro.git
cd kavro
cp .env.docker.example .env
docker-compose up -d
```

Open http://localhost:8000/docs

## API

- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/keys/publish
- GET /api/v1/keys/{user_id}
- POST /api/v1/messages/
- GET /api/v1/messages/inbox

## Frontend

Check client/demo_client.py for working example.
See docs/FRONTEND_INTEGRATION.md for how to connect any frontend.

## Tech

Python, FastAPI, PostgreSQL, Redis, NaCl

25 tests passing. CI with GitHub Actions.

## Deploy

```
curl -O https://raw.githubusercontent.com/ashishkrshaw/kavro/main/deploy-ec2.sh
sudo ./deploy-ec2.sh
```

## Author

Ashish Kumar Shaw
github.com/ashishkrshaw
