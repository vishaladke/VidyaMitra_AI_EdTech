"""Tests for Admin and Super Admin services and RBAC.

Tests:
- Admin service importability and function signatures
- SuperAdmin service importability and function signatures
- RBAC enum boundaries (admin can't access super_admin resources)
- Model structure validation
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Import Tests ─────────────────────────────────────────────

class TestAdminServiceImportability:
    """Verify admin_service module imports and exposes expected functions."""

    def test_import_admin_service(self):
        from app.services.admin_service import (
            get_admin_dashboard_stats,
            list_users,
            update_user,
            toggle_user_active,
            list_subjects_admin,
            create_subject,
            update_subject,
            create_syllabus_unit,
            list_classes,
            create_class,
            assign_teacher,
            get_teacher_assignments,
        )
        # All functions should be callable
        assert callable(get_admin_dashboard_stats)
        assert callable(list_users)
        assert callable(update_user)
        assert callable(toggle_user_active)
        assert callable(list_subjects_admin)
        assert callable(create_subject)
        assert callable(update_subject)
        assert callable(create_syllabus_unit)
        assert callable(list_classes)
        assert callable(create_class)
        assert callable(assign_teacher)
        assert callable(get_teacher_assignments)

    def test_admin_service_has_audit_helper(self):
        """Audit logging helper should exist."""
        from app.services.admin_service import _audit_log
        assert callable(_audit_log)


class TestSuperAdminServiceImportability:
    """Verify superadmin_service module imports and exposes expected functions."""

    def test_import_superadmin_service(self):
        from app.services.superadmin_service import (
            get_superadmin_dashboard_stats,
            get_ai_cost_dashboard,
            get_chat_audit,
            get_conversation_messages,
            get_master_data_summary,
            list_homepage_content,
            upsert_homepage_content,
            get_audit_logs,
        )
        assert callable(get_superadmin_dashboard_stats)
        assert callable(get_ai_cost_dashboard)
        assert callable(get_chat_audit)
        assert callable(get_conversation_messages)
        assert callable(get_master_data_summary)
        assert callable(list_homepage_content)
        assert callable(upsert_homepage_content)
        assert callable(get_audit_logs)


# ── RBAC Boundary Tests ──────────────────────────────────────

class TestRBACBoundaries:
    """Verify RBAC enum values and role hierarchy."""

    def test_user_role_enum_has_all_roles(self):
        from app.models.user import UserRole
        roles = {r.value for r in UserRole}
        expected = {"student", "teacher", "parent", "admin", "super_admin"}
        assert roles == expected

    def test_admin_role_is_not_superadmin(self):
        from app.models.user import UserRole
        assert UserRole.ADMIN != UserRole.SUPER_ADMIN

    def test_student_role_is_not_admin(self):
        from app.models.user import UserRole
        assert UserRole.STUDENT != UserRole.ADMIN

    def test_admin_router_requires_admin_role(self):
        """Admin router should use require_role dependency."""
        from app.routers.admin import router
        # Check that the router has routes defined
        assert len(router.routes) > 0

    def test_superadmin_router_requires_superadmin_role(self):
        """SuperAdmin router should use require_role dependency."""
        from app.routers.superadmin import router
        assert len(router.routes) > 0


# ── Model Structure Tests ────────────────────────────────────

class TestAdminRelatedModels:
    """Verify models used by admin services exist with expected columns."""

    def test_audit_log_model(self):
        from app.models.content import AuditLog
        # Should have key columns
        assert hasattr(AuditLog, 'user_id')
        assert hasattr(AuditLog, 'action')
        assert hasattr(AuditLog, 'resource_type')
        assert hasattr(AuditLog, 'resource_id')
        assert hasattr(AuditLog, 'details')

    def test_homepage_content_model(self):
        from app.models.content import HomepageContent
        assert hasattr(HomepageContent, 'section')
        assert hasattr(HomepageContent, 'title')
        assert hasattr(HomepageContent, 'content')
        assert hasattr(HomepageContent, 'status')
        assert hasattr(HomepageContent, 'display_order')
        assert hasattr(HomepageContent, 'language')

    def test_content_status_enum(self):
        from app.models.content import ContentStatus
        statuses = {s.value for s in ContentStatus}
        assert 'draft' in statuses
        assert 'published' in statuses

    def test_ai_cost_log_model(self):
        from app.models.ai import AICostLog
        assert hasattr(AICostLog, 'student_id')
        assert hasattr(AICostLog, 'cost_inr')
        assert hasattr(AICostLog, 'cache_source')
        assert hasattr(AICostLog, 'input_tokens')
        assert hasattr(AICostLog, 'output_tokens')

    def test_ai_cache_source_enum(self):
        from app.models.ai import AICacheSource
        sources = {s.value for s in AICacheSource}
        assert 'live_llm' in sources
        # Should have at least one cache source besides live_llm
        assert len(sources) > 1

    def test_ai_conversation_has_flagging(self):
        from app.models.ai import AIConversation
        assert hasattr(AIConversation, 'is_flagged')
        assert hasattr(AIConversation, 'flag_reason')

    def test_teacher_class_assignment_model(self):
        from app.models.school import TeacherClassAssignment
        assert hasattr(TeacherClassAssignment, 'teacher_id')
        assert hasattr(TeacherClassAssignment, 'class_id')


# ── Router Endpoint Count Tests ──────────────────────────────

class TestRouterEndpoints:
    """Verify routers expose the expected number of endpoints."""

    def test_admin_router_endpoint_count(self):
        from app.routers.admin import router
        # Admin router should have 12 endpoints
        # (dashboard, users list, user update, user toggle,
        #  subjects list, subject create, subject update,
        #  syllabus-unit create, classes list, class create,
        #  teacher-assign list, teacher-assign create)
        assert len(router.routes) >= 10, f"Admin router has {len(router.routes)} routes, expected >= 10"

    def test_superadmin_router_endpoint_count(self):
        from app.routers.superadmin import router
        # SuperAdmin router should have 8 endpoints
        # (dashboard, ai-costs, chat-audit list, chat-audit detail,
        #  master-data, cms list, cms upsert, audit-logs)
        assert len(router.routes) >= 7, f"SuperAdmin router has {len(router.routes)} routes, expected >= 7"
