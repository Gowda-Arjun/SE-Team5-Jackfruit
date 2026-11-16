# Unit Test Report: Team 5 HMS

STP v1.0 deliverables "Automated test suites" and "Coverage report" (STP Section 8), and the course deliverable *"Unit test report showing code and branch coverage"* (Jackfruit guidelines, Development Team deliverables). It covers the **unit** and **integration** levels of STP Section 5.2. End-to-end browser tests are in [SYSTEM_TEST_REPORT.md](SYSTEM_TEST_REPORT.md). The overall verdict against the exit criteria is in [TEST_REPORT.md](TEST_REPORT.md), and per-requirement status is in [RTM.md](RTM.md).

| | |
|---|---|
| Build under test | `main` at `0c91b99` (frozen feature set, after HMS-36 and HMS-37) |
| Executed | 16 Nov 2026, locally (Windows 11, Python 3.12.7, pytest 9.2.0, pytest-django 4.14.0, Django 5.1.15, SQLite) and in CI (GitHub Actions run [43735448753](https://github.com/Gowda-Arjun/SE-Team5-Jackfruit/actions/runs/43735448753), PostgreSQL 15) |
| Coverage tool | coverage.py 7.17.3, `--branch`, over application code (migrations and tests excluded) |
| Prepared by | Arnav Sharath Hanchanur (Test Lead) |
| Raw evidence | [`test-evidence/unit/junit.xml`](test-evidence/unit/junit.xml) (per-test results), [`test-evidence/unit/coverage_report.txt`](test-evidence/unit/coverage_report.txt) (line-level coverage) |

## 1. Summary

| Metric | Result |
|---|---|
| Automated test cases | **158** (46 unit `UT_nn`, 112 integration `IT_nn`) in 26 files |
| Passed | **157** locally; the 1 skipped case is PostgreSQL-only and passes in CI (CI: **158 passed**) |
| Failed | **0** |
| Run time | 143 s locally (SQLite); 41.6 s in CI (PostgreSQL) |
| Statement coverage | **88%** (1555 of 1776 statements) |
| Branch coverage | **68%** (191 of 280 branches) |
| STP 5.2 target | Branch >= 70% overall and >= 80% for AllocationModule and FeeModule: **not met** (see Section 3) |
| Requirements with at least one unit/integration test | 28 of 31 (all 20 functional requirements) |

## 2. Scope and approach

- **Unit (`UT_nn`)**: one model, form, service function, decorator, log filter or settings value tested without going through a URL, e.g. `allocate_room()` capacity checks, OTP hashing and expiry, `mask_pii()`, the audit-log immutability guard. White-box: written by each module owner next to the code (STP 9.1).
- **Integration (`IT_nn`)**: a request goes through the Django test client (URL routing, `role_required` decorator, view, form, model, database), or a management command runs against the database. Most of these also cross an app boundary: allocation and fee views write to `audit`, complaint status changes send email, the payment webhook updates `FeeStatement` and creates a `Receipt`, reports read allocation and fee data.
- Classification rule used for this report: a test that uses the test `client` or `call_command` is IT, everything else is UT. IDs are numbered in file order; the requirement column traces each case to SRS v1.0 (anchor test cases are listed in [RTM.md](RTM.md)).
- Tools: pytest + pytest-django + Django test client, run on every PR by `.github/workflows/ci.yml` against PostgreSQL 15. The STP's Jenkins/SonarQube, Postman and factory_boy/freezegun were not used ([DEVIATIONS.md](DEVIATIONS.md) D1, D13); time-dependent cases (OTP expiry, session expiry, audit retention) move the stored timestamps instead of freezing the clock.

### Test design techniques used (STP 5.4)

| Technique | Where | Example cases |
|---|---|---|
| Boundary value analysis | Room capacity N-1 / N / N+1; capacity below occupancy; 5 MB upload limit; OTP expiry; 20-minute session | `test_boundaries_n_minus_1_n_n_plus_1_occupancy`, `test_capacity_less_than_occupancy_rejected_by_db_constraint`, `test_oversized_photo_rejected`, `test_expired_otp_is_rejected`, `test_expired_session_redirects_to_login` |
| Equivalence partitioning | Upload type (JPG/PNG vs GIF, script, EXE, renamed file); fee amount (positive / zero / negative); report type (valid / unknown) | `test_unsafe_uploads_rejected` (parametrised), `test_non_positive_amount_is_rejected`, `test_unknown_report_type_rejected` |
| Decision table | Allocation eligibility: room active x gender policy x free bed | `test_gender_mismatch_rejected_and_logged`, `test_inactive_room_rejected_and_logged`, boundaries test |
| State transition | Complaint Open -> In Progress -> Resolved; room-change Pending -> Approved / Rejected | `test_full_workflow_records_history_audit_and_notifies`, `test_resolved_back_to_open_is_refused`, `test_invalid_transitions_rejected_and_audited` (parametrised), `test_cannot_decide_non_pending_request` |
| Error guessing / negative | Webhook replay, bad signature, amount mismatch, null order id; IDOR on photos, receipts, tickets; duplicate room / term | `test_replayed_success_webhook_credits_only_once`, `test_other_student_cannot_download_photo`, `test_another_student_cannot_download_receipt` |

## 3. Code and branch coverage

Command: `coverage run --branch --source=accounts,allocation,audit,complaints,core,fees,reports --omit="*/migrations/*,*/tests/*" -m pytest`, then `coverage report -m`.

### 3.1 By module

| Module | Statements | Covered | **Statement %** | Branches | Covered | **Branch %** | STP branch target | Met? |
|---|---|---|---|---|---|---|---|---|
| AuthModule (`accounts`) | 157 | 150 | 96% | 20 | 13 | 65% | 70% | No |
| AllocationModule (`allocation`) | 584 | 473 | 81% | 102 | 64 | 63% | 80% (module) | No |
| Audit component (`audit`) | 91 | 89 | 98% | 6 | 6 | 100% | 70% | Yes |
| ComplaintModule (`complaints`) | 178 | 172 | 97% | 18 | 18 | 100% | 70% | Yes |
| Core / Web UI (`core`) | 187 | 164 | 88% | 46 | 33 | 72% | 70% | Yes |
| FeeModule (`fees`) | 442 | 372 | 84% | 72 | 43 | 60% | 80% (module) | No |
| ReportingModule (`reports`) | 137 | 135 | 99% | 16 | 14 | 88% | 70% | Yes |
| **Total** | **1776** | **1555** | **88%** | **280** | **191** | **68%** | 70% (overall) | **No** |

The overall-row target is the STP's: 70% branch overall. Modules without their own target in STP 5.2 are shown against the 70% overall figure for comparison only.

### 3.2 By file (files with branches or uncovered lines)

| File | Statements | Statement % | Branches | Branch % | Combined % |
|---|---|---|---|---|---|
| `accounts/forms.py` | 11 | 100% | 2 | 100% | 100% |
| `accounts/models.py` | 47 | 96% | 0 | n/a | 96% |
| `accounts/password_reset_forms.py` | 14 | 93% | 2 | 50% | 88% |
| `accounts/password_reset_views.py` | 44 | 98% | 10 | 70% | 93% |
| `accounts/views.py` | 19 | 84% | 6 | 50% | 76% |
| `allocation/forms.py` | 93 | 96% | 22 | 59% | 89% |
| `allocation/management/commands/seed_scale.py` | 42 | 0% | 4 | 0% | 0% |
| `allocation/models.py` | 60 | 95% | 0 | n/a | 95% |
| `allocation/services.py` | 162 | 92% | 26 | 88% | 91% |
| `allocation/views.py` | 198 | 75% | 50 | 56% | 71% |
| `audit/management/commands/archive_audit.py` | 26 | 100% | 4 | 100% | 100% |
| `audit/models.py` | 26 | 96% | 2 | 100% | 96% |
| `audit/views.py` | 1 | 0% | 0 | n/a | 0% |
| `complaints/forms.py` | 25 | 100% | 6 | 100% | 100% |
| `complaints/models.py` | 42 | 95% | 0 | n/a | 95% |
| `complaints/services.py` | 33 | 94% | 2 | 100% | 94% |
| `complaints/views.py` | 62 | 97% | 10 | 100% | 97% |
| `core/decorators.py` | 13 | 100% | 2 | 100% | 100% |
| `core/management/commands/seed_demo.py` | 52 | 88% | 10 | 100% | 90% |
| `core/views.py` | 102 | 83% | 34 | 62% | 78% |
| `fees/forms.py` | 22 | 95% | 2 | 50% | 92% |
| `fees/gateway.py` | 60 | 57% | 10 | 10% | 50% |
| `fees/models.py` | 55 | 95% | 0 | n/a | 95% |
| `fees/services.py` | 54 | 89% | 14 | 86% | 88% |
| `fees/views.py` | 210 | 84% | 46 | 63% | 80% |
| `reports/exports.py` | 40 | 100% | 4 | 50% | 95% |
| `reports/forms.py` | 14 | 100% | 2 | 100% | 100% |
| `reports/services.py` | 52 | 96% | 6 | 100% | 97% |
| `reports/views.py` | 21 | 100% | 4 | 100% | 100% |

All other application files (`admin.py`, `apps.py`, `urls.py`, `core/log_filters.py`, `audit/services.py`, `reports/views.py`, the audit archive/restore commands, ...) are at 100%. Line numbers of every uncovered statement and partial branch are in [`coverage_report.txt`](test-evidence/unit/coverage_report.txt).

### 3.3 What is not covered, and why

| Area | Uncovered | Reason / risk |
|---|---|---|
| `allocation/management/commands/seed_scale.py` | 42 statements, 0% | HMS-27 scale-data script, run by hand for TC-Scale-01 ([perf/scale_results.md](perf/scale_results.md)); not part of the request path. Without it AllocationModule would be at 87% statements / 65% branches |
| `fees/gateway.py` | Live Razorpay adapter (`create_order`, ledger fetch), branch 10% | Needs Razorpay test keys and network; CI uses the mock gateway by design (D8). Signature verification is tested without the SDK (`test_razorpay_signature_verification_does_not_require_sdk`) |
| `allocation/views.py` | Block list / create / edit views (lines 66-108), the student-edit form on `GET` (255-267), the error messages when a room-change approval hits a full, inactive or wrong-gender room and the reject / invalid-action errors (422-435) | No pytest case opens the block pages; block creation is exercised end to end by ST_20 in the system run, which coverage does not measure. The approval error paths reuse the service exceptions that are unit tested (`test_approve_into_full_room_fails_cleanly` covers the service) |
| `fees/views.py` | My-fees messages when no fee structure exists or the allocation ended (50-55), the Razorpay checkout page (150-160), Razorpay-format webhook events (188-195) | Mock-gateway path fully tested; the Razorpay branches need live test keys (D8) |
| `core/views.py` | Dashboard fallbacks for when an app or model is absent (`_get_model` returns `None`) | Defensive code from when modules were merged in parallel; all apps are present now, so these branches cannot run. Candidate for removal in maintenance |
| `accounts/views.py` | Staff user opening the student profile page (403, line 13); plain `GET` of the profile form (31-33) | Tests POST the form directly. ST_03 opens the page with `GET` in the system run |

**Assessment.** Statement coverage (88%) is good and every requirement has executed tests, but the plan's branch targets are missed: 68% overall, AllocationModule 63%, FeeModule 60%. The gap is concentrated in error branches of two view files and the live-gateway adapter. This is recorded in [TEST_REPORT.md](TEST_REPORT.md) Section 9 and is item M-07 of the [maintenance plan](MAINTENANCE_PLAN.md); the most direct fix is a small set of view-level tests for the block pages and the allocation and fee error messages listed above.

## 4. Results by module

| Module | Test files | UT | IT | Total | Passed | Skipped | Failed |
|---|---|---|---|---|---|---|---|
| AuthModule | `test_password_reset`, `test_profile`, `test_session` | 0 | 10 | 10 | 10 | 0 | 0 |
| AllocationModule | `test_allocation`, `test_blocks_rooms`, `test_my_room`, `test_room_change`, `test_student_records` | 7 | 21 | 28 | 28 | 0 | 0 |
| Audit component | `test_audit`, `test_retention` | 7 | 5 | 12 | 11 | 1 | 0 |
| ComplaintModule | `test_complaints`, `test_data_protection`, `test_status_workflow` | 15 | 23 | 38 | 38 | 0 | 0 |
| Core / Web UI | `test_dashboards`, `test_health`, `test_security_settings`, `test_security_validation`, `test_seed_demo`, `test_smoke` | 2 | 15 | 17 | 17 | 0 | 0 |
| FeeModule | `test_fee_statements`, `test_fee_structures`, `test_no_card_fields`, `test_payments`, `test_reconciliation` | 7 | 30 | 37 | 37 | 0 | 0 |
| ReportingModule | `test_exports`, `test_reports` | 8 | 8 | 16 | 16 | 0 | 0 |
| **Total** | 26 files | **46** | **112** | **158** | **157** | **1** | **0** |

## 5. Requirement coverage by test level

Course Phase-3 guideline: 8-10 unit, integration and system test cases per implemented use case. Counts below are executed cases per requirement across this report (UT, IT) and the system test report (ST). A case that verifies two requirements counts for both.

| Req ID | Requirement | Pri. | UT | IT | ST | Total | System test cases |
|---|---|---|---|---|---|---|---|
| HMS-F-001 | Log in with role | High | 0 | 7 | 4 | 11 | ST_01, ST_02, ST_18, ST_19 |
| HMS-F-002 | Student profile update | Med | 0 | 3 | 1 | 4 | ST_03 |
| HMS-F-003 | OTP password reset (10 min) | Med | 0 | 4 | 1 | 5 | ST_04 |
| HMS-F-004 | Session timeout (20 min) | High | 0 | 4 | 1 | 5 | ST_05 |
| HMS-F-005 | RBAC: 403 and logged | High | 0 | 18 | 2 | 20 | ST_17, ST_18 |
| HMS-F-010 | View own room and roommates | High | 0 | 3 | 1 | 4 | ST_06 |
| HMS-F-011 | Admin CRUD on student records | High | 0 | 4 | 1 | 5 | ST_19 |
| HMS-F-012 | Allocate / reallocate room | High | 3 | 1 | 3 | 7 | ST_07, ST_22, ST_23 |
| HMS-F-013 | Room-change request and approval | Med | 1 | 8 | 2 | 11 | ST_08, ST_29 |
| HMS-F-014 | Manage blocks, rooms, capacity | High | 0 | 5 | 2 | 7 | ST_20, ST_21 |
| HMS-F-015 | Prevent over-allocation | High | 3 | 0 | 1 | 4 | ST_22 |
| HMS-F-020 | Itemised fee statement | High | 2 | 3 | 1 | 6 | ST_09 |
| HMS-F-021 | Online fee payment (sandbox) | High | 2 | 10 | 2 | 14 | ST_10, ST_32 |
| HMS-F-022 | Fee structure per term | Med | 1 | 7 | 1 | 9 | ST_24 |
| HMS-F-023 | PDF payment receipt | Med | 0 | 5 | 1 | 6 | ST_11 |
| HMS-F-024 | Reconcile payments / defaulters | High | 0 | 5 | 1 | 6 | ST_12 |
| HMS-F-030 | Raise maintenance complaint | Med | 1 | 10 | 2 | 13 | ST_13, ST_25 |
| HMS-F-031 | Complaint status workflow | Med | 5 | 6 | 2 | 13 | ST_14, ST_27 |
| HMS-F-040 | Occupancy / vacancy / fee reports | Med | 7 | 5 | 2 | 14 | ST_15, ST_28 |
| HMS-F-041 | CSV and PDF export | Low | 1 | 3 | 1 | 5 | ST_16 |
| HMS-NF-001 | p95 <= 2 s at 200 users | High | 0 | 0 | 0 | 0 | - |
| HMS-NF-002 | 99.5% availability | High | 0 | 1 | 0 | 1 | - |
| HMS-NF-003 | Data protection, no card data | High | 8 | 7 | 1 | 16 | ST_26 |
| HMS-NF-004 | 3-year audit retention | High | 1 | 4 | 0 | 5 | - |
| HMS-NF-005 | Responsive, WCAG 2.1 AA | Med | 0 | 0 | 1 | 1 | ST_30 |
| HMS-NF-006 | 5,000 students / 2,000 rooms | Med | 0 | 0 | 0 | 0 | - |
| HMS-SR-001 | TLS 1.2+, HTTP redirected | High | 1 | 0 | 0 | 1 | - |
| HMS-SR-002 | Salted password hashing | High | 1 | 0 | 0 | 1 | - |
| HMS-SR-003 | RBAC at view layer | High | 0 | 18 | 3 | 21 | ST_11, ST_17, ST_26 |
| HMS-SR-004 | Immutable audit log | High | 6 | 1 | 1 | 8 | ST_33 |
| HMS-SR-005 | Gateway only, no card data | High | 3 | 0 | 1 | 4 | ST_10 |

All 20 functional requirements have executed cases at the unit/integration level and at least one system case. 12 functional requirements have fewer than 8 cases in total (HMS-F-002, HMS-F-003, HMS-F-004, HMS-F-010, HMS-F-011, HMS-F-012, HMS-F-014, HMS-F-015, HMS-F-020, HMS-F-023, HMS-F-024, HMS-F-041). For each of them the positive path and the main negative or access-control path are covered, but the count is below the guideline's 8-10; topping these up is item M-08 of the [maintenance plan](MAINTENANCE_PLAN.md). HMS-NF-001, HMS-NF-006 and HMS-SR-001 are verified outside pytest (Locust, the scale script and `check --deploy`; see [TEST_REPORT.md](TEST_REPORT.md)).

## 6. Defects found at unit and integration level

| Defect | Found by | Severity (STP 14.3) | Resolution |
|---|---|---|---|
| Technician could open the Admin/Warden dashboard | RBAC review, regression test `test_technician_cannot_access_admin_dashboard` | 2 | Fixed in PR #50 |
| `SELECT ... FOR UPDATE` on a nullable join failed on PostgreSQL | Allocation tests on PostgreSQL in CI | 2 | Fixed in `a0bf9a3` |
| Two fee migrations numbered `0003` after parallel PRs | `makemigrations --check` in CI | 3 | Renumbered to `0005` (PR #67) |

No unit or integration defect is open. Defects found by the system run are in [SYSTEM_TEST_REPORT.md](SYSTEM_TEST_REPORT.md) Section 6.

## 7. How to reproduce

```bash
pip install -r requirements.txt coverage
pytest -v --junitxml=docs/test-evidence/unit/junit.xml
coverage run --branch --source=accounts,allocation,audit,complaints,core,fees,reports \
  --omit="*/migrations/*,*/tests/*" -m pytest
coverage report -m              # add `coverage html` for a browsable report
```

To run the PostgreSQL-only trigger test locally, set `POSTGRES_DB` (and user/password/host) as in CI or use `docker compose up`.

## Appendix A. Test case list

Every automated case with its result from this run. **Steps and test data** for each case are the body of the named test function (arrange, act, assert). Expected result = the assertions; actual result = Pass means every assertion held.

### AuthModule

| Test Case ID | Test function | Description | Requirement | Result | Time (s) |
|---|---|---|---|---|---|
| IT_01 | `test_password_reset.py::test_forgot_password_creates_hashed_otp` | Forgot password creates hashed otp | HMS-F-003 | Pass | 3.13 |
| IT_02 | `test_password_reset.py::test_unknown_email_returns_generic_response` | Unknown email returns generic response | HMS-F-003 | Pass | 0.01 |
| IT_03 | `test_password_reset.py::test_reset_password_success_and_single_use` | Reset password success and single use | HMS-F-003 | Pass | 3.04 |
| IT_04 | `test_password_reset.py::test_expired_otp_is_rejected` | Expired otp is rejected | HMS-F-003 | Pass | 1.83 |
| IT_05 | `test_profile.py::test_student_can_update_own_profile` | Student can update own profile | HMS-F-002 | Pass | 0.63 |
| IT_06 | `test_profile.py::test_unauthenticated_user_cannot_access_profile` | Unauthenticated user cannot access profile | HMS-F-002, HMS-F-005, HMS-SR-003 | Pass | 0.01 |
| IT_07 | `test_profile.py::test_student_can_only_update_own_profile` | Student can only update own profile | HMS-F-002 | Pass | 1.25 |
| IT_08 | `test_session.py::test_session_expiry_age_is_20_minutes` | Session expiry age is 20 minutes | HMS-F-004 | Pass | 0.62 |
| IT_09 | `test_session.py::test_active_request_refreshes_session_expiry` | Active request refreshes session expiry | HMS-F-004 | Pass | 1.91 |
| IT_10 | `test_session.py::test_expired_session_redirects_to_login` | Expired session redirects to login | HMS-F-004 | Pass | 2.70 |

### AllocationModule

| Test Case ID | Test function | Description | Requirement | Result | Time (s) |
|---|---|---|---|---|---|
| UT_01 | `test_allocation.py::test_boundaries_n_minus_1_n_n_plus_1_occupancy` | Room with capacity 2: N-1 (1st allocation), N (2nd allocation), N+1 (3rd allocation rejected). | HMS-F-015 | Pass | 0.63 |
| UT_02 | `test_allocation.py::test_gender_mismatch_rejected_and_logged` | Gender mismatch rejected and logged | HMS-F-012 | Pass | 1.22 |
| UT_03 | `test_allocation.py::test_inactive_room_rejected_and_logged` | Inactive room rejected and logged | HMS-F-012 | Pass | 1.15 |
| UT_04 | `test_allocation.py::test_reallocation_moves_occupancy` | Reallocation moves occupancy | HMS-F-012 | Pass | 1.24 |
| UT_05 | `test_allocation.py::test_second_active_allocation_impossible` | Second active allocation impossible | HMS-F-015 | Pass | 0.66 |
| IT_11 | `test_allocation.py::test_allocate_view_success_and_student_403` | Allocate view success and student 403 | HMS-F-012, HMS-F-005, HMS-SR-003 | Pass | 1.58 |
| IT_12 | `test_blocks_rooms.py::test_create_and_edit_room` | Create and edit room | HMS-F-014 | Pass | 0.64 |
| IT_13 | `test_blocks_rooms.py::test_duplicate_room_number_in_same_block_rejected` | Duplicate room number in same block rejected | HMS-F-014 | Pass | 0.70 |
| UT_06 | `test_blocks_rooms.py::test_capacity_less_than_occupancy_rejected_by_db_constraint` | Capacity less than occupancy rejected by db constraint | HMS-F-015 | Pass | 0.01 |
| IT_14 | `test_blocks_rooms.py::test_student_gets_403_on_admin_pages` | Student gets 403 on admin pages | HMS-F-014, HMS-F-005, HMS-SR-003 | Pass | 0.61 |
| IT_15 | `test_blocks_rooms.py::test_room_deactivation` | Room deactivation | HMS-F-014 | Pass | 0.61 |
| IT_16 | `test_blocks_rooms.py::test_availability_counts_in_room_list` | Availability counts in room list | HMS-F-014 | Pass | 0.69 |
| IT_17 | `test_my_room.py::test_student_views_own_room_and_roommates` | Student views own room and roommates | HMS-F-010 | Pass | 1.87 |
| IT_18 | `test_my_room.py::test_student_without_allocation_sees_message` | Student without allocation sees message | HMS-F-010 | Pass | 0.59 |
| IT_19 | `test_my_room.py::test_admin_gets_403_on_my_room` | Admin gets 403 on my room | HMS-F-010, HMS-F-005, HMS-SR-003 | Pass | 0.57 |
| IT_20 | `test_room_change.py::test_submit_room_change_request_success` | Student submits a valid room change request. | HMS-F-013 | Pass | 1.28 |
| IT_21 | `test_room_change.py::test_submit_without_active_allocation_fails` | Student without an active allocation cannot submit. | HMS-F-013 | Pass | 0.76 |
| IT_22 | `test_room_change.py::test_duplicate_pending_request_refused` | Only one PENDING request allowed per student. | HMS-F-013 | Pass | 0.62 |
| IT_23 | `test_room_change.py::test_student_sees_request_status` | Student can view their request status (Pending, Approved, Rejected). | HMS-F-013 | Pass | 0.64 |
| IT_24 | `test_room_change.py::test_queue_access_control` | Student cannot access the change queue (403), while staff can access (200). | HMS-F-013, HMS-F-005, HMS-SR-003 | Pass | 1.02 |
| IT_25 | `test_room_change.py::test_approve_room_change_moves_student` | Approve reallocates the student, adjusts occupancies, logs audit. | HMS-F-013 | Pass | 0.67 |
| IT_26 | `test_room_change.py::test_approve_into_full_room_fails_cleanly` | Approving into a full room fails cleanly, request stays PENDING. | HMS-F-013 | Pass | 0.68 |
| IT_27 | `test_room_change.py::test_reject_room_change_request` | Reject marks request REJECTED, allocation stays intact, logs audit. | HMS-F-013 | Pass | 1.77 |
| UT_07 | `test_room_change.py::test_cannot_decide_non_pending_request` | Only PENDING requests can be decided. | HMS-F-013 | Pass | 1.28 |
| IT_28 | `test_student_records.py::test_create_student_appears_in_list` | Create student appears in list | HMS-F-011 | Pass | 0.64 |
| IT_29 | `test_student_records.py::test_edit_student_persists` | Edit student persists | HMS-F-011 | Pass | 1.26 |
| IT_30 | `test_student_records.py::test_deactivate_hides_student_from_list_and_blocks_login` | Deactivate hides student from list and blocks login | HMS-F-011 | Pass | 1.67 |
| IT_31 | `test_student_records.py::test_student_role_gets_403` | Student role gets 403 | HMS-F-011, HMS-F-005, HMS-SR-003 | Pass | 0.41 |

### Audit component

| Test Case ID | Test function | Description | Requirement | Result | Time (s) |
|---|---|---|---|---|---|
| UT_08 | `test_audit.py::test_write_audit_records_actor_action_target` | Write audit records actor action target | HMS-SR-004 | Pass | 0.43 |
| UT_09 | `test_audit.py::test_audit_entry_cannot_be_updated` | Audit log is immutable. | HMS-SR-004 | Pass | 0.45 |
| UT_10 | `test_audit.py::test_audit_entry_cannot_be_deleted` | Audit entry cannot be deleted | HMS-SR-004 | Pass | 0.37 |
| UT_11 | `test_audit.py::test_audit_rolls_back_with_callers_transaction` | Audit rolls back with callers transaction | HMS-SR-004 | Pass | 0.63 |
| UT_12 | `test_audit.py::test_anonymous_actor_stored_as_null` | Anonymous actor stored as null | HMS-SR-004 | Pass | 0.00 |
| IT_32 | `test_audit.py::test_admin_screen_is_read_only` | Admin screen is read only | HMS-SR-004 | Pass | 0.94 |
| UT_13 | `test_audit.py::test_database_blocks_bulk_update_on_postgres` | The model guard can be bypassed by queryset.update(); the PostgreSQL trigger cannot. | HMS-SR-004 | Skipped locally (SQLite); Pass in CI | 0.06 |
| UT_14 | `test_retention.py::test_retention_setting_is_three_years` | Audit logs are retained for at least 3 years. | HMS-NF-004 | Pass | 0.01 |
| IT_33 | `test_retention.py::test_archive_exports_only_rows_past_retention` | Archive exports only rows past retention | HMS-NF-004 | Pass | 0.61 |
| IT_34 | `test_retention.py::test_archive_all` | Archive all | HMS-NF-004 | Pass | 0.62 |
| IT_35 | `test_retention.py::test_restore_round_trip_keeps_original_timestamps` | Archived logs are retrievable on request. | HMS-NF-004 | Pass | 0.64 |
| IT_36 | `test_retention.py::test_restore_twice_does_not_duplicate` | Restore twice does not duplicate | HMS-NF-004 | Pass | 0.67 |

### ComplaintModule

| Test Case ID | Test function | Description | Requirement | Result | Time (s) |
|---|---|---|---|---|---|
| IT_37 | `test_complaints.py::test_raise_complaint_creates_open_ticket` | Unique ticket id and status Open. | HMS-F-030 | Pass | 0.59 |
| UT_15 | `test_complaints.py::test_ticket_ids_are_unique` | Ticket ids are unique | HMS-F-030 | Pass | 0.56 |
| IT_38 | `test_complaints.py::test_valid_photo_is_stored_with_random_name` | Valid photo is stored with random name | HMS-F-030 | Pass | 0.57 |
| IT_39 | `test_complaints.py::test_unsafe_uploads_rejected` | File-upload safety. (case: evil.php) | HMS-F-030 (TC-Sec-09) | Pass | 0.47 |
| IT_40 | `test_complaints.py::test_unsafe_uploads_rejected` | File-upload safety. (case: evil.png) | HMS-F-030 (TC-Sec-09) | Pass | 0.62 |
| IT_41 | `test_complaints.py::test_unsafe_uploads_rejected` | File-upload safety. (case: doc.png) | HMS-F-030 (TC-Sec-09) | Pass | 0.65 |
| IT_42 | `test_complaints.py::test_oversized_photo_rejected` | Oversized photo rejected | HMS-F-030 (TC-Sec-09) | Pass | 0.60 |
| IT_43 | `test_complaints.py::test_missing_fields_show_errors` | Missing fields show errors | HMS-F-030 | Pass | 0.57 |
| IT_44 | `test_complaints.py::test_student_sees_only_own_complaints` | Student sees only own complaints | HMS-F-030 | Pass | 1.09 |
| IT_45 | `test_complaints.py::test_admin_cannot_use_student_complaint_form` | Admin cannot use student complaint form | HMS-F-030, HMS-F-005, HMS-SR-003 | Pass | 0.39 |
| IT_46 | `test_complaints.py::test_anonymous_redirected_to_login` | Anonymous redirected to login | HMS-F-030 | Pass | 0.03 |
| IT_47 | `test_data_protection.py::test_owner_downloads_photo_as_attachment` | Owner downloads photo as attachment | HMS-NF-003 | Pass | 0.54 |
| IT_48 | `test_data_protection.py::test_other_student_cannot_download_photo` | IDOR attempt returns 404. | HMS-NF-003 | Pass | 0.99 |
| IT_49 | `test_data_protection.py::test_warden_can_download_photo` | Warden can download photo | HMS-NF-003 | Pass | 0.91 |
| IT_50 | `test_data_protection.py::test_unassigned_technician_cannot_download_photo` | Unassigned technician cannot download photo | HMS-NF-003 | Pass | 1.25 |
| IT_51 | `test_data_protection.py::test_no_photo_is_404` | No photo is 404 | HMS-NF-003 | Pass | 0.69 |
| IT_52 | `test_data_protection.py::test_photo_not_reachable_via_public_media_url` | Uploads are not served from a public /media/ URL. | HMS-NF-003 | Pass | 0.62 |
| UT_16 | `test_data_protection.py::test_mask_pii` | Mask pii (case: login failed for stu1@pes.edu) | HMS-NF-003 | Pass | 0.01 |
| UT_17 | `test_data_protection.py::test_mask_pii` | Mask pii (case: call 9876543210 now) | HMS-NF-003 | Pass | 0.01 |
| UT_18 | `test_data_protection.py::test_mask_pii` | Mask pii (case: guardian +91 9876543210) | HMS-NF-003 | Pass | 0.06 |
| UT_19 | `test_data_protection.py::test_mask_pii` | Mask pii (case: ticket CMP-000123 updated) | HMS-NF-003 | Pass | 0.01 |
| UT_20 | `test_data_protection.py::test_log_records_are_masked` | Log records are masked | HMS-NF-003 | Pass | 0.01 |
| UT_21 | `test_data_protection.py::test_no_card_fields_in_complaint_or_any_model` | TC-Sec-06 style schema check: no card/CVV/PAN fields anywhere in HMS. | HMS-SR-005 | Pass | 0.01 |
| UT_22 | `test_data_protection.py::test_django_loggers_mask_pii` | Django's own loggers use only the masking handler and do not bypass it via their defaults. (case: django) | HMS-NF-003 | Pass | 0.01 |
| UT_23 | `test_data_protection.py::test_django_loggers_mask_pii` | Django's own loggers use only the masking handler and do not bypass it via their defaults. (case: django.server) | HMS-NF-003 | Pass | 0.01 |
| UT_24 | `test_data_protection.py::test_root_handlers_mask_pii` | App loggers (e.g. complaints.services) propagate to root, whose handlers all mask PII. | HMS-NF-003 | Pass | 0.01 |
| IT_53 | `test_data_protection.py::test_student_cannot_reach_admin_records_by_id` | Guessing another record's id from a student account is refused (403). | HMS-NF-003, HMS-F-005, HMS-SR-003 | Pass | 1.23 |
| UT_25 | `test_status_workflow.py::test_full_workflow_records_history_audit_and_notifies` | Open -> In Progress -> Resolved, timestamped, student notified. | HMS-F-031 | Pass | 1.20 |
| UT_26 | `test_status_workflow.py::test_invalid_transitions_rejected_and_audited` | Invalid transitions rejected and audited (case: OPEN-RESOLVED) | HMS-F-031 | Pass | 1.21 |
| UT_27 | `test_status_workflow.py::test_invalid_transitions_rejected_and_audited` | Invalid transitions rejected and audited (case: IN_PROGRESS-OPEN) | HMS-F-031 | Pass | 1.41 |
| UT_28 | `test_status_workflow.py::test_resolved_back_to_open_is_refused` | Resolved back to open is refused | HMS-F-031 | Pass | 1.32 |
| UT_29 | `test_status_workflow.py::test_garbage_status_rejected` | Garbage status rejected | HMS-F-031 | Pass | 1.17 |
| IT_54 | `test_status_workflow.py::test_warden_updates_status_from_queue` | Warden updates status from queue | HMS-F-031 | Pass | 1.31 |
| IT_55 | `test_status_workflow.py::test_queue_filter_by_status` | Queue filter by status | HMS-F-031 | Pass | 1.09 |
| IT_56 | `test_status_workflow.py::test_student_cannot_open_queue_or_change_status` | Student cannot open queue or change status | HMS-F-031, HMS-F-005, HMS-SR-003 | Pass | 0.54 |
| IT_57 | `test_status_workflow.py::test_technician_sees_only_assigned` | Technician sees only assigned | HMS-F-031 | Pass | 1.22 |
| IT_58 | `test_status_workflow.py::test_student_sees_timeline_on_own_ticket` | Student sees timeline on own ticket | HMS-F-031 | Pass | 1.14 |
| IT_59 | `test_status_workflow.py::test_student_cannot_view_another_students_ticket` | IDOR protection: another student's ticket id returns 404. | HMS-F-031 | Pass | 1.12 |

### Core / Web UI

| Test Case ID | Test function | Description | Requirement | Result | Time (s) |
|---|---|---|---|---|---|
| IT_60 | `test_dashboards.py::test_student_dashboard_shows_room_and_current_balance` | Student dashboard shows room and current balance | HMS-F-005, HMS-SR-003 | Pass | 0.69 |
| IT_61 | `test_dashboards.py::test_admin_dashboard_shows_occupancy_numbers` | Admin dashboard shows occupancy numbers | HMS-F-005, HMS-SR-003 | Pass | 0.78 |
| IT_62 | `test_dashboards.py::test_navigation_is_role_based_and_skips_unregistered_urls` | Navigation is role based and skips unregistered urls (case: STUDENT) | HMS-F-005, HMS-SR-003 | Pass | 0.63 |
| IT_63 | `test_dashboards.py::test_navigation_is_role_based_and_skips_unregistered_urls` | Navigation is role based and skips unregistered urls (case: WARDEN) | HMS-F-005, HMS-SR-003 | Pass | 0.57 |
| IT_64 | `test_dashboards.py::test_technician_cannot_access_admin_dashboard` | Technician cannot access admin dashboard | HMS-F-005, HMS-SR-003 | Pass | 0.66 |
| IT_65 | `test_health.py::test_healthz_returns_200` | Healthz returns 200 | HMS-NF-002 | Pass | 0.01 |
| UT_30 | `test_security_settings.py::test_production_https_security_flags` | Production https security flags | HMS-SR-001 | Pass | 0.00 |
| IT_66 | `test_security_validation.py::test_post_without_csrf_token_is_rejected` | A form POST without a CSRF token gets 403. | HMS-F-004 (TC-Sec-08) | Pass | 0.72 |
| IT_67 | `test_security_validation.py::test_denied_role_access_returns_403_and_is_logged` | A Student on a Warden/Admin page gets 403 and the attempt is logged. | HMS-F-005, HMS-SR-003 | Pass | 0.66 |
| IT_68 | `test_seed_demo.py::test_seed_demo_creates_users_and_is_idempotent` | Seed demo creates users and is idempotent | HMS-F-001 | Pass | 7.39 |
| IT_69 | `test_seed_demo.py::test_seeded_accounts_can_log_in` | Seeded accounts can log in | HMS-F-001 | Pass | 8.03 |
| IT_70 | `test_smoke.py::test_health_check` | Health check | HMS-F-001 | Pass | 0.01 |
| IT_71 | `test_smoke.py::test_home_requires_login` | Home requires login | HMS-F-001 | Pass | 0.00 |
| IT_72 | `test_smoke.py::test_dashboard_by_role` | Dashboard by role (case: STUDENT-Welcome) | HMS-F-001 | Pass | 0.65 |
| IT_73 | `test_smoke.py::test_dashboard_by_role` | Dashboard by role (case: ADMIN) | HMS-F-001 | Pass | 0.63 |
| UT_31 | `test_smoke.py::test_password_is_hashed` | Passwords are stored as salted hashes, never plaintext. | HMS-SR-002 | Pass | 0.60 |
| IT_74 | `test_smoke.py::test_login_page_and_login_flow` | Login page and login flow | HMS-F-001 | Pass | 1.20 |

### FeeModule

| Test Case ID | Test function | Description | Requirement | Result | Time (s) |
|---|---|---|---|---|---|
| UT_32 | `test_fee_statements.py::test_statement_uses_fee_structure_for_allocated_room_type` | Statement uses fee structure for allocated room type | HMS-F-020 | Pass | 0.65 |
| UT_33 | `test_fee_statements.py::test_existing_statement_amount_stays_fixed_after_structure_edit` | Existing statement amount stays fixed after structure edit | HMS-F-022 | Pass | 0.75 |
| IT_75 | `test_fee_statements.py::test_fee_statement_balance_is_due_minus_paid` | Fee statement balance is due minus paid | HMS-F-020 | Pass | 0.74 |
| UT_34 | `test_fee_statements.py::test_missing_fee_structure_raises_no_fee_structure` | Missing fee structure raises no fee structure | HMS-F-020 | Pass | 0.53 |
| IT_76 | `test_fee_statements.py::test_student_sees_only_their_own_fee_statement` | Student sees only their own fee statement | HMS-F-020 | Pass | 1.14 |
| IT_77 | `test_fee_statements.py::test_student_without_allocation_sees_no_statement_message` | Student without allocation sees no statement message | HMS-F-020 | Pass | 0.57 |
| IT_78 | `test_fee_structures.py::test_warden_can_create_fee_structure_and_audit_it` | Warden can create fee structure and audit it | HMS-F-022 | Pass | 0.66 |
| IT_79 | `test_fee_structures.py::test_duplicate_term_and_room_type_is_rejected` | Duplicate term and room type is rejected | HMS-F-022 | Pass | 0.66 |
| IT_80 | `test_fee_structures.py::test_non_positive_amount_is_rejected` | Non positive amount is rejected (case: 0.00) | HMS-F-022 | Pass | 0.61 |
| IT_81 | `test_fee_structures.py::test_non_positive_amount_is_rejected` | Non positive amount is rejected (case: -1.00) | HMS-F-022 | Pass | 0.59 |
| IT_82 | `test_fee_structures.py::test_student_is_forbidden_from_fee_structure_pages` | Student is forbidden from fee structure pages | HMS-F-022, HMS-F-005, HMS-SR-003 | Pass | 0.57 |
| IT_83 | `test_fee_structures.py::test_edit_saves_changes_and_writes_audit` | Edit saves changes and writes audit | HMS-F-022 | Pass | 0.60 |
| IT_84 | `test_fee_structures.py::test_admin_create_and_edit_are_audited` | Admin create and edit are audited | HMS-F-022 | Pass | 0.59 |
| UT_35 | `test_no_card_fields.py::test_hms_models_do_not_store_card_data` | Hms models do not store card data | HMS-SR-005 | Pass | 0.00 |
| IT_85 | `test_payments.py::test_successful_webhook_updates_payment_and_statement` | Successful webhook updates payment and statement | HMS-F-021 | Pass | 0.56 |
| IT_86 | `test_payments.py::test_webhook_rejects_bad_signature_and_audits_denial` | Webhook rejects bad signature and audits denial | HMS-F-021 (TC-Sec-10) | Pass | 0.66 |
| IT_87 | `test_payments.py::test_replayed_success_webhook_credits_only_once` | Replayed success webhook credits only once | HMS-F-021 (TC-Sec-10) | Pass | 0.58 |
| IT_88 | `test_payments.py::test_webhook_rejects_amount_mismatch` | Webhook rejects amount mismatch | HMS-F-021 (TC-Sec-10) | Pass | 0.45 |
| IT_89 | `test_payments.py::test_failed_webhook_does_not_change_statement_balance` | Failed webhook does not change statement balance | HMS-F-021 | Pass | 0.43 |
| IT_90 | `test_payments.py::test_pay_now_creates_pending_payment_and_redirects_to_checkout` | Pay now creates pending payment and redirects to checkout | HMS-F-021 | Pass | 0.50 |
| IT_91 | `test_payments.py::test_pay_now_reports_zero_balance` | Pay now reports zero balance | HMS-F-021 | Pass | 0.48 |
| IT_92 | `test_payments.py::test_mock_checkout_offers_signed_test_outcomes` | Mock checkout offers signed test outcomes | HMS-F-021 | Pass | 0.66 |
| IT_93 | `test_payments.py::test_student_fee_page_offers_pay_now` | Student fee page offers pay now | HMS-F-021 | Pass | 0.85 |
| UT_36 | `test_payments.py::test_razorpay_signature_verification_does_not_require_sdk` | Razorpay signature verification does not require sdk | HMS-F-021 | Pass | 0.00 |
| UT_37 | `test_payments.py::test_payment_has_no_card_data_fields` | Payment has no card data fields | HMS-SR-005 | Pass | 0.00 |
| UT_38 | `test_payments.py::test_multiple_payments_can_have_null_gateway_order_ids` | Multiple payments can have null gateway order ids | HMS-F-021 | Pass | 0.57 |
| IT_94 | `test_payments.py::test_webhook_without_order_id_does_not_match_null_order` | Webhook without order id does not match null order | HMS-F-021 (TC-Sec-10) | Pass | 0.73 |
| IT_95 | `test_payments.py::test_receipt_download_for_owner_returns_pdf` | Receipt download for owner returns pdf | HMS-F-023 | Pass | 0.63 |
| IT_96 | `test_payments.py::test_another_student_cannot_download_receipt` | Another student cannot download receipt | HMS-F-023 | Pass | 1.15 |
| IT_97 | `test_payments.py::test_pending_payment_has_no_downloadable_receipt` | Pending payment has no downloadable receipt | HMS-F-023 | Pass | 0.62 |
| IT_98 | `test_payments.py::test_warden_can_download_receipt` | Warden can download receipt | HMS-F-023 | Pass | 1.20 |
| IT_99 | `test_payments.py::test_my_fees_shows_successful_payment_receipt` | My fees shows successful payment receipt | HMS-F-023 | Pass | 0.61 |
| IT_100 | `test_reconciliation.py::test_reconciliation_detects_ledger_mismatch` | Reconciliation detects ledger mismatch | HMS-F-024 | Pass | 1.23 |
| IT_101 | `test_reconciliation.py::test_mock_gateway_matches_its_successful_database_payments` | Mock gateway matches its successful database payments | HMS-F-024 | Pass | 1.29 |
| IT_102 | `test_reconciliation.py::test_reconciliation_defaulters_match_overdue_unpaid_statements` | Reconciliation defaulters match overdue unpaid statements | HMS-F-024 | Pass | 1.21 |
| IT_103 | `test_reconciliation.py::test_student_is_forbidden_from_reconciliation` | Student is forbidden from reconciliation | HMS-F-024, HMS-F-005, HMS-SR-003 | Pass | 0.61 |
| IT_104 | `test_reconciliation.py::test_gateway_outage_shows_service_unavailable_message` | Gateway outage shows service unavailable message | HMS-F-024 | Pass | 0.63 |

### ReportingModule

| Test Case ID | Test function | Description | Requirement | Result | Time (s) |
|---|---|---|---|---|---|
| UT_39 | `test_exports.py::test_pdf_contains_every_row_and_total` | Pdf contains every row and total | HMS-F-041 | Pass | 0.01 |
| IT_105 | `test_exports.py::test_csv_export_matches_screen` | Exported file matches the on-screen data. | HMS-F-041 | Pass | 3.01 |
| IT_106 | `test_exports.py::test_pdf_export_is_downloadable` | Pdf export is downloadable | HMS-F-041 | Pass | 3.00 |
| IT_107 | `test_exports.py::test_export_buttons_shown_with_report` | Export buttons shown with report | HMS-F-041 | Pass | 2.73 |
| UT_40 | `test_reports.py::test_occupancy_matches_allocations` | Figures match the underlying allocation records. | HMS-F-040 | Pass | 2.15 |
| UT_41 | `test_reports.py::test_occupancy_range_includes_old_allocation` | An allocation that ended 300 days ago counts only when the range covers it. | HMS-F-040 | Pass | 2.18 |
| UT_42 | `test_reports.py::test_vacancy_lists_rooms_with_free_beds` | Vacancy lists rooms with free beds | HMS-F-040 | Pass | 2.04 |
| UT_43 | `test_reports.py::test_fee_collection_counts_only_successful_payments` | Fee collection counts only successful payments | HMS-F-040 | Pass | 2.03 |
| UT_44 | `test_reports.py::test_defaulters_are_past_due_with_balance` | Defaulters are past due with balance | HMS-F-040 | Pass | 2.08 |
| UT_45 | `test_reports.py::test_invalid_date_range_rejected` | Invalid date range rejected | HMS-F-040 | Pass | 0.00 |
| UT_46 | `test_reports.py::test_unknown_report_type_rejected` | Unknown report type rejected | HMS-F-040 | Pass | 0.00 |
| IT_108 | `test_reports.py::test_report_page_renders_table` | Report page renders table | HMS-F-040 | Pass | 2.83 |
| IT_109 | `test_reports.py::test_report_page_bad_range_is_400` | Report page bad range is 400 | HMS-F-040 | Pass | 0.55 |
| IT_110 | `test_reports.py::test_report_page_without_params_shows_form` | Report page without params shows form | HMS-F-040 | Pass | 0.55 |
| IT_111 | `test_reports.py::test_students_cannot_open_reports` | Students cannot open reports | HMS-F-040, HMS-F-005, HMS-SR-003 | Pass | 0.52 |
| IT_112 | `test_reports.py::test_missing_module_gives_friendly_message` | Missing module gives friendly message | HMS-F-040 | Pass | 0.55 |
