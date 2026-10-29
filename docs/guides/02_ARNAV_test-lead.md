# Arnav: Test Lead + Complaints / Reports / Audit (complete instructions)

Read `00_TEAM_WORKFLOW_read_first.md` first.

**Your jobs:**
1. Create the backlog (issues, milestones, Project fields).
2. Add CI (HMS-02).
3. **Approve Arjun's own PRs** (he can't approve his own).
4. Commit your already-built features: **Sprint 1** HMS-02, 18, 19, 03, 20 · **Sprint 2** HMS-31, 34, 32, 33, 35, 36, 37.
5. Record both demo videos and own the final RTM.

**Good news:** all your code is already written and tested. On real PostgreSQL every PR applied in order passes lint, the migration check and the tests. Each PR is ready to copy from:

```
Group Project\ARNAV_PRS\HMS-xx\files\          <- copy this folder's contents into the repo
Group Project\ARNAV_PRS\HMS-xx\*.txt           <- small snippets you paste into shared files (only some PRs)
```
**Never** copy the `hms\` folder wholesale. It contains everything at once, plus teammates' empty stub files.

Folder used below: `C:\Users\Arnav\Projects\PES\PES SEM-5\SE\Group Project` (call it **GP**).

---

## PART A: Day 1 morning setup

### A1. Delete the empty Project on your own account (1 min)
github.com → your profile → **Projects** → **HMS - Team 5 Backlog** (the one under *Arnav060706*) → **⋯** → **Settings** → bottom → **Delete this project**.

### A2. Wait for Arjun: "Project created, you're Admin"
Arjun creates **HMS - Team 5 Backlog** on *his* account, makes you Admin and links it to the repo.

### A3. Create the backlog (5–10 min). Use your **phone hotspot** (college Wi-Fi drops GitHub connections)
```powershell
cd "C:\Users\Arnav\Projects\PES\PES SEM-5\SE\Group Project\HMS-02_Arnav_ci-and-docs"
gh auth status
python docs/backlog/create_backlog.py --dry-run
python docs/backlog/create_backlog.py
```
- `gh auth status` must list `project` in the token scopes. If it doesn't, run `gh auth refresh -s project`.
- "network error, retrying…" lines are fine. If the run dies, run it again; nothing gets duplicated.
- If you see `Project "HMS - Team 5 Backlog" not found under Gowda-Arjun`, the title doesn't match exactly or Arjun hasn't made you Admin yet.
- `could not assign arjav188` means Arjav hasn't accepted his invite. Assign him later on each of his issues (right sidebar → Assignees).

**Check on GitHub:** 37 issues, **#1 = [HMS-01]**, **#37 = [HMS-37]**, two milestones, and the Project shows Story Points, Sprint and Priority.

### A4. Finish the board (5 min)
In Arjun's Project:
- **⋯ → Workflows**: turn on Item added → Todo, Item closed → Done, Pull request merged → Done, Auto-add (`is:issue,pr`).
- **New view** → **Board**, grouped by **Status**.
- **New view** → **Table** → Group by **Sprint** → show the **Story Points** field (column header ⋯ → *Sum*).
- **Take screenshots** of both views and the issue list. That's your Deliverable 1 evidence.

Tell everyone: **"Backlog is up. Arjun, go ahead with HMS-01."** Send Arjun the `HMS-01_Arjun_project-setup.zip` if you haven't already.

### A5. Approve Arjun's HMS-01 PR
Open it → **Files changed** → **Review changes** → **Approve** → **Submit review**. Arjun merges.

### A6. Clone the repo and set up (after HMS-01 is merged)
```powershell
cd "C:\Users\Arnav\Projects\PES\PES SEM-5\SE\Group Project"
git clone https://github.com/Gowda-Arjun/SE-Team5-Jackfruit.git
cd SE-Team5-Jackfruit
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```
All later commands run from this folder (**repo**) with `(.venv)` active.

---

## PART B: The recipe for each of your PRs

For PR **HMS-xx**, with branch name and `git add` paths taken from the tables below:

```powershell
git checkout main
git pull
pip install -r requirements.txt
git checkout -b <branch>
robocopy "..\ARNAV_PRS\HMS-xx\files" . /E
```
`robocopy` prints a summary; that's normal. Next, apply any snippet listed for that PR (see the tables). Then:

```powershell
python manage.py migrate
pytest
flake8
python manage.py makemigrations --check --dry-run
git status
git add <paths from the table>
git commit -m "<message from the table>"
git push -u origin <branch>
```
On GitHub: **Compare & pull request** → title `[HMS-xx] …` → description must include **`Closes #xx`** → **Create pull request** → wait for green ticks → Arjun merges.

`git status` should show **only** the paths in the table as changed. If anything else shows up, don't add it.

---

## PART C: Sprint 1 PRs (Day 1). Open them in this order

| # | Issue | Branch | Snippet | `git add` | Commit message |
|---|---|---|---|---|---|
| 1 | **HMS-02** (#2) CI + backlog docs | `hms-02-ci-and-docs` | – | `.github docs` | `HMS-02: GitHub Actions CI, PR checks, templates, backlog and team guides` |
| 2 | **HMS-18** (#18) audit log | `hms-18-audit-log` | – | `audit` | `HMS-18: append-only audit log with write_audit() and PostgreSQL trigger` |
| 3 | **HMS-19** (#19) raise complaint | `hms-19-raise-complaint` | – | `complaints` | `HMS-19: students raise complaints with ticket id and safe photo upload` |
| 4 | **HMS-03** (#3) seed data | `hms-03-seed-demo` | – | `core/management core/tests/test_seed_demo.py` | `HMS-03: seed_demo command with synthetic users, rooms and fees` |
| 5 | **HMS-20** (#20) Sprint 1 video | `hms-20-sprint1-video` | – | `docs/SPRINT_1_REVIEW.md docs/videos/sprint1_demo.mp4` | `HMS-20: Sprint 1 demo video and review` |

Notes:
- **HMS-02** is the first PR that runs CI. If `test` goes red, open Details and send me or the team the error. After it merges, Arjun turns on branch protection.
- **HMS-18 goes in as early as possible.** Arjun's `allocate_room` calls `write_audit`.
- Its `0002_immutable_trigger` migration only does anything on PostgreSQL (CI). Locally on SQLite it's skipped, which is expected.
- **HMS-03:** rooms and fees are seeded automatically once Arjun's and Armaan's models are merged. Before that, the command prints "skipped" for them.
- **HMS-20:** do it last (Part E).

---

## PART D: Sprint 2 PRs (Day 2). Open them in this order

| # | Issue | Branch | Snippet to apply before testing | `git add` | Commit message |
|---|---|---|---|---|---|
| 1 | **HMS-31** (#31) status workflow | `hms-31-complaint-status` | – | `complaints` | `HMS-31: complaint status workflow with history, audit and notification` |
| 2 | **HMS-34** (#34) data protection | `hms-34-data-protection` | Paste `ARNAV_PRS\HMS-34\PASTE_AT_END_OF_config_settings.py.txt` at the **end** of `config\settings.py` | `complaints core/log_filters.py config/settings.py` | `HMS-34: owner-only photo download and PII masking in logs` |
| 3 | **HMS-32** (#32) reports | `hms-32-reports` | – | `reports` | `HMS-32: occupancy, vacancy, fee-collection and defaulter reports` |
| 4 | **HMS-33** (#33) CSV/PDF export | `hms-33-report-export` | Add the line from `ARNAV_PRS\HMS-33\ADD_TO_requirements.txt.txt` (`reportlab>=4.2`) at the **end** of `requirements.txt`, then `pip install -r requirements.txt` | `reports requirements.txt` | `HMS-33: CSV and PDF export of reports (ReportLab)` |
| 5 | **HMS-35** (#35) audit retention | `hms-35-audit-retention` | Paste `ARNAV_PRS\HMS-35\PASTE_AT_END_OF_config_settings.py.txt` at the **end** of `config\settings.py` | `audit config/settings.py` | `HMS-35: 3-year audit retention with archive and restore commands` |
| 6 | **HMS-36** (#36) final docs | `hms-36-final-docs` | Append the rows in `ARNAV_PRS\HMS-36\ADD_ROWS_TO_docs_DEVIATIONS.md.txt` to the table in `docs\DEVIATIONS.md` (just above the `<!-- Add a row… -->` comment) | `docs/RTM.md docs/DEVIATIONS.md` | `HMS-36: final RTM and deviations` |
| 7 | **HMS-37** (#37) Sprint 2 video | `hms-37-sprint2-video` | – | `docs/SPRINT_2_REVIEW.md docs/videos/sprint2_demo.mp4` | `HMS-37: Sprint 2 demo video and final review` |

Notes:
- **Shared files** (`config\settings.py`, `requirements.txt`, `docs\DEVIATIONS.md`): **never overwrite them.** Only append the snippet, because teammates add their own lines too. If GitHub reports a conflict, follow Section 5 of the shared guide ("Accept Both").
- **HMS-32 / HMS-33 tests** skip automatically until Arjun's `allocation` and Armaan's `fees` models are merged. Once those are merged, the tests run for real. If they fail because a teammate named a field differently, change the names in the block at the top of `reports\services.py` (`ROOM_MODEL`, `PAYMENT_SUCCESS`, `PAYMENT_DATE_FIELD`, …) and push the fix on the same branch.
- **HMS-36:** before opening it, look at `docs\RTM.md` and set any rows that teammates have finished to **A** (ask them). It's fine to update RTM again in HMS-37.
- **Add links** for the complaint and report pages to the dashboards/nav. That's Armaan's HMS-16. Tell him the URL names: `complaints:my_complaints`, `complaints:create`, `complaints:queue`, `reports:index`.

---

## PART E: Demo videos

**Before recording:**
```powershell
git checkout main
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```
Record with **Win + Alt + R** (Xbox Game Bar) or OBS. Use a browser window at a normal size. Log in as the seeded `admin`, `warden` and `student01` (password at the top of `core/management/commands/seed_demo.py`).

**Sprint 1, about 60 seconds (`docs/videos/sprint1_demo.mp4`):**
1. Register a new student (Arjav's page) → log in → empty student dashboard.
2. Log out → log in as **admin** → blocks/rooms page → student list.
3. Allocate `student01` to a room → success. Try a full room → "no free beds" error.
4. Fee structure page.
5. Log in as **student01** → My room (with roommates) → fee statement → raise a complaint (with a photo) → it appears as Open.
6. As the student, open `/reports/` in the address bar → **403**.

**Sprint 2, about 2 minutes (`docs/videos/sprint2_demo.mp4`):** the Sprint 1 flow quickly, then:
1. OTP password reset.
2. Room change request → approved.
3. Pay fees through the sandbox → receipt PDF.
4. Warden moves a complaint Open → In Progress → Resolved; the student sees the timeline.
5. Reports: occupancy and defaulters → Export CSV and PDF.
6. Admin → Audit logs (read-only).

**Committing the video:** keep it under **25 MB** (use HandBrake's "Fast 720p30" if it's bigger). Create the folder `docs\videos\` and put the file there. Then fill in the review file you copied from `ARNAV_PRS\HMS-20\files` (or HMS-37): tick the items done and add the points. Then follow the Part B recipe with the paths from the tables. If the video is over 100 MB, upload it to YouTube (unlisted) or Google Drive and put the link in the review file and README instead.

---

## PART F: Reviewing others (when Arjun asks)
Approve Arjun's own PRs: open the PR → **Files changed** → **Review changes** → **Approve**. Check that CI is green and that only `allocation/` (and the expected shared lines) changed.

## PART G: Test Lead wrap-up (Day 2 night)
- `docs\RTM.md`: every row has a status; anything not **A** has a reason in the Status cell.
- `docs\DEVIATIONS.md`: every teammate has added their deviations. Ask in the group: "Anything you did differently from SRS/SAD/Test Plan?"
- Tell Arjun to tag `v1.0` and freeze.
