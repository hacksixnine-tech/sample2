# PHANTOM Security & Governance Architecture

## 1. Executive Summary & Security Philosophy

The **PHANTOM** platform (Statewide Video Intelligence & Real-Time Investigation Platform) is engineered for high-security law-enforcement and public safety operations. The architecture strictly complies with **Zero-Trust Network Architecture (ZTNA)**, the **Principle of Least Privilege (PoLP)**, and strict evidentiary chain-of-custody standards.

```
+-----------------------------------------------------------------------------+
| CLIENT TIER (Browser C2 Console / Mobile App / AI Worker Edge Nodes)        |
+-----------------------------------------------------------------------------+
                                       |
                   [ TLS 1.3 / HTTPS / Secure WSS ]
                                       v
+-----------------------------------------------------------------------------+
| PERIMETER SECURITY MIDDLEWARE                                               |
| - Trusted Host Header Validation                                            |
| - Enterprise Security Headers (HSTS, CSP, X-Frame-Options, MIME-sniffing)   |
| - Sliding Window Rate Limiting (Brute-force & DoS Throttling)                |
| - Distributed Correlation Request ID & Structured Access Logging           |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
| AUTHENTICATION & PRINCIPAL RESOLUTION                                       |
| - JWT Access Tokens (HS256 / RS256, Expiry: 15m)                            |
| - Long-lived Refresh Tokens (Rotatable, Expiry: 7d)                         |
| - Cryptographic Bcrypt (Salt rounds: 12) Password Verification              |
| - Internal Service API Keys (HMAC Constant-Time Verification)               |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
| GRANULAR SERVER-SIDE ROLE-BASED ACCESS CONTROL (RBAC)                       |
| - Explicit Dependency Enforcement on REST & WebSocket Streams               |
| - Anti-Privilege Escalation Barriers                                        |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
| BUSINESS LOGIC & DATA LAYER                                                 |
| - Parameterized SQL via SQLAlchemy 2.0 Async ORM (SQL Injection Immune)     |
| - PostGIS Geo-Spatial Operations & Bounding Box Validations                 |
| - SSRF-Hardened Ingestion Services                                          |
+-----------------------------------------------------------------------------+
                                       |
                                       v
+-----------------------------------------------------------------------------+
| CENTRALIZED IMMUTABLE AUDIT TRAIL                                           |
| - Append-Only PostgreSQL Table with Strict Schema & DB CHECK Constraints     |
| - Zero DELETE / UPDATE API Surfaces                                         |
+-----------------------------------------------------------------------------+
```

---

## 2. Threat Modeling & Risk Mitigation (STRIDE)

| Threat Category | Target Asset / Vector | Attack Scenario | Architectural Mitigation in PHANTOM |
| :--- | :--- | :--- | :--- |
| **Spoofing** | User Identity & API Consumers | An attacker steals or crafts arbitrary credentials/tokens. | Strict JWT signature verification with cryptographic secrets; Bcrypt password hashes; separate refresh tokens; token type enforcement (`access` vs `refresh`). |
| **Tampering** | Evidence Metadata, Audit Logs, Telemetry | A compromised insider or external attacker modifies historical audit records or camera locations. | Append-only database constraints; complete absence of `DELETE`/`UPDATE` routes on `/api/v1/audit`; ORM audit hooks on critical state transitions. |
| **Repudiation** | Operator Actions (Vehicle Search, Camera Feed Access) | An officer denies performing an unauthorized license plate or dossier search. | Centralized immutable audit trail logging user UUID, client IP, user-agent, timestamp, action type, and search parameters on every query. |
| **Information Disclosure** | Live RTSP Streams, Watchlist Data, PII | Unauthorized access to video feeds or suspect databases. | Strict server-side RBAC dependencies (`require_camera_view`, `require_watchlist_read`); sanitization of sensitive payload fields; stripped stack traces in production. |
| **Denial of Service** | Login & Heavy Geo-Spatial Query Endpoints | Automated brute-force attacks on `/auth/login` or expensive PostGIS spatial searches. | In-memory sliding-window `RateLimitMiddleware` throttling requests by IP with custom threshold rules (e.g. 10 req/min on `/auth/login`); payload size constraints. |
| **Elevation of Privilege** | User Management & Role Assignment | A standard police officer promotes themselves or another user to `SYSTEM_ADMIN`. | **Privilege Escalation Protection**: Non-administrators are strictly blocked from assigning administrative roles, modifying administrator profiles, or elevating privileges. |
| **SSRF (Server-Side Request Forgery)** | Camera RTSP & External Stream Registration | Attacker submits `http://169.254.169.254/` (cloud metadata) or `file:///etc/passwd` as stream URLs. | Stream URL schema validation rejecting non-network protocols; private IP and cloud metadata blacklists in validation layer. |

---

## 3. RBAC (Role-Based Access Control) Permission Matrix

PHANTOM defines fine-grained permissions attached to standard government and law-enforcement roles:

| Permission | System Admin | Police Officer | Investigator | Analyst | Viewer | Auditor | AI Worker |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **All Capabilities (`*`)** | **YES** | No | No | No | No | No | No |
| **User Management (`user:manage`)** | **YES** | No | No | No | No | No | No |
| **Audit Log Viewing (`audit:view`)** | **YES** | No | **YES** | No | No | **YES** | No |
| **Camera Feed View (`camera:view`)** | **YES** | **YES** | **YES** | **YES** | **YES** | **YES** | No |
| **Camera Configuration (`camera:manage`)**| **YES** | **YES** | No | No | No | No | No |
| **Stream Management (`stream:manage`)** | **YES** | **YES** | No | No | No | No | No |
| **Alerts View (`alert:view`)** | **YES** | **YES** | **YES** | **YES** | **YES** | **YES** | No |
| **Alerts Resolve/Ack (`alert:manage`)** | **YES** | **YES** | No | No | No | No | No |
| **Watchlist View (`watchlist:view`)** | **YES** | **YES** | No | **YES** | No | **YES** | No |
| **Watchlist Edit (`watchlist:manage`)** | **YES** | **YES** | No | No | No | No | No |
| **Vehicle Search / ANPR (`vehicle:search`)**| **YES** | **YES** | **YES** | **YES** | No | No | **YES** |
| **Incident Investigation (`incident:manage`)**| **YES** | **YES** | **YES** | No | No | No | No |
| **Evidence Metadata Export (`evidence:export`)**| **YES** | **YES** | **YES** | No | No | No | No |
| **AI Stream Ingestion (`ai:ingest`)** | **YES** | No | No | No | No | No | **YES** |

---

## 4. Secret Management & Credential Hygiene

1. **Environment Separation**:
   - Production secrets (`SECRET_KEY`, `POSTGRES_PASSWORD`, `AI_WORKER_API_KEY`) must never be committed to source control.
   - Secrets are injected via container environment variables or external secret managers (HashiCorp Vault, AWS Secrets Manager).
2. **Key Rotation Protocol**:
   - `SECRET_KEY`: Rotated on a 90-day cadence. Older tokens are phased out using active token versioning or rolling secret arrays.
   - `AI_WORKER_API_KEY`: High-entropy 64-character hex strings rotated via automated secret manager deployment.
3. **Password Security**:
   - Passwords must meet complexity requirements (minimum 8 characters, alphanumeric and special symbols).
   - Hashed using **Bcrypt** with automatic work factor calibration (work factor $\ge 12$).

---

## 5. Incident Response & Forensic Runbook

In the event of a suspected breach, anomalous credential usage, or privilege abuse:

### Step 1: Identification & Alerting
- Real-time audit logs flag `SECURITY_VIOLATION` events with client IP, timestamp, and attempted resource.
- Rate limiter monitors trigger automated temporary IP blocks upon threshold breaches.

### Step 2: Immediate Containment
```bash
# 1. Deactivate compromised user account immediately
UPDATE users SET is_active = FALSE WHERE username = '<compromised_username>';

# 2. Invalidate active worker keys in environment
export AI_WORKER_API_KEY="<new-rotated-secret-key>"
```

### Step 3: Forensic Inspection via Audit Trail
```sql
-- Query all actions taken by the compromised user in the last 24 hours
SELECT id, created_at, action, resource_type, resource_id, ip_address, details
FROM audit_logs
WHERE user_id = '<user_uuid>' AND created_at >= NOW() - INTERVAL '24 hours'
ORDER BY created_at ASC;
```

### Step 4: Remediation & Post-Incident Review
- Revoke all outstanding refresh tokens by changing the master signing key or updating user token version.
- Re-run security test suite: `pytest backend/tests/security -v`.

---

## 6. Data Privacy, Minimization & Retention Guidelines

1. **Law Enforcement Evidentiary Retention**:
   - ANPR and sighting telemetry are retained in hot storage for 90 days, after which automated partitioning archives data to encrypted cold storage or deletes unflagged sightings according to state retention policies.
2. **PII Masking & Access Control**:
   - Unauthenticated endpoints never return officer names, badge numbers, or contact information.
   - Evidence exports require explicit authorization and log the export reason directly into the immutable audit trail.
3. **Transport Encryption**:
   - All REST APIs, streaming WebSockets, and database connections require TLS 1.3 in transit.
