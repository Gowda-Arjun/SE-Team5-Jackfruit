# Arjun: Repo Owner + AllocationModule (complete instructions)

Read `00_TEAM_WORKFLOW_read_first.md` first. It covers install, cloning, the per-issue git cycle and conflicts.

**Your jobs:**
1. Repo administration (settings, Project board, branch protection, release).
2. **Review and merge every PR** (the course grades this).
3. Your own issues: **Sprint 1** HMS-01, 09, 10, 11, 12, 13 (21 points); **Sprint 2** HMS-25, 26, 27 (10 points).

Arnav will send you **`HMS-01_Arjun_project-setup.zip`**. Keep it handy.

---

## PART A: Day 1 morning setup (do these in order, ~40 min total)

### A1. Add Arjav as a collaborator (2 min)
Repo → **Settings** → **Collaborators** → **Add people** → `arjav188` → Add. Tell Arjav to accept the email invite.
Also check that `Arnav060706` and `armaanyt07-jpg` are listed.

### A2. Allow GitHub Actions (2 min)
Repo → **Settings** → **Actions** → **General**:
- *Actions permissions*: **Allow all actions and reusable workflows**
- *Workflow permissions*: **Read and write permissions** → **Save**

### A3. Create the Project board (5 min)
GitHub only links a Project to repos of the same owner, so the Project must be on **your** account.
1. Your profile picture (top right) → **Your projects** → **New project** → **Table** → name it exactly **`HMS - Team 5 Backlog`** → **Create project**.
2. In the project: **⋯** (top right) → **Settings** → **Manage access** → invite **`Arnav060706`** → role **Admin**. Add `arjav188` and `armaanyt07-jpg` as **Write** too, so they can move their cards.
3. Go to the repo → **Projects** tab → **Link a project** → select **HMS - Team 5 Backlog**.

### A4. Tell Arnav: "Project created, you're Admin, go."
Arnav runs the script that creates the labels, the Sprint 1 / Sprint 2 milestones, all 37 issues with story points and assignees, and fills your Project.
**Wait for him to say "backlog is up"** before doing A5. Then check that issue **#1 is `[HMS-01] Project setup…`**.

### A5. Commit HMS-01 (your setup PR, issue #1) (~10 min)
```powershell
cd $HOME\Documents
git clone https://github.com/Gowda-Arjun/SE-Team5-Jackfruit.git
cd SE-Team5-Jackfruit
git checkout -b hms-01-project-setup
```
Unzip **`HMS-01_Arjun_project-setup.zip`** directly into this folder (choose **Replace** for `README.md`). You should now see `manage.py`, `config\`, `accounts\`, `allocation\` and so on next to the PDFs.

Check it runs:
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
pytest
flake8
```
`pytest` should show **6 passed**. Then commit only the setup files:
```powershell
git add manage.py config core accounts allocation fees complaints reports audit templates requirements.txt Dockerfile docker-compose.yml .env.example .gitignore .flake8 pytest.ini README.md
git status
git commit -m "HMS-01: Django project skeleton, one app per module, PostgreSQL via Docker Compose"
git push -u origin hms-01-project-setup
```
On GitHub: **Compare & pull request** → title `[HMS-01] Project setup` → description `Closes #1` → **Create pull request**.
(No CI runs yet, because the workflow arrives in Arnav's HMS-02. That's expected.)
Ask **Arnav to approve it** (Files changed → Review changes → Approve). Then click **Merge pull request** → **Confirm**, and **Delete branch**.

### A6. Merge Arnav's HMS-02 (CI) PR
Arnav opens `[HMS-02] CI with GitHub Actions + backlog docs`. This is the first time CI runs. Wait for the green ticks, then review and merge (see Part B).
Check the **Actions** tab: the workflow **CI** should show a green run.

### A7. Protect `main` (3 min, only after A6 is merged and CI has run once)
Repo → **Settings** → **Branches** → **Add branch protection rule** (or **Add classic branch protection rule**):
- Branch name pattern: `main`
- ☑ **Require a pull request before merging** → ☑ Require approvals: **1**
- ☑ **Require status checks to pass before merging** → search and add **`test`** and **`linked-issue`**
- ☑ **Do not allow bypassing the above settings** (optional)
- **Create**

### A8. Project board automation (Arnav may already have done this, so check)
Project → **⋯** → **Workflows**: turn on **Item added to project** (→ Todo), **Item closed** (→ Done), **Pull request merged** (→ Done) and **Auto-add to project** (filter `is:issue,pr`).

Now tell everyone: **"main is ready, pull and start Sprint 1."**

---

## PART B: How to review and merge a PR (you do this ~30 times)

1. Open the PR. At the bottom, the checks **`test`** and **`linked-issue`** must be ✅. If one is ❌, comment "CI failing, please fix" and stop.
2. **Is it the right person?** The PR author must be the issue's assignee.
3. **Files changed** tab: skim it. Does it stay in that person's module? No `.venv`, `db.sqlite3`, `__pycache__` or `.env` files? Does it have tests?
4. **Review changes** → **Approve** (optional comment like "Looks good, tested locally") → **Submit review**.
5. **Merge pull request** → **Confirm merge** → **Delete branch**.
6. If it says **"This branch has conflicts"**, ask the author to merge `main` into their branch (Section 5 of the shared guide). Don't resolve other people's conflicts yourself.
7. **Your own PRs:** ask **Arnav** to approve. You can't approve your own.

Optional local test of a PR before merging:
```powershell
git fetch origin
git checkout hms-11-allocate-room
pytest
git checkout main
```

**Merge order on Day 1** (so nothing breaks): HMS-01 → HMS-02 → HMS-18 (Arnav's audit log, needed by your allocation) → everything else as it comes in.

---

## PART C: Your Sprint 1 issues (Day 1 afternoon)

Follow the cycle in Section 4 of the shared guide for each. Prepend the **AI prompt header** (Section 7 of the shared guide) to each prompt below. Stick to the model and field names in Section 6 of the shared guide exactly, because Arnav's reports and seed data use them.

### C1. HMS-09 (#9): Blocks / floors / rooms and capacity (3 SP). Branch `hms-09-blocks-rooms`
> In the `allocation` app create models `Block(name unique, gender_policy choices "M"/"F")` and `Room(block FK PROTECT, floor int, number, room_type choices "SINGLE"/"SHARED", capacity positive int, occupancy positive int default 0, is_active bool default True)` with `UniqueConstraint(block, number)` and `CheckConstraint occupancy >= 0 and occupancy <= capacity`. Add Warden/Admin pages: block list/create/edit and room list/create/edit/deactivate, showing per-block totals of beds, occupied and free beds (availability counts). URL names `allocation:room_list` and friends. Register both in Django admin. Tests: create/edit room; duplicate room number in the same block rejected; capacity < occupancy rejected by the DB constraint; student gets 403 on these pages. (HMS-F-014, TC-Alloc-05)

PR description: `Closes #9`.

### C2. HMS-10 (#10): Student records CRUD (3 SP). Branch `hms-10-student-records`
> Add Warden/Admin pages to list (search by name/roll number, paginated 25), create, edit and deactivate students. Creating a student creates `accounts.User(role=STUDENT, username=roll number, email, roll_number)` plus `accounts.StudentProfile(full_name, gender, phone, address, guardian_name, guardian_phone, emergency_contact)` in one transaction and sets an unusable or temporary password. **Deactivate** sets `user.is_active=False`; never delete. Log create/edit/deactivate with `write_audit`. URL name `allocation:student_list`. Tests: create appears in list; edit persists; deactivate hides the student from active list and blocks login; student role gets 403. (HMS-F-011, TC-Alloc-02)

### C3. HMS-11 + HMS-12 (#11, #12): Allocate / reallocate and prevent over-allocation (5 + 3 SP). Branch `hms-11-allocate-room`
One PR, description with both `Closes #11` and `Closes #12`.
> Create `Allocation(student FK User PROTECT, room FK Room PROTECT, start_date default today, end_date null, status "ACTIVE"/"ENDED")` with a partial `UniqueConstraint(fields=["student"], condition=Q(status="ACTIVE"))`. In `allocation/services.py` write `allocate_room(student, room, actor)`: inside `transaction.atomic()`, lock the room with `Room.objects.select_for_update().get(pk=room.pk)`. Raise `RoomInactive`, `GenderPolicyMismatch` (block.gender_policy != student.profile.gender), `RoomFull` (occupancy >= capacity). If the student already has an ACTIVE allocation it is a **reallocation**: end the old one (status ENDED, end_date today, old room occupancy -1) and create the new one in the same transaction. Increment occupancy. Call `write_audit(actor, "ROOM_ALLOCATED", allocation, details={...})` on success and `write_audit(..., outcome="DENIED")` when rejected, before raising. Add a Warden/Admin allocation form (choose student + room, only active rooms with free beds listed) at URL name `allocation:allocate`, showing clear messages: "This room has no free beds. Choose another room." / "This block is not available for this student." Tests: boundaries N-1 / N / N+1 occupancy; gender mismatch; inactive room; reallocation moves occupancy; second ACTIVE allocation impossible; audit rows written. (HMS-F-012, HMS-F-015, TC-Alloc-03, TC-Alloc-06)

### C4. HMS-13 (#13): Student views own room and roommates (2 SP). Branch `hms-13-my-room`
> Student-only page at URL name `allocation:my_room` showing block, floor, room number, room type and the names of other students with an ACTIVE allocation in the same room. Students see only their own room. If there's no allocation, show "You have not been allocated a room yet." Tests: correct room and roommates; another student's data never shown; admin gets 403. (HMS-F-010, TC-Alloc-01)

### C5. Update the RTM later
After HMS-36 (Arnav) adds `docs/RTM.md`, set your rows (F-010 to F-015) to **A** in any later PR of yours.

### C6. Close Sprint 1 (Day 1 night, after Arnav's video PR HMS-20 is merged)
Repo → **Issues** → **Milestones** → **Sprint 1**. Any open issue that won't be finished: open it → right sidebar **Milestone** → change to **Sprint 2**. Then click **Close** on the Sprint 1 milestone.

---

## PART D: Your Sprint 2 issues (Day 2)

### D1. HMS-25 (#25): Room change request (5 SP). Branch `hms-25-room-change`
> Create `RoomChangeRequest(student FK User, current_room FK Room, preferred_room FK Room null, reason text, status "PENDING"/"APPROVED"/"REJECTED", created_at, decided_by FK User null, decided_at null)`. Student page `allocation:room_change_request` to submit one (only one PENDING at a time; needs an ACTIVE allocation). Warden/Admin queue `allocation:room_change_queue` listing PENDING requests with Approve/Reject buttons. Approve calls `allocate_room(student, preferred_room, actor)` in the same transaction and sets APPROVED, decided_by and decided_at; if `allocate_room` raises, the request stays PENDING and the error is shown. Reject sets REJECTED. Only PENDING→APPROVED/REJECTED are allowed. Audit every decision. Tests: submit, duplicate pending refused, approve moves the student, approve into a full room fails cleanly, reject, student sees status. (HMS-F-013, TC-Alloc-04)

### D2. HMS-26 (#26): Performance (3 SP). Branch `hms-26-performance`
1. Add `db_index=True` / indexes on columns used in filters (status, due dates, `Allocation(status)`); use `select_related` in list views; paginate lists (25 per page).
2. `pip install locust` (dev tool only, **don't** add it to `requirements.txt`). Create `perf/locustfile.py`: users log in as `student01` (after `seed_demo`) and load the dashboard, my-room and complaints pages.
3. Run `python manage.py seed_demo`, then `python manage.py runserver`, and in another terminal:
   ```powershell
   locust -f perf/locustfile.py --host http://127.0.0.1:8000 --users 200 --spawn-rate 20 --run-time 2m --headless --html docs/perf/locust_report.html
   ```
4. Commit `perf/locustfile.py` and `docs/perf/locust_report.html`. In the PR, write the p95 figure. If it's above 2 s on a laptop dev server, say so; it goes in DEVIATIONS as "indicative only, dev server". (HMS-NF-001, TC-Perf-01)

### D3. HMS-27 (#27): Scale test (2 SP). Branch `hms-27-scale-test`
> Management command `python manage.py seed_scale` (in `allocation/management/commands/`) that bulk-creates 5,000 students with profiles and 2,000 rooms across 20 blocks using `bulk_create`, tagged so it can be re-run safely. Then time the room list, student list and reports pages (Django debug toolbar or `time` in the browser network tab) and note the timings in `docs/perf/scale_results.md`. (HMS-NF-006, TC-Scale-01)

---

## PART E: Freeze (Day 2 night, after Arnav's HMS-36 and HMS-37 are merged)

1. Check the **Actions** tab: the latest run on `main` is green.
2. Repo → **Releases** → **Draft a new release** → **Choose a tag** → type `v1.0` → **Create new tag on publish** → target `main` → title `HMS v1.0: final submission` → paste the summary from `docs/SPRINT_2_REVIEW.md` → **Publish release**.
3. **Milestones** → close **Sprint 2**.
4. Tell the team: **"Frozen. No more merges."** (Development cycle frozen, Deliverable 3d.)
