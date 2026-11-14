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
| D7 | Deliverables 2g/2h, 3b | Separate Sprint 1 demo video (HMS-20, 1 min) and Sprint 2 demo video (HMS-37, 2 min) | One combined final demo video (HMS-37, ~3 min) covering both sprints; HMS-20 closed as merged into HMS-37 and its story point moved to HMS-37 | Team decision: Sprint 1 finished late (D3), so a separate Sprint 1 recording would show an incomplete build days before the final one |
| D8 | HMS-NF-001 / TC-Perf-01 | 200-user Locust run p95 <= 2 s | The local SQLite/Django development-server run recorded a 6.2 s aggregate p95 and 7.3% failures under concurrent login load | SQLite serializes concurrent writes and is only the documented local fallback; CI and Docker Compose use PostgreSQL. The attached report is indicative of this development environment, not a production capacity result |

<!-- Add a row whenever your PR differs from what the SRS/SAD/STP says. -->
