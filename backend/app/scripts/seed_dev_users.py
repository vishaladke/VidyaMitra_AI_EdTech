"""Seed script — creates test users for all 5 roles (local dev only).

Run after Alembic migration:
    cd backend
    python -m app.scripts.seed_dev_users

Creates:
    Student:     9999999001  "राम पाटील"        grade 7
    Teacher:     9999999002  "सुनीता जाधव"
    Parent:      9999999003  "महेश कुलकर्णी"
    Admin:       9999999004  "Admin User"
    Super Admin: 9999999005  "Super Admin"       (with TOTP secret)
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import select
from app.database import async_session, engine
from app.models.base import Base
from app.models.user import User, UserRole, StudentProfile, TeacherProfile, ParentProfile
from app.utils.security import generate_totp_secret


SEED_USERS = [
    {
        "phone": "9999999001",
        "full_name": "राम पाटील",
        "role": UserRole.STUDENT,
        "profile": {"grade": 7, "board": "maharashtra_state", "medium": "marathi", "city": "Solapur"},
    },
    {
        "phone": "9999999002",
        "full_name": "सुनीता जाधव",
        "role": UserRole.TEACHER,
        "profile": {},
    },
    {
        "phone": "9999999003",
        "full_name": "महेश कुलकर्णी",
        "role": UserRole.PARENT,
        "profile": {"city": "Solapur"},
    },
    {
        "phone": "9999999004",
        "full_name": "Admin User",
        "role": UserRole.ADMIN,
        "profile": None,
    },
    {
        "phone": "9999999005",
        "full_name": "Super Admin",
        "role": UserRole.SUPER_ADMIN,
        "profile": None,
    },
]


async def seed():
    async with async_session() as db:
        for user_data in SEED_USERS:
            # Check if already exists
            result = await db.execute(
                select(User).where(User.phone == user_data["phone"])
            )
            existing = result.scalar_one_or_none()
            if existing:
                print(f"  ⏩ {user_data['role'].value:12s} {user_data['phone']}  already exists")
                continue

            # Create user
            user = User(
                phone=user_data["phone"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_active=True,
            )

            # Super Admin gets TOTP secret
            if user_data["role"] == UserRole.SUPER_ADMIN:
                user.totp_secret = generate_totp_secret()
                print(f"  🔐 Super Admin TOTP secret: {user.totp_secret}")

            db.add(user)
            await db.flush()

            # Create role-specific profile
            profile_data = user_data.get("profile")
            if user_data["role"] == UserRole.STUDENT and profile_data:
                profile = StudentProfile(user_id=user.id, **profile_data)
                db.add(profile)
            elif user_data["role"] == UserRole.TEACHER:
                profile = TeacherProfile(user_id=user.id)
                db.add(profile)
            elif user_data["role"] == UserRole.PARENT:
                profile = ParentProfile(
                    user_id=user.id,
                    city=profile_data.get("city", "Solapur") if profile_data else "Solapur",
                )
                db.add(profile)

            # Link parent to student
            if user_data["role"] == UserRole.PARENT:
                student_result = await db.execute(
                    select(User).where(User.phone == "9999999001")
                )
                student = student_result.scalar_one_or_none()
                if student:
                    from app.models.user import ParentStudentLink
                    link = ParentStudentLink(
                        parent_id=user.id,
                        student_id=student.id,
                        relationship_type="parent",
                        is_primary=True,
                    )
                    db.add(link)

            print(f"  ✅ {user_data['role'].value:12s} {user_data['phone']}  {user_data['full_name']}")

        await db.commit()
        print("\n🎉 Seeding complete!")


def main():
    print("🌱 Seeding dev database with test users...\n")
    asyncio.run(seed())


if __name__ == "__main__":
    main()
