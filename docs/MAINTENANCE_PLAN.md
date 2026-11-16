# Product Maintenance Plan: Team 5 HMS

Course deliverable *System Validation: validation report + maintenance plan* (Jackfruit guidelines) and STP v1.0 Section 8 "Maintenance plan input". It turns the known defects, residual risks and deferred items from testing into a maintained backlog, and says how HMS is kept running, patched and released after the v1.0 freeze.

Inputs: [TEST_REPORT.md](TEST_REPORT.md) (residual risks, Section 10), [UNIT_TEST_REPORT.md](UNIT_TEST_REPORT.md) (coverage gaps), [SYSTEM_TEST_REPORT.md](SYSTEM_TEST_REPORT.md) (defects DEF-ST-01, OBS-01), [DEVIATIONS.md](DEVIATIONS.md), [RTM.md](RTM.md) (4 requirements at status P).

## 1. Scope and ownership

The maintained product is the `main` branch from tag `v1.0` onward: the seven Django apps, the Docker Compose deployment, the CI workflow and the documentation in `docs/`.

| Area | Owner (maintainer) | Backup |
|---|---|---|
| AuthModule (`accounts/`), security settings, health check | Arjav | Arnav |
| AllocationModule (`allocation/`), deployment (`Dockerfile`, `docker-compose.yml`), performance | Arjun (repo owner) | Armaan |
| FeeModule (`fees/`), payment gateway adapter | Armaan | Arjun |
| ComplaintModule, ReportingModule, Audit (`complaints/`, `reports/`, `audit/`), CI, test suites, RTM | Arnav (Test Lead) | Arjav |

The repo owner (Arjun) approves and merges every change, as during the sprints.

## 2. Maintenance backlog

Each item becomes a GitHub issue with the `maintenance` label and its severity or priority. Severity bands and response times are the ones in STP Section 14.3.

### 2.1 Corrective (defects)

| ID | Item | Severity | Owner | Fix |
|---|---|---|---|---|
| M-01 | DEF-ST-01: a zero or negative fee amount shows the raw database message *Constraint "fees_structure_amount_positive" is violated.* when the browser check is bypassed | 4 | Armaan | Add `clean_amount()` to `FeeStructureForm` ("Amount must be greater than zero."); extend `test_non_positive_amount_is_rejected` to assert the message |
| M-02 | OBS-01: after a room change into another room type, My fees labels the existing statement with the new room type but keeps the original amount | 4 | Armaan | Show the room type stored with the statement instead of the student's current room type |

### 2.2 Adaptive (environment and dependencies)

| ID | Item | Priority | Owner | Plan |
|---|---|---|---|---|
| M-03 | Django 5.1.15 is out of support and has 9 published advisories (pip-audit, TEST_REPORT Section 5) | High | Arjun | Move `requirements.txt` to Django 5.2 LTS; run CI, the system run and `check --deploy`; release as `v1.1.0` |
| M-04 | Razorpay API or test-key changes | Medium | Armaan | Keep the gateway behind `fees/gateway.py`; re-check signature format and ledger fields when Razorpay announces changes; CI stays on the mock gateway |
| M-05 | Python and PostgreSQL version updates | Low | Arjun | Bump the CI matrix first; upgrade `Dockerfile` and Compose images only after CI is green |

### 2.3 Preventive (risk reduction)

| ID | Item | Priority | Owner | Plan |
|---|---|---|---|---|
| M-06 | No login or OTP rate limiting (TC-Sec-12, D14) | High | Arjav | Throttle failed logins and OTP requests per account and IP; log the lock-outs; add tests for the threshold (BVA at N-1, N, N+1) |
| M-07 | Branch coverage below the STP targets: 68% overall, AllocationModule 63%, FeeModule 60% | Medium | Arjun, Armaan | View tests for the block pages, room-change approval errors, my-fees error messages and malformed webhooks (UNIT_TEST_REPORT Section 3.3); target 70% / 80% |
| M-08 | 12 functional requirements have fewer than the guideline's 8 test cases across all levels | Medium | Module owners | Add negative and boundary cases per requirement (UNIT_TEST_REPORT Section 5) |
| M-09 | HMS-NF-001 (p95 <= 2 s at 200 users) unproven outside SQLite + dev server | Medium | Arjun | Repeat the Locust run on PostgreSQL behind Gunicorn (Compose); record in `docs/perf/` |
| M-10 | HMS-SR-001 TLS not scanned (no staging host, D6) | Medium | Arjav | When a host exists: Nginx with TLS 1.2+, HTTP to HTTPS redirect, testssl.sh scan |
| M-11 | HMS-NF-005 accessibility audit (TC-UX-01) not recorded | Medium | Arjav | axe DevTools and keyboard-only pass at 360 / 768 / 1366 px; fix Severity 1-2 findings |
| M-12 | `/healthz/` does not check the database ([uptime.md](uptime.md)) | Low | Arjav | Add a `SELECT 1` to the health check so the uptime monitor also catches a dead database |
| M-13 | Dashboard fallback code for absent apps in `core/views.py` cannot run any more (uncovered branches) | Low | Arnav | Remove it, keeping behaviour covered by `core/tests/test_dashboards.py` |

### 2.4 Perfective (enhancements, only on request)

| ID | Item | Notes |
|---|---|---|
| M-14 | Optional REST API (SRS 3.3) | Same `role_required` checks at the API layer (HMS-SR-003) |
| M-15 | Technician screens instead of assignment in Django admin (D17) | |
| M-16 | Structured JSON logs once a log server exists (D18) | Keep `MaskPIIFilter` on every handler |

**Order of work:** M-03 and M-06 first (security), then M-01/M-02 (quick fixes), then M-07/M-08 (test debt), then the rest.

## 3. Change and release process

1. Every change starts as a GitHub issue (defect with severity, or maintenance item) and is done on a branch `fix-<issue>-<slug>` or `maint-<issue>-<slug>`.
2. The pull request must pass CI: flake8, `makemigrations --check`, and the full pytest suite on PostgreSQL 15. A defect fix includes a regression test that fails before the fix.
3. The module owner of the code being changed reviews it, and the repo owner merges. Nobody merges their own PR.
4. Before a release, the Test Lead runs the system test suite (`docs/test-evidence/system/run_system_tests.py`) and updates `results.json`, the RTM row for every affected requirement, and DEVIATIONS.md for any change against SRS/SAD.
5. Versions follow semantic versioning from `v1.0`: `v1.0.x` for defect fixes, `v1.x.0` for dependency upgrades or new behaviour. Each release gets a tag and a GitHub release note listing the issues it closes.
6. Database changes are only made through Django migrations. A migration that changes or removes data needs a tested reverse migration or a documented restore from backup.

## 4. Operations

| Task | Frequency | How | Owner |
|---|---|---|---|
| Health check | Every 5 minutes | External uptime monitor on `/healthz/`; Compose restarts containers (`restart: unless-stopped`) | Arjav |
| Database backup | Daily, keep 30 days | `docker compose exec db pg_dump -U hms hms \| gzip > backups/hms-<date>.sql.gz`, copied off the host | Arjun |
| Restore drill | Each semester | Restore the latest backup into a fresh Compose stack and run the smoke suite (login, allocate, pay, raise complaint, report) | Arjun |
| Audit log archive (HMS-NF-004) | Monthly | `python manage.py archive_audit` exports rows older than `AUDIT_RETENTION_DAYS` (3 years) to `.jsonl.gz`; archives are kept with the backups. Rows are never deleted from the append-only table (D12); `restore_audit` brings an archive back on request | Arnav |
| Dependency and static scans | Monthly and before each release | `pip-audit -r requirements.txt` and `bandit -r` (commands in TEST_REPORT Section 11); High or Critical findings become Severity 2 issues | Arnav |
| Secret rotation | Each semester, or at once if exposed | New `DJANGO_SECRET_KEY` (logs everyone out) and `PAYMENT_WEBHOOK_SECRET` (update the gateway dashboard at the same time); Razorpay keys from its dashboard | Arjun, Armaan |
| Fee structures for the new term | Before each term | Warden adds the term's fee structures; existing statements keep their amounts (HMS-F-022) | Warden (user) |
| Data clean-up at year end | Yearly | Deactivate (never delete) students who have left; their records stay for audit and fee history | Warden (user) |

## 5. Defect handling after release

- Anyone can report a defect as a GitHub issue with steps, expected and actual result, screenshot, and the affected requirement ID.
- The owning module's maintainer sets the severity (STP 14.3) within one working day.
- Severity 1 (e.g. RBAC bypass, wrong allocation, card data stored): fix within 1 working day; if needed, disable the affected feature until fixed. Severity 2: within 3 working days. Severity 3: next release. Severity 4: when convenient, listed in the release notes.
- A defect is closed only after the reporter (or the Test Lead) re-runs the case on the release that contains the fix.

## 6. Documentation upkeep

| Document | Updated when |
|---|---|
| `README.md` | Run instructions, environment variables or roles change |
| `docs/RTM.md` | A requirement's code, tests or status changes |
| `docs/DEVIATIONS.md` | Any change differs from SRS v1.0, SAD v1.0 or STP v1.0 |
| `docs/TEST_REPORT.md`, `docs/UNIT_TEST_REPORT.md`, `docs/SYSTEM_TEST_REPORT.md` | Each release (re-run coverage, pytest and the system run) |
| This plan | Each release: close finished items, add new ones |
