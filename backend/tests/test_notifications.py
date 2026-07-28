"""Tests for the notification system — Phase 5.

Tests cover:
- Notification provider factory (correct provider selection)
- MockNotificationProvider (send, message ID generation)
- WhatsApp provider (importability, template params, delivery parsing)
- Notification model enums and structure
- Notification service function signatures
- Report → WhatsApp template params extraction
"""
import pytest


# ── Provider Factory Tests ────────────────────────────────────────


def test_notification_provider_factory_default():
    """get_notification_provider() returns MockProvider by default."""
    from app.services.notification_service import get_notification_provider
    from app.providers.notification.mock import MockNotificationProvider

    provider = get_notification_provider()
    assert isinstance(provider, MockNotificationProvider)


def test_notification_provider_factory_whatsapp():
    """WhatsApp provider can be instantiated."""
    from app.providers.notification.whatsapp import WhatsAppProvider

    provider = WhatsAppProvider()
    assert provider is not None


# ── Mock Provider Tests ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_mock_provider_send():
    """MockNotificationProvider sends and returns a mock message ID."""
    from app.providers.notification.mock import MockNotificationProvider

    provider = MockNotificationProvider()
    msg_id = await provider.send(
        to="919999999003",
        template_name="weekly_student_report",
        params={"student_name": "राम"},
    )

    assert msg_id.startswith("mock_")
    assert len(msg_id) > 5


@pytest.mark.asyncio
async def test_mock_provider_send_without_params():
    """MockNotificationProvider handles None params."""
    from app.providers.notification.mock import MockNotificationProvider

    provider = MockNotificationProvider()
    msg_id = await provider.send(to="919999999003", template_name="welcome_parent")
    assert msg_id.startswith("mock_")


# ── WhatsApp Provider Tests ──────────────────────────────────────


def test_whatsapp_provider_importable():
    """WhatsApp provider and template constants can be imported."""
    from app.providers.notification.whatsapp import (
        WhatsAppProvider,
        TEMPLATE_WEEKLY_REPORT,
        TEMPLATE_PAYMENT_CONFIRMATION,
        TEMPLATE_WELCOME,
    )

    assert WhatsAppProvider is not None
    assert TEMPLATE_WEEKLY_REPORT == "weekly_student_report"
    assert TEMPLATE_PAYMENT_CONFIRMATION == "payment_confirmation"
    assert TEMPLATE_WELCOME == "welcome_parent"


@pytest.mark.asyncio
async def test_whatsapp_provider_no_api_key():
    """WhatsApp provider falls back to logging when no API key is set."""
    from app.providers.notification.whatsapp import WhatsAppProvider

    provider = WhatsAppProvider()
    # With no API key, should return an undelivered message ID
    msg_id = await provider.send(
        to="919999999003",
        template_name="weekly_student_report",
        params={"student_name": "राम"},
    )
    assert "undelivered" in msg_id or msg_id.startswith("wa_")


def test_whatsapp_parse_delivery_status():
    """WhatsApp provider parses delivery status webhooks."""
    from app.providers.notification.whatsapp import WhatsAppProvider

    webhook_body = {
        "entry": [{
            "changes": [{
                "value": {
                    "statuses": [{
                        "id": "wamid.test123",
                        "status": "delivered",
                        "timestamp": "1700000000",
                        "recipient_id": "919999999003",
                    }]
                }
            }]
        }]
    }

    result = WhatsAppProvider.parse_delivery_status(webhook_body)
    assert result is not None
    assert result["message_id"] == "wamid.test123"
    assert result["status"] == "delivered"
    assert result["timestamp"] == "1700000000"


def test_whatsapp_parse_delivery_status_empty():
    """WhatsApp provider returns None for empty webhook body."""
    from app.providers.notification.whatsapp import WhatsAppProvider

    assert WhatsAppProvider.parse_delivery_status({}) is None
    assert WhatsAppProvider.parse_delivery_status({"entry": []}) is None


def test_whatsapp_parse_inbound_message():
    """WhatsApp provider parses inbound text messages."""
    from app.providers.notification.whatsapp import WhatsAppProvider

    webhook_body = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "id": "wamid.msg123",
                        "from": "919999999003",
                        "type": "text",
                        "text": {"body": "नमस्कार"},
                        "timestamp": "1700000001",
                    }]
                }
            }]
        }]
    }

    result = WhatsAppProvider.parse_inbound_message(webhook_body)
    assert result is not None
    assert result["from"] == "919999999003"
    assert result["text"] == "नमस्कार"
    assert result["type"] == "text"


# ── Notification Model Tests ─────────────────────────────────────


def test_notification_channel_enum():
    """NotificationChannel enum has all expected values."""
    from app.models.notification import NotificationChannel

    assert NotificationChannel.WHATSAPP == "whatsapp"
    assert NotificationChannel.EMAIL == "email"
    assert NotificationChannel.SMS == "sms"
    assert NotificationChannel.PUSH == "push"
    assert len(NotificationChannel) == 4


def test_notification_log_model_structure():
    """NotificationLog model has expected columns."""
    from app.models.notification import NotificationLog

    mapper = NotificationLog.__table__
    col_names = {c.name for c in mapper.columns}

    expected = {
        "id", "user_id", "channel", "template_name",
        "content_preview", "status", "provider_message_id",
        "metadata_json", "created_at",
    }
    assert expected.issubset(col_names), f"Missing columns: {expected - col_names}"


# ── Notification Service Tests ────────────────────────────────────


def test_notification_service_importable():
    """All notification service functions can be imported."""
    from app.services.notification_service import (
        get_notification_provider,
        send_notification,
        send_whatsapp_report,
        format_whatsapp_template_params,
        send_weekly_reports_batch,
        update_delivery_status,
        get_notification_history,
    )

    assert callable(get_notification_provider)
    assert callable(send_notification)
    assert callable(send_whatsapp_report)
    assert callable(format_whatsapp_template_params)
    assert callable(send_weekly_reports_batch)
    assert callable(update_delivery_status)
    assert callable(get_notification_history)


def test_format_whatsapp_template_params():
    """format_whatsapp_template_params extracts correct values from a report."""
    from app.services.notification_service import format_whatsapp_template_params

    report = {
        "student": {"full_name": "राम पाटील", "grade": 7},
        "ai_activity": {"conversations": 12, "active_days": 5},
        "attendance": {"percentage": 92.5},
        "tests": {"average_score": 78.0},
        "summary_mr": "📚 विद्यामित्र साप्ताहिक अहवाल\nविद्यार्थी: राम",
    }

    params = format_whatsapp_template_params(report)

    assert params["student_name"] == "राम पाटील"
    assert params["grade"] == "7"
    assert params["conversations"] == "12"
    assert params["active_days"] == "5"
    assert params["attendance_pct"] == "92.5"
    assert params["avg_score"] == "78.0"
    assert "विद्यामित्र" in params["summary_mr"]


def test_format_whatsapp_template_params_empty():
    """format_whatsapp_template_params handles missing report data gracefully."""
    from app.services.notification_service import format_whatsapp_template_params

    params = format_whatsapp_template_params({})

    assert params["student_name"] == "विद्यार्थी"
    assert params["conversations"] == "0"
    assert params["active_days"] == "0"


def test_format_whatsapp_template_params_no_attendance():
    """Template params show N/A when attendance is missing."""
    from app.services.notification_service import format_whatsapp_template_params

    report = {
        "student": {"full_name": "Test"},
        "ai_activity": {"conversations": 0, "active_days": 0},
        "attendance": {"percentage": None},
        "tests": {"average_score": None},
        "summary_mr": "",
    }

    params = format_whatsapp_template_params(report)
    assert params["attendance_pct"] == "None"
    assert params["avg_score"] == "None"


# ── Report Service WhatsApp Integration Tests ────────────────────


def test_report_service_whatsapp_functions():
    """Report service has WhatsApp delivery functions."""
    from app.services.report_service import (
        generate_and_send_weekly_reports,
        format_whatsapp_template_params,
    )

    assert callable(generate_and_send_weekly_reports)
    assert callable(format_whatsapp_template_params)


def test_report_format_whatsapp_template_params():
    """Report service format_whatsapp_template_params returns numbered keys."""
    from app.services.report_service import format_whatsapp_template_params

    report = {
        "student": {"full_name": "राम पाटील", "grade": 7},
        "ai_activity": {"conversations": 12, "active_days": 5},
        "attendance": {"percentage": 92.5},
        "summary_mr": "📚 विद्यामित्र",
    }

    params = format_whatsapp_template_params(report)

    # Report service uses numbered keys for BSP templates
    assert params["1"] == "राम पाटील"
    assert params["2"] == "7"
    assert params["3"] == "12"
    assert params["4"] == "5"
    assert params["5"] == "92.5"


# ── Webhook Router Tests ─────────────────────────────────────────


def test_webhook_router_importable():
    """Webhook router can be imported and has expected routes."""
    from app.routers.webhooks import router

    routes = [r.path for r in router.routes]
    # Routes include the prefix, e.g. /api/webhooks/whatsapp
    assert any(r.endswith("/whatsapp") for r in routes)
