# Phase 4: Admin + Super Admin Panels — Completion Plan

> Phase 3 complete (2026-07-14). Phase 4 backend + admin frontend complete (2026-07-20).
> **This plan covers the remaining Phase 4 items.**

## Current Status

### ✅ Already Complete

| Component | Status | Details |
|-----------|--------|---------|
| [admin_service.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/services/admin_service.py) | ✅ | 362 lines — dashboard stats, user CRUD, subject CRUD, syllabus units, class management, teacher assignment, audit logging |
| [superadmin_service.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/services/superadmin_service.py) | ✅ | 373 lines — dashboard stats, AI cost dashboard, chat audit, master data, CMS, audit logs |
| [admin.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/routers/admin.py) router | ✅ | 12 endpoints — dashboard, users, subjects, syllabus-units, classes, teacher-assign |
| [superadmin.py](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/backend/app/routers/superadmin.py) router | ✅ | 8 endpoints — dashboard, ai-costs, chat-audit, master-data, cms, audit-logs |
| Admin [DashboardPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/admin/DashboardPage.tsx) | ✅ | Stats cards + module navigation |
| Admin [SyllabusCRUDPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/admin/SyllabusCRUDPage.tsx) | ✅ | Subject/syllabus unit management |
| Admin [UserManagementPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/admin/UserManagementPage.tsx) | ✅ | User listing, search, update, toggle active |
| Admin [ClassManagementPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/admin/ClassManagementPage.tsx) | ✅ | Class creation + teacher assignment |
| SuperAdmin [DashboardPage.tsx](file:///c:/009/My%20Own%20Project/VidyaMitra_AI_EdTech/frontend/src/pages/superadmin/DashboardPage.tsx) | ✅ | Stats cards + module navigation |

---

## Remaining Work

### Frontend — Super Admin Pages

#### [NEW] `frontend/src/pages/superadmin/AICostDashboardPage.tsx`
- Detailed AI cost breakdown: daily/weekly/monthly costs in ₹
- Per-user cost table, cache-hit rate chart, token usage breakdown
- Cost trend over time (line chart or bar chart)
- Calls `GET /super-admin/ai-costs`

#### [NEW] `frontend/src/pages/superadmin/ChatAuditPage.tsx`
- Full AI conversation list with search/filter by user, date, flagged status
- Drill-down into individual conversations with full message history
- Calls `GET /super-admin/chat-audit` and `GET /super-admin/chat-audit/{id}`

#### [NEW] `frontend/src/pages/superadmin/MasterDataPage.tsx`
- Subjects, boards, grades management with CRUD operations
- Calls `GET /super-admin/master-data` and admin subject endpoints

---

### Frontend — Routing

#### [MODIFY] `frontend/src/App.tsx`
Wire actual routes for admin and super admin sub-pages instead of wildcard fallbacks:

**Admin routes:**
- `/admin/syllabus` → `SyllabusCRUDPage`
- `/admin/users` → `UserManagementPage`
- `/admin/classes` → `ClassManagementPage`

**Super Admin routes:**
- `/super-admin/ai-costs` → `AICostDashboardPage`
- `/super-admin/chat-audit` → `ChatAuditPage`
- `/super-admin/master-data` → `MasterDataPage`

---

### Tests

#### [NEW] `backend/tests/test_admin_superadmin.py`
- Admin service importability, function signatures
- SuperAdmin service importability, function signatures
- RBAC boundary checks (admin can't access superadmin endpoints, student can't access admin endpoints)

---

## Verification Plan

### Automated Tests
```bash
cd backend && pytest tests/ -v
cd frontend && npx tsc --noEmit && npx vite build
```

### Manual Verification
1. Login as admin → navigate to each sub-page (syllabus, users, classes)
2. Login as super admin → navigate to AI costs, chat audit, master data
3. Verify RBAC: admin cannot access super admin pages
4. Verify routing: all navigation links work correctly
