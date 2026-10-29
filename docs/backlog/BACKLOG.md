# HMS Product Backlog & Sprint Plan

Source of truth: [`backlog.csv`](backlog.csv). Every item traces to an SRS v1.0 requirement. Owners follow Test Plan 9.1 (module owners). Story points use the Fibonacci scale (1 = trivial, 8 = largest item).

## Sprint 1 - 19-23 Oct 2026 (completed late, 28 Oct)

**Points:** 56 total - Arjav 13, Arjun 21, Armaan 10, Arnav 12

| ID | Item | Requirement | Owner | SP | Priority |
|---|---|---|---|---|---|
| HMS-01 | Project setup: Django project with one app per module and PostgreSQL | HMS-NF-006 | Arjun | 5 | High |
| HMS-02 | CI with GitHub Actions + PR template + CODEOWNERS | Process | Arnav | 3 | High |
| HMS-03 | Seed demo data command (blocks/rooms/students/admin) | STP 6.3 test data | Arnav | 2 | Medium |
| HMS-04 | Register and log in with institute email/roll number and role | HMS-F-001 | Arjav | 5 | High |
| HMS-05 | Store passwords as salted hashes | HMS-SR-002 | Arjav | 1 | High |
| HMS-06 | Enforce role-based access control at view (and API) layer | HMS-F-005 / HMS-SR-003 | Arjav | 3 | High |
| HMS-07 | Expire inactive session after 20 minutes | HMS-F-004 | Arjav | 2 | High |
| HMS-08 | Student updates own profile (phone/address/emergency contact) | HMS-F-002 | Arjav | 2 | Medium |
| HMS-09 | Admin manages hostel blocks/floors/rooms and capacity | HMS-F-014 | Arjun | 3 | High |
| HMS-10 | Admin creates/views/updates/deactivates student records | HMS-F-011 | Arjun | 3 | High |
| HMS-11 | Admin allocates or reallocates a room (availability + gender policy) | HMS-F-012 | Arjun | 5 | High |
| HMS-12 | Prevent allocation beyond room capacity | HMS-F-015 | Arjun | 3 | High |
| HMS-13 | Student views own room and roommates | HMS-F-010 | Arjun | 2 | High |
| HMS-14 | Admin configures fee structure per term and room type | HMS-F-022 | Armaan | 3 | Medium |
| HMS-15 | Student views itemised fee statement | HMS-F-020 | Armaan | 3 | High |
| HMS-16 | Student and Admin dashboards wired to live data | SRS 3.1 / SAD 4.5 | Armaan | 3 | Medium |
| HMS-17 | No card data stored - schema review | HMS-SR-005 | Armaan | 1 | High |
| HMS-18 | Immutable audit log for admin actions | HMS-SR-004 | Arnav | 3 | High |
| HMS-19 | Student raises maintenance complaint with optional photo | HMS-F-030 | Arnav | 3 | Medium |
| HMS-20 | Sprint 1 demo video (1 min) uploaded to repo | Deliverable 2g/2h | Arnav | 1 | High |

## Sprint 2 - 26-30 Oct 2026

**Points:** 53 total - Arjav 9, Arjun 10, Armaan 16, Arnav 18

| ID | Item | Requirement | Owner | SP | Priority |
|---|---|---|---|---|---|
| HMS-21 | Password reset via OTP to registered email | HMS-F-003 | Arjav | 3 | Medium |
| HMS-22 | Responsive and accessible UI (360px / WCAG 2.1 AA) | HMS-NF-005 | Arjav | 3 | Medium |
| HMS-23 | HTTPS-only security settings (TLS 1.2+/HSTS/secure cookies) | HMS-SR-001 | Arjav | 2 | High |
| HMS-24 | Health check and restart policy | HMS-NF-002 | Arjav | 1 | High |
| HMS-25 | Student room change request and Admin approve/reject | HMS-F-013 | Arjun | 5 | Medium |
| HMS-26 | Performance: indexes/pagination + Locust run (p95 <= 2s) | HMS-NF-001 | Arjun | 3 | High |
| HMS-27 | Scale test with 5000 students / 2000 rooms | HMS-NF-006 | Arjun | 2 | Medium |
| HMS-28 | Online fee payment via sandbox gateway (Razorpay/Stripe test) | HMS-F-021 | Armaan | 8 | High |
| HMS-29 | PDF payment receipt download | HMS-F-023 | Armaan | 3 | Medium |
| HMS-30 | Reconcile payments and flag fee defaulters | HMS-F-024 | Armaan | 5 | High |
| HMS-31 | Admin/technician updates complaint status and notifies student | HMS-F-031 | Arnav | 3 | Medium |
| HMS-32 | Occupancy/vacancy/fee-collection reports for a date range | HMS-F-040 | Arnav | 5 | Medium |
| HMS-33 | Export reports as CSV and PDF | HMS-F-041 | Arnav | 3 | Low |
| HMS-34 | Data protection: per-user filtering and no PII in logs | HMS-NF-003 | Arnav | 2 | High |
| HMS-35 | Audit log retention (3 years) and archive export | HMS-NF-004 | Arnav | 2 | High |
| HMS-36 | Final documentation: deviations + RTM status + README | Deliverable 3c | Arnav | 2 | High |
| HMS-37 | Sprint 2 demo video (2 min) uploaded to repo | Deliverable 3b | Arnav | 1 | High |
