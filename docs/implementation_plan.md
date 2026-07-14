# Phase 4: Admin + Super Admin Panels

> Phase 3 is complete (2026-07-14). This is the next implementation plan.

## Goal

Build **functional Admin and Super Admin panels** — replacing Phase 1 shells with real features: syllabus CRUD (PDF upload), user management, class/section management, AI cost dashboard, chat audit access, and CMS.

---

## Prerequisite

> [!IMPORTANT]
> **Recommended: Verify infrastructure before Phase 4:**
> 1. Install Docker Desktop
> 2. `docker compose up -d postgres redis`
> 3. `alembic upgrade head && python -m app.scripts.seed_dev_users && python -m app.scripts.seed_syllabus`
> 4. `pytest tests/ -v` — all 6 test files should pass
> 5. Login as each role and verify navigation

---

## Scope

### In Scope (Phase 4)
1. **Admin:** Syllabus CRUD (PDF upload + versioning), user management, class/section management
2. **Super Admin:** AI cost dashboard, full chat audit, homepage CMS, master data management

### Out of Scope (Phase 5+)
- Payment integration
- WhatsApp BSP delivery
- Ad-slot management (DPDP Act compliance)

---

## Proposed Changes

### Backend — Admin Service

#### [NEW] `backend/app/services/admin_service.py`
- `crud_syllabus_upload(admin_id, file, subject_id)` — PDF upload + versioning
- `crud_users(admin_id, filters)` — list/update user profiles
- `crud_classes(admin_id)` — create/update classes and sections
- `assign_teacher_to_class(admin_id, teacher_id, class_id, subject_id)`

#### [MODIFY] `backend/app/routers/admin.py`
Replace dashboard shell with functional endpoints.

---

### Backend — Super Admin Service

#### [NEW] `backend/app/services/superadmin_service.py`
- `get_ai_cost_dashboard()` — tokens used, ₹ cost, cache-hit rate, per-user breakdown
- `get_chat_audit_log(filters)` — full AI conversation access with search
- `crud_master_data()` — subjects, boards, grades management
- `crud_homepage_content()` — marketing page CMS

#### [MODIFY] `backend/app/routers/superadmin.py`
Replace dashboard shell with functional endpoints.

---

### Frontend — Admin Pages

#### [MODIFY] `frontend/src/pages/admin/DashboardPage.tsx`
#### [NEW] `frontend/src/pages/admin/SyllabusCRUDPage.tsx`
#### [NEW] `frontend/src/pages/admin/UserManagementPage.tsx`
#### [NEW] `frontend/src/pages/admin/ClassManagementPage.tsx`

---

### Frontend — Super Admin Pages

#### [MODIFY] `frontend/src/pages/superadmin/DashboardPage.tsx`
#### [NEW] `frontend/src/pages/superadmin/AICostDashboardPage.tsx`
#### [NEW] `frontend/src/pages/superadmin/ChatAuditPage.tsx`
#### [NEW] `frontend/src/pages/superadmin/MasterDataPage.tsx`

---

## Open Questions

> [!IMPORTANT]
> **1. PDF upload storage:** Should we use local filesystem (dev) or R2 (production)? The storage provider abstraction already exists.

> [!NOTE]
> **2. AI cost calculation:** Should costs be calculated in real-time from `ai_messages.tokens_used` and `ai_messages.cost_inr`, or cached/aggregated periodically?

---

## Verification Plan

### Automated Tests
```bash
cd backend && pytest tests/ -v
cd frontend && npx tsc --noEmit && npx vite build
```

### Manual Verification
1. Login as admin → syllabus CRUD works
2. Upload PDF → stored and retrievable
3. Create class + assign teacher → reflected in roster
4. Login as super admin → AI cost dashboard shows data
5. Chat audit → search and filter conversations
