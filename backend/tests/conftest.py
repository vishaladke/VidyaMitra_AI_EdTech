"""Test fixtures for backend tests.

Handles Python 3.14 + asyncpg + Starlette BaseHTTPMiddleware event loop
compatibility issues on Windows. The core issue is that asyncpg's connection
teardown tries to create tasks on a closed loop during pytest cleanup.
"""
import asyncio
import sys
import uuid
import warnings
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.user import UserRole
from app.utils.security import create_access_token


# ── Python 3.14 + Windows: suppress asyncpg teardown noise ──────
# asyncpg's connection cleanup creates tasks on a closing loop, which
# raises RuntimeError on Python 3.14's stricter event loop. These errors
# happen ONLY during cleanup and don't affect test correctness.
# Filter them to keep test output clean.
warnings.filterwarnings("ignore", message="coroutine.*was never awaited", category=RuntimeWarning)


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async tests.

    On Windows + Python 3.14, we need a fresh loop that outlives
    all async fixtures to avoid teardown race conditions.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # Give pending tasks a moment to clean up
    loop.run_until_complete(asyncio.sleep(0.1))
    loop.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client that talks to the FastAPI app."""
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
