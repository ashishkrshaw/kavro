# Architecture

How Kavro is structured and why.

## Overview

```
Client -> API -> PostgreSQL (users, messages)
            -> Redis (rate limiting, sessions)
```

Client does all encryption. Server just stores and relays encrypted blobs.

## Folder structure

```
app/
  api/        - endpoints (auth, keys, messages)
  core/       - security, config, middleware
  db/         - database connection
  tests/      - pytest tests
  models.py   - db tables
  schemas.py  - pydantic models
  main.py     - fastapi app
```

## Why this structure

API layer handles http stuff. Core has business logic. Keeps things separate so easier to test and modify.

## Database

Using SQLAlchemy Core (not ORM) with async postgres. More explicit, you see exactly what queries run.

Tables: users, devices (public keys), messages, audit_logs

## Security layers

1. HTTPS - encrypts in transit
2. Client encryption - nacl for messages
3. Field encryption - fernet for sensitive db fields
4. Rate limiting - redis based
5. Brute force protection - lockout after failed logins
6. Security headers - HSTS, CSP etc

## Auth

JWT tokens. Passwords hashed with bcrypt. Token expires in 24h by default.

## Testing

Pytest with async support. Uses sqlite for tests so no need for real postgres. 25 tests covering auth, keys, messages.

## Scaling

For bigger scale would add message queue, read replicas, external logging. But current setup handles thousands of users fine.
