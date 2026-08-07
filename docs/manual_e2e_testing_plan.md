# VidyaMitra — Manual End-to-End Testing Plan

> **Version:** 1.0  
> **Date:** 2026-08-04  
> **Tester:** _______________  
> **Environment:** Local dev (Docker Postgres + Redis, Backend :8000, Gateway :4000, Frontend :5173)

---

## Table of Contents

1. [Pre-Requisites & Setup](#1-pre-requisites--setup)
2. [Infrastructure Verification](#2-infrastructure-verification)
3. [Public Pages (No Auth)](#3-public-pages-no-auth)
4. [Authentication Flow](#4-authentication-flow)
5. [Student Role — Full Walkthrough](#5-student-role--full-walkthrough)
6. [Teacher Role — Full Walkthrough](#6-teacher-role--full-walkthrough)
7. [Parent Role — Full Walkthrough](#7-parent-role--full-walkthrough)
8. [Admin Role — Full Walkthrough](#8-admin-role--full-walkthrough)
9. [Super Admin Role — Full Walkthrough](#9-super-admin-role--full-walkthrough)
10. [RBAC Cross-Role Matrix](#10-rbac-cross-role-matrix)
11. [Payments & Subscription Flow](#11-payments--subscription-flow)
12. [AI Guru Chat Flow](#12-ai-guru-chat-flow)
13. [Realtime Gateway](#13-realtime-gateway)
14. [Security & Middleware](#14-security--middleware)
15. [Edge Cases & Negative Tests](#15-edge-cases--negative-tests)
16. [API-Level Endpoint Checklist](#16-api-level-endpoint-checklist)
17. [Test Result Summary Template](#17-test-result-summary-template)

---

## 1. Pre-Requisites & Setup

### 1.1 Environment Checklist

| # | Item | Command to Verify | Expected | ✅/❌ |
|---|------|-------------------|----------|------|
| 1 | Docker Desktop running | `docker --version` | v29+ | |
| 2 | Python 3.12+ | `python --version` | 3.12+ | |
| 3 | Node.js 20+ | `node --version` | 20+ | |
| 4 | `.env` file created | Check file exists in project root | Has `JWT_SECRET`, `SUPERADMIN_URL_PATH` set | |

### 1.2 Start All Services

Run these in **separate terminals**:

```bash
# Terminal 1: Infrastructure
docker compose up -d postgres redis
docker compose ps   # Wait for both "healthy"

# Terminal 2: Backend
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
python -m app.scripts.seed_dev_users
python -m app.scripts.seed_syllabus
python -m app.scripts.seed_subscriptions
uvicorn app.main:app --reload --port 8000

# Terminal 3: Realtime Gateway
cd realtime-gateway
npm run dev    # port 4000

# Terminal 4: Frontend
cd frontend
npm run dev    # port 5173
```

### 1.3 Test User Reference

| Role | Phone | Name | OTP | Extra Auth |
|------|-------|------|-----|------------|
| Student | `9999999001` | राम पाटील | `123456` | — |
| Teacher | `9999999002` | सुनीता जाधव | `123456` | — |
| Parent | `9999999003` | महेश कुलकर्णी | `123456` | — |
| Admin | `9999999004` | Admin User | `123456` | — |
| Super Admin | `9999999005` | Super Admin | `123456` | TOTP (Google Authenticator) |

> [!NOTE]
> The Super Admin TOTP secret is printed during `seed_dev_users`. Scan it with Google Authenticator or use `pyotp` to generate the code.

---

## 2. Infrastructure Verification

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 2.1 | Postgres is healthy | `docker compose ps` | Status: `healthy` | | |
| 2.2 | Redis is healthy | `docker compose ps` | Status: `healthy` | | |
| 2.3 | Backend health | `curl http://localhost:8000/health` | `{"status":"healthy","service":"vidyamitra-backend"}` | | |
| 2.4 | Gateway health | `curl http://localhost:4000/health` | `{"status":"healthy","service":"vidyamitra-realtime-gateway"}` | | |
| 2.5 | Frontend loads | Open `http://localhost:5173` | Page renders, no console errors | | |
| 2.6 | API docs available | Open `http://localhost:8000/docs` | Swagger UI loads with all endpoints | | |
| 2.7 | Alembic at head | `alembic current` (in backend dir) | Shows current revision at head | | |
| 2.8 | Backend pytest | `pytest tests/ -v` (in backend dir) | All 130 tests pass | | |

---

## 3. Public Pages (No Auth)

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 3.1 | Homepage renders | Navigate to `http://localhost:5173/` | विद्यामित्र homepage loads with branding, hero, features | | |
| 3.2 | Homepage responsive | Resize browser to mobile width (375px) | Layout adapts, no overflow/breakage | | |
| 3.3 | Login link works | Click "लॉगिन / साइन अप" on homepage | Redirects to `/login` | | |
| 3.4 | Login page renders | Navigate to `/login` | विद्यामित्र logo, phone input field, "OTP पाठवा" button visible | | |
| 3.5 | Subscription plans (public API) | `curl http://localhost:8000/api/payments/plans` | Returns 4 plans (Free Trial ₹0, Monthly ₹99, Quarterly ₹249, Annual ₹799) | | |
| 3.6 | Unknown route redirects | Navigate to `/nonexistent-page` | Redirects to `/` (homepage) | | |
| 3.7 | Protected route redirect | Navigate to `/student` without auth | Redirects to `/login` | | |

---

## 4. Authentication Flow

### 4.1 OTP Request & Verification (Existing Users)

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 4.1.1 | Phone input validation | Enter `12345` (< 10 digits) on login page | "OTP पाठवा" button remains disabled | | |
| 4.1.2 | Non-numeric rejected | Type letters in phone field | Only digits accepted (letters stripped) | | |
| 4.1.3 | Request OTP (Student) | Enter `9999999001`, click "OTP पाठवा" | Advances to OTP entry step. Shows `OTP टाका (9999999001)` | | |
| 4.1.4 | Wrong OTP | Enter `000000` | Error message: "OTP चुकीचा आहे" or similar | | |
| 4.1.5 | Correct OTP (Student) | Enter `123456`, click "पुष्टी करा" | Logs in → Redirects to `/student` dashboard | | |
| 4.1.6 | Change number | After OTP step, click "← नंबर बदला" | Returns to phone entry step | | |

### 4.2 OTP via API (curl)

| # | Test Case | Command | Expected Result | ✅/❌ |
|---|-----------|---------|-----------------|------|
| 4.2.1 | Request OTP API | `curl -X POST http://localhost:8000/api/auth/request-otp -H "Content-Type: application/json" -d "{\"phone\":\"9999999001\"}"` | `{"message":"OTP sent","expires_in":300}` | |
| 4.2.2 | Verify OTP API | `curl -X POST http://localhost:8000/api/auth/verify-otp -H "Content-Type: application/json" -d "{\"phone\":\"9999999001\",\"otp\":\"123456\"}"` | Returns `access_token`, `refresh_token`, `user` object with `role: "student"` | |
| 4.2.3 | Get current user | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/auth/me` | Returns user details matching logged-in user | |
| 4.2.4 | Token refresh | `curl -X POST http://localhost:8000/api/auth/refresh -H "Content-Type: application/json" -d "{\"refresh_token\":\"<REFRESH_TOKEN>\"}"` | Returns new `access_token` | |

### 4.3 New User Registration

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 4.3.1 | New phone OTP | Enter a new phone (e.g., `9876543210`), request OTP, enter `123456` | Registration form appears (name, role, grade) | | |
| 4.3.2 | Role selection UI | On registration form | Three role buttons visible: विद्यार्थी, शिक्षक, पालक | | |
| 4.3.3 | Grade selector (student) | Select "विद्यार्थी" role | Grade dropdown appears (इयत्ता 1–12) | | |
| 4.3.4 | Grade hidden (non-student) | Select "शिक्षक" or "पालक" | Grade dropdown hidden | | |
| 4.3.5 | Complete registration | Fill name, select role, click "नोंदणी पूर्ण करा" | User created → redirected to role dashboard | | |
| 4.3.6 | Empty name blocked | Leave name empty, try to submit | Button disabled | | |

### 4.4 Super Admin TOTP (2FA)

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 4.4.1 | OTP → TOTP prompt | Enter `9999999005`, verify with `123456` | Advances to TOTP step (🔐 Authenticator Code screen), not dashboard | | |
| 4.4.2 | Wrong TOTP | Enter `000000` | Error message | | |
| 4.4.3 | Correct TOTP | Enter valid TOTP from authenticator app | Logs in → Redirects to `/super-admin` dashboard | | |
| 4.4.4 | TOTP API | `curl -X POST http://localhost:8000/api/auth/verify-totp -H "Content-Type: application/json" -d "{\"temp_token\":\"<TEMP_TOKEN>\",\"totp_code\":\"<CODE>\"}"` | Returns `access_token`, `refresh_token`, user with `role: "super_admin"` | |

### 4.5 Logout

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 4.5.1 | Logout button visible | When logged in, check sidebar bottom | "बाहेर पडा" button with logout icon visible | | |
| 4.5.2 | Logout works | Click logout button | Redirected to `/login`, tokens cleared | | |
| 4.5.3 | Post-logout protection | After logout, navigate to `/student` | Redirected to `/login` | | |

---

## 5. Student Role — Full Walkthrough

> **Login as:** Phone `9999999001`, OTP `123456`

### 5.1 Dashboard

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 5.1.1 | Dashboard loads | Login as student | `/student` page loads with user greeting, module cards | | |
| 5.1.2 | User name displayed | Check sidebar | Shows "राम पाटील" and "🎓 विद्यार्थी" | | |
| 5.1.3 | Sidebar navigation | Check sidebar items | 6 items: डॅशबोर्ड, अभ्यासक्रम, असाइनमेंट, चाचण्या, AI गुरू, प्रगती | | |
| 5.1.4 | Active nav highlight | Click different nav items | Active item is visually highlighted | | |
| 5.1.5 | Dashboard API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/students/dashboard` | Returns user info + module list | | |

### 5.2 Syllabus Browser

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 5.2.1 | Syllabus page loads | Click "अभ्यासक्रम" in sidebar | `/student/syllabus` loads, shows subject cards | | |
| 5.2.2 | Subjects displayed | Check subject list | 6 subjects for grade 7: गणित, विज्ञान, मराठी, हिंदी, English, सामाजिक शास्त्र | | |
| 5.2.3 | Subject → topic tree | Click on a subject card | Chapter/topic tree expands for that subject | | |
| 5.2.4 | Subjects API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/syllabus/subjects` | Returns 6 subjects with `id`, `name`, `name_en`, `grade` | | |
| 5.2.5 | Subject tree API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/syllabus/subjects/<SUBJECT_ID>/tree` | Returns nested chapter → topic tree structure | | |

### 5.3 AI Guru Chat

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 5.3.1 | AI Guru page loads | Click "AI गुरू" in sidebar | `/student/ai-guru` loads with chat interface | | |
| 5.3.2 | Chat input visible | Check page | Text input + send button visible | | |
| 5.3.3 | Send message | Type a question and press send | Message appears in chat, typing indicator shows, response arrives | | |
| 5.3.4 | Chat API (REST) | `curl -X POST http://localhost:8000/api/ai/chat -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d "{\"message\":\"गणित म्हणजे काय?\"}"` | Returns AI response with `response`, `source`, `conversation_id` | | |
| 5.3.5 | Conversation history | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/ai/conversations` | Returns list of past conversations | | |

> [!IMPORTANT]
> AI Chat requires `ANTHROPIC_API_KEY` in `.env` to get live Claude responses. Without it, the service may return a fallback/error. If no key is configured, verify the error handling is graceful.

### 5.4 Subscription Page

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 5.4.1 | Subscription page loads | Navigate to `/student/subscription` | Current status + plan comparison grid loads | | |
| 5.4.2 | Plans displayed | Check plan cards | 4 plans: Free Trial (₹0), Monthly (₹99), Quarterly (₹249), Annual (₹799) | | |
| 5.4.3 | Plan features visible | Check each plan card | Features shown: AI conversations/day, voice, weekly reports, priority support | | |
| 5.4.4 | Payment flow (mock) | Click subscribe on a paid plan | Mock checkout flow completes (offline_mock provider) | | |
| 5.4.5 | Payment history | Check history section | Displays previous payment records (or empty state) | | |

---

## 6. Teacher Role — Full Walkthrough

> **Login as:** Phone `9999999002`, OTP `123456`

### 6.1 Dashboard

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 6.1.1 | Dashboard loads | Login as teacher | `/teacher` page loads with stats cards and module navigation | | |
| 6.1.2 | User name displayed | Check sidebar | Shows "सुनीता जाधव" and "👨‍🏫 शिक्षक" | | |
| 6.1.3 | Sidebar navigation | Check items | 6 items: डॅशबोर्ड, वर्ग यादी, उपस्थिती, चाचण्या, विद्यार्थी प्रगती, AI वापर | | |
| 6.1.4 | Dashboard stats API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/teachers/dashboard` | Returns user info + stats object | | |

### 6.2 Student Roster

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 6.2.1 | Roster page loads | Click "वर्ग यादी" | `/teacher/roster` loads | | |
| 6.2.2 | Student list API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/teachers/students` | Returns students list (may be empty if no class assigned — expected with seed data) | | |
| 6.2.3 | Student detail | Click on a student (if available) | Shows detailed progress, AI stats, subject distribution | | |

### 6.3 Attendance

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 6.3.1 | Attendance page loads | Click "उपस्थिती" | `/teacher/attendance` loads with date picker + student list | | |
| 6.3.2 | Tap to cycle status | Click a student status | Cycles: present → absent → late → present | | |
| 6.3.3 | Date picker works | Change date | Student list reloads for selected date | | |
| 6.3.4 | Bulk save | Mark attendance for multiple students, save | Summary counts update (present/absent/late) | | |
| 6.3.5 | Attendance summary API | `curl -H "Authorization: Bearer <TOKEN>" "http://localhost:8000/api/teachers/attendance/summary"` | Returns per-student attendance summary | | |

### 6.4 Student Progress

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 6.4.1 | Progress page loads | Click "विद्यार्थी प्रगती" | `/teacher/progress` loads | | |
| 6.4.2 | Student detail drill-down | Click on a student | Shows AI stats, subject distribution, recent conversations | | |

### 6.5 AI Usage Oversight

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 6.5.1 | AI Usage page loads | Click "AI वापर" | `/teacher/ai-usage` loads | | |
| 6.5.2 | Period selector | Change period (7/30/90 days) | Data refreshes for selected period | | |
| 6.5.3 | Flagged conversations | Check flagged section | Shows flagged/safety-triggered conversations (or empty state) | | |
| 6.5.4 | AI Usage API | `curl -H "Authorization: Bearer <TOKEN>" "http://localhost:8000/api/teachers/ai-usage?days=7"` | Returns overview with top topics, active students, flagged conversations | | |

---

## 7. Parent Role — Full Walkthrough

> **Login as:** Phone `9999999003`, OTP `123456`

### 7.1 Dashboard

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 7.1.1 | Dashboard loads | Login as parent | `/parent` page loads with children cards, stats, module navigation | | |
| 7.1.2 | User name displayed | Check sidebar | Shows "महेश कुलकर्णी" and "👨‍👧‍👦 पालक" | | |
| 7.1.3 | Sidebar navigation | Check items | 5 items: डॅशबोर्ड, मुले, प्रगती, अहवाल, सूचना | | |
| 7.1.4 | Dashboard API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/parents/dashboard` | Returns user info, stats, children array | | |

### 7.2 Linked Children

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 7.2.1 | Children listed | Check dashboard or children section | Shows linked child: राम पाटील (student `9999999001`) | | |
| 7.2.2 | Children API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/parents/children` | Returns `children` array with at least 1 child | | |

### 7.3 Child Progress

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 7.3.1 | Child progress page | Click on child card or navigate to `/parent/children/<childId>` | Shows individual child progress: AI stats, attendance, subject bars, test scores | | |
| 7.3.2 | Child progress API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/parents/children/<CHILD_UUID>` | Returns child progress detail | | |
| 7.3.3 | Unauthorized child | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/parents/children/<RANDOM_UUID>` | 404 — child not linked to this parent | | |

### 7.4 Weekly Reports

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 7.4.1 | Reports page loads | Click "अहवाल" | `/parent/reports` loads with weekly reports per child | | |
| 7.4.2 | Report content | Check report card | Stats grid + Marathi WhatsApp summary preview visible | | |
| 7.4.3 | Reports API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/parents/reports` | Returns reports array for all linked children | | |

### 7.5 Notification Settings

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 7.5.1 | Notification page loads | Click "सूचना" | `/parent/notifications` loads | | |
| 7.5.2 | Toggle WhatsApp | Toggle WhatsApp switch | Switch state changes | | |
| 7.5.3 | Toggle Email | Toggle email switch | Switch state changes | | |
| 7.5.4 | Save preferences | Save notification settings | API call succeeds, preferences persisted | | |
| 7.5.5 | Get preferences API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/parents/notifications` | Returns current preferences (whatsapp, email booleans) | | |
| 7.5.6 | Update preferences API | `curl -X PUT http://localhost:8000/api/parents/notifications -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d "{\"whatsapp\":true,\"email\":true}"` | Returns updated preferences | | |

---

## 8. Admin Role — Full Walkthrough

> **Login as:** Phone `9999999004`, OTP `123456`

### 8.1 Dashboard

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 8.1.1 | Dashboard loads | Login as admin | `/admin` page loads with stats cards + module navigation | | |
| 8.1.2 | Dashboard API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/admin/dashboard` | Returns user info + stats (user counts, subject counts, etc.) | | |

### 8.2 Syllabus Management

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 8.2.1 | Syllabus page loads | Click "अभ्यासक्रम" | `/admin/syllabus` loads | | |
| 8.2.2 | Subjects listed | Check subject list | Shows seeded subjects (filtered by grade/board) | | |
| 8.2.3 | Create subject | Create a new subject via form | Subject appears in list | | |
| 8.2.4 | Update subject | Edit an existing subject | Changes reflected | | |
| 8.2.5 | Create syllabus unit | Create a chapter under a subject | Unit appears in tree | | |
| 8.2.6 | List subjects API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/admin/subjects` | Returns subjects array | | |

### 8.3 User Management

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 8.3.1 | User management page | Click "वापरकर्ते" | `/admin/users` loads | | |
| 8.3.2 | User listing | Check user table | Shows all seeded users (5+) | | |
| 8.3.3 | Search users | Type a name in search | List filters to matching users | | |
| 8.3.4 | Filter by role | Select a role filter | Only that role's users shown | | |
| 8.3.5 | Toggle user active | Click toggle on a user | User active/inactive status changes | | |
| 8.3.6 | Update user | Edit a user's name/phone/email | Changes persisted | | |
| 8.3.7 | Users API | `curl -H "Authorization: Bearer <TOKEN>" "http://localhost:8000/api/admin/users?limit=50"` | Returns paginated user list | | |
| 8.3.8 | User search API | `curl -H "Authorization: Bearer <TOKEN>" "http://localhost:8000/api/admin/users?search=राम"` | Returns filtered results | | |
| 8.3.9 | Role filter API | `curl -H "Authorization: Bearer <TOKEN>" "http://localhost:8000/api/admin/users?role=student"` | Returns only student users | | |

### 8.4 Class Management

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 8.4.1 | Class page loads | Click "वर्ग" | `/admin/classes` loads | | |
| 8.4.2 | Create class | Create a class (e.g., grade 7, name "A") | Class appears in list | | |
| 8.4.3 | Assign teacher | Assign teacher to class | Assignment saved | | |
| 8.4.4 | Classes API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/admin/classes` | Returns classes array | | |
| 8.4.5 | Teacher assignments API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/admin/teacher-assign` | Returns teacher-class assignments | | |

---

## 9. Super Admin Role — Full Walkthrough

> **Login as:** Phone `9999999005`, OTP `123456` → TOTP from authenticator app
> 
> **API prefix:** `/{SUPERADMIN_URL_PATH}/api/...` (check your `.env` for `SUPERADMIN_URL_PATH`)

### 9.1 Dashboard

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 9.1.1 | Dashboard loads | Login as super admin (OTP + TOTP) | `/super-admin` page loads with full platform stats | | |
| 9.1.2 | Sidebar navigation | Check items | 7 items: Dashboard, Master Data, AI Cost, Chat Audit, CMS, Reports, Security | | |
| 9.1.3 | Dashboard API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/<SA_PATH>/api/dashboard` | Returns full platform stats | | |

### 9.2 AI Cost Dashboard

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 9.2.1 | AI Cost page loads | Click "AI Cost" | Page loads with token breakdown, ₹ costs, cache-hit rate | | |
| 9.2.2 | Period selector | Change days (30/60/90) | Data refreshes | | |
| 9.2.3 | AI Cost API | `curl -H "Authorization: Bearer <TOKEN>" "http://localhost:8000/<SA_PATH>/api/ai-costs?days=30"` | Returns cost breakdown | | |

### 9.3 Chat Audit

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 9.3.1 | Chat audit page loads | Click "Chat Audit" | `/super-admin/chat-audit` loads | | |
| 9.3.2 | Search conversations | Type search query | Results filter by keyword | | |
| 9.3.3 | Flagged-only filter | Toggle flagged-only | Shows only flagged conversations | | |
| 9.3.4 | Chat Audit API | `curl -H "Authorization: Bearer <TOKEN>" "http://localhost:8000/<SA_PATH>/api/chat-audit?limit=50"` | Returns conversation audit log | | |
| 9.3.5 | Conversation detail API | `curl -H "Authorization: Bearer <TOKEN>" "http://localhost:8000/<SA_PATH>/api/chat-audit/<CONVERSATION_ID>"` | Returns all messages in conversation | | |

### 9.4 Master Data

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 9.4.1 | Master data page | Click "Master Data" | `/super-admin/master-data` loads | | |
| 9.4.2 | Data categories | Check page content | Shows subjects, boards, grades management | | |
| 9.4.3 | Master Data API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/<SA_PATH>/api/master-data` | Returns grades, boards, subjects, units summary | | |

### 9.5 Homepage CMS

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 9.5.1 | CMS API list | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/<SA_PATH>/api/cms` | Returns homepage content sections (or empty) | | |
| 9.5.2 | CMS create/update | `curl -X POST ... -d "{\"section\":\"hero\",\"title\":\"Welcome\",\"content\":\"Test\",\"status\":\"draft\"}"` | Content created/updated | | |

### 9.6 Audit Logs

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 9.6.1 | Audit logs API | `curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/<SA_PATH>/api/audit-logs` | Returns admin action audit logs | | |
| 9.6.2 | Filter by action | `curl ... "http://localhost:8000/<SA_PATH>/api/audit-logs?action=<action_type>"` | Returns filtered audit logs | | |

---

## 10. RBAC Cross-Role Matrix

### 10.1 Frontend Route Protection

| # | Logged in as | Navigate to | Expected Result | ✅/❌ |
|---|-------------|-------------|-----------------|------|
| 10.1.1 | Student | `/teacher` | Redirect to `/student` (or access denied) | |
| 10.1.2 | Student | `/parent` | Redirect to `/student` (or access denied) | |
| 10.1.3 | Student | `/admin` | Redirect to `/student` (or access denied) | |
| 10.1.4 | Student | `/super-admin` | Redirect to `/student` (or access denied) | |
| 10.1.5 | Teacher | `/student` | Redirect to `/teacher` (or access denied) | |
| 10.1.6 | Teacher | `/admin` | Redirect to `/teacher` (or access denied) | |
| 10.1.7 | Parent | `/student` | Redirect to `/parent` (or access denied) | |
| 10.1.8 | Parent | `/teacher` | Redirect to `/parent` (or access denied) | |
| 10.1.9 | Admin | `/student` | Redirect to `/admin` (or access denied) | |
| 10.1.10 | Admin | `/super-admin` | Redirect to `/admin` (or access denied) | |
| 10.1.11 | Not logged in | `/student` | Redirect to `/login` | |
| 10.1.12 | Not logged in | `/admin` | Redirect to `/login` | |

### 10.2 API-Level RBAC Enforcement

Test each role's token against every other role's endpoints. Every cross-role call should return **403 Forbidden**.

| # | Token Role | Endpoint | Expected | ✅/❌ |
|---|-----------|----------|----------|------|
| 10.2.1 | Student | `GET /api/teachers/dashboard` | 403 | |
| 10.2.2 | Student | `GET /api/parents/dashboard` | 403 | |
| 10.2.3 | Student | `GET /api/admin/dashboard` | 403 | |
| 10.2.4 | Teacher | `GET /api/students/dashboard` | 403 | |
| 10.2.5 | Teacher | `GET /api/parents/dashboard` | 403 | |
| 10.2.6 | Teacher | `GET /api/admin/dashboard` | 403 | |
| 10.2.7 | Parent | `GET /api/students/dashboard` | 403 | |
| 10.2.8 | Parent | `GET /api/teachers/dashboard` | 403 | |
| 10.2.9 | Parent | `GET /api/admin/dashboard` | 403 | |
| 10.2.10 | Admin | `GET /api/students/dashboard` | 403 | |
| 10.2.11 | Admin | `GET /api/teachers/dashboard` | 403 | |
| 10.2.12 | Admin | `GET /api/parents/dashboard` | 403 | |
| 10.2.13 | No token | `GET /api/students/dashboard` | 401 | |
| 10.2.14 | No token | `GET /api/teachers/dashboard` | 401 | |
| 10.2.15 | No token | `GET /api/admin/dashboard` | 401 | |
| 10.2.16 | No token | `GET /<SA_PATH>/api/dashboard` | 404 (obscured path) | |
| 10.2.17 | Student | `POST /api/ai/chat` | 200 (correct role) | |
| 10.2.18 | Teacher | `POST /api/ai/chat` | 403 (student-only) | |
| 10.2.19 | Admin | `GET /<SA_PATH>/api/dashboard` | 403 (super_admin only) | |
| 10.2.20 | Student | `GET /api/syllabus/subjects` | 200 (correct role) | |

---

## 11. Payments & Subscription Flow

> **Provider:** `offline_mock` (default in local dev — no real payments)

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 11.1 | List plans (no auth) | `curl http://localhost:8000/api/payments/plans` | 4 plans returned with prices in ₹ | | |
| 11.2 | Create order | `curl -X POST -H "Authorization: Bearer <STUDENT_TOKEN>" -H "Content-Type: application/json" -d "{\"subscription_id\":\"<PLAN_UUID>\"}" http://localhost:8000/api/payments/create-order` | Returns order details for checkout | | |
| 11.3 | Verify payment (mock) | `curl -X POST -H "Authorization: Bearer <STUDENT_TOKEN>" -H "Content-Type: application/json" -d "{\"order_id\":\"<ORDER_ID>\",\"payment_id\":\"mock_pay_xxx\",\"signature\":\"mock_sig\"}" http://localhost:8000/api/payments/verify` | Returns success, subscription activated | | |
| 11.4 | Check subscription status | `curl -H "Authorization: Bearer <STUDENT_TOKEN>" http://localhost:8000/api/payments/subscription` | Returns active subscription details | | |
| 11.5 | Payment history | `curl -H "Authorization: Bearer <STUDENT_TOKEN>" http://localhost:8000/api/payments/history` | Returns payment records (or empty) | | |
| 11.6 | Webhook (valid signature) | `curl -X POST -H "Content-Type: application/json" -H "X-Razorpay-Signature: test" -d "{\"event\":\"payment.captured\",\"payload\":{\"payment\":{\"entity\":{\"id\":\"pay_test\",\"order_id\":\"order_test\"}}}}" http://localhost:8000/api/payments/webhook` | Processed or acknowledged | | |
| 11.7 | Webhook (no signature) | Send webhook without `X-Razorpay-Signature` header | Rejected (401 or handled gracefully) | | |
| 11.8 | UI: Subscription page | Login as student → `/student/subscription` | Plan cards display, checkout flow works with mock | | |

---

## 12. AI Guru Chat Flow

> [!WARNING]
> Requires `ANTHROPIC_API_KEY` in `.env` for live Claude responses. Without it, test graceful fallback behavior.

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 12.1 | Chat page loads | Student → `/student/ai-guru` | Chat interface renders with input box | | |
| 12.2 | Send syllabus question | Type "गणितात त्रिकोणाचे क्षेत्रफळ कसे काढतात?" | Response in Marathi about triangle area formula | | |
| 12.3 | Safety: distress detection | Type a distress-related message | Safety response triggered (Marathi helpline message) | | |
| 12.4 | Off-topic rejection | Ask about non-syllabus topic (e.g., "IPL कोण जिंकेल?") | Polite redirect to syllabus topics | | |
| 12.5 | Conversation persistence | Send 2-3 messages, reload page | Previous conversation available in history | | |
| 12.6 | Conversation list API | `GET /api/ai/conversations` | Returns conversation list with IDs | | |
| 12.7 | Conversation detail API | `GET /api/ai/conversations/<ID>` | Returns full message thread | | |
| 12.8 | Cache hit (repeat question) | Send the exact same question twice | Second response comes faster (from cache), `source` field indicates cache | | |
| 12.9 | Typing indicator | Send a message | Typing indicator (animation) shows while waiting | | |
| 12.10 | Chat bubble styling | Check message display | Student messages on right, AI responses on left, distinct styling | | |

---

## 13. Realtime Gateway

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 13.1 | Gateway health | `curl http://localhost:4000/health` | `{"status":"healthy","service":"vidyamitra-realtime-gateway"}` | | |
| 13.2 | Socket.io connects | Open browser DevTools → Network → WS tab while on AI Guru page | WebSocket connection established to `:4000` | | |
| 13.3 | JWT auth required | Try to connect without token | Connection rejected | | |
| 13.4 | WhatsApp webhook endpoint | `curl -X POST http://localhost:8000/api/webhooks/whatsapp -H "Content-Type: application/json" -d "{\"test\":true}"` | Returns `{"status":"acknowledged","type":"unknown"}` | | |

---

## 14. Security & Middleware

### 14.1 Security Headers

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 14.1.1 | OWASP headers present | `curl -I http://localhost:8000/health` | Headers include: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block` | | |
| 14.1.2 | Strict-Transport-Security | Check response headers | `Strict-Transport-Security` header present | | |
| 14.1.3 | Content-Security-Policy | Check response headers | CSP header set | | |

### 14.2 CORS

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 14.2.1 | CORS allows frontend | Make request from `localhost:5173` | Request succeeds with CORS headers | | |
| 14.2.2 | CORS blocks unknown | `curl -H "Origin: https://evil.com" -I http://localhost:8000/health` | No `Access-Control-Allow-Origin: https://evil.com` | | |

### 14.3 Rate Limiting

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 14.3.1 | OTP rate limit | Send 10+ OTP requests rapidly for same phone | Rate limited (429 or error after threshold) | | |
| 14.3.2 | Super Admin lockout | Send 5+ wrong TOTP codes | Account locked for 15 minutes | | |

### 14.4 Request Validation

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 14.4.1 | Oversized payload rejected | Send POST with body > 10MB | 413 Payload Too Large (or similar rejection) | | |
| 14.4.2 | Invalid content-type | Send POST with `Content-Type: text/plain` to a JSON endpoint | Rejected or handled gracefully | | |

### 14.5 Token Security

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 14.5.1 | Expired token rejected | Use an expired JWT | 401 Unauthorized | | |
| 14.5.2 | Tampered token rejected | Modify JWT payload and send | 401 Unauthorized | | |
| 14.5.3 | Invalid token format | Send `Authorization: Bearer invalid-string` | 401 Unauthorized | | |
| 14.5.4 | Missing auth header | Send request without `Authorization` header | 401 Unauthorized | | |

---

## 15. Edge Cases & Negative Tests

| # | Test Case | Steps | Expected Result | ✅/❌ | Notes |
|---|-----------|-------|-----------------|------|-------|
| 15.1 | Non-existent student detail | Teacher: `GET /api/teachers/students/<random-uuid>` | 404 Not Found | | |
| 15.2 | Invalid UUID format | Teacher: `GET /api/teachers/students/not-a-uuid` | 422 Validation Error | | |
| 15.3 | Inactive user login | Admin toggles user inactive → user tries to login | Login rejected or token refresh fails | | |
| 15.4 | Duplicate phone registration | Try registering with an existing phone | Returns existing user tokens (auto-login) | | |
| 15.5 | Empty message to AI | Send `""` to AI chat | Validation error or handled gracefully | | |
| 15.6 | Very long message to AI | Send 10,000+ character message | Handled (truncated or rejected) | | |
| 15.7 | SQL injection attempt | Send `' OR 1=1 --` in search fields | No data leak, parameterized queries block it | | |
| 15.8 | XSS in user name | Register with name `<script>alert(1)</script>` | Name displayed as text, not executed | | |
| 15.9 | Concurrent session | Login same user in two browsers | Both sessions work independently | | |
| 15.10 | Network error handling | Stop backend → interact with frontend | Graceful error messages, no white screen | | |
| 15.11 | Parent accesses wrong child | Parent: `GET /api/parents/children/<other-child-id>` | 404 (not linked to this parent) | | |
| 15.12 | Invalid payment plan ID | `POST /api/payments/create-order` with fake plan UUID | 400 Bad Request | | |

---

## 16. API-Level Endpoint Checklist

### Auth Endpoints (`/api/auth/`)

| Method | Endpoint | Auth Required | Tested ✅/❌ |
|--------|----------|---------------|-------------|
| POST | `/api/auth/request-otp` | No | |
| POST | `/api/auth/verify-otp` | No | |
| POST | `/api/auth/verify-totp` | No (uses temp_token) | |
| POST | `/api/auth/refresh` | No (uses refresh_token) | |
| GET | `/api/auth/me` | Yes (any role) | |
| GET | `/api/auth/totp-setup` | Yes (super_admin) | |

### Student Endpoints (`/api/students/`)

| Method | Endpoint | Auth Required | Tested ✅/❌ |
|--------|----------|---------------|-------------|
| GET | `/api/students/dashboard` | Student | |

### Syllabus Endpoints (`/api/syllabus/`)

| Method | Endpoint | Auth Required | Tested ✅/❌ |
|--------|----------|---------------|-------------|
| GET | `/api/syllabus/subjects` | Student | |
| GET | `/api/syllabus/subjects/{id}/tree` | Student | |
| GET | `/api/syllabus/units/{id}` | Student | |
| GET | `/api/syllabus/subjects/{id}/progress` | Student | |

### AI Endpoints (`/api/ai/`)

| Method | Endpoint | Auth Required | Tested ✅/❌ |
|--------|----------|---------------|-------------|
| POST | `/api/ai/chat` | Student | |
| GET | `/api/ai/conversations` | Student | |
| GET | `/api/ai/conversations/{id}` | Student | |

### Teacher Endpoints (`/api/teachers/`)

| Method | Endpoint | Auth Required | Tested ✅/❌ |
|--------|----------|---------------|-------------|
| GET | `/api/teachers/dashboard` | Teacher | |
| GET | `/api/teachers/students` | Teacher | |
| GET | `/api/teachers/students/{id}` | Teacher | |
| POST | `/api/teachers/attendance` | Teacher | |
| POST | `/api/teachers/attendance/bulk` | Teacher | |
| GET | `/api/teachers/attendance/summary` | Teacher | |
| GET | `/api/teachers/ai-usage` | Teacher | |
| POST | `/api/teachers/assignments` | Teacher | |
| GET | `/api/teachers/assignments` | Teacher | |

### Parent Endpoints (`/api/parents/`)

| Method | Endpoint | Auth Required | Tested ✅/❌ |
|--------|----------|---------------|-------------|
| GET | `/api/parents/dashboard` | Parent | |
| GET | `/api/parents/children` | Parent | |
| GET | `/api/parents/children/{id}` | Parent | |
| GET | `/api/parents/reports` | Parent | |
| GET | `/api/parents/reports/{child_id}` | Parent | |
| GET | `/api/parents/notifications` | Parent | |
| PUT | `/api/parents/notifications` | Parent | |

### Admin Endpoints (`/api/admin/`)

| Method | Endpoint | Auth Required | Tested ✅/❌ |
|--------|----------|---------------|-------------|
| GET | `/api/admin/dashboard` | Admin / Super Admin | |
| GET | `/api/admin/users` | Admin / Super Admin | |
| PUT | `/api/admin/users/{id}` | Admin / Super Admin | |
| POST | `/api/admin/users/{id}/toggle` | Admin / Super Admin | |
| GET | `/api/admin/subjects` | Admin / Super Admin | |
| POST | `/api/admin/subjects` | Admin / Super Admin | |
| PUT | `/api/admin/subjects/{id}` | Admin / Super Admin | |
| POST | `/api/admin/syllabus-units` | Admin / Super Admin | |
| GET | `/api/admin/classes` | Admin / Super Admin | |
| POST | `/api/admin/classes` | Admin / Super Admin | |
| POST | `/api/admin/teacher-assign` | Admin / Super Admin | |
| GET | `/api/admin/teacher-assign` | Admin / Super Admin | |

### Super Admin Endpoints (`/{SA_PATH}/api/`)

| Method | Endpoint | Auth Required | Tested ✅/❌ |
|--------|----------|---------------|-------------|
| GET | `/{SA_PATH}/api/dashboard` | Super Admin | |
| GET | `/{SA_PATH}/api/ai-costs` | Super Admin | |
| GET | `/{SA_PATH}/api/chat-audit` | Super Admin | |
| GET | `/{SA_PATH}/api/chat-audit/{id}` | Super Admin | |
| GET | `/{SA_PATH}/api/master-data` | Super Admin | |
| GET | `/{SA_PATH}/api/cms` | Super Admin | |
| POST | `/{SA_PATH}/api/cms` | Super Admin | |
| GET | `/{SA_PATH}/api/audit-logs` | Super Admin | |

### Payment Endpoints (`/api/payments/`)

| Method | Endpoint | Auth Required | Tested ✅/❌ |
|--------|----------|---------------|-------------|
| GET | `/api/payments/plans` | No | |
| POST | `/api/payments/create-order` | Yes (any) | |
| POST | `/api/payments/verify` | Yes (any) | |
| POST | `/api/payments/webhook` | No (signature verified) | |
| GET | `/api/payments/subscription` | Yes (any) | |
| GET | `/api/payments/history` | Yes (any) | |

### Webhook Endpoints (`/api/webhooks/`)

| Method | Endpoint | Auth Required | Tested ✅/❌ |
|--------|----------|---------------|-------------|
| POST | `/api/webhooks/whatsapp` | No | |

### Health Endpoint

| Method | Endpoint | Auth Required | Tested ✅/❌ |
|--------|----------|---------------|-------------|
| GET | `/health` | No | |

---

## 17. Test Result Summary Template

Fill this out after completing all tests.

### Summary

| Category | Total Tests | Passed | Failed | Blocked | Notes |
|----------|------------|--------|--------|---------|-------|
| Infrastructure (§2) | 8 | | | | |
| Public Pages (§3) | 7 | | | | |
| Auth: OTP/TOTP (§4) | 18 | | | | |
| Student Role (§5) | 15 | | | | |
| Teacher Role (§6) | 14 | | | | |
| Parent Role (§7) | 16 | | | | |
| Admin Role (§8) | 14 | | | | |
| Super Admin (§9) | 12 | | | | |
| RBAC Matrix (§10) | 32 | | | | |
| Payments (§11) | 8 | | | | |
| AI Guru Chat (§12) | 10 | | | | |
| Realtime Gateway (§13) | 4 | | | | |
| Security (§14) | 12 | | | | |
| Edge Cases (§15) | 12 | | | | |
| **TOTAL** | **~182** | | | | |

### Defects Found

| # | Severity | Section | Test # | Description | Steps to Reproduce | Screenshot |
|---|----------|---------|--------|-------------|---------------------|------------|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

### Sign-Off

| | Name | Date | Signature |
|---|------|------|-----------|
| Tested by | | | |
| Reviewed by | | | |

---

> [!TIP]
> **Testing workflow suggestion:** Work through sections 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 sequentially (login as each role, complete all tests, logout). Then do section 10 (RBAC matrix) which requires switching between roles. Finish with sections 11–15 (cross-cutting concerns).
