# Hostel Management System (HMS) - Team 5

SE Jackfruit mini-project (UE24CS341A). Django 5 + PostgreSQL 15 + Bootstrap 5.

| Member | SRN | Module |
|---|---|---|
| Arjav Chandranath | PES2UG24CS080 | AuthModule (`accounts/`) |
| Arjun Mohan Gowda | PES2UG24CS082 | AllocationModule (`allocation/`) - repo owner |
| Armaan Ali | PES2UG24CS083 | FeeModule (`fees/`) |
| Arnav Sharath Hanchanur | PES2UG24CS084 | Complaints, Reports, Audit (`complaints/`, `reports/`, `audit/`) - Test Lead |

Design documents: SRS, SAD and Test Plan PDFs in this repo. Backlog and sprint plan: [docs/backlog/BACKLOG.md](docs/backlog/BACKLOG.md). Deviations from those documents: [docs/DEVIATIONS.md](docs/DEVIATIONS.md).

## Run locally (quick, SQLite)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000. To give a user the Admin role, set **Role** on the user in http://127.0.0.1:8000/admin/.

## Run with PostgreSQL (same as CI)

```bash
cp .env.example .env
docker compose up --build
```

## Tests and lint

```bash
pytest
flake8
```

## How we work

1. Pick your issue on the Project board, move it to **In Progress**.
2. `git checkout main && git pull`, then `git checkout -b hms-11-allocate-room`.
3. Only edit your own app folder where possible (all apps are already wired into `config/urls.py` and `INSTALLED_APPS`).
4. Push and open a PR with `Closes #<issue>` in the description. CI must be green.
5. Arjun (repo owner) reviews and merges. The issue closes automatically and moves to **Done**.
