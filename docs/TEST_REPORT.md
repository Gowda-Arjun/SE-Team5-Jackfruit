# Test Summary Report: Team 5 HMS (final)

Test Plan v1.0 (STP) deliverable "Test Summary Report", owned by the Test Lead (Arnav). Final status per requirement: [RTM.md](RTM.md). Detailed test cases and results by level: [UNIT_TEST_REPORT.md](UNIT_TEST_REPORT.md) (unit and integration, code and branch coverage) and [SYSTEM_TEST_REPORT.md](SYSTEM_TEST_REPORT.md) (end-to-end browser tests). Follow-up work: [MAINTENANCE_PLAN.md](MAINTENANCE_PLAN.md).

**Executed:** 15 Nov 2026, on `main` with HMS-30 (#70) and HMS-36 merged in, i.e. the frozen feature set.

## 1. Environments

| Environment | Database | Runs |
|---|---|---|
| Local (Windows 11, Python 3.12.7, pytest 9.2, Django 5.1.15) | SQLite | Full suite, coverage, Bandit, pip-audit, `check --deploy` |
| CI (GitHub Actions, `.github/workflows/ci.yml`, Python 3.12) | PostgreSQL 15 | flake8, `makemigrations --check`, full suite on every PR and on `main` |

The Test Plan's tools differ from what we used; see [DEVIATIONS.md](DEVIATIONS.md) D1 (GitHub Actions instead of Jenkins/SonarQube) and D13 (pytest + Django test client instead of Selenium/Postman/ZAP/testssl).

## 2. Summary

| Metric | Result |
|---|---|
| Automated tests | **158**: 157 passed and 1 skipped locally (PostgreSQL-only audit trigger test); all pass in CI on PostgreSQL |
| Failures | 0 |
| System tests (browser, 16 Nov 2026) | **33 of 33 passed**, all 20 functional requirements covered end to end ([SYSTEM_TEST_REPORT.md](SYSTEM_TEST_REPORT.md)) |
| RTM status | 31 requirements: **27 A, 4 P, 0 N** |
| Statement coverage | 88% |
| Branch coverage | 68% |
| Bandit | 0 High, 0 Medium, 2 Low (both dispositioned below) |
| pip-audit | 9 advisories, all in Django 5.1.15 (see Section 5) |
| `check --deploy` (`DJANGO_DEBUG=0`) | No issues |

## 3. Results by module

| Module | Owner | Test files | Tests | Result |
|---|---|---|---|---|
| AuthModule (`accounts/`) | Arjav | `test_password_reset`, `test_profile`, `test_session` | 10 | Pass |
| AllocationModule (`allocation/`) | Arjun | `test_allocation`, `test_blocks_rooms`, `test_my_room`, `test_room_change`, `test_student_records` | 28 | Pass |
| Audit (`audit/`) | Arnav | `test_audit`, `test_retention` | 12 | Pass (trigger test in CI) |
| ComplaintModule (`complaints/`) | Arnav | `test_complaints`, `test_data_protection`, `test_status_workflow` | 38 | Pass |
| Core / security (`core/`) | All | `test_dashboards`, `test_health`, `test_security_settings`, `test_security_validation`, `test_seed_demo`, `test_smoke` | 17 | Pass |
| FeeModule (`fees/`) | Armaan | `test_fee_statements`, `test_fee_structures`, `test_no_card_fields`, `test_payments`, `test_reconciliation` | 37 | Pass |
| ReportingModule (`reports/`) | Arnav | `test_exports`, `test_reports` | 16 | Pass |
| **Total** | | 26 files | **158** | **Pass** |

## 4. Coverage

`coverage run --branch` over the application code (migrations and tests excluded).

| Module | Statements | Branches |
|---|---|---|
| accounts | 96% | 65% |
| allocation | 81% | 63% |
| audit | 98% | 100% |
| complaints | 97% | 100% |
| core | 88% | 72% |
| fees | 84% | 60% |
| reports | 99% | 88% |
| **Total** | **88%** | **68%** |

Main uncovered code: `allocation/management/commands/seed_scale.py` (the HMS-27 scale data script, run by hand, not by pytest), error branches in the allocation and fee views, and the live Razorpay path in `fees/gateway.py` (CI uses the mock gateway, D8).

## 5. Security validation

STP Section 5.1: TC-Sec-01 to TC-Sec-06 verify the SRS security requirements; TC-Sec-07 to TC-Sec-12 are the extra OWASP-based cases.

| Case | Method | Result |
|---|---|---|
| TC-Sec-01 Data protection (HMS-NF-003) | `complaints/tests/test_data_protection.py`: per-user filtering, photo download permissions, PII masking in every log handler | Pass |
| TC-Sec-02 TLS (HMS-SR-001) | `core/tests/test_security_settings.py` + `check --deploy`. No TLS scan (no staging host, D6) | Partial |
| TC-Sec-03 Password hashing (HMS-SR-002) | `test_password_is_hashed` (PBKDF2 prefix, no plaintext) | Pass |
| TC-Sec-04 Vertical escalation (HMS-SR-003, HMS-F-005) | Student / Technician / Admin 403 tests in every module; 403 logged to `django.request` | Pass |
| TC-Sec-05 Immutable audit (HMS-SR-004) | `audit/tests/test_audit.py`: update/delete blocked in the ORM and by a PostgreSQL trigger (CI) | Pass |
| TC-Sec-06 No card data (HMS-SR-005) | Schema scan of every model for card fields; payment hands off to the gateway | Pass |
| TC-Sec-07 Injection | Code review: no raw SQL, no `safe` filter / `mark_safe`; ORM parameterises queries, templates auto-escape. Bandit: no injection findings | Pass (method per D13) |
| TC-Sec-08 Session and CSRF | `test_post_without_csrf_token_is_rejected`; 20-minute expiry in `accounts/tests/test_session.py` | Pass |
| TC-Sec-09 File upload | Bad extension, renamed script, wrong type, over 5 MB all rejected; randomised names; no public media URL | Pass |
| TC-Sec-10 Payment webhook | Bad signature, replay, amount mismatch, missing order id all rejected | Pass |
| TC-Sec-11 Dependencies / static analysis | Bandit 1.9.4 and pip-audit 2.10.1 | Findings, see below |
| TC-Sec-12 Brute force / OTP | Not built (D14) | Not executed |

**Bandit findings (both Low, accepted):**
- B105 `core/management/commands/seed_demo.py`: the demo password `Hostel@Demo2026` is hard-coded on purpose for synthetic demo accounts only (STP 6.3). It is never used for real users.
- B406 `fees/views.py`: `xml.sax.saxutils.escape` is used to *escape* text for the PDF receipt, not to parse XML. False positive.

**pip-audit findings (open, residual risk):** Django 5.1.15 has 9 published advisories (PYSEC-2026-198, -199, -201, -2090, -2091, -2092, -3717, -4035). Fixes exist only in Django 5.2.15+ / 6.0.6+, as the 5.1 series is out of support. Disposition: not fixed before freeze because a framework upgrade would need a full regression cycle. The recommended next step after the demo is moving `requirements.txt` to the Django 5.2 LTS line and re-running this suite. No other dependency has known advisories.

## 6. Performance and scale

| Case | Result |
|---|---|
| TC-Perf-01 (HMS-NF-001) | 200-user Locust run on SQLite + Django dev server: p95 6.2 s, 7.3% failures from SQLite write locking at login. **Target not met in this environment** (D9). Report: [perf/locust_report.html](perf/locust_report.html) |
| TC-Scale-01 (HMS-NF-006) | 5,000 students / 2,000 rooms seeded with `seed_scale`; room list, student list and reports pages respond in 4-7 ms with 25-row pagination. Pass. [perf/scale_results.md](perf/scale_results.md) |

## 7. Test cases updated for sprint changes

Changes to the STP v1.0 test cases made during the sprints:

- **Executed with different tools than planned.** Unit, integration and security cases run with pytest + Django test client instead of Postman and ZAP/testssl; the planned Selenium system suite is a Playwright browser run with 33 cases (D13). Detailed cases are in [UNIT_TEST_REPORT.md](UNIT_TEST_REPORT.md) (UT_nn / IT_nn, one per automated test) and [SYSTEM_TEST_REPORT.md](SYSTEM_TEST_REPORT.md) (ST_nn, in the course test-case template), rather than a separate `/docs/test-cases` folder.
- **Added for sprint changes:** room-change queue and approval into a full room (HMS-25); webhook replay, amount mismatch and null order id (HMS-28); receipt access by other students (HMS-29); reconciliation with gateway outage (HMS-30); complaint photo access and PII masking in Django's own loggers (HMS-34); archive/restore round trip (HMS-35); Technician 403 on the admin dashboard (#50).
- **Added at freeze (HMS-36):** `core/tests/test_security_validation.py`: CSRF rejection (TC-Sec-08) and "403 is logged" (AC-F-005), which had no automated case.
- **Changed scope:** TC-Auth-01 tests login only, since accounts are created by the Admin, not by self-registration (D10). TC-Sec-12 is not executed (D14). TC-Ops-01 and TC-Ops-02 stay partial, as planned in STP Section 4.

## 8. Defects found and fixed

| Defect | Found by | Fix |
|---|---|---|
| Technician could open the Admin/Warden dashboard | Review of RBAC | PR #50, regression test `test_technician_cannot_access_admin_dashboard` |
| `SELECT ... FOR UPDATE` on a nullable join failed on PostgreSQL | Running on PostgreSQL | Commit `a0bf9a3` (`allocation/services.py`) |
| Two fee migrations both numbered `0003` after parallel PRs | Merge of HMS-26 (#67) | Renumbered to `0005` on top of `0004_receipt` |
| `cp .env.example .env` left `PAYMENT_GATEWAY` empty, so "Pay now" and reconciliation raised `Unsupported PAYMENT_GATEWAY` under Docker Compose | HMS-36 run-instruction check | `.env.example` now sets `PAYMENT_GATEWAY=mock` and a webhook secret (HMS-36) |

| Zero fee amount, when the browser's `min` check is bypassed, shows the raw database constraint name instead of a readable message (DEF-ST-01, Severity 4) | System test ST_24 | Open, deferred to [MAINTENANCE_PLAN.md](MAINTENANCE_PLAN.md) |

No Severity 1 or 2 defects are open in project code.

## 9. Exit criteria (STP 5.5.2)

| Criterion | Status |
|---|---|
| 100% of planned cases executed, >= 95% passing | Not fully met: 33 of 37 anchor cases executed in full (TC-Sec-02 and TC-Ops-02 partial; TC-Sec-12 and TC-UX-01 not executed). Of the 33, 31 passed (TC-Perf-01 target missed, TC-Sec-11 findings open), 94%. All 158 automated tests and all 33 system tests pass |
| No open Severity 1/2 defects | Met for project code; Django advisories open as residual risk (Section 5) |
| High-priority FRs and all five SRs pass | All FRs pass; HMS-SR-001 partial (no TLS scan) |
| Branch coverage >= 70% overall, >= 80% Allocation and Fee | Not met: 68% overall, Allocation 63%, Fee 60% |
| SonarQube gate | Not applicable (no SonarQube, D1); flake8 and Bandit used instead |
| HMS-NF-001 met; HMS-NF-005 audit clean | Not met / not recorded (D9; NF-005 partial) |
| Every RTM row A, or N/P with justification | Met |
| UAT walkthrough signed off | Pending: walkthrough happens at the final demo |

## 10. Residual risks and known limitations

1. Django 5.1.15 is out of support and has open advisories (upgrade to 5.2 LTS).
2. Performance target unproven on PostgreSQL behind Gunicorn; only the SQLite dev-server run exists.
3. No login or OTP rate limiting (TC-Sec-12).
4. Accessibility audit (TC-UX-01) not recorded.
5. Branch coverage below the plan's targets in AllocationModule and FeeModule.

## 11. How to reproduce

```bash
pytest                                   # full suite
pip install coverage
coverage run --branch --source=accounts,allocation,audit,complaints,core,fees,reports \
  --omit="*/migrations/*,*/tests/*" -m pytest && coverage report
pip install bandit pip-audit             # in a separate venv
bandit -r accounts allocation audit complaints config core fees reports -x "*/tests/*,*/migrations/*"
pip-audit -r requirements.txt
DJANGO_DEBUG=0 DJANGO_SECRET_KEY=<50+ random chars> DJANGO_ALLOWED_HOSTS=hms.example python manage.py check --deploy
pip install playwright && playwright install chromium     # once, for the system tests
python docs/test-evidence/system/run_system_tests.py --server-python .venv/Scripts/python.exe
```
