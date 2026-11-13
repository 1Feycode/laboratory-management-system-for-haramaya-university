# Technology Stack and Component Justifications

This document documents the approved technology stack for the Laboratory Asset Management and Maintenance Tracking System, detailing the specific responsibilities and operational justifications for each selection.

---

## 1. Complete Technology Stack Matrix

| Layer | Selected Technology | Version | Purpose / Operational Role | Justification |
|---|---|---|---|---|
| **Backend Framework** | **Python / FastAPI** | Python 3.11+ / FastAPI 0.110+ | High-performance asynchronous REST API server. | Native async support; automatic OpenAPI/Swagger documentation; strict schema validation; high execution speed. |
| **Data Validation** | **Pydantic** | v2.6+ | Request and response schema serialization and validation. | High-speed Rust-based core; eliminates invalid data before it reaches domain services; ensures type safety. |
| **ORM & Persistence**| **SQLAlchemy** | 2.0+ | Object-Relational Mapping and database abstraction. | Modern typed syntax; fine-grained transactional control; prevents SQL injection; support for complex joins. |
| **Database Migrations**| **Alembic** | 1.13+ | Automated database schema version control. | Reproducible forward and backward schema evolution; tracks migration history in Git. |
| **Database Engine** | **PostgreSQL** | 15+ | Relational data persistence and audit vault. | Industrial-grade ACID compliance; strong foreign key constraints; native `JSONB` support for immutable audit logs. |
| **Frontend Framework**| **React.js** | 18+ (TypeScript) | Single Page Application (SPA) client interface. | Declarative component model; rich ecosystem; strong developer community; seamless mobile responsiveness. |
| **Frontend Build Tool**| **Vite** | 5.0+ | Development server and production bundler. | Sub-second hot module replacement (HMR); lightweight memory footprint on 8 GB RAM machines; fast build times. |
| **Styling & Layout** | **Tailwind CSS** | 3.4+ | Utility-first responsive CSS styling. | Rapid responsive UI development; zero runtime CSS overhead; easily customized for university branding. |
| **Hardware Scanning** | **HTML5-QRCode** | 2.3+ | In-browser camera barcode/QR code reader. | Cross-platform camera access without requiring native mobile wrappers; works in standard mobile browsers. |
| **Authentication** | **JWT / bcrypt**| PyJWT 2.8+ / bcrypt 4.1+ | Stateless token-based security and password hashing. | Cryptographically secure password hashing; stateless authorization tokens with role claims; low server memory overhead. Stage 2 uses the maintained `bcrypt` library directly rather than the older Passlib wrapper; bcrypt cost 12 remains the approved format. |

---

## 2. Development Profile for 8 GB RAM Hardware

To maintain development efficiency on standard Windows laptops with 8 GB RAM:
- **No Heavy Container Overhead:** The development environment uses native local processes:
  - Local PostgreSQL running as a standard Windows service (~60 MB RAM idle).
  - FastAPI running via Uvicorn hot-reload (~80 MB RAM idle).
  - Vite React development server running via Node.js (~120 MB RAM idle).
- Total development memory footprint is under **300 MB**, leaving ample system memory for browser debugging and operating system tasks.
