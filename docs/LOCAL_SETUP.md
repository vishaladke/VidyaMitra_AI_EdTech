# Local Development Setup Guide

## Prerequisites

You need three things installed:

### 1. Docker Desktop
- Download: https://www.docker.com/products/docker-desktop/
- After install, ensure Docker Desktop is running (whale icon in system tray)
- Verify: `docker --version` and `docker compose version`

### 2. Python 3.12+
- Download: https://www.python.org/downloads/
- **Important**: During install, check ✅ "Add Python to PATH"
- Verify: `python --version` (should show 3.12+)

### 3. Node.js 20+ (already installed ✅)
- You have Node v24.18.0 and npm 11.16.0

---

## Step-by-Step Setup

### Step 1: Environment File
```bash
cd VidyaMitra_AI_EdTech
cp .env.example .env
```

Edit `.env` and set at minimum:
```
JWT_SECRET=<any-random-32-char-string>
SUPERADMIN_URL_PATH=<any-unguessable-path>
```

All other values have working defaults for local dev.

### Step 2: Start Infrastructure (Docker)
```bash
docker compose up -d postgres redis
```
This starts:
- **PostgreSQL 16** with pgvector at `localhost:5432`
- **Redis 7** at `localhost:6379`

Wait ~10 seconds for both to be healthy:
```bash
docker compose ps   # both should show "healthy"
```

### Step 3: Backend Setup (Python)
```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate it (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e ".[dev]"

# Run Alembic migration (creates all 22 tables)
alembic upgrade head

# Seed dev users
python -m app.scripts.seed_dev_users

# Start backend
uvicorn app.main:app --reload --port 8000
```

### Step 4: Realtime Gateway (Node.js)
Open a **new terminal**:
```bash
cd realtime-gateway
npm install          # already done ✅
npm run dev          # starts on port 4000
```

### Step 5: Frontend (React)
Open a **new terminal**:
```bash
cd frontend
npm install          # already done ✅
npm run dev          # starts on port 5173
```

---

## Verifying Everything Works

### 1. Health checks
```bash
# Backend
curl http://localhost:8000/health
# → {"status":"healthy","service":"vidyamitra-backend"}

# Gateway
curl http://localhost:4000/health
# → {"status":"healthy","service":"vidyamitra-realtime-gateway"}

# Frontend
# Open http://localhost:5173 in browser
```

### 2. Auth flow test
```bash
# Request OTP (dev mock — no SMS sent)
curl -X POST http://localhost:8000/api/auth/request-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "9999999001"}'
# → {"message":"OTP sent","expires_in":300}

# Verify OTP with dev code "123456"
curl -X POST http://localhost:8000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "9999999001", "otp": "123456"}'
# → {"access_token":"...", "refresh_token":"...", "user": {...}}
```

### 3. RBAC test
```bash
# Use the access_token from above
TOKEN="<paste access_token here>"

# Student can access student dashboard
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/students/dashboard
# → 200 OK

# Student CANNOT access admin dashboard
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/admin/dashboard
# → 403 Forbidden
```

### 4. Backend tests
```bash
cd backend
pytest tests/ -v
```

### 5. Browse the UI
Open http://localhost:5173 in your browser:
1. You'll see the **विद्यामित्र** homepage
2. Click **लॉगिन / साइन अप**
3. Enter phone: `9999999001`
4. Enter OTP: `123456`
5. You'll land on the **Student Dashboard** with Marathi module cards

---

## Seed Users (Dev Mode)

| Role | Phone | Name | OTP |
|------|-------|------|-----|
| Student | `9999999001` | राम पाटील | `123456` |
| Teacher | `9999999002` | सुनीता जाधव | `123456` |
| Parent | `9999999003` | महेश कुलकर्णी | `123456` |
| Admin | `9999999004` | Admin User | `123456` |
| Super Admin | `9999999005` | Super Admin | `123456` + TOTP |

> **Note:** Super Admin requires a TOTP code after OTP. The TOTP secret is printed during seeding — scan it with Google Authenticator.

---

## Common Issues

### "Port already in use"
```bash
# Find what's using the port
netstat -ano | findstr :8000
# Kill it
taskkill /PID <pid> /F
```

### "Cannot connect to Postgres"
Make sure Docker Desktop is running and the container is healthy:
```bash
docker compose ps
docker compose logs postgres
```

### "Alembic migration fails"
Ensure `DATABASE_URL` in `.env` points to the running Postgres:
```
DATABASE_URL=postgresql+asyncpg://edtech:edtech_local_dev@localhost:5432/edtech_platform
```
Note: use `localhost` (not `postgres`) when running outside Docker.
