"""Secrets validation and rotation helper.

Pre-launch checklist item: "Secrets rotated from whatever was used in local dev."

This script validates that all secrets are properly configured for the target
environment, and warns about any that are still using default/dev values.

Usage:
    python -m app.scripts.validate_secrets
    python -m app.scripts.validate_secrets --env pilot
    python -m app.scripts.validate_secrets --env production
"""
import sys
import os
import secrets
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


# ── Default/dev values that MUST be changed before deploy ─────────

DANGEROUS_DEFAULTS = {
    "JWT_SECRET": [
        "change_me_to_a_long_random_string",
        "",
    ],
    "SUPERADMIN_URL_PATH": [
        "change-me-to-something-unguessable",
        "",
    ],
    "DEV_OTP_CODE": [
        "123456",  # Must be removed or randomized in production
    ],
}

REQUIRED_FOR_PILOT = {
    "DATABASE_URL": "Neon PostgreSQL connection string",
    "REDIS_URL": "Upstash Redis URL",
    "JWT_SECRET": "Unique, random 64-char string",
    "SUPERADMIN_URL_PATH": "Unguessable URL path for Super Admin",
}

REQUIRED_FOR_PRODUCTION = {
    **REQUIRED_FOR_PILOT,
    "ANTHROPIC_API_KEY": "Claude API key for AI Guru",
    "RAZORPAY_KEY_ID": "Razorpay live API key",
    "RAZORPAY_KEY_SECRET": "Razorpay live secret key",
    "RAZORPAY_WEBHOOK_SECRET": "Razorpay webhook secret",
    "WHATSAPP_BSP_API_KEY": "WhatsApp BSP API key",
    "WHATSAPP_BSP_URL": "WhatsApp BSP API base URL",
    "WHATSAPP_PHONE_NUMBER_ID": "WhatsApp business phone number ID",
}


def generate_secure_secret(length: int = 64) -> str:
    """Generate a cryptographically secure random string."""
    return secrets.token_urlsafe(length)


def validate_secrets(target_env: str = "pilot") -> dict:
    """Validate all secrets for the target environment.

    Returns dict with:
    - errors: critical issues that MUST be fixed
    - warnings: non-critical but recommended changes
    - ok: properly configured items
    """
    errors = []
    warnings = []
    ok = []

    # ── Check dangerous defaults ──────────────────────────────────
    for var_name, dangerous_values in DANGEROUS_DEFAULTS.items():
        current_value = os.environ.get(var_name, "")
        if current_value in dangerous_values:
            if target_env == "local":
                warnings.append(
                    f"⚠️  {var_name} is using a default value "
                    f"(acceptable for local dev)"
                )
            else:
                errors.append(
                    f"🚫 {var_name} is using a default/dev value — "
                    f"MUST be changed before {target_env} deploy"
                )
        else:
            ok.append(f"✅ {var_name} is set to a custom value")

    # ── Check required vars for target environment ────────────────
    required = REQUIRED_FOR_PILOT if target_env == "pilot" else REQUIRED_FOR_PRODUCTION

    for var_name, description in required.items():
        current_value = os.environ.get(var_name, "")
        if not current_value:
            errors.append(f"🚫 {var_name} is not set — {description}")
        else:
            ok.append(f"✅ {var_name} is configured")

    # ── Check JWT_SECRET strength ─────────────────────────────────
    jwt_secret = os.environ.get("JWT_SECRET", "")
    if jwt_secret and len(jwt_secret) < 32:
        warnings.append(
            f"⚠️  JWT_SECRET is only {len(jwt_secret)} chars — "
            f"recommend 64+ chars for production"
        )

    # ── Check environment consistency ─────────────────────────────
    env = os.environ.get("ENVIRONMENT", "local")
    if target_env != "local" and env == "local":
        warnings.append(
            f"⚠️  ENVIRONMENT is set to 'local' — should be '{target_env}' "
            f"for {target_env} deploy"
        )

    # ── Check payment provider consistency ────────────────────────
    payment = os.environ.get("PAYMENT_PROVIDER", "offline_mock")
    if target_env == "production" and payment != "razorpay_live":
        warnings.append(
            f"⚠️  PAYMENT_PROVIDER is '{payment}' — "
            f"should be 'razorpay_live' for production"
        )
    elif target_env == "pilot" and payment == "offline_mock":
        warnings.append(
            f"⚠️  PAYMENT_PROVIDER is 'offline_mock' — "
            f"consider switching to 'razorpay_test' for pilot"
        )

    # ── Check OTP provider ────────────────────────────────────────
    otp = os.environ.get("OTP_PROVIDER", "dev_mock")
    if target_env != "local" and otp == "dev_mock":
        errors.append(
            f"🚫 OTP_PROVIDER is 'dev_mock' — "
            f"MUST use 'firebase' or 'msg91' for {target_env}"
        )

    # ── Check notification provider ───────────────────────────────
    notif = os.environ.get("NOTIFICATION_PROVIDER", "mock")
    if target_env == "production" and notif == "mock":
        warnings.append(
            f"⚠️  NOTIFICATION_PROVIDER is 'mock' — "
            f"switch to 'whatsapp' for production"
        )

    return {"errors": errors, "warnings": warnings, "ok": ok}


def print_validation_report(results: dict, target_env: str):
    """Print a formatted validation report."""
    print(f"\n{'='*60}")
    print(f"  🔐 VidyaMitra Secrets Validation — {target_env.upper()}")
    print(f"{'='*60}\n")

    if results["errors"]:
        print(f"❌ ERRORS ({len(results['errors'])}) — must fix before deploy:\n")
        for err in results["errors"]:
            print(f"  {err}")
        print()

    if results["warnings"]:
        print(f"⚠️  WARNINGS ({len(results['warnings'])}) — recommended:\n")
        for warn in results["warnings"]:
            print(f"  {warn}")
        print()

    if results["ok"]:
        print(f"✅ OK ({len(results['ok'])}):\n")
        for item in results["ok"]:
            print(f"  {item}")
        print()

    # Summary
    total = len(results["errors"]) + len(results["warnings"]) + len(results["ok"])
    print(f"{'='*60}")
    if results["errors"]:
        print(f"  ❌ {len(results['errors'])} critical issues — NOT ready for {target_env}")
    elif results["warnings"]:
        print(f"  ⚠️  {len(results['warnings'])} warnings — mostly ready for {target_env}")
    else:
        print(f"  ✅ All {total} checks passed — ready for {target_env}")
    print(f"{'='*60}\n")

    # Generate suggested secrets if there are errors
    if results["errors"]:
        print("💡 Suggested secure values:\n")
        print(f"  JWT_SECRET={generate_secure_secret(64)}")
        print(f"  SUPERADMIN_URL_PATH={generate_secure_secret(24)}")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate secrets for deployment")
    parser.add_argument(
        "--env",
        choices=["local", "pilot", "production"],
        default="pilot",
        help="Target environment (default: pilot)",
    )
    args = parser.parse_args()

    results = validate_secrets(args.env)
    print_validation_report(results, args.env)

    # Exit with error code if there are critical issues
    if results["errors"]:
        sys.exit(1)
