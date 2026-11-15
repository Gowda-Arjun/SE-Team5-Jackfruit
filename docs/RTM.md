# Requirements Traceability Matrix (final)

Final status of STP v1.0 Section 13.2 at development freeze. Each SRS v1.0 requirement is linked to its design reference (SAD 3.8), module, backlog item, owner, Test Plan case and the automated tests that execute it.

**Status:** N = not tested, P = partially tested, A = all mapped test cases passed.
**Summary:** 31 requirements: **27 A, 4 P, 0 N**. Results and evidence are in [TEST_REPORT.md](TEST_REPORT.md).

## Functional requirements

| Req ID | Requirement (short) | Design ref | Module | Backlog | Owner | Test case(s) | Automated test(s) | Status |
|---|---|---|---|---|---|---|---|---|
| HMS-F-001 | Log in with institute email/roll number and role | DS-Auth-01 | AuthModule | HMS-04 | Arjav | TC-Auth-01 | `core/tests/test_smoke.py` (login flow, dashboard by role), `core/tests/test_seed_demo.py::test_seeded_accounts_can_log_in` | A (accounts created by Admin, see [D10](DEVIATIONS.md)) |
| HMS-F-002 | Student profile update | DS-Auth-03 | AuthModule | HMS-08 | Arjav | TC-Auth-02 | `accounts/tests/test_profile.py` | A |
| HMS-F-003 | OTP password reset (10 min) | DS-Auth-04 | AuthModule | HMS-21 | Arjav | TC-Auth-03, TC-Sec-12 | `accounts/tests/test_password_reset.py` (hashed OTP, single use, expiry) | A (TC-Sec-12 rate limiting not built, see [D14](DEVIATIONS.md)) |
| HMS-F-004 | Session timeout (20 min) | DS-Auth-05 | AuthModule | HMS-07 | Arjav | TC-Auth-04, TC-Sec-08 | `accounts/tests/test_session.py`, `core/tests/test_security_validation.py::test_post_without_csrf_token_is_rejected` | A |
| HMS-F-005 | Enforce RBAC (403 and logged) | DS-Auth-02 | AuthModule | HMS-06 | Arjav | TC-Auth-05, TC-Sec-04 | `core/tests/test_security_validation.py::test_denied_role_access_returns_403_and_is_logged`, plus 403 tests in every module | A |
| HMS-F-010 | View own room and roommates | DS-Alloc-03 | AllocationModule | HMS-13 | Arjun | TC-Alloc-01 | `allocation/tests/test_my_room.py` | A |
| HMS-F-011 | Admin CRUD on student records | DS-Alloc-04 | AllocationModule | HMS-10 | Arjun | TC-Alloc-02 | `allocation/tests/test_student_records.py` | A |
| HMS-F-012 | Allocate / reallocate room | DS-Alloc-01 | AllocationModule | HMS-11 | Arjun | TC-Alloc-03 | `allocation/tests/test_allocation.py` (gender policy, inactive room, reallocation) | A |
| HMS-F-013 | Room-change request and approval | DS-Alloc-05 | AllocationModule | HMS-25 | Arjun | TC-Alloc-04 | `allocation/tests/test_room_change.py` | A |
| HMS-F-014 | Manage blocks, rooms, capacity | DS-Alloc-06 | AllocationModule | HMS-09 | Arjun | TC-Alloc-05 | `allocation/tests/test_blocks_rooms.py` | A |
| HMS-F-015 | Prevent over-allocation | DS-Alloc-02 | AllocationModule, PostgreSQL | HMS-12 | Arjun | TC-Alloc-06 | `allocation/tests/test_allocation.py::test_boundaries_n_minus_1_n_n_plus_1_occupancy`, `::test_second_active_allocation_impossible`, `allocation/tests/test_blocks_rooms.py::test_capacity_less_than_occupancy_rejected_by_db_constraint` | A |
| HMS-F-020 | Itemised fee statement | DS-Fee-03 | FeeModule | HMS-15 | Armaan | TC-Fee-01 | `fees/tests/test_fee_statements.py` | A |
| HMS-F-021 | Online fee payment (sandbox) | DS-Fee-01 | FeeModule, gateway adapter | HMS-28 | Armaan | TC-Fee-02, TC-Sec-10 | `fees/tests/test_payments.py` (signed webhook, replay, amount mismatch, failed payment) | A |
| HMS-F-022 | Configure fee structure per term | DS-Fee-04 | FeeModule | HMS-14 | Armaan | TC-Fee-03 | `fees/tests/test_fee_structures.py` | A |
| HMS-F-023 | PDF payment receipt | DS-Fee-05 | FeeModule | HMS-29 | Armaan | TC-Fee-04 | `fees/tests/test_payments.py` (receipt owner / other student / pending / warden) | A |
| HMS-F-024 | Reconcile payments / flag defaulters | DS-Fee-02 | FeeModule | HMS-30 | Armaan | TC-Fee-05 | `fees/tests/test_reconciliation.py` | A |
| HMS-F-030 | Raise maintenance complaint | DS-Maint-01 | ComplaintModule | HMS-19 | Arnav | TC-Maint-01, TC-Sec-09 | `complaints/tests/test_complaints.py` (incl. `test_unsafe_uploads_rejected`) | A |
| HMS-F-031 | Complaint status workflow | DS-Maint-02 | ComplaintModule | HMS-31 | Arnav | TC-Maint-02 | `complaints/tests/test_status_workflow.py` | A |
| HMS-F-040 | Occupancy / vacancy / fee reports | DS-Rep-01 | ReportingModule | HMS-32 | Arnav | TC-Rep-01 | `reports/tests/test_reports.py` | A |
| HMS-F-041 | CSV and PDF export | DS-Rep-02 | ReportingModule | HMS-33 | Arnav | TC-Rep-02 | `reports/tests/test_exports.py` | A |

## Non-functional and security requirements

| Req ID | Requirement (short) | Design ref | Module | Backlog | Owner | Test case(s) | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| HMS-NF-001 | p95 <= 2 s at 200 users | DS-Perf-01 | Web UI, all modules | HMS-26 | Arjun | TC-Perf-01 | [Locust report](perf/locust_report.html): p95 6.2 s, 7.3% failures on SQLite dev server | P (target not met in the local environment, see [D9](DEVIATIONS.md)) |
| HMS-NF-002 | 99.5% availability | DS-Ops-01 | Deployment config | HMS-24 | Arjav | TC-Ops-02 | `core/tests/test_health.py`, `core/tests/test_smoke.py::test_health_check`, Compose `restart: unless-stopped` ([uptime.md](uptime.md)) | P (partial by design, STP Section 4; no soak test) |
| HMS-NF-003 | Data protection, no card data | DS-Sec-02 | All modules | HMS-34 | Arnav | TC-Sec-01, TC-Sec-06, TC-Sec-07 | `complaints/tests/test_data_protection.py` (per-user filtering, photo access, PII masking in logs), `fees/tests/test_no_card_fields.py`; TC-Sec-07 by code review + Bandit | A (TC-Sec-07 method, see [D13](DEVIATIONS.md)) |
| HMS-NF-004 | 3-year audit retention | DS-Ops-02 | Audit component | HMS-35 | Arnav | TC-Ops-01 | `audit/tests/test_retention.py` (setting, archive, restore round trip) | A (config + archive/restore, partial by design per STP Section 4) |
| HMS-NF-005 | Responsive and WCAG 2.1 AA UI | DS-UX-01 | Web UI | HMS-22 | Arjav | TC-UX-01 | Responsive templates and labelled forms (HMS-22, PR #62) | P (manual audit at 3 viewports not recorded) |
| HMS-NF-006 | 5,000 students / 2,000 rooms; modular | DS-Scale-01 | All modules | HMS-01, HMS-27 | Arjun | TC-Scale-01 | [scale_results.md](perf/scale_results.md): paginated pages 4-7 ms on the full dataset | A |
| HMS-SR-001 | TLS 1.2+ only, HTTP redirected | DS-Sec-03 | Deployment config | HMS-23 | Arjav | TC-Sec-02 | `core/tests/test_security_settings.py`; `manage.py check --deploy` clean with `DJANGO_DEBUG=0` | P (no staging host to scan, see [D6](DEVIATIONS.md)) |
| HMS-SR-002 | Salted password hashing | DS-Sec-01 | AuthModule | HMS-05 | Arjav | TC-Sec-03 | `core/tests/test_smoke.py::test_password_is_hashed` | A |
| HMS-SR-003 | RBAC at view (and API) layer | DS-Sec-04 | AuthModule | HMS-06 | Arjav | TC-Sec-04 | `core/tests/test_security_validation.py`, 403 tests in every module | A (no REST API built, see [D2](DEVIATIONS.md)) |
| HMS-SR-004 | Immutable audit log | DS-Sec-05 | Audit component | HMS-18 | Arnav | TC-Sec-05 | `audit/tests/test_audit.py` (PostgreSQL trigger test runs in CI) | A |
| HMS-SR-005 | Gateway only, no card data | DS-Sec-06 | FeeModule | HMS-17 | Armaan | TC-Sec-06 | `fees/tests/test_no_card_fields.py`, `fees/tests/test_payments.py::test_payment_has_no_card_data_fields` | A |

## Additional security validation (STP 5.1.2, not tied to an SRS requirement)

| Case | Result |
|---|---|
| TC-Sec-07 Injection | No raw SQL (`.raw`, `cursor`, `.extra`) and no `safe` template filter or `mark_safe` in the code; Django ORM parameterises queries and templates auto-escape. Bandit: no injection findings |
| TC-Sec-08 CSRF | Passed: POST without a token is rejected with 403 |
| TC-Sec-09 File upload | Passed: wrong extension, script renamed to `.png`, wrong declared type and over-5 MB uploads rejected; stored names are randomised and photos are not reachable via a public media URL |
| TC-Sec-10 Payment webhook | Passed: unsigned / bad-signature, replayed and amount-mismatch webhooks rejected |
| TC-Sec-11 Dependencies | Executed: pip-audit flags Django 5.1.15 (see [TEST_REPORT.md](TEST_REPORT.md#security-validation)) |
| TC-Sec-12 Brute force / OTP | Not built: see [D14](DEVIATIONS.md) |
