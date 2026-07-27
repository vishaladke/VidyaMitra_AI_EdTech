"""Seed subscription plans — run once to populate the subscriptions table.

Usage:
    python -m app.scripts.seed_subscriptions

Plans match the pricing in ARCHITECTURE.md § public homepage:
- Free Trial: 30 days, ₹0
- Monthly: 30 days, ₹99
- Quarterly: 90 days, ₹249 (17% savings)
- Annual: 365 days, ₹799 (33% savings)
"""
import asyncio
import logging

from sqlalchemy import select
from app.database import async_session_factory
from app.models.payment import Subscription

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PLANS = [
    {
        "name": "Free Trial",
        "description": "30 दिवस मोफत — AI गुरू बेसिक ऍक्सेस",
        "price_inr": 0.00,
        "duration_days": 30,
        "features": {
            "ai_conversations_per_day": 5,
            "voice_enabled": False,
            "weekly_reports": True,
            "priority_support": False,
        },
        "is_active": True,
    },
    {
        "name": "Monthly",
        "description": "मासिक सदस्यता — सर्व वैशिष्ट्ये अनलॉक",
        "price_inr": 99.00,
        "duration_days": 30,
        "features": {
            "ai_conversations_per_day": -1,  # unlimited
            "voice_enabled": True,
            "weekly_reports": True,
            "priority_support": False,
        },
        "is_active": True,
    },
    {
        "name": "Quarterly",
        "description": "त्रैमासिक सदस्यता — 17% बचत",
        "price_inr": 249.00,
        "duration_days": 90,
        "features": {
            "ai_conversations_per_day": -1,
            "voice_enabled": True,
            "weekly_reports": True,
            "priority_support": True,
        },
        "is_active": True,
    },
    {
        "name": "Annual",
        "description": "वार्षिक सदस्यता — 33% बचत, सर्वोत्तम मूल्य",
        "price_inr": 799.00,
        "duration_days": 365,
        "features": {
            "ai_conversations_per_day": -1,
            "voice_enabled": True,
            "weekly_reports": True,
            "priority_support": True,
            "early_access": True,
        },
        "is_active": True,
    },
]


async def seed_subscriptions():
    """Insert subscription plans if they don't already exist."""
    async with async_session_factory() as db:
        for plan_data in PLANS:
            # Check if plan already exists
            result = await db.execute(
                select(Subscription).where(Subscription.name == plan_data["name"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.info(f"  ⏭️  Plan already exists: {plan_data['name']}")
                continue

            plan = Subscription(**plan_data)
            db.add(plan)
            logger.info(f"  ✅ Created plan: {plan_data['name']} — ₹{plan_data['price_inr']}")

        await db.commit()
        logger.info("🎉 Subscription plans seeded successfully")


if __name__ == "__main__":
    print("🌱 Seeding subscription plans...")
    asyncio.run(seed_subscriptions())
