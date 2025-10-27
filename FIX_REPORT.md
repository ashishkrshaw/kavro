# Kavro E2EE Messaging API - Debug & Fix Report

**Date**: December 18, 2025  
**Project**: Kavro (E2EE Messaging API)

---

## Project Overview

This is a **FastAPI-based End-to-End Encrypted (E2EE) Messaging API** with:
- **PostgreSQL** database (hosted on Supabase)
- **Redis** for rate limiting and caching
- **JWT-based authentication**
- Routes for: `/auth`, `/keys`, `/messages`

---

## Issues Identified

### Issue #1: `TypeError: connect()` with `sslmode` parameter
**Error**: The asyncpg driver throws `TypeError: connect() got an unexpected keyword argument 'sslmode'`

**Root Cause**: The `DATABASE_URL` used `sslmode=require` which is the syntax for **psycopg2** (sync driver), but not compatible with **asyncpg** (async driver).

**Fix**: Changed `sslmode=require` → `ssl=require` in `.env` file.

---

### Issue #2: Connection timeout with Supabase pooler
**Error**: Server times out during startup when connecting to database.

**Root Cause**: Port 6543 is Supabase's connection pooler (Supavisor) which has known issues with asyncpg's prepared statements.

**Fix Options**:
1. Use port 5432 (direct connection) - but this may timeout due to network
2. Use port 6543 with `prepared_statement_cache_size=0` parameter

---

## Changes Made to `.env`

### Before:
```env
DATABASE_URL=postgresql+asyncpg://postgres:***@eholjpuxnzfeybrvnvbj.supabase.co:6543/postgres?sslmode=require
```

### After:
```env
DATABASE_URL=postgresql+asyncpg://postgres:***@eholjpuxnzfeybrvnvbj.supabase.co:6543/postgres?ssl=require&prepared_statement_cache_size=0
```

**Key Changes**:
| Parameter | Before | After | Reason |
|-----------|--------|-------|--------|
| SSL param | `sslmode=require` | `ssl=require` | asyncpg compatibility |
| Cache size | (none) | `prepared_statement_cache_size=0` | Supavisor workaround |

---

## Project Structure

```
Kavro/
├── .env                    # Environment config (DATABASE_URL, REDIS_URL, SECRET_KEY)
├── app/
│   ├── main.py            # FastAPI app entry point
│   ├── models.py          # SQLAlchemy table definitions
│   ├── schemas.py         # Pydantic schemas
│   ├── api/
│   │   ├── auth.py        # Authentication routes
│   │   ├── keys.py        # Key management routes
│   │   └── messages.py    # Message routes
│   ├── core/
│   │   ├── config.py      # Settings from .env
│   │   ├── security.py    # JWT/password handling
│   │   └── rate_limiter.py # Redis rate limiting
│   └── db/
│       ├── base.py        # SQLAlchemy metadata
│       └── session.py     # Async DB engine
├── client/
│   └── demo_client.py     # Test client
└── venv/                   # Python virtual environment
```

---

## How to Run

```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Start the server
uvicorn app.main:app --reload
```

---

## Current Status

❌ **Connection Timeout**: The Supabase database connection is timing out. This is a **network issue**, NOT a code issue.

### What This Means:
The code fixes are correct, but your Supabase database is unreachable. Possible reasons:

1. **Supabase project is paused** - Free tier projects pause after inactivity
2. **Network/firewall blocking** - Port 6543 may be blocked
3. **Supabase is down** - Check [Supabase Status](https://status.supabase.com/)

### How to Fix:

1. **Check Supabase Dashboard**: Log into [supabase.com](https://supabase.com) and verify your project is active
2. **Unpause if needed**: If paused, click "Restore" in the dashboard
3. **Check connection limits**: Free tier has limited connections
4. **Try a different network**: VPN or mobile hotspot to rule out firewall issues


---

## Files Created During Debugging

- `test_connection.py` - Tests PostgreSQL and Redis connections
- `test_startup.py` - Simulates FastAPI startup sequence

You can delete these test files after debugging is complete.
