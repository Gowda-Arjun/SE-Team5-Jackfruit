# Deviations from SRS v1.0, SAD v1.0 and Test Plan v1.0

Deliverables Part-2 (2i) requires deviations to be documented and explained at the final demo.

| # | Document / section | What the document says | What we did | Why |
|---|---|---|---|---|
| D1 | SAD 3.6, STP 6 (tools) | CI/CD with Jenkins (+ SonarQube stage) | GitHub Actions (lint, migration check, tests on PostgreSQL 15) | Course Deliverables Part-2 (2b) requires GitHub Actions; no Jenkins server needed |
| D2 | SAD 1.2, 4.6; STP 7 | Three sprints (optional REST API / Technician role in Sprint 3) | Two sprints (19-23 Oct, 26-30 Oct) | Course defines exactly two sprints. REST API and Technician sub-role are out of scope unless time permits |
| D3 | Sprint 1 dates | Sprint 1: 19-23 Oct | Sprint 1 completed 28 Oct, Sprint 2 by 30 Oct | Team started late; scope unchanged |
| D4 | SAD ADR-03 | PostgreSQL in every environment incl. local dev | PostgreSQL in CI and Docker Compose; SQLite fallback for quick local runs when `POSTGRES_DB` is unset | Lets every member run the app without Docker. CI still enforces PostgreSQL behaviour |
| D5 | SAD 3.6 | Python 3.11 | Python 3.12 | Current stable version on team machines; no API differences for Django 5.1 |
| D6 | SAD 3.4 (Nginx/Gunicorn) | Staging VM behind Nginx + Gunicorn with TLS | Demo runs on Django dev server / Docker Compose | No staging VM within the timeline; HTTPS settings covered by HMS-SR-001 settings and `check --deploy` |

<!-- Add a row whenever your PR differs from what the SRS/SAD/STP says. -->
