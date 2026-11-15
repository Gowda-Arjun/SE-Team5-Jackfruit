# Sprint 1 Review: Team 5 HMS

**Window:** 19-23 Oct 2026 (planned) · completed 28 Oct 2026 (see [DEVIATIONS](DEVIATIONS.md) D3)
**Demo video:** [`docs/videos/final_demo.mp4`](videos/final_demo.mp4), Part 1 (0:00-1:20). One combined video covers both sprints (DEVIATIONS D7).

## Goal

A working base product: login with roles, hostel blocks and rooms, room allocation within capacity, fee structure and statement, complaints, the audit log and CI.

## Completed items

| ID | Item | Owner | SP | PR |
|---|---|---|---|---|
| HMS-01 | Project setup: Django, one app per module, PostgreSQL | Arjun | 5 | #38 |
| HMS-02 | GitHub Actions CI, PR template, CODEOWNERS | Arnav | 3 | #39 |
| HMS-03 | `seed_demo` synthetic data command | Arnav | 2 | #44 |
| HMS-04 | Register / log in with role | Arjav | 5 | #45 |
| HMS-05 | Salted password hashing | Arjav | 1 | #45 |
| HMS-06 | Role-based access control | Arjav | 3 | #50 |
| HMS-07 | 20-minute session timeout | Arjav | 2 | #48 |
| HMS-08 | Student profile update | Arjav | 2 | #49 |
| HMS-09 | Blocks, floors, rooms and capacity | Arjun | 3 | #53 |
| HMS-10 | Admin student records | Arjun | 3 | #54 |
| HMS-11 | Allocate / reallocate room | Arjun | 5 | #55 |
| HMS-12 | Prevent over-allocation | Arjun | 3 | #55 |
| HMS-13 | Student views room and roommates | Arjun | 2 | #56 |
| HMS-14 | Fee structure per term and room type | Armaan | 3 | #42 |
| HMS-15 | Itemised fee statement | Armaan | 3 | #46 |
| HMS-16 | Dashboards with live data | Armaan | 3 | #47 |
| HMS-17 | No card data stored (schema check) | Armaan | 1 | #43 |
| HMS-18 | Append-only audit log | Arnav | 3 | #40 |
| HMS-19 | Raise complaint with photo | Arnav | 3 | #41 |
| HMS-20 | Sprint 1 demo video, merged into HMS-37 | Arnav | 0 | #51 |

**Velocity:** 55 of 55 story points (Arjav 13, Arjun 21, Armaan 10, Arnav 11).

## What the demo shows (video Part 1)

Login as Student and Admin with role-based dashboards; blocks and rooms; allocating a student and the "no free beds" refusal at capacity; fee structure and the student's fee statement; a student raising a complaint with a photo; a student getting 403 on `/reports/`.

## Review and retrospective

- **Went well:** CI ran lint, the migration check and the tests on PostgreSQL for every PR; each member worked in their own app folder; every PR linked its backlog issue.
- **Blockers:** the team started late, so the sprint closed on 28 Oct instead of 23 Oct (D3). Reports and dashboards depended on the allocation and fee models being merged first.
- **Changed for Sprint 2:** the Sprint 1 video was folded into one final video (D7) rather than recording an incomplete build.
