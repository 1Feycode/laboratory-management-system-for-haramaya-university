# Testing Strategy and Test Architecture

This document defines the automated verification and quality assurance architecture for the Laboratory Asset Management and Maintenance Tracking System.

---

## 1. Testing Pyramid & Tool Selection

```text
               ┌───────────────────────┐
               │  End-to-End Testing   │  Playwright / Manual Acceptance
               │   (Critical Flows)    │  (Asset -> QR -> Fault -> Fix)
               └───────────┬───────────┘
                           │
               ┌───────────▼───────────┐
               │  API & DB Integration │  Pytest + HTTPX AsyncClient
               │   (Endpoints & SQL)   │  (PostgreSQL Test Fixtures)
               └───────────┬───────────┘
                           │
               ┌───────────▼───────────┐
               │     Unit Testing      │  Pytest (Backend Services/Schemas)
               │ (Isolated Components) │  Vitest (React Components & Hooks)
               └───────────────────────┘
```

| Testing Layer | Target Environment | Framework / Tool | Scope of Verification |
|---|---|---|---|
| **Backend Unit** | Local venv | **Pytest** | Pydantic schema validation, password hashing, asset code formatting. |
| **API & DB Integration**| Local PostgreSQL | **Pytest + HTTPX AsyncClient** | REST routes, JWT bearer headers, transaction rollback, foreign key constraints. |
| **Frontend Unit** | Node.js | **Vitest + React Testing Library** | Component rendering, form input validation, role-based visibility. |
| **End-to-End (E2E)** | Local browser | **Playwright** | Complete lifecycle: registration -> QR generation -> fault report -> closure. |

---

## 2. Test Environment Setup & Database Fixtures

Integration tests use an isolated test database (e.g., `hu_lab_test`) running on the local PostgreSQL instance to ensure true relational behavior (e.g., UUID functions, JSONB operators, foreign key cascades).

**Standard Pytest Fixture Architecture (`tests/conftest.py`):**
```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.main import app
from app.db.base import Base
from app.api.deps import get_db

TEST_DATABASE_URL = "postgresql+asyncpg://hu_admin:local_dev_password@localhost:5432/hu_lab_test"

@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine):
    async with AsyncSession(db_engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

---

## 3. High-Priority Test Cases

### 1. Asset & QR Lifecycle Tests
- `test_create_asset_with_unique_code`: Asserts that an asset receives an auto-generated code conforming to `HU-{COLLEGE}-{DEPT}-{SEQ}`.
- `test_duplicate_serial_number_conflict`: Re-registering the same manufacturer serial number returns HTTP 409 Conflict.
- `test_bench_lookup_by_code`: Querying `/api/v1/assets/lookup/{code}` resolves the complete passport with latency < 200 ms.

### 2. Maintenance & Lockout Tests
- `test_critical_fault_locks_asset`: Reporting a `CRITICAL` fault immediately sets asset status to `DEFECTIVE` and prevents transfers.
- `test_maintenance_log_and_closure`: Logging repair actions and custodian sign-off restores the asset to `OPERATIONAL`.

### 3. Transfer State Machine Tests
- `tests/test_transfers.py::test_transfer_requires_dual_acceptance_and_preserves_location_history`: Verifies state transitions, origin retention before approval, final location update, audit history, and the active-transfer metadata lock.
- `tests/test_transfers.py::test_transfer_rejects_invalid_scope_and_restores_asset`: Verifies room/laboratory integrity, receiver scope, rejection notes, and restoration at the origin.
- `tests/test_transfers.py::test_non_operational_asset_cannot_start_transfer`: Confirms only `OPERATIONAL` assets can enter a transfer.
- `tests/test_transfers.py::test_failed_final_commit_rolls_back_transfer_and_location`: Confirms a failed commit leaves transfer status, asset location, and asset status unchanged.

### 4. Security & Audit Immutability Tests
- `test_unauthenticated_requests_blocked`: Accessing protected endpoints without a Bearer token returns HTTP 401.
- `test_insufficient_role_forbidden`: A `LAB_TECH` attempting to provision a user account returns HTTP 403.
- `test_audit_log_immutable`: Direct SQL `UPDATE` or `DELETE` executions on `audit_logs` fail at the database constraint level.
