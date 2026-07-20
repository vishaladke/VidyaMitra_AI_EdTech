"""001 — Initial schema: all 22 tables for VidyaMitra EdTech.

Revision ID: 001_initial
Revises: None
Create Date: 2026-07-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extensions ────────────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')

    # ── Enums ─────────────────────────────────────────────
    user_role = postgresql.ENUM("student", "teacher", "parent", "admin", "super_admin", name="user_role", create_type=False)
    gender_enum = postgresql.ENUM("male", "female", "other", name="gender_enum", create_type=False)
    payment_status = postgresql.ENUM("pending", "success", "failed", "refunded", name="payment_status", create_type=False)
    payment_provider_enum = postgresql.ENUM("offline_mock", "razorpay_test", "razorpay_live", name="payment_provider_enum", create_type=False)
    attendance_status = postgresql.ENUM("present", "absent", "late", name="attendance_status", create_type=False)
    question_type = postgresql.ENUM("mcq", "short_answer", "long_answer", "true_false", name="question_type", create_type=False)
    difficulty_level = postgresql.ENUM("easy", "medium", "hard", name="difficulty_level", create_type=False)
    ai_cache_source = postgresql.ENUM("exact_redis", "semantic_pgvector", "faq_bank", "live_llm", name="ai_cache_source", create_type=False)
    content_status = postgresql.ENUM("draft", "published", "archived", name="content_status", create_type=False)
    assignment_type = postgresql.ENUM("homework", "test", "practice", name="assignment_type", create_type=False)
    notification_channel = postgresql.ENUM("whatsapp", "email", "sms", "push", name="notification_channel", create_type=False)

    # Create all enums
    for e in [user_role, gender_enum, payment_status, payment_provider_enum,
              attendance_status, question_type, difficulty_level, ai_cache_source,
              content_status, assignment_type, notification_channel]:
        e.create(op.get_bind(), checkfirst=True)

    # ── Users ─────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("phone", sa.String(15), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=True),
        sa.Column("role", user_role, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("totp_secret", sa.String(64), nullable=True),
        sa.Column("totp_verified", sa.Boolean, server_default=sa.text("false")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_users_phone", "users", ["phone"])
    op.create_index("idx_users_role", "users", ["role"])

    # ── Schools (stubbed) ─────────────────────────────────
    op.create_table(
        "schools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("city", sa.String(100), server_default="Solapur"),
        sa.Column("board", sa.String(50), server_default="maharashtra_state"),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("contact_phone", sa.String(15), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Classes ───────────────────────────────────────────
    op.create_table(
        "classes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id", ondelete="SET NULL"), nullable=True),
        sa.Column("grade", sa.SmallInteger, nullable=False),
        sa.Column("name", sa.String(50), nullable=True),
        sa.Column("academic_year", sa.String(10), nullable=False, server_default="2026-27"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Sections ──────────────────────────────────────────
    op.create_table(
        "sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(10), nullable=False, server_default="A"),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Student Profiles ──────────────────────────────────
    op.create_table(
        "student_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("grade", sa.SmallInteger, nullable=False),
        sa.Column("board", sa.String(50), nullable=False, server_default="maharashtra_state"),
        sa.Column("medium", sa.String(20), nullable=False, server_default="marathi"),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id", ondelete="SET NULL"), nullable=True),
        sa.Column("section_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sections.id", ondelete="SET NULL"), nullable=True),
        sa.Column("date_of_birth", sa.Date, nullable=True),
        sa.Column("gender", gender_enum, nullable=True),
        sa.Column("city", sa.String(100), server_default="Solapur"),
        sa.Column("streak_days", sa.SmallInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_student_profiles_grade", "student_profiles", ["grade"])
    op.create_index("idx_student_profiles_school", "student_profiles", ["school_id"])

    # ── Teacher Profiles ──────────────────────────────────
    op.create_table(
        "teacher_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("schools.id", ondelete="SET NULL"), nullable=True),
        sa.Column("qualification", sa.String(255), nullable=True),
        sa.Column("subjects", postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Parent Profiles ───────────────────────────────────
    op.create_table(
        "parent_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("city", sa.String(100), server_default="Solapur"),
        sa.Column("notification_preferences", postgresql.JSONB, server_default='{"whatsapp": true, "email": false}'),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Parent-Student Links ──────────────────────────────
    op.create_table(
        "parent_student_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", sa.String(50), server_default="parent"),
        sa.Column("is_primary", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("parent_id", "student_id", name="uq_parent_student_link"),
    )
    op.create_index("idx_parent_student_parent", "parent_student_links", ["parent_id"])
    op.create_index("idx_parent_student_student", "parent_student_links", ["student_id"])

    # ── Subjects ──────────────────────────────────────────
    op.create_table(
        "subjects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("name_en", sa.String(100), nullable=True),
        sa.Column("grade", sa.SmallInteger, nullable=False),
        sa.Column("board", sa.String(50), nullable=False, server_default="maharashtra_state"),
        sa.Column("icon_url", sa.Text, nullable=True),
        sa.Column("display_order", sa.SmallInteger, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", "grade", "board", name="uq_subject_name_grade_board"),
    )

    # ── Teacher-Class Assignments ─────────────────────────
    op.create_table(
        "teacher_class_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("teacher_id", "class_id", "subject_id", name="uq_teacher_class_subject"),
    )

    # ── Syllabus Units ────────────────────────────────────
    op.create_table(
        "syllabus_units",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("syllabus_units.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("title_en", sa.String(255), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("unit_type", sa.String(20), nullable=False, server_default="chapter"),
        sa.Column("display_order", sa.SmallInteger, server_default=sa.text("0")),
        sa.Column("version", sa.SmallInteger, nullable=False, server_default=sa.text("1")),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("pdf_url", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_syllabus_units_subject", "syllabus_units", ["subject_id"])
    op.create_index("idx_syllabus_units_parent", "syllabus_units", ["parent_id"])

    # ── Assignments ───────────────────────────────────────
    op.create_table(
        "assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("assignment_type", assignment_type, nullable=False, server_default="homework"),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("syllabus_unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("syllabus_units.id", ondelete="SET NULL"), nullable=True),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Questions ─────────────────────────────────────────
    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=True),
        sa.Column("syllabus_unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("syllabus_units.id", ondelete="SET NULL"), nullable=True),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("question_type", question_type, nullable=False, server_default="mcq"),
        sa.Column("options", postgresql.JSONB, nullable=True),
        sa.Column("correct_answer", sa.Text, nullable=True),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column("marks", sa.Numeric(4, 2), nullable=False, server_default=sa.text("1.0")),
        sa.Column("difficulty", difficulty_level, server_default="medium"),
        sa.Column("display_order", sa.SmallInteger, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Test Attempts ─────────────────────────────────────
    op.create_table(
        "test_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("answers", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("max_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_graded", sa.Boolean, server_default=sa.text("false")),
        sa.Column("graded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── AI Conversations ──────────────────────────────────
    op.create_table(
        "ai_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("is_flagged", sa.Boolean, server_default=sa.text("false")),
        sa.Column("flag_reason", sa.Text, nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_ai_conversations_student", "ai_conversations", ["student_id"])

    # ── AI Messages ───────────────────────────────────────
    op.create_table(
        "ai_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("topic_tag", sa.String(100), nullable=True),
        sa.Column("is_voice", sa.Boolean, server_default=sa.text("false")),
        sa.Column("audio_url", sa.Text, nullable=True),
        sa.Column("cache_source", ai_cache_source, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_ai_messages_conversation", "ai_messages", ["conversation_id"])

    # ── AI Cost Logs ──────────────────────────────────────
    op.create_table(
        "ai_cost_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_conversations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_messages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("cache_source", ai_cache_source, nullable=False),
        sa.Column("model_used", sa.String(50), nullable=True),
        sa.Column("input_tokens", sa.Integer, server_default=sa.text("0")),
        sa.Column("output_tokens", sa.Integer, server_default=sa.text("0")),
        sa.Column("prompt_cache_hit", sa.Boolean, server_default=sa.text("false")),
        sa.Column("cost_usd", sa.Numeric(10, 6), server_default=sa.text("0")),
        sa.Column("cost_inr", sa.Numeric(10, 4), server_default=sa.text("0")),
        sa.Column("response_time_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_ai_cost_logs_student", "ai_cost_logs", ["student_id"])
    op.create_index("idx_ai_cost_logs_created", "ai_cost_logs", ["created_at"])

    # ── AI Semantic Cache ─────────────────────────────────
    op.create_table(
        "ai_semantic_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("normalized_question", sa.Text, nullable=False),
        sa.Column("question_embedding", Vector(1536)),
        sa.Column("grade", sa.SmallInteger, nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("hit_count", sa.Integer, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── FAQ Bank ──────────────────────────────────────────
    op.create_table(
        "faq_bank",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("question_embedding", Vector(1536)),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("grade", sa.SmallInteger, nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("syllabus_unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("syllabus_units.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Attendance Records ────────────────────────────────
    op.create_table(
        "attendance_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("status", attendance_status, nullable=False, server_default="present"),
        sa.Column("marked_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("student_id", "class_id", "date", name="uq_attendance_student_class_date"),
    )
    op.create_index("idx_attendance_student_date", "attendance_records", ["student_id", "date"])
    op.create_index("idx_attendance_class_date", "attendance_records", ["class_id", "date"])

    # ── Subscriptions ─────────────────────────────────────
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("price_inr", sa.Numeric(10, 2), nullable=False),
        sa.Column("duration_days", sa.Integer, nullable=False),
        sa.Column("features", postgresql.JSONB, server_default="{}"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Payments ──────────────────────────────────────────
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("amount_inr", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("status", payment_status, nullable=False, server_default="pending"),
        sa.Column("provider", payment_provider_enum, nullable=False),
        sa.Column("provider_order_id", sa.String(255), nullable=True),
        sa.Column("provider_payment_id", sa.String(255), nullable=True),
        sa.Column("provider_signature", sa.String(255), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, server_default="{}"),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_payments_user", "payments", ["user_id"])
    op.create_index("idx_payments_status", "payments", ["status"])

    # ── Notification Logs ─────────────────────────────────
    op.create_table(
        "notification_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", notification_channel, nullable=False),
        sa.Column("template_name", sa.String(100), nullable=True),
        sa.Column("content_preview", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), server_default="sent"),
        sa.Column("provider_message_id", sa.String(255), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Homepage Content ──────────────────────────────────
    op.create_table(
        "homepage_content",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("section", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("media_url", sa.Text, nullable=True),
        sa.Column("display_order", sa.SmallInteger, server_default=sa.text("0")),
        sa.Column("status", content_status, server_default="draft"),
        sa.Column("language", sa.String(10), server_default="mr"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Ad Slots (DPDP-compliant) ─────────────────────────
    op.create_table(
        "ad_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("placement", sa.String(50), nullable=False),
        sa.Column("content_html", sa.Text, nullable=True),
        sa.Column("target_url", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("false")),
        sa.Column("impressions", sa.Integer, server_default=sa.text("0")),
        sa.Column("clicks", sa.Integer, server_default=sa.text("0")),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── Audit Logs ────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", postgresql.JSONB, server_default="{}"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_audit_logs_user", "audit_logs", ["user_id"])
    op.create_index("idx_audit_logs_created", "audit_logs", ["created_at"])
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"])

    # ── Vector indexes (IVFFlat) — create after tables ────
    # Note: IVFFlat requires data to exist for training. At init time with no data,
    # we skip the IVFFlat index and will add it once the FAQ bank is seeded.
    # For now, use exact (sequential) search which works fine at small scale.


def downgrade() -> None:
    # Drop all tables in reverse dependency order
    tables = [
        "audit_logs", "ad_slots", "homepage_content", "notification_logs",
        "payments", "subscriptions", "attendance_records",
        "faq_bank", "ai_semantic_cache", "ai_cost_logs", "ai_messages", "ai_conversations",
        "test_attempts", "questions", "assignments",
        "syllabus_units", "subjects",
        "teacher_class_assignments", "parent_student_links",
        "parent_profiles", "teacher_profiles", "student_profiles",
        "sections", "classes", "schools", "users",
    ]
    for t in tables:
        op.drop_table(t)

    # Drop enums
    enums = [
        "notification_channel", "assignment_type", "content_status",
        "ai_cache_source", "difficulty_level", "question_type",
        "attendance_status", "payment_provider_enum", "payment_status",
        "gender_enum", "user_role",
    ]
    for e in enums:
        sa.Enum(name=e).drop(op.get_bind(), checkfirst=True)
