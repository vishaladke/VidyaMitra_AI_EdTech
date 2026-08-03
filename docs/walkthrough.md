# Walkthrough — VidyaMitra EdTech Platform

> Last updated: 2026-08-03

## Summary

**Phase 1** scaffold — ✅ COMPLETE.  
**Phase 2** AI Guru + Syllabus — ✅ COMPLETE.  
**Phase 3** Teacher + Parent Dashboards — ✅ COMPLETE.  
**Phase 4** Admin + Super Admin Panels — ✅ COMPLETE.  
**Phase 5** Payments + WhatsApp Reports — ✅ COMPLETE.  
**Phase 6** Security Hardening + Deploy Configs — 🚧 IN PROGRESS.

All three services compile and build with zero errors. The platform has **functional dashboards for all 5 roles** with full backend APIs, payment processing (offline_mock → razorpay_test → razorpay_live), WhatsApp notification integration, subscription management, and **production-grade security middleware** (OWASP headers, rate limiting, request validation, Sentry error tracking).

---

## Phase 5 Changes (Payments + WhatsApp Reports)

### Backend — Payment Providers (2 files, fully implemented)

| File | Lines | Purpose |
|------|-------|---------|
| [razorpay_test.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/providers/payment/razorpay_test.py) | ~170 | Full Razorpay sandbox: create_order (INR→paise), verify_payment (HMAC sig), verify_webhook, fetch_payment_details |
| [razorpay_live.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/providers/payment/razorpay_live.py) | ~45 | Inherits from test — validates live key prefix, stricter logging |

### Backend — Services (3 files)

| File | Lines | Purpose |
|------|-------|---------|
| [payment_service.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/services/payment_service.py) | ~280 | Full flow: plan listing, order creation, verify+activate, webhook handling (captured/failed/refund), subscription status, payment history |
| [notification_service.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/services/notification_service.py) | ~230 | Provider factory, send+log, WhatsApp report delivery, batch weekly reports, delivery status updates, notification history |
| [report_service.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/services/report_service.py) | +60 | Added generate_and_send_weekly_reports(), format_whatsapp_template_params() |

### Backend — Schemas (1 new file)

| File | Purpose |
|------|---------|
| [payment.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/schemas/payment.py) | SubscriptionPlanResponse, PaymentOrderRequest/Response, PaymentVerifyRequest/Response, RazorpayWebhookEvent, PaymentHistoryItem/Response, UserSubscriptionResponse |

### Backend — Routers (2 new files)

| File | Endpoints | Purpose |
|------|-----------|---------| 
| [payments.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/routers/payments.py) | 6 | Plans (public), create-order, verify, webhook (sig verified), subscription status, history |
| [webhooks.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/routers/webhooks.py) | 1 | WhatsApp inbound — delivery status updates + inbound message handling |

### Backend — WhatsApp Provider (1 file, fully implemented)

| File | Lines | Purpose |
|------|-------|---------|
| [whatsapp.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/providers/notification/whatsapp.py) | ~200 | BSP integration (AiSensy/Interakt/Gupshup compatible), template messages, delivery receipt parsing, inbound message parsing |

### Backend — Seed Data (1 new file)

| File | Purpose |
|------|---------|
| [seed_subscriptions.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/scripts/seed_subscriptions.py) | 4 plans: Free Trial (₹0/30d), Monthly (₹99/30d), Quarterly (₹249/90d), Annual (₹799/365d) with Marathi descriptions |

### Backend — Config Updates

| File | Changes |
|------|---------|
| [config.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/config.py) | Added `NOTIFICATION_PROVIDER` (mock/whatsapp), `WHATSAPP_BSP_URL` |
| [.env.example](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/.env.example) | Added `NOTIFICATION_PROVIDER`, `WHATSAPP_BSP_URL` |
| [main.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/main.py) | Mounted `payments` and `webhooks` routers |

### Backend — Tests (2 new files, 44 test cases)

| File | Test Cases |
|------|------------|
| [test_payments.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/tests/test_payments.py) | Provider factory, offline mock (create/verify/webhook), Razorpay inheritance, model enums (PaymentStatus/ProviderEnum/SubscriptionStatus), model structure, service importability (8 functions), schema validation, router endpoints (count + paths), seed data (4 plans) |
| [test_notifications.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/tests/test_notifications.py) | Provider factory, mock provider (send + no params), WhatsApp provider (importability, no-key fallback, delivery status parsing, empty webhook, inbound messages), model enums (NotificationChannel), model structure, service importability (7 functions), template params extraction (3 cases), report service WhatsApp functions, webhook router |

### Frontend — Student Pages (1 new file)

| File | Features |
|------|----------|
| [SubscriptionPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/student/SubscriptionPage.tsx) | Current subscription status card, plan comparison grid (4 plans with ₹ pricing and Marathi labels), Razorpay checkout integration + mock payment flow for dev, payment history table with status badges |

### Frontend — Parent Pages (1 new file)

| File | Features |
|------|----------|
| [NotificationSettingsPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/parent/NotificationSettingsPage.tsx) | WhatsApp/email toggle switches, phone number display, report preview with WhatsApp-style Marathi message bubble, delivery history list |

### Frontend — Routing

[App.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/App.tsx) — 2 new routes:
- `/student/subscription` → `SubscriptionPage`
- `/parent/notifications` → `NotificationSettingsPage`

---

## Phase 3 Changes (Teacher + Parent)

### Backend — New Services (3 files)

| File | Lines | Purpose |
|------|-------|---------| 
| [teacher_service.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/services/teacher_service.py) | ~380 | Roster, attendance (single/bulk), attendance summary, student detail, AI usage overview, assignment CRUD |
| [parent_service.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/services/parent_service.py) | ~200 | Linked children, dashboard stats, child progress (parent auth check), notification prefs |
| [report_service.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/services/report_service.py) | ~210 | Weekly report generation, Marathi summary builder for WhatsApp, batch report generation |

### Backend — Upgraded Routers (2 files)

| File | Endpoints | Purpose |
|------|-----------|---------| 
| [teachers.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/routers/teachers.py) | 10 | Dashboard, roster, student detail, single/bulk attendance, attendance summary, AI usage, assignment CRUD |
| [parents.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/routers/parents.py) | 7 | Dashboard, children list, child detail, weekly reports (all/per-child), notification prefs get/update |

### Frontend — Teacher Pages (4 files)

| File | Features |
|------|----------|
| [DashboardPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/teacher/DashboardPage.tsx) | Stats cards, module navigation, Marathi greeting |
| [AttendancePage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/teacher/AttendancePage.tsx) | Tap-to-cycle status, date picker, bulk save, live summary |
| [StudentProgressPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/teacher/StudentProgressPage.tsx) | Roster list → drill-down detail with AI stats |
| [AIUsagePage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/teacher/AIUsagePage.tsx) | Period selector, flagged conversations, top topics |

### Frontend — Parent Pages (3 files)

| File | Features |
|------|----------|
| [DashboardPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/parent/DashboardPage.tsx) | Children cards with streak, stats overview |
| [ChildProgressPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/parent/ChildProgressPage.tsx) | AI stats, 30-day attendance, subject progress, test scores |
| [ReportsPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/parent/ReportsPage.tsx) | Weekly reports per child + Marathi WhatsApp summary |

---

## Phase 4 Changes (Admin + Super Admin)

### Backend — Services (2 files)

| File | Lines | Purpose |
|------|-------|---------|
| [admin_service.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/services/admin_service.py) | ~362 | Dashboard stats, user CRUD, subject CRUD, syllabus units, class management, teacher assignment |
| [superadmin_service.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/services/superadmin_service.py) | ~373 | Dashboard stats, AI cost dashboard, chat audit log, master data, CMS, audit logs |

### Frontend — Admin + Super Admin Pages (8 files)

| Role | File | Features |
|------|------|----------|
| Admin | [DashboardPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/admin/DashboardPage.tsx) | Stats cards + module navigation |
| Admin | [SyllabusCRUDPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/admin/SyllabusCRUDPage.tsx) | Subject/syllabus unit management |
| Admin | [UserManagementPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/admin/UserManagementPage.tsx) | User listing, search, update, toggle |
| Admin | [ClassManagementPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/admin/ClassManagementPage.tsx) | Class creation + teacher assignment |
| SuperAdmin | [DashboardPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/superadmin/DashboardPage.tsx) | Stats cards + module navigation |
| SuperAdmin | [AICostDashboardPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/superadmin/AICostDashboardPage.tsx) | Period selector, daily cost trend, per-user costs |
| SuperAdmin | [ChatAuditPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/superadmin/ChatAuditPage.tsx) | Searchable conversation list, message drill-down |
| SuperAdmin | [MasterDataPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/superadmin/MasterDataPage.tsx) | Boards, grades, subjects accordion |

---

## Phase 6 Changes (Security Hardening + Deploy)

### Backend — Security Middleware Wiring (3 modules activated)

These modules were **built in Phase 1 but never mounted in main.py** — now activated:

| File | Lines | Purpose |
|------|-------|---------|
| [security_headers.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/middleware/security_headers.py) | ~120 | OWASP security headers (X-Frame-Options, HSTS, CSP, etc.) + request validation (payload size, content-type) |
| [rate_limiter.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/middleware/rate_limiter.py) | ~74 | Redis-backed sliding-window rate limiter (per-IP, per-user, Super Admin login lockout) |
| [sentry.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/monitoring/sentry.py) | ~119 | Sentry SDK integration with FastAPI, SQLAlchemy, Redis instrumenting; DPDP-compliant (no PII) |

### Backend — Configuration Updates (3 files)

| File | Changes |
|------|---------|
| [main.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/main.py) | Mounted SecurityHeadersMiddleware + RequestValidationMiddleware, init_sentry() call, dynamic CORS, version from config |
| [config.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/config.py) | Added `SENTRY_DSN`, `APP_VERSION`, `FRONTEND_URL`, `cors_origins_with_frontend` property |
| [pyproject.toml](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/pyproject.toml) | Added `sentry-sdk[fastapi]` as optional `monitoring` dependency + included in dev |

### Backend — Tests (1 new file, 26 test cases)

| File | Test Cases |
|------|------------|
| [test_security.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/tests/test_security.py) | SecurityHeaders middleware, RequestValidation, RateLimiter structure, Sentry graceful degradation (no DSN/no crash), config security (JWT, CORS, Super Admin URL), Razorpay webhook signature tamper detection, main.py integration |

### Frontend — Deploy Config Files (2 new files)

| File | Purpose |
|------|---------|
| [_redirects](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/public/_redirects) | Cloudflare Pages SPA catch-all (`/* /index.html 200`) |
| [_headers](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/public/_headers) | Production security headers (OWASP, CSP with Razorpay, cache control for assets/SW) |

### Deploy Config Updates (2 files)

| File | Changes |
|------|---------|
| [render.yaml](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/render.yaml) | Added `SENTRY_DSN` from secrets, `APP_VERSION` env var |
| [.env.example](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/.env.example) | Added `SENTRY_DSN`, `APP_VERSION`, `FRONTEND_URL` |

---

## Cumulative File Count

| Layer | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6 | Total |
|-------|---------|---------|---------|---------|---------|---------|-------|
| Backend Models | 11 | — | — | — | — | — | 11 |
| Backend Services | 2 | 5 | 3 | 2 | 2 (+1 enhanced) | — | 14 |
| Backend Routers | 7 | 2 | — (upgraded) | — (upgraded) | 2 | — | 11 |
| Backend Schemas | 6 | 1 | — | — | 1 | — | 8 |
| Backend Tests | 3 | 1 | 1 | 1 | 2 | 1 | **9** |
| Backend Scripts | 1 | 1 | — (bug fix) | — | 1 | — | 3 |
| Backend Providers | 8 | — | — | — | 2 (upgraded) | — | 8 |
| Backend Middleware | 3 | — | — | — | — | — (wired) | 3 |
| Backend Monitoring | 1 | — | — | — | — | — (wired) | 1 |
| Gateway | 6 | — (upgraded) | — | — | — | — | 6 |
| Frontend Pages | 8 | 3 | 7 | 8 | 2 | — | 28 |
| Frontend Components | 3 | 5 | — | — | — | — | 8 |
| Frontend Hooks/API | 4 | — | — | — | — | — | 4 |
| Frontend Deploy | — | — | — | — | — | 2 | 2 |

---

## Verification Results (2026-08-03 Full Stack Test)

### Infrastructure
| Check | Result |
|-------|--------|
| Docker Desktop | ✅ v29.6.1 |
| PostgreSQL 16 + pgvector | ✅ Healthy on port 5432 |
| Redis 7 | ✅ Healthy on port 6379 |
| Alembic `upgrade head` | ✅ All 22 tables at head |
| Seed data (users/syllabus/subscriptions) | ✅ All loaded |

### Backend Test Suite
| Check | Result |
|-------|--------|
| `pytest tests/ -v` | ✅ **130 passed** in 1.98s |
| Warnings | 2 Sentry deprecation (non-blocking) |

### Service Health
| Check | Result |
|-------|--------|
| Backend `localhost:8000/health` | ✅ `{"status":"healthy"}` |
| Gateway `localhost:4000/health` | ✅ `{"status":"healthy"}` |
| Frontend `localhost:5173` | ✅ 200 OK |

### Five-Role Auth + RBAC Matrix
| Role | OTP Login | Own Dashboard | Cross-Role Blocked |
|------|-----------|---------------|-------------------|
| Student | ✅ Token issued | ✅ 200 | ✅ 3/3 → 403 |
| Teacher | ✅ Token issued | ✅ 200 | ✅ 3/3 → 403 |
| Parent | ✅ Token issued | ✅ 200 | ✅ 3/3 → 403 |
| Admin | ✅ Token issued | ✅ 200 | ✅ 3/3 → 403 |
| Super Admin | ✅ `requires_totp: true` | ⏸️ Needs TOTP | ✅ Correctly blocked |
| Unauthenticated | — | ❌ 401/404 | ✅ 5/5 blocked |

### Feature Endpoints (13 tested)
| Check | Result |
|-------|--------|
| Student dashboard + syllabus + plans | ✅ 3/3 |
| Teacher dashboard + AI usage | ✅ 2/2 |
| Teacher roster | ⚠️ 404 (no class in seed data — expected) |
| Parent dashboard + children + reports | ✅ 3/3 |
| Admin dashboard + users + subjects | ✅ 3/3 |
| Payment plans (public) | ✅ 200 |

### Frontend Compilation
| Check | Result |
|-------|--------|
| `tsc --noEmit` | ✅ Zero errors |
| `vite build` | ✅ 1706 modules, 483 KB JS, PWA SW |
| Security middleware mounted | ✅ SecurityHeaders + RequestValidation + CORS |
| Sentry initialization | ✅ Graceful no-op when DSN empty |
| Deploy configs | ✅ `_redirects` + `_headers` for Cloudflare Pages |

---

## How to Run Locally

See [LOCAL_SETUP.md](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/docs/LOCAL_SETUP.md)

| Step | Command |
|------|---------|
| 1 | `docker compose up -d postgres redis` |
| 2 | `cd backend && pip install -e ".[dev]"` |
| 3 | `alembic upgrade head` |
| 4 | `python -m app.scripts.seed_dev_users` |
| 5 | `python -m app.scripts.seed_syllabus` |
| 6 | `python -m app.scripts.seed_subscriptions` |
| 7 | `uvicorn app.main:app --reload` |
| 8 | `cd realtime-gateway && npm run dev` |
| 9 | `cd frontend && npm run dev` |

### Test Users

| Role | Phone | Name | Pages |
|------|-------|------|-------|
| Student | `9999999001` | राम पाटील | Dashboard, AI Guru, Syllabus, **Subscription** |
| Teacher | `9999999002` | सुनीता जाधव | Dashboard, Attendance, Progress, AI Usage |
| Parent | `9999999003` | महेश कुलकर्णी | Dashboard, Child Progress, Reports, **Notifications** |
| Admin | `9999999004` | Admin User | Dashboard, Syllabus CRUD, Users, Classes |
| Super Admin | `9999999005` | Super Admin | Dashboard, AI Costs, Chat Audit, Master Data |

### New in Phase 5

| Feature | URL | Role |
|---------|-----|------|
| Subscription Plans | `/student/subscription` | Student |
| Notification Settings | `/parent/notifications` | Parent |
| Payment API | `/api/payments/*` | Authenticated |
| WhatsApp Webhook | `/api/webhooks/whatsapp` | System (from gateway) |
