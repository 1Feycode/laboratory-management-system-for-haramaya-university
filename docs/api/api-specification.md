# REST API Specification (OpenAPI Details)

This document provides complete request and response schemas, parameters, and error formats for the primary endpoints of the Laboratory Asset Management and Maintenance Tracking System (`/api/v1`).

---

## 1. Authentication Endpoints

### 1.1 `POST /api/v1/auth/login`
- **Description:** Authenticates user credentials and issues JWT tokens.
- **Security:** Public.
- **Request (Form URL-Encoded):**
  - `username` (string, required): User institutional email.
  - `password` (string, required): Plaintext password.
- **Response (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "e44d5162-8e10-41ff-8c10-09252c442e91",
      "email": "dr.meseret@haramaya.edu.et",
      "full_name": "Dr. Meseret Girma",
      "role": "ULMD_ADMIN",
      "department_id": null
    }
  }
  ```
- **Error Responses:**
  - `401 Unauthorized`: Invalid email or password.
  - `403 Forbidden`: Account is inactive.

---

## 2. Asset Management Endpoints

### 2.1 `POST /api/v1/assets`
- **Description:** Registers a new durable laboratory instrument.
- **Security:** `LAB_MANAGER`, `ULMD_ADMIN`.
- **Request Body (`application/json`):**
  ```json
  {
    "serial_number": "UV1900-SN84729",
    "model_number": "UV-1900i Double-Beam",
    "manufacturer_name": "Shimadzu",
    "category_id": "8c593672-887e-405e-85a2-f852e92c21aa",
    "laboratory_id": "e44d5162-8e10-41ff-8c10-09252c442e91",
    "room_id": "d027f6e7-c62d-4d7a-8fbb-5481d9f8ce32",
    "purchase_date": "2025-09-15",
    "commissioning_date": "2025-10-01",
    "warranty_expiry_date": "2027-10-01"
  }
  ```
- **Response (`201 Created`):**
  ```json
  {
    "id": "b182fb5a-5ffb-46d5-bb90-07e4d82531cd",
    "asset_code": "HU-HiT-CHEM-0014",
    "serial_number": "UV1900-SN84729",
    "model_number": "UV-1900i Double-Beam",
    "manufacturer_name": "Shimadzu",
    "category_name": "Spectrophotometer",
    "college_code": "HiT",
    "department_code": "CHEM",
    "laboratory_name": "Analytical Spectroscopy Lab",
    "room_number": "B-08",
    "operational_status": "OPERATIONAL",
    "last_calibrated_date": null,
    "next_calibration_due": "2026-04-01",
    "qr_code_url": "/api/v1/assets/b182fb5a-5ffb-46d5-bb90-07e4d82531cd/qr",
    "created_at": "2026-11-11T14:35:10Z"
  }
  ```
- **Error Responses:**
  - `400 Bad Request`: Validation failure.
  - `409 Conflict`: Serial number already registered for this manufacturer.

### 2.2 `GET /api/v1/assets/lookup/{asset_code}`
- **Description:** Rapid bench lookup triggered by physical QR code scan.
- **Security:** Authenticated.
- **Path Parameter:** `asset_code` (e.g., `HU-HiT-CHEM-0014`).
- **Response (`200 OK`):**
  ```json
  {
    "id": "b182fb5a-5ffb-46d5-bb90-07e4d82531cd",
    "asset_code": "HU-HiT-CHEM-0014",
    "model_number": "UV-1900i Double-Beam",
    "manufacturer_name": "Shimadzu",
    "category": "Spectrophotometer",
    "laboratory": "Analytical Spectroscopy Lab",
    "room": "B-08",
    "operational_status": "OPERATIONAL",
    "calibration_status": "VALID",
    "next_calibration_due": "2026-04-01",
    "active_work_orders_count": 0
  }
  ```
- **Error Responses:**
  - `404 Not Found`: Asset code does not exist.

---

## 3. Maintenance & Work Order Endpoints

### 3.1 `POST /api/v1/work-orders`
- **Description:** Submit fault report and open maintenance ticket.
- **Security:** `LAB_TECH`, `LAB_MANAGER`, `ULMD_ADMIN`.
- **Request Body (`application/json`):**
  ```json
  {
    "asset_id": "b182fb5a-5ffb-46d5-bb90-07e4d82531cd",
    "severity": "HIGH",
    "fault_description": "Deuterium lamp fails ignition test; error code E-04 during optical initialization."
  }
  ```
- **Response (`201 Created`):**
  ```json
  {
    "id": "4164b360-15ef-4577-bc60-d72b22bbbe85",
    "ticket_number": "WO-2026-0142",
    "asset_id": "b182fb5a-5ffb-46d5-bb90-07e4d82531cd",
    "asset_code": "HU-HiT-CHEM-0014",
    "reported_by": "Abebe Kebede",
    "severity": "HIGH",
    "status": "OPEN",
    "fault_description": "Deuterium lamp fails ignition test; error code E-04 during optical initialization.",
    "created_at": "2026-11-11T14:40:00Z"
  }
  ```

### 3.2 `POST /api/v1/work-orders/{id}/logs`
- **Description:** Log diagnostic actions and spare parts for an assigned ticket.
- **Security:** `MAINTENANCE_TECH`, `ULMD_ADMIN`.
- **Request Body (`application/json`):**
  ```json
  {
    "actions_taken": "Replaced deuterium lamp assembly; cleaned optical mirrors; executed photometric self-test.",
    "spare_parts_used": "Shimadzu D2 Lamp Part #228-34010-91",
    "labor_hours": 2.50,
    "outcome_condition": "OPERATIONAL"
  }
  ```
- **Response (`201 Created`):**
  ```json
  {
    "id": "7f9a2e1d-4c3b-4a5f-8e9a-1b2c3d4e5f6a",
    "work_order_id": "4164b360-15ef-4577-bc60-d72b22bbbe85",
    "technician_name": "Taye Belay (Tech Unit)",
    "actions_taken": "Replaced deuterium lamp assembly; cleaned optical mirrors; executed photometric self-test.",
    "labor_hours": 2.50,
    "outcome_condition": "OPERATIONAL",
    "created_at": "2026-11-11T16:00:00Z"
  }
  ```

### 3.3 `PUT /api/v1/work-orders/{id}/close`
- **Description:** Custodian Lab Manager signs off on completed repair, closing ticket and restoring equipment to operational status.
- **Security:** `LAB_MANAGER`, `ULMD_ADMIN`.
- **Request Body (`application/json`):**
  ```json
  {
    "confirmed": true,
    "verification_notes": "Conducted baseline scan on standard reference water sample; absorbance matches calibration curve."
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "id": "4164b360-15ef-4577-bc60-d72b22bbbe85",
    "status": "CLOSED",
    "asset_status": "OPERATIONAL",
    "closed_at": "2026-11-11T16:15:00Z"
  }
  ```
