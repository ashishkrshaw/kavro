# How Kavro Works

This doc explains the design decisions I made while building Kavro. If you're wondering "why did he do it that way?" - this is the place.

## The Big Picture

```
Client encrypts message
       ↓
Sends to Kavro server
       ↓
Server stores encrypted blob (can't read it)
       ↓
Recipient fetches
       ↓
Client decrypts
```

The key thing: **the server never sees plaintext messages**. Even if someone hacks the database, they just get encrypted garbage.

## Folder Structure

I organized it like this:

```
app/
├── api/           # HTTP endpoints (thin layer, just handles requests)
├── core/          # The important stuff - security, encryption, config
├── db/            # Database connection
├── tests/         # Tests for everything
├── models.py      # What tables look like
├── schemas.py     # What requests/responses look like
└── main.py        # Where it all starts
```

**Why separate api/ and core/?**

The API layer just handles HTTP stuff - parsing requests, returning responses. All the real logic lives in core/. This way if I want to add a CLI or something later, I can reuse the core logic.

## Database Choices

**Why SQLAlchemy Core instead of ORM?**

I went with raw SQLAlchemy queries instead of the full ORM because:
- It's more explicit - you can see exactly what SQL runs
- Less magic = easier to debug
- Faster for async stuff

So instead of:
```python
user = User.query.filter_by(username='john').first()  # ORM magic
```

I write:
```python
q = sa.select(users).where(users.c.username == 'john')  # explicit
```

**Why PostgreSQL?**

It's solid, handles async well with asyncpg, and is free. Plus everyone knows it.

## Security Layers

I have three layers of encryption:

1. **HTTPS** - encrypts data in transit
2. **Client-side encryption** - messages encrypted before sending (using NaCl)
3. **Field encryption** - sensitive stuff in DB is encrypted with Fernet

Why so many? Defense in depth. If one layer fails, others still protect you.

## Rate Limiting

I use Redis to track request counts. Each endpoint has limits:

- Registration: 3/hour (prevent spam accounts)
- Login: 5/15min (prevent brute force)
- Messages: 30/min (prevent spam)

If you hit the limit, you get a 429 error.

## Auth Flow

**Registration:**
1. User sends username + password
2. I validate (Pydantic checks format)
3. Hash password with bcrypt
4. Create user in DB
5. Return JWT token

**Login:**
1. Check if account is locked (brute force protection)
2. Find user
3. Verify password
4. Reset failure counter
5. Return JWT token

**Brute force protection:**
After 5 failed logins, account locks for 5 minutes. This counter lives in Redis.

## Message Flow

**Sending:**
1. Client encrypts message with recipient's public key
2. Sends: ciphertext (base64), ephemeral key, optional metadata
3. I store it as-is (can't decrypt it anyway)
4. Log the action

**Receiving:**
1. Client fetches inbox
2. I return all their encrypted messages
3. Client decrypts with their private key
4. Client sends "ack" to mark as delivered

## What I'd Change for Scale

Right now Kavro is designed for small-medium use. For bigger scale I'd add:

- **Message queue** - instead of direct DB writes, push to RabbitMQ/SQS
- **Read replicas** - separate DB for reads vs writes
- **External logging** - send logs to CloudWatch instead of stdout
- **S3 for attachments** - if supporting images/files

But for now, this works fine for thousands of users.

## Testing

I have 25 tests covering:
- All API endpoints
- Success and error cases
- Auth edge cases
- Message permission checks

Run them with:
```bash
pytest app/tests/ -v
```

Tests use SQLite in-memory so they're fast and don't need real PostgreSQL.

## Questions?

If something doesn't make sense, open an issue. I'm happy to explain.
