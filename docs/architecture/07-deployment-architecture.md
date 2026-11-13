# 07. Deployment Architecture Specification

## 1. Development & Local Deployment Profile (Windows 8 GB RAM)
On the Windows 10/11 development laptop, the React/Vite frontend and FastAPI/Uvicorn backend run as native processes. PostgreSQL 15+ runs as the only Docker Desktop service. No application containers, Kubernetes, or additional infrastructure services are required for Stages 1 and 2.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   WINDOWS 10/11 HOST (8 GB TOTAL RAM)                  │
│                                                                        │
│   ┌─────────────────────┐   ┌─────────────────────┐   ┌────────────┐   │
│   │ Node.js (Vite HMR)  │   │ Python Virtual Env  │   │ Docker Desktop       │
│   │ React Dev Server    │   │ FastAPI / Uvicorn   │   │ PostgreSQL 15+       │
│   │ (Port 5173)         │   │ (Port 8000)         │   │ (localhost:5432)     │
│   └─────────────────────┘   └─────────────────────┘   │ Named data volume    │
│                                                       └──────────────────────┘
│                                                                        │
│   Only PostgreSQL runs in Docker; resource use depends on Docker Desktop│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Local Setup Guide (Windows + Docker Desktop)

### Step 1: Database Setup
1. If the repository-root `.env` does not exist, copy `.env.example` to `.env`; preserve existing local credentials. Set a strong local `POSTGRES_PASSWORD` and the matching password in `DATABASE_URL`.
2. From the repository root, start the database:
   ```powershell
   docker compose up -d db
   docker compose ps
   ```
3. Wait until the `db` service is `healthy`. Compose maps the container's port `5432` to the configured Windows host port (default `5432`) on `127.0.0.1`.
4. PostgreSQL data is stored in the named volume `hu_lab_postgres_data`. Do not remove the volume during routine development. PostgreSQL is not installed directly on Windows.
5. Configure a random `SECRET_KEY` of at least 32 bytes. Keep it in the ignored root `.env`; never commit it.
6. `ASSET_PUBLIC_BASE_URL` is optional. Leave it unset until the public frontend origin is confirmed. Once confirmed, set it to the frontend origin only (no path, query, credentials, or trailing application route). QR labels then link to the protected asset lookup route; if unset, the QR continues to contain the asset code only. The frontend origin must be reachable by intended scanning devices and use HTTPS in production.

### Step 2: Backend Virtual Environment
1. Open PowerShell / Command Prompt and navigate to `backend/`.
2. Create and activate a Python virtual environment:
   ```cmd
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Install dependencies:
   ```cmd
   python -m pip install -r requirements.txt
   ```
4. Configure environment variables in the repository-root `.env`. The Stage 2 application requires `SECRET_KEY`.
5. Run database migrations:
   ```cmd
   python -m alembic upgrade head
   ```
   Revision `20261113_01` adds the approved identity tables and seeds the five canonical roles. It does not create the rest of the business schema.
6. On first setup only, provision an administrator interactively:
   ```cmd
   python -m app.cli create-admin
   ```
   No default account or password is generated, and public self-registration is disabled.
7. Start the FastAPI development server:
   ```cmd
   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

### Step 3: Frontend Setup
1. Open a separate terminal and navigate to `frontend/`.
2. If `frontend/.env.local` does not exist, copy `frontend/.env.example` to it; preserve existing local settings. Install dependencies:
   ```cmd
   npm.cmd install
   ```
3. Launch the Vite development server:
   ```cmd
   npm.cmd run dev
   ```
4. Access the web application at `http://localhost:5173`.
5. Verify the API with `http://127.0.0.1:8000/health` and the database connection with `http://127.0.0.1:8000/health/ready`. Authentication endpoints are documented at `http://127.0.0.1:8000/docs`.

The backend runs directly on Windows and therefore connects to PostgreSQL at `127.0.0.1` using the published host port. If the backend is later added to Compose, its database host must be the Compose service name `db` and its port must be `5432`.

No canonical production frontend origin is configured in the repository. The illustrative `https://labs.haramaya.edu.et` value in earlier CORS design text is not an approved deployment hostname; configure both `CORS_ORIGINS` and `ASSET_PUBLIC_BASE_URL` only after the actual origin is confirmed by the deployment owner.

---

## 3. Production Deployment Considerations (Haramaya University Intranet)

When deployed onto university data center servers managed by the ICT Directorate:
1. **Reverse Proxy & TLS Termination:** Nginx serves as the reverse proxy, terminating TLS 1.3 certificates and forwarding API traffic to Uvicorn workers.
2. **Process Management:** Uvicorn runs behind Gunicorn with 4 worker processes (`gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`).
3. **Static File Serving:** The React production build (`npm run build`) is served directly by Nginx as static HTML/JS/CSS assets with cache headers.
4. **Automated Backups:** A nightly cron job executes `pg_dump` and syncs encrypted database snapshots to institutional network storage.
5. **Token Revocation Store:** Stage 2 uses an in-process refresh-token revocation set and per-process rate limiter. Replace these with a persistent shared store before enabling multiple workers or production traffic; in-memory revocations do not survive restart.
