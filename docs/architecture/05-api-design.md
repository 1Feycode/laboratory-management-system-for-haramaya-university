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
| `POST` | `/api/v1/auth/refresh` | Rotate access and refresh tokens | Refresh cookie | HttpOnly cookie | New Access Token and rotated cookie |
| `GET` | `/api/v1/auth/me` | Current active user profile | Bearer token | None | Safe User profile |
| `GET` | `/api/v1/users` | List university users | `ULMD_ADMIN` | Query: `role`, `department_id` | Paginated list of users |
| `POST` | `/api/v1/users` | Provision user account | `ULMD_ADMIN` | `UserCreateSchema` | `201 Created` with User info |
| `GET` | `/api/v1/users/{id}` | View user profile | `ULMD_ADMIN` | Path: user UUID | Safe user profile |
| `PATCH` | `/api/v1/users/{id}` | Update profile, role, department, or account status | `ULMD_ADMIN` | `UserUpdateSchema` | Updated safe user profile |
| `GET` | `/api/v1/users/departments` | List department assignment options | `ULMD_ADMIN` | None | Department ID, name, and code |
| `POST` | `/api/v1/auth/logout` | Revoke refresh token / clear cookie | Refresh cookie optional | None | `204 No Content` |

Stages 2 and 3 implement the authentication, user-management, and organizational hierarchy endpoints in this catalog. Asset and other business modules remain planned. Paginated listings use the shared `page` / `size` envelope; request and response fields are detailed in the [API specification](../api/api-specification.md).

### Institutional Hierarchy
| Method | Endpoint Path | Functionality | Permitted Roles | Request Payload | Response |
|---|---|---|---|---|---|
| `GET`, `POST`, `PATCH`, `DELETE` | `/api/v1/hierarchy/colleges[/{id}]` | Read, create, update, and constraint-aware delete | Reads: Authenticated; writes: `ULMD_ADMIN` | College schemas; list query `page`, `size`, `search` | Paginated/read DTO, `201`, `200`, or `204` |
| `GET`, `POST`, `PATCH`, `DELETE` | `/api/v1/hierarchy/departments[/{id}]` | Department CRUD, filter by college | Reads: Authenticated; writes: `ULMD_ADMIN` | Department schemas; list query includes `college_id` | Paginated/read DTO, `201`, `200`, or `204` |
| `GET`, `POST`, `PATCH`, `DELETE` | `/api/v1/hierarchy/laboratories[/{id}]` | Laboratory CRUD, filter by department/type | Reads: Authenticated; writes: `ULMD_ADMIN` | Laboratory schemas; list query includes `department_id`, `lab_type` | Paginated/read DTO, `201`, `200`, or `204` |
| `GET`, `POST`, `PATCH`, `DELETE` | `/api/v1/hierarchy/rooms[/{id}]` | Room CRUD, filter by laboratory | Reads: Authenticated; writes: `ULMD_ADMIN` | Room schemas; list query includes `laboratory_id` | Paginated/read DTO, `201`, `200`, or `204` |

These hierarchy APIs are implemented for Stage 3. A separate `Location` entity is not part of the approved ERD; physical location is modeled through the laboratory/room relationship.

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
| `POST` | `/api/v1/work-orders` | Report fault / open ticket | `LAB_TECH`, designated `LAB_MANAGER`, `ULMD_ADMIN` | `asset_id`, `severity`, `failure_category`, `fault_description` | `201 Created` full work order |
| `GET` | `/api/v1/work-orders` | List filtered tickets | All canonical roles, scoped | Query: `page`, `size`, `status`, `severity`, `asset_id` | Paginated work orders with history |
| `GET` | `/api/v1/work-orders/{order_id}` | Retrieve ticket and history | All canonical roles, scoped | Path: `order_id` | Work order with logs and status history |
| `PUT` | `/api/v1/work-orders/{order_id}/assign` | Assign active Maintenance Technician | `ULMD_ADMIN` | `{"assigned_to": "UUID"}` | `ASSIGNED` work order |
| `PUT` | `/api/v1/work-orders/{order_id}/status` | Start, pause for parts, or resume | Assigned `MAINTENANCE_TECH` | `{"status": "IN_PROGRESS"}` or `{"status": "AWAITING_PARTS"}` | Updated work order |
| `POST` | `/api/v1/work-orders/{order_id}/external-parts-approval` | Submit external-parts request | Assigned `MAINTENANCE_TECH` | `{"request_details": "..."}` | `AWAITING_APPROVAL` work order |
| `PUT` | `/api/v1/work-orders/{order_id}/external-parts-approval/decision` | Approve or reject an external-parts request | Existing roles explicitly configured in `MAINTENANCE_APPROVER_ROLES` | `decision` (`APPROVED` or `REJECTED`), optional `decision_notes` | Prior status restored on approval; rejection remains `AWAITING_APPROVAL` |
| `POST` | `/api/v1/work-orders/{order_id}/logs` | Submit repair activity | Assigned `MAINTENANCE_TECH`, `ULMD_ADMIN` | `actions_taken`, `spare_parts_used`, `labor_hours`, `outcome_condition` | `201 Created`; work order `RESOLVED` |
| `PUT` | `/api/v1/work-orders/{order_id}/close` | Confirm or reject repair | Custodian `LAB_MANAGER`, `ULMD_ADMIN` | `{"confirmed": true, "verification_notes": "..."}` | Closed or returned to `IN_PROGRESS` |

**Stage 6 behavior:** All transitions and audit snapshots are transactional. `MAINTENANCE_APPROVER_ROLES` accepts existing role names only and defaults to empty; no role is enabled without an explicit environment configuration. Approval trigger, authority, evidence, approval count, and rejection disposition remain unresolved. A confirmed close requires the latest outcome to be `OPERATIONAL`; closure rules for degraded/unrepairable outcomes and the proposed local-repair path also remain unresolved. See the [detailed API specification](../api/api-specification.md#4-maintenance--work-order-endpoints) and [DEC-02](../design/phase-2-open-decisions.md#dec-02-outcome-external-parts-approval-state).

### Calibrations & Compliance
| Method | Endpoint Path | Functionality | Permitted Roles | Request Payload | Response |
|---|---|---|---|---|---|
| `GET` | `/api/v1/calibrations/due` | Overdue/upcoming calibrations | Authenticated | Required non-negative `within_days`, `page`, `size` | Paginated assets due by requested cutoff |
| `GET` | `/api/v1/calibrations` | Calibration history | `ULMD_ADMIN`, `MAINTENANCE_TECH`, `AUDITOR` | Query: optional `asset_id`, `page`, `size` | Paginated calibration logs |
| `POST` | `/api/v1/calibrations` | Log calibration certificate | `MAINTENANCE_TECH`, `ULMD_ADMIN`| `CalibrationLogCreateSchema` | `201 Created` |
| `GET` | `/api/v1/reports/downtime` | Uptime/downtime analytics | `ULMD_ADMIN`, `AUDITOR` | Query: `college_id`, `date_range`| Analytical aggregation charts |
| `GET` | `/api/v1/reports/inventory` | Filterable inventory export | `ULMD_ADMIN`, `AUDITOR` | Query: `college_id`, `status`, `format` | CSV/JSON inventory report |
| `GET` | `/api/v1/reports/calibration-compliance` | Calibration compliance summary | `ULMD_ADMIN`, `AUDITOR` | Query: `college_id` | Compliance counts and overdue list |
| `GET` | `/api/v1/audits` | Query immutable audit log | `ULMD_ADMIN`, `AUDITOR` | Query: `entity_type`, `entity_id` | Paginated audit trail |
| `GET` | `/api/v1/audits/{id}` | Single audit record | `ULMD_ADMIN`, `AUDITOR` | Path: `id` | Audit record with JSONB snapshots |

Calibration history and due endpoints are implemented in Stage 7. The history endpoint is read-only and does not accept a date range; binary certificate attachments and calibration-compliance reporting are not implemented. `within_days` is required so the caller selects the warning horizon; no default reminder window or background notification is inferred. There is no approved preventive-maintenance schedule/activity model in the ERD or data dictionary, so no such endpoints are implemented.
