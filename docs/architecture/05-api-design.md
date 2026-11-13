# 05. REST API Design Specification

## 1. API Design Principles & Standards
The system REST API is built adhering to modern OpenAPI 3.1 and REST standards:
- **Base URI Prefix:** All endpoints are versioned under `/api/v1`.
- **Resource Naming:** Nouns in plural form (e.g., `/api/v1/assets`, `/api/v1/work-orders`).
- **HTTP Methods:** `GET` for retrieval, `POST` for creation, `PUT` for complete/state updates, `PATCH` for partial mutations, and `DELETE` (where soft-archiving or removal is permitted).
- **Standard HTTP Status Codes:**
  - `200 OK`: Request succeeded with response body.
  - `201 Created`: Resource successfully created.
  - `400 Bad Request`: Validation failure or malformed payload.
  - `401 Unauthorized`: Missing, invalid, or expired JWT token.
  - `403 Forbidden`: Authenticated user lacks the required RBAC role.
  - `404 Not Found`: Resource does not exist.
  - `409 Conflict`: Business rule violation (e.g., duplicate serial number, asset state locked).
  - `422 Unprocessable Entity`: Pydantic schema validation error.

---

## 2. Standard Pagination & Filtering Specification
All collection endpoints support standardized query parameters:
- `page` (integer, default: 1)
- `size` (integer, default: 20, max: 100)
- `sort_by` (string, e.g., `created_at`, `asset_code`)
- `sort_order` (string: `asc` or `desc`, default: `desc`)
- `search` (string, general full-text search across codes and models)

**Standard Paginated Response Envelope:**
```json
{
  "items": [ ... ],
  "total": 142,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

---

## 3. Core API Endpoint Catalog

### Authentication & User Management
| Method | Endpoint Path | Functionality | Permitted Roles | Request Payload | Response |
|---|---|---|---|---|---|
| `POST` | `/api/v1/auth/login` | User login & token generation | Public | Form: `username`, `password` | Access Token (JWT), User Object |
| `POST` | `/api/v1/auth/refresh` | Rotate access token | Public | Cookie / Body: `refresh_token` | New Access Token |
| `GET` | `/api/v1/auth/me` | Current user profile | Authenticated | None | User profile & permissions |
| `GET` | `/api/v1/users` | List university users | `ULMD_ADMIN` | Query: `role`, `department_id` | Paginated list of users |
| `POST` | `/api/v1/users` | Provision user account | `ULMD_ADMIN` | `UserCreateSchema` | `201 Created` with User info |
| `POST` | `/api/v1/auth/logout` | Revoke refresh token / clear cookie | Authenticated | None | `204 No Content` |

### Institutional Hierarchy
| Method | Endpoint Path | Functionality | Permitted Roles | Request Payload | Response |
|---|---|---|---|---|---|
| `GET` | `/api/v1/hierarchy/colleges` | List colleges & departments | Authenticated | Query: `include_depts` | List of colleges with child trees |
| `POST` | `/api/v1/hierarchy/colleges` | Register university college | `ULMD_ADMIN` | `{"name": "...", "code": "..."}` | `201 Created` |
| `GET` | `/api/v1/hierarchy/departments` | List departments | Authenticated | Query: `college_id` | List of departments |
| `GET` | `/api/v1/hierarchy/laboratories` | List laboratories & rooms | Authenticated | Query: `department_id` | List of laboratories and rooms |
| `POST` | `/api/v1/hierarchy/laboratories` | Register laboratory | `ULMD_ADMIN` | `LabCreateSchema` | `201 Created` |
| `POST` | `/api/v1/hierarchy/rooms` | Register room | `ULMD_ADMIN` | `RoomCreateSchema` | `201 Created` |

### Asset Management & QR Codes
| Method | Endpoint Path | Functionality | Permitted Roles | Request Payload | Response |
|---|---|---|---|---|---|
| `GET` | `/api/v1/assets` | Filterable asset inventory | Authenticated | Query: `lab_id`, `status`, `search` | Paginated asset summary list |
| `POST` | `/api/v1/assets` | Register durable asset | `LAB_MANAGER`, `ULMD_ADMIN` | `AssetCreateSchema` | `201 Created` with Asset Passport |
| `GET` | `/api/v1/assets/{id}` | Complete asset passport | Authenticated | Path: `id` (UUID) | Asset details, specs, history |
| `GET` | `/api/v1/assets/lookup/{code}` | Bench lookup by asset code | Authenticated | Path: `code` (e.g. `HU-HiT-CHEM-0014`) | Asset details and condition |
| `GET` | `/api/v1/assets/{id}/qr` | Vector QR code image | Authenticated | Path: `id` | SVG/PNG image data |
| `PATCH` | `/api/v1/assets/{id}` | Update permitted asset metadata | `LAB_MANAGER` (own lab), `ULMD_ADMIN` | `AssetUpdateSchema` | Updated asset passport |

### Inter-Laboratory Transfers
| Method | Endpoint Path | Functionality | Permitted Roles | Request Payload | Response |
|---|---|---|---|---|---|
| `GET` | `/api/v1/transfers` | List transfers by role scope | Authenticated | Query: `status`, `laboratory_id` | Paginated transfer list |
| `POST` | `/api/v1/transfers` | Initiate asset transfer | `LAB_MANAGER`, `ULMD_ADMIN` | `TransferCreateSchema` | `201 Created` with Transfer record |
| `PUT` | `/api/v1/transfers/{id}/accept`| Receiving LM accepts custody| `LAB_MANAGER`, `ULMD_ADMIN` | `{"notes": "..."}` | Updated Transfer record |
| `PUT` | `/api/v1/transfers/{id}/reject`| Receiver or ULMD rejects transfer | `LAB_MANAGER`, `ULMD_ADMIN` | `{"reason": "..."}` | Transfer `REJECTED`; asset restored |
| `PUT` | `/api/v1/transfers/{id}/approve`| ULMD finalizes relocation | `ULMD_ADMIN` | `{"approved": true}` | Updated Transfer record |

### Maintenance & Work Orders
| Method | Endpoint Path | Functionality | Permitted Roles | Request Payload | Response |
|---|---|---|---|---|---|
| `POST` | `/api/v1/work-orders` | Report fault / open ticket | `LAB_TECH`, `LAB_MANAGER`, `ULMD_ADMIN`| `WorkOrderCreateSchema` | `201 Created` with Ticket # |
| `GET` | `/api/v1/work-orders` | List open/active tickets | Authenticated | Query: `status`, `severity` | Paginated ticket list |
| `GET` | `/api/v1/work-orders/{id}` | Ticket detail and history | Authenticated | Path: `id` | Work order, logs, asset summary |
| `PUT` | `/api/v1/work-orders/{id}/assign`| Assign technician | `ULMD_ADMIN` | `{"technician_id": "UUID"}` | Updated ticket record |
| `PUT` | `/api/v1/work-orders/{id}/status`| Move to `IN_PROGRESS`/`AWAITING_PARTS` | `MAINTENANCE_TECH`, `ULMD_ADMIN` | `{"status": "IN_PROGRESS"}` | Updated ticket record |
| `POST` | `/api/v1/work-orders/{id}/logs` | Submit repair actions | `MAINTENANCE_TECH`, `ULMD_ADMIN`| `MaintenanceLogCreateSchema` | `201 Created` with service log |
| `PUT` | `/api/v1/work-orders/{id}/close`| Lab Manager sign-off | `LAB_MANAGER`, `ULMD_ADMIN` | `{"confirmed": true, "verification_notes": "..."}` | Closed ticket, operational asset |
| `PUT` | `/api/v1/work-orders/{id}/reject`| Lab Manager rejects repair | `LAB_MANAGER`, `ULMD_ADMIN` | `{"verification_notes": "..."}` | Ticket back to `IN_PROGRESS` |

### Calibrations & Compliance
| Method | Endpoint Path | Functionality | Permitted Roles | Request Payload | Response |
|---|---|---|---|---|---|
| `GET` | `/api/v1/calibrations/due` | Overdue/upcoming calibrations | Authenticated | Query: `within_days` | List of assets needing service |
| `GET` | `/api/v1/calibrations` | Calibration history | Authenticated | Query: `asset_id`, `date_range` | Paginated calibration logs |
| `POST` | `/api/v1/calibrations` | Log calibration certificate | `MAINTENANCE_TECH`, `ULMD_ADMIN`| `CalibrationLogCreateSchema` | `201 Created` |
| `GET` | `/api/v1/reports/downtime` | Uptime/downtime analytics | `ULMD_ADMIN`, `AUDITOR` | Query: `college_id`, `date_range`| Analytical aggregation charts |
| `GET` | `/api/v1/reports/inventory` | Filterable inventory export | `ULMD_ADMIN`, `AUDITOR` | Query: `college_id`, `status`, `format` | CSV/JSON inventory report |
| `GET` | `/api/v1/reports/calibration-compliance` | Calibration compliance summary | `ULMD_ADMIN`, `AUDITOR` | Query: `college_id` | Compliance counts and overdue list |
| `GET` | `/api/v1/audits` | Query immutable audit log | `ULMD_ADMIN`, `AUDITOR` | Query: `entity_type`, `entity_id` | Paginated audit trail |
| `GET` | `/api/v1/audits/{id}` | Single audit record | `ULMD_ADMIN`, `AUDITOR` | Path: `id` | Audit record with JSONB snapshots |
