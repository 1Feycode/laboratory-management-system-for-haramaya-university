# 08. Technology Decisions (Architecture Decision Records - ADRs)

This document formalizes the primary architectural and technical decisions made during the system design phase, documenting the context, evaluated alternatives, and trade-offs.

---

## ADR-01: Adoption of Modular Monolith Architecture Pattern
- **Status:** Approved.
- **Context:** Haramaya University oversees 90–150+ laboratories. The system requires strict referential integrity across assets, rooms, work orders, and transfers. Development must remain practical on standard developer hardware (Windows 8 GB RAM).
- **Decision:** Adopt a Modular Monolithic architecture instead of distributed microservices.
- **Consequences:**
  - *Positive:* Eliminates network latency between components; simplifies transactional rollback during asset transfers; minimizes memory footprint (< 300 MB); provides a straightforward single-repository deployment model.
  - *Negative:* All modules share the same database instance; horizontal scaling scales the entire monolith rather than individual high-load modules.

---

## ADR-02: Selection of FastAPI (Python) for Backend Framework
- **Status:** Approved.
- **Context:** The system requires an asynchronous REST API, strict schema validation, automatic documentation, and high developer productivity.
- **Alternatives Evaluated:** Django REST Framework (DRF), Express.js (Node.js), Spring Boot (Java).
- **Decision:** Implement the backend using FastAPI with Python 3.11+.
- **Consequences:**
  - *Positive:* Native asynchronous concurrency; automated interactive OpenAPI/Swagger documentation; high-speed data validation via Pydantic v2; clean dependency injection architecture.
  - *Negative:* Requires explicit architecture structuring (unlike Django’s built-in admin and battery-included ORM).

---

## ADR-03: Selection of PostgreSQL as Primary Relational Store
- **Status:** Approved.
- **Context:** The system requires strict ACID compliance, complex foreign key constraints (cascading restrictions), partial indexing, and immutable audit logging.
- **Alternatives Evaluated:** MySQL, MongoDB.
- **Decision:** Use PostgreSQL 15+.
- **Consequences:**
  - *Positive:* Robust referential integrity; native `JSONB` data types perfectly suited for storing before/after audit snapshots; powerful partial and composite indexing; proven reliability in academic and enterprise environments.
  - *Negative:* Slightly higher initial memory footprint than SQLite, but easily configured to run within 80 MB on Windows.

---

## ADR-04: In-Browser Camera QR Code Scanning via HTML5-QRCode
- **Status:** Approved.
- **Context:** Bench technicians need to scan QR codes on equipment without requiring the university to build, sign, and distribute native mobile apps (Android/iOS) through public app stores.
- **Alternatives Evaluated:** Native React Native mobile app, external Bluetooth barcode scanner hardware.
- **Decision:** Integrate the `html5-qrcode` library within the React Single Page Application.
- **Consequences:**
  - *Positive:* Zero app store installation barrier; technicians access the scanner through standard mobile browsers (Chrome, Safari); immediate asset lookup via camera stream.
  - *Negative:* Requires mobile browser camera permissions; performance depends on mobile camera focus quality under low-light laboratory conditions.

---

## ADR-05: Stateless JWT Authentication with HttpOnly Refresh Token Cookies
- **Status:** Approved.
- **Context:** Security architecture must prevent cross-site scripting (XSS) token theft while maintaining scalable stateless authentication.
- **Decision:** Issue short-lived access tokens (30 minutes) stored in memory or client headers, paired with long-lived refresh tokens (7 days) stored in secure `HttpOnly` cookies.
- **Consequences:**
  - *Positive:* Shields refresh credentials from malicious JavaScript injection; keeps authentication verification fast without requiring database lookups on every single API request.
  - *Negative:* Immediate token revocation requires maintaining an in-memory or database token blocklist.
