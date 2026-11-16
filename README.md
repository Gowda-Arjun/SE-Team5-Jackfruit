# Hostel Management System (HMS) - Team 5

SE Jackfruit mini-project (UE24CS341A). Django 5 + PostgreSQL 15 + Bootstrap 5.

| Member | SRN | Module |
|---|---|---|
| Arjav Chandranath | PES2UG24CS080 | AuthModule (`accounts/`) |
| Arjun Mohan Gowda | PES2UG24CS082 | AllocationModule (`allocation/`) - repo owner |
| Armaan Ali | PES2UG24CS083 | FeeModule (`fees/`) |
| Arnav Sharath Hanchanur | PES2UG24CS084 | Complaints, Reports, Audit (`complaints/`, `reports/`, `audit/`) - Test Lead |

## Documentation

| Document | Where |
|---|---|
| SRS, SAD, Test Plan (v1.0) | PDFs in the repo root |
| Backlog and sprint plan | [docs/backlog/BACKLOG.md](docs/backlog/BACKLOG.md) (also the GitHub Project board) |
| Deviations from SRS / SAD / Test Plan | [docs/DEVIATIONS.md](docs/DEVIATIONS.md) |
| Requirements Traceability Matrix (final) | [docs/RTM.md](docs/RTM.md) |
| Test Summary Report (results, coverage, security, exit criteria) | [docs/TEST_REPORT.md](docs/TEST_REPORT.md) |
| Unit Test Report (unit and integration cases, code and branch coverage) | [docs/UNIT_TEST_REPORT.md](docs/UNIT_TEST_REPORT.md) |
| System Test Report (end-to-end browser test cases ST_01-ST_33) | [docs/SYSTEM_TEST_REPORT.md](docs/SYSTEM_TEST_REPORT.md) |
| Maintenance Plan | [docs/MAINTENANCE_PLAN.md](docs/MAINTENANCE_PLAN.md) |
| Performance and scale results | [docs/perf/](docs/perf/) |
| Health check and restart policy | [docs/uptime.md](docs/uptime.md) |
| Team guides | [docs/guides/](docs/guides/) |

## What it does

| Role | Features |
|---|---|
| Student | Log in, update profile, reset password by email OTP, view room and roommates, request a room change, view fee statement, pay online (sandbox) and download a PDF receipt, raise complaints with a photo and track their status |
| Warden / Admin | Manage blocks, rooms and student records; allocate and reallocate rooms; approve or reject room changes; set fee structures; reconcile payments and list defaulters; update complaint status; occupancy / vacancy / fee-collection reports with CSV and PDF export; read-only audit log |
| Technician | See and update only the complaints assigned to them |

## Run locally (quick, SQLite)

Needs Python 3.12.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo      # demo accounts, blocks/rooms and fee structures (safe to re-run)
python manage.py runserver
```

Open http://127.0.0.1:8000 and log in with a demo account. All demo accounts use the password `Hostel@Demo2026` (synthetic data only):

| Username | Role |
|---|---|
| `admin` | Admin (can also open http://127.0.0.1:8000/admin/) |
| `warden` | Warden |
| `student01` ... `student10` | Students (01-05 male, 06-10 female) |

Without `.env`, the app uses SQLite, `DEBUG=1`, the console email backend (OTP emails are printed in the terminal) and the mock payment gateway.

## Run with PostgreSQL (same as CI)

```bash
cp .env.example .env            # defaults work as-is; change DJANGO_SECRET_KEY for anything shared
docker compose up --build       # runs migrations, then serves on http://localhost:8000
docker compose exec web python manage.py seed_demo
```

Payments use the offline mock gateway (`PAYMENT_GATEWAY=mock`). For Razorpay test mode, set `PAYMENT_GATEWAY=razorpay` and the `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` test keys in `.env`.

Optional data for the scale and performance runs: `python manage.py seed_scale` (5,000 students, 2,000 rooms) and the Locust file in [perf/locustfile.py](perf/locustfile.py).

## Tests and lint

```bash
pytest                                    # full suite (the audit trigger test needs PostgreSQL and runs in CI)
flake8
python manage.py makemigrations --check --dry-run
```

CI (GitHub Actions) runs all three against PostgreSQL 15 on every pull request. Results, coverage and security scans: [docs/TEST_REPORT.md](docs/TEST_REPORT.md).

End-to-end system tests run in a browser against a throw-away copy of the app (needs `pip install playwright && playwright install chromium` once): `python docs/test-evidence/system/run_system_tests.py --server-python .venv/Scripts/python.exe`. See [docs/SYSTEM_TEST_REPORT.md](docs/SYSTEM_TEST_REPORT.md).

## Development freeze

Development is frozen after HMS-36 (final documentation) and HMS-37 (final demo video) are merged, at tag `v1.0`. After the freeze, only fixes for defects found during evaluation go into `main`, each through a PR.

## How we work

1. Pick your issue on the Project board, move it to **In Progress**.
2. `git checkout main && git pull`, then `git checkout -b hms-11-allocate-room`.
3. Only edit your own app folder where possible (all apps are already wired into `config/urls.py` and `INSTALLED_APPS`).
4. Push and open a PR with `Closes #<issue>` in the description. CI must be green.
5. Arjun (repo owner) reviews and merges. The issue closes automatically and moves to **Done**.
