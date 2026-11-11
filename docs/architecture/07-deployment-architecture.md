# 07. Deployment Architecture Specification

## 1. Development & Local Deployment Profile (Windows 8 GB RAM)
To accommodate developer workflows on a standard Windows 10/11 laptop constrained to **8 GB of RAM**, the system avoids heavy container runtimes (such as Kubernetes or Docker Desktop) during local development and instead executes as native, lightweight Windows processes.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   WINDOWS 10/11 HOST (8 GB TOTAL RAM)                  │
│                                                                        │
│   ┌─────────────────────┐   ┌─────────────────────┐   ┌────────────┐   │
│   │ Node.js (Vite HMR)  │   │ Python 3.11 Virtual │   │ PostgreSQL │   │
│   │ React Dev Server    │   │ Environment         │   │ 15 Service │   │
│   │ (Port 5173)         │   │ Uvicorn (Port 8000) │   │ (Port 5432)│   │
│   │ ~120 MB RAM         │   │ ~90 MB RAM          │   │ ~80 MB RAM │   │
│   └─────────────────────┘   └─────────────────────┘   └────────────┘   │
│                                                                        │
│   Combined Memory Footprint: ~290 MB RAM                               │
│   Available for OS, Web Browser, and IDE: ~7.7 GB RAM                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Local Setup Guide (Windows Native)

### Step 1: Database Setup
1. Install PostgreSQL 15+ for Windows via the official installer.
2. Initialize database cluster and verify the service is running.
3. Open `psql` (or pgAdmin) and create the project database:
   ```sql
   CREATE DATABASE hu_lab_management;
   CREATE USER hu_admin WITH ENCRYPTED PASSWORD 'local_dev_password';
   GRANT ALL PRIVILEGES ON DATABASE hu_lab_management TO hu_admin;
   ```

### Step 2: Backend Virtual Environment
1. Open PowerShell / Command Prompt and navigate to `backend/`.
2. Create and activate a Python virtual environment:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```
4. Configure environment variables in `.env` (copied from `.env.example`).
5. Run database migrations:
   ```cmd
   alembic upgrade head
   ```
6. Start the FastAPI development server:
   ```cmd
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

### Step 3: Frontend Setup
1. Open a separate terminal and navigate to `frontend/`.
2. Install dependencies:
   ```cmd
   npm install
   ```
3. Launch the Vite development server:
   ```cmd
   npm run dev
   ```
4. Access the web application at `http://localhost:5173`.

---

## 3. Production Deployment Considerations (Haramaya University Intranet)

When deployed onto university data center servers managed by the ICT Directorate:
1. **Reverse Proxy & TLS Termination:** Nginx serves as the reverse proxy, terminating TLS 1.3 certificates and forwarding API traffic to Uvicorn workers.
2. **Process Management:** Uvicorn runs behind Gunicorn with 4 worker processes (`gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`).
3. **Static File Serving:** The React production build (`npm run build`) is served directly by Nginx as static HTML/JS/CSS assets with cache headers.
4. **Automated Backups:** A nightly cron job executes `pg_dump` and syncs encrypted database snapshots to institutional network storage.
