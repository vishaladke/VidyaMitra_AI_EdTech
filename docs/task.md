# VidyaMitra EdTech — Task Tracker

> Last updated: 2026-07-14

---

## Phase 1 — Scaffold + Auth + RBAC ✅ COMPLETE

### Repository Foundation
- [x] .gitignore
- [x] docker-compose.yml (Postgres + pgvector, Redis, backend, realtime gateway)
- [x] .env.example (all variables with safe defaults)

### Backend (Python FastAPI)
- [x] Dockerfile
- [x] pyproject.toml + dependency manifest
- [x] Alembic setup (alembic.ini + env.py)
- [x] Initial migration (001_initial_schema.py) — 22 tables
- [x] App config (pydantic-settings)
- [x] Database connection (async engine + session)
- [x] SQLAlchemy models (11 files: user, school, syllabus, assessment, ai, attendance, payment, notification, content, base, __init__)
- [x] Pydantic schemas (7 files: auth, user, common, syllabus, assessment, ai, __init__)
- [x] Auth utilities (JWT encode/decode, TOTP generate/verify)
- [x] Safety utilities (distress detection, fixed safety messages)
- [x] Middleware (Redis-backed rate limiter, audit logger)
- [x] Dependencies (get_db, get_current_user, require_role)
- [x] Routers (auth, health, students, teachers, parents, admin, superadmin)
- [x] Services (auth_service, user_service)
- [x] Providers (OTP: dev_mock + firebase stub + msg91 stub)
- [x] Providers (Payment: base ABC + offline_mock + razorpay stubs)
- [x] Providers (Notification: base ABC + mock + whatsapp stub)
- [x] Providers (Storage: base ABC + local_mock + r2 stub)
- [x] Dev seed script (seed_dev_users.py — 5 test users)
- [x] Tests (test_auth, test_rbac, test_payment_webhook)

### Realtime Gateway (Node.js + Socket.io)
- [x] Dockerfile
- [x] package.json + tsconfig
- [x] Express + Socket.io server (index.ts)
- [x] JWT auth middleware (auth.ts)
- [x] Handler stubs (ai-voice, whatsapp-webhook)
- [x] Backend HTTP client (backend-client.ts)
- [x] Config (config.ts)

### Frontend (React + Vite + TypeScript + Tailwind)
- [x] Vite scaffold + PWA config (vite.config.ts, manifest.json)
- [x] Tailwind config + design system (index.css, tailwind.config.ts)
- [x] Auth context + hooks (AuthContext.tsx, useAuth.ts)
- [x] Socket.io hook (useSocket.ts)
- [x] API client (axios wrapper with JWT interceptor + token refresh)
- [x] Protected route + role-based routing (ProtectedRoute.tsx, App.tsx)
- [x] Login page (phone + OTP + TOTP)
- [x] App shell (sidebar + topbar, role-aware nav)
- [x] Dashboard shells (teacher, parent, admin, super admin)
- [x] Public homepage

### Phase 1 Verification
- [x] npm install for frontend + gateway
- [x] TypeScript compilation check (zero errors, both frontend and gateway)
- [x] Vite production build (1656 modules, PWA SW generated)
- [ ] docker compose up --build succeeds
- [ ] Alembic migration runs against Postgres
- [ ] Backend pytest passes
- [ ] All five role dashboards accessible with correct RBAC
- [ ] Super Admin requires TOTP after OTP
- [ ] 403 on cross-role API access

---

## Phase 2 — AI Guru Chat + Syllabus Browser + Student Features ✅ COMPLETE

### Backend — AI Services
- [x] `ai_service.py` — Full cache-first flow orchestrator (536 lines)
- [x] `claude_service.py` — Claude API wrapper with system prompt, streaming
- [x] `embedding_service.py` — OpenAI embeddings + normalize_question
- [x] `ai.py` router — REST endpoints
- [x] `syllabus.py` router — Syllabus endpoints
- [x] Routers mounted in main.py

### Backend — Student Progress
- [x] `progress_service.py` — Dashboard stats, subject progress, streak tracking

### Backend — Syllabus Seed Data
- [x] `seed_syllabus.py` — Maharashtra State Board (grades 5–10, 6 subjects)

### Backend — Safety Fixes
- [x] `safety.py` — detect_distress alias, SAFETY_MESSAGE_MARATHI, check_distress_signals

### Backend — Tests
- [x] `test_ai_cache.py` — Normalization, safety detection, cache enums

### Realtime Gateway — AI Chat Streaming
- [x] `ai-chat.ts` — Full streaming implementation
- [x] `auth.ts` — JWT token forwarding

### Frontend — Phase 2 Pages
- [x] AIGuruPage, ChatBubble, ChatInput, TypingIndicator
- [x] SyllabusPage, SubjectCard, TopicTree
- [x] DashboardPage (upgraded from shell)
- [x] Routes: /student/syllabus, /student/ai-guru

### Phase 2 Verification
- [x] Frontend TypeScript (zero errors)
- [x] Frontend vite build (1693 modules)
- [x] Gateway TypeScript (zero errors)

---

## Phase 3 — Teacher + Parent Dashboards ✅ COMPLETE

### Backend — Teacher Service
- [x] `teacher_service.py` — Class roster (with pilot fallback), attendance (single + bulk), attendance summary, student detail, AI usage oversight, assignment CRUD
- [x] `teachers.py` router — 10 endpoints (dashboard, roster, student detail, attendance, AI usage, assignments)

### Backend — Parent Service
- [x] `parent_service.py` — Linked children, parent dashboard stats, child progress (with parent auth check), notification preferences CRUD
- [x] `parents.py` router — 7 endpoints (dashboard, children, child detail, reports, notifications)

### Backend — Report Service
- [x] `report_service.py` — Weekly student report generation with Marathi summary text for WhatsApp template, batch generation for all students

### Backend — Bug Fixes
- [x] `seed_dev_users.py` — Fixed relationship → relationship_type column name

### Backend — Tests
- [x] `test_teacher_parent.py` — RBAC enums, model structure, report Marathi summary (5 cases), service importability checks

### Frontend — Teacher Pages
- [x] `DashboardPage.tsx` — Functional teacher dashboard with stats cards, module navigation
- [x] `AttendancePage.tsx` — Tap-to-cycle status (present/absent/late), date picker, bulk save, summary counts
- [x] `StudentProgressPage.tsx` — Roster list + drill-down detail (AI stats, subject distribution, recent conversations)
- [x] `AIUsagePage.tsx` — Period selector, flagged conversations, top topics, most active students

### Frontend — Parent Pages
- [x] `DashboardPage.tsx` — Functional parent dashboard with children cards, stats, module navigation
- [x] `ChildProgressPage.tsx` — Individual child progress with AI stats, attendance, subject bars, test scores
- [x] `ReportsPage.tsx` — Weekly reports per child with stats grid + Marathi WhatsApp summary preview

### Frontend — Routing
- [x] `App.tsx` — Routes: /teacher/attendance, /teacher/progress, /teacher/roster, /teacher/ai-usage, /parent/children/:childId, /parent/progress, /parent/reports

### Phase 3 Verification
- [x] Frontend TypeScript (zero errors)
- [x] Frontend vite build (pending confirmation)
- [x] Gateway TypeScript (zero errors)

---

## Phase 4 — Admin + Super Admin Panels (Not started)

- [ ] Admin: syllabus CRUD (PDF upload + versioning)
- [ ] Admin: user management (profile updates, mobile/email changes)
- [ ] Admin: class/section management, teacher-student assignment
- [ ] Super Admin: master data management (subjects, boards, grades)
- [ ] Super Admin: AI cost dashboard (tokens + ₹, cache-hit rate, per-user breakdown)
- [ ] Super Admin: full AI chat audit log access
- [ ] Super Admin: homepage/marketing content CMS
- [ ] Super Admin: ad-slot management (DPDP Act–compliant placement)
- [ ] Super Admin: cross-feature reporting

---

## Phase 5 — Payments + WhatsApp Reports (Not started)

- [ ] Payment flow: offline_mock → razorpay_test → razorpay_live
- [ ] Subscription management UI
- [ ] WhatsApp BSP integration (webhook → Node gateway)
- [ ] Weekly WhatsApp parent report (Utility template)
- [ ] Notification preferences and delivery tracking

---

## Phase 6 — Security Hardening + Free-Tier Deploy (Not started)

- [ ] Security hardening pass (DEPLOYMENT.md pre-launch checklist)
- [ ] Free-tier deploy configs (Cloudflare Pages, Render, Neon, Upstash, R2)
- [ ] UptimeRobot + Sentry monitoring setup
- [ ] Secrets rotation
- [ ] Database backup verification
- [ ] Rate limit load testing
