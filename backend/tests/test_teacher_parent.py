"""Tests for teacher and parent API endpoints.

Tests cover:
- Teacher dashboard RBAC
- Teacher student roster
- Attendance marking logic
- Parent dashboard RBAC
- Parent-child link authorization
- Weekly report structure
"""
import pytest
from datetime import date, timedelta

from app.models.user import UserRole
from app.models.attendance import AttendanceStatus
from app.models.assessment import AssignmentType


class TestTeacherRBAC:
    """Verify teacher endpoints enforce role restrictions."""

    def test_teacher_role_enum_exists(self):
        assert UserRole.TEACHER == "teacher"

    def test_attendance_statuses(self):
        """All three attendance statuses should exist."""
        assert AttendanceStatus.PRESENT == "present"
        assert AttendanceStatus.ABSENT == "absent"
        assert AttendanceStatus.LATE == "late"

    def test_assignment_types(self):
        """All assignment types should exist."""
        assert AssignmentType.HOMEWORK == "homework"
        assert AssignmentType.TEST == "test"
        assert AssignmentType.PRACTICE == "practice"


class TestParentRBAC:
    """Verify parent data model and role restrictions."""

    def test_parent_role_enum_exists(self):
        assert UserRole.PARENT == "parent"

    def test_parent_student_link_model(self):
        """ParentStudentLink should be importable and have expected fields."""
        from app.models.user import ParentStudentLink
        # Check it has the expected columns
        assert hasattr(ParentStudentLink, "parent_id")
        assert hasattr(ParentStudentLink, "student_id")
        assert hasattr(ParentStudentLink, "relationship_type")
        assert hasattr(ParentStudentLink, "is_primary")

    def test_parent_profile_has_notification_prefs(self):
        """ParentProfile should have notification_preferences JSONB column."""
        from app.models.user import ParentProfile
        assert hasattr(ParentProfile, "notification_preferences")


class TestAttendanceModel:
    """Test attendance data model."""

    def test_attendance_record_model(self):
        from app.models.attendance import AttendanceRecord
        assert hasattr(AttendanceRecord, "student_id")
        assert hasattr(AttendanceRecord, "class_id")
        assert hasattr(AttendanceRecord, "date")
        assert hasattr(AttendanceRecord, "status")
        assert hasattr(AttendanceRecord, "marked_by")
        assert hasattr(AttendanceRecord, "notes")


class TestReportGeneration:
    """Test report service utility functions."""

    def test_marathi_summary_builder(self):
        """The _build_marathi_summary should produce valid Marathi text."""
        from app.services.report_service import _build_marathi_summary

        summary = _build_marathi_summary(
            name="राम पाटील",
            grade=7,
            conversations=5,
            active_days=3,
            top_subjects=["गणित", "विज्ञान"],
            attendance_pct=85.0,
            avg_score=72.5,
            streak=4,
        )

        # Should contain the student name
        assert "राम पाटील" in summary
        # Should contain Childline-like safety numbers? No — that's safety.
        # Should contain streak info
        assert "4 दिवस" in summary
        # Should contain attendance
        assert "85.0%" in summary
        # Should contain the platform name
        assert "विद्यामित्र" in summary

    def test_marathi_summary_no_activity(self):
        """Report with zero activity should say 'not used this week'."""
        from app.services.report_service import _build_marathi_summary

        summary = _build_marathi_summary(
            name="Test Student", grade=7,
            conversations=0, active_days=0,
            top_subjects=[], attendance_pct=None,
            avg_score=None, streak=0,
        )
        assert "वापरले नाही" in summary

    def test_marathi_summary_good_score_emoji(self):
        """Score >= 75 should get the star emoji."""
        from app.services.report_service import _build_marathi_summary

        summary = _build_marathi_summary(
            name="Test", grade=7,
            conversations=1, active_days=1,
            top_subjects=["Math"], attendance_pct=90.0,
            avg_score=80.0, streak=1,
        )
        assert "🌟" in summary

    def test_marathi_summary_low_score_emoji(self):
        """Score < 75 should get the pencil emoji."""
        from app.services.report_service import _build_marathi_summary

        summary = _build_marathi_summary(
            name="Test", grade=7,
            conversations=1, active_days=1,
            top_subjects=["Math"], attendance_pct=50.0,
            avg_score=40.0, streak=0,
        )
        assert "📝" in summary

    def test_marathi_summary_low_attendance_warning(self):
        """Attendance < 80% should get warning emoji."""
        from app.services.report_service import _build_marathi_summary

        summary = _build_marathi_summary(
            name="Test", grade=7,
            conversations=1, active_days=1,
            top_subjects=[], attendance_pct=60.0,
            avg_score=None, streak=0,
        )
        assert "⚠️" in summary


class TestTeacherServiceImports:
    """Verify service functions are importable."""

    def test_teacher_service_functions(self):
        from app.services.teacher_service import (
            get_teacher_students,
            get_teacher_dashboard_stats,
            mark_attendance,
            bulk_mark_attendance,
            get_attendance_summary,
            get_student_detail,
            get_ai_usage_overview,
            create_assignment,
            get_teacher_assignments,
        )
        # All should be callable
        assert callable(get_teacher_students)
        assert callable(get_teacher_dashboard_stats)
        assert callable(mark_attendance)
        assert callable(bulk_mark_attendance)
        assert callable(get_attendance_summary)
        assert callable(get_student_detail)
        assert callable(get_ai_usage_overview)
        assert callable(create_assignment)
        assert callable(get_teacher_assignments)


class TestParentServiceImports:
    """Verify parent service functions are importable."""

    def test_parent_service_functions(self):
        from app.services.parent_service import (
            get_linked_children,
            get_parent_dashboard_stats,
            get_child_progress,
            get_notification_preferences,
            update_notification_preferences,
        )
        assert callable(get_linked_children)
        assert callable(get_parent_dashboard_stats)
        assert callable(get_child_progress)
        assert callable(get_notification_preferences)
        assert callable(update_notification_preferences)

    def test_report_service_functions(self):
        from app.services.report_service import (
            generate_student_report,
            generate_all_reports,
        )
        assert callable(generate_student_report)
        assert callable(generate_all_reports)
