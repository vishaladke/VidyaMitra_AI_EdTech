"""Test fixtures for backend tests."""
import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.user import UserRole
from app.utils.security import create_access_token


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def make_auth_header(user_id: uuid.UUID, role: str) -> dict:
    """Helper: create an Authorization header with a valid JWT."""
    token = create_access_token(user_id, role)
    return {"Authorization": f"Bearer {token}"}


# Pre-generated test user IDs
TEST_STUDENT_ID = uuid.uuid4()
TEST_TEACHER_ID = uuid.uuid4()
TEST_PARENT_ID = uuid.uuid4()
TEST_ADMIN_ID = uuid.uuid4()
TEST_SUPERADMIN_ID = uuid.uuid4()

TEST_USERS = {
    "student": (TEST_STUDENT_ID, UserRole.STUDENT.value),
    "teacher": (TEST_TEACHER_ID, UserRole.TEACHER.value),
    "parent": (TEST_PARENT_ID, UserRole.PARENT.value),
    "admin": (TEST_ADMIN_ID, UserRole.ADMIN.value),
    "super_admin": (TEST_SUPERADMIN_ID, UserRole.SUPER_ADMIN.value),
}
