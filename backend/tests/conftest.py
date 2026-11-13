import asyncio
import os
import uuid
from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import make_url

from app.core.config import get_settings
from app.core.rate_limit import auth_rate_limiter
from app.core.token_store import refresh_token_store
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.models import College, Department, Role, User

TEST_ROLE_IDS = {
    "ULMD_ADMIN": uuid.UUID("00000000-0000-4000-8000-000000000001"),
    "MAINTENANCE_TECH": uuid.UUID("00000000-0000-4000-8000-000000000002"),
    "LAB_MANAGER": uuid.UUID("00000000-0000-4000-8000-000000000003"),
    "LAB_TECH": uuid.UUID("00000000-0000-4000-8000-000000000004"),
    "AUDITOR": uuid.UUID("00000000-0000-4000-8000-000000000005"),
}
TEST_ROLE_DESCRIPTIONS = {
    "ULMD_ADMIN": "University-wide application administrator",
    "MAINTENANCE_TECH": "Laboratory Technology Unit specialist",
    "LAB_MANAGER": "Laboratory custodian and manager",
    "LAB_TECH": "Laboratory technician or technical assistant",
    "AUDITOR": "Read-only inventory and compliance auditor",
}


def _test_database_url() -> str:
    application_url = make_url(get_settings().database_url)
    value = os.getenv("TEST_DATABASE_URL")
    if value:
        url = make_url(value)
    else:
        if not application_url.database:
            raise RuntimeError("The application database URL must include a database name")
        url = application_url.set(database=f"{application_url.database}_test")
    if (
        not url.database
        or not url.database.endswith("_test")
        or url == application_url
    ):
        raise RuntimeError(
            "Tests require a separate PostgreSQL database whose name ends with _test"
        )
    return url.render_as_string(hide_password=False)


@pytest.fixture(scope="session")
def test_engine():
    engine = create_async_engine(_test_database_url(), poolclass=NullPool)
    yield engine

    async def cleanup() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    asyncio.run(cleanup())


@pytest.fixture(autouse=True)
def isolated_test_data(test_engine) -> Iterator[None]:
    async def reset() -> None:
        async with test_engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(test_engine, expire_on_commit=False)
        async with factory() as session:
            session.add_all(
                [
                    Role(
                        id=TEST_ROLE_IDS[name],
                        name=name,
                        description=TEST_ROLE_DESCRIPTIONS[name],
                    )
                    for name in TEST_ROLE_IDS
                ]
            )
            await session.commit()

    asyncio.run(reset())
    asyncio.run(auth_rate_limiter.clear())
    asyncio.run(refresh_token_store.clear())
    yield


@pytest.fixture
def client(test_engine) -> Iterator[TestClient]:
    factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


async def _insert_test_user(
    test_engine,
    *,
    email: str,
    password_hash: str,
    role_name: str,
    department_id: uuid.UUID | None = None,
    is_active: bool = True,
) -> User:
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        role = await session.get(Role, TEST_ROLE_IDS[role_name])
        user = User(
            email=email,
            hashed_password=password_hash,
            full_name="Test User",
            role=role,
            department_id=department_id,
            is_active=is_active,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


def insert_test_user(test_engine, **kwargs) -> User:
        return asyncio.run(_insert_test_user(test_engine, **kwargs))


async def _insert_test_department(test_engine) -> uuid.UUID:
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        college = College(name="Test College", code="TC")
        session.add(college)
        await session.flush()
        department = Department(
            college_id=college.id,
            name="Test Department",
            code="TEST",
        )
        session.add(department)
        await session.commit()
        return department.id


def insert_test_department(test_engine) -> uuid.UUID:
    return asyncio.run(_insert_test_department(test_engine))
