# Proposed System Architecture (Phase 1 Baseline)

This document outlines the high-level system architecture and architectural rationale established during the Phase 1 Requirements Engineering phase.

---

## 1. Architectural Style: Modular Monolith
The system is architected as a **Modular Monolith**. Rather than introducing distributed microservices—which introduce network latency, distributed transaction complexity, and high infrastructure overhead—the system organizes all domain capabilities into clear, logically separated modules running within a single cohesive backend application.

```
┌─────────────────────────────────────────────────────────────┐
│                    REACT CLIENT LAYER                       │
│    Single Page Application (SPA) + Tailwind CSS + QR Hook   │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / REST (JSON + JWT)
┌──────────────────────────────▼──────────────────────────────┐
│                    FASTAPI BACKEND CORE                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Security, CORS, Authentication & Role-Based Scoping   │  │
│  └───────────────────────────┬───────────────────────────┘  │
│                              │                              │
│  ┌───────────────────────────▼───────────────────────────┐  │
│  │                   DOMAINS & SERVICES                  │  │
│  │  - Identity & Access      - Asset & QR Lifecycle      │  │
│  │  - Hierarchy Management   - Maintenance & Work Orders │  │
│  │  - Transfer Engine        - Calibration Tracking      │  │
│  │  - Audit & Compliance     - Executive Analytics       │  │
│  └───────────────────────────┬───────────────────────────┘  │
│                              │ SQLAlchemy 2.0 ORM           │
└──────────────────────────────┼──────────────────────────────┘
                               │ Connection Pool (asyncpg)
┌──────────────────────────────▼──────────────────────────────┐
│                  POSTGRESQL RELATIONAL STORE                │
│    Normalized Relational Schema (3NF) + JSONB Audit Logs    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Key Architectural Tenets

### 1. Separation of Concerns
- **Client Presentation:** The React frontend manages user state, form validation, responsive presentation, and device hardware integration (camera QR scanning).
- **Application Services:** The FastAPI backend enforces authentication, business rules, multi-step workflow transitions, and authorization scoping.
- **Persistence:** PostgreSQL guarantees data integrity via primary/foreign key constraints, uniqueness rules, and ACID transaction boundaries.

### 2. High Performance on Modest Hardware
The architecture is explicitly optimized for deployment on standard institutional hardware and development laptops with **8 GB RAM**:
- Asynchronous non-blocking I/O via FastAPI and asyncpg.
- Selective database querying (avoiding `SELECT *`) with explicit relationship loading (`selectinload`).
- Zero heavy runtime dependencies (no Kubernetes, no Redis required for MVP).

### 3. Traceable and Immutable Operations
Given the statutory accountability required by Haramaya University Senate Legislation, all asset transfers, condition modifications, and maintenance sign-offs produce synchronous, immutable records in an append-only audit trail.
