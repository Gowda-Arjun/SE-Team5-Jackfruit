# Team 5 HMS: Shared Workflow (everyone reads this first)

**Repo:** https://github.com/Gowda-Arjun/SE-Team5-Jackfruit · **Repo owner:** Arjun (`Gowda-Arjun`), who reviews and merges every PR
**Today's starting point:** the repo has only `README.md` and the SRS/SAD/Test Plan PDFs. Everything else is added through the PRs described in these guides.

| Person | GitHub | Role (Test Plan 9.1) | Guide |
|---|---|---|---|
| Arjun Mohan Gowda | `Gowda-Arjun` | Repo owner, environment, AllocationModule, performance | `01_ARJUN_repo-owner.md` |
| Arnav Sharath Hanchanur | `Arnav060706` | Test Lead (CI, backlog/RTM, seed data, security), Complaints, Reports, Audit | `02_ARNAV_test-lead.md` |
| Arjav Chandranath | `arjav188` | AuthModule, accessibility | `03_ARJAV_auth.md` |
| Armaan Ali | `armaanyt07-jpg` | FeeModule, payment gateway | `04_ARMAAN_fees.md` |

---

## 1. Schedule

| When | What | Who |
|---|---|---|
| **Day 1 (Wed 28 Oct), morning** | Setup: collaborators, Actions, Project board, backlog issues, setup PR (HMS-01), CI PR (HMS-02) | Arjun + Arnav (others install tools meanwhile) |
| **Day 1, afternoon–evening** | **Sprint 1:** everyone builds and PRs their Sprint 1 issues; Arjun reviews and merges | Everyone |
| **Day 1, night** | Sprint 1 demo video (1 min), Sprint 1 review, close milestone | Arnav records, everyone checks |
| **Day 2 (Thu 29 Oct)** | **Sprint 2:** everyone builds and PRs their Sprint 2 issues | Everyone |
| **Day 2, night** | Sprint 2 video (2 min), final docs, RTM, tag `v1.0` (freeze) | Arnav + Arjun |
| Fri 30 Oct | Buffer only: fixes, re-record if needed | – |

**Hard rule:** nobody opens a PR or creates an issue until Arnav says "backlog is up". The issue numbers must match the backlog IDs (#1 = HMS-01 … #37 = HMS-37).

---

## 2. One-time install (everyone, ~15 min, do it before Day 1 starts)

1. **Python 3.12:** https://www.python.org/downloads/. During install, tick **"Add python.exe to PATH"**.
2. **Git:** https://git-scm.com/download/win (all defaults).
3. **VS Code** (or any editor).
4. Optional but handy: **GitHub CLI** https://cli.github.com, then run `gh auth login`.
5. Tell Git who you are (use the email of your GitHub account):
   ```powershell
   git config --global user.name "Your Name"
   ```
   ```powershell
   git config --global user.email "you@example.com"
   ```
6. **Accept the repo invite:** check your email or https://github.com/notifications. Arjav, you're not a collaborator yet, so Arjun is adding you.

---

## 3. Get the code (after HMS-01 is merged, ~Day 1 mid-morning)

```powershell
cd $HOME\Documents
git clone https://github.com/Gowda-Arjun/SE-Team5-Jackfruit.git
cd SE-Team5-Jackfruit
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Open http://127.0.0.1:8000. You should see the login page. Press **Ctrl+C** in the terminal to stop the server.

- If `.venv\Scripts\activate` says "running scripts is disabled", run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again.
- To make your superuser an Admin in the app: open http://127.0.0.1:8000/admin → Users → your user → **Role = Admin** → Save.
- Every new terminal: `cd` into the repo, then run `.venv\Scripts\activate` again.
- After pulling others' work, always run `pip install -r requirements.txt` and `python manage.py migrate`.
- Once HMS-03 is merged, `python manage.py seed_demo` creates demo accounts (admin, warden, student01–student10). The password is at the top of `core/management/commands/seed_demo.py`.

---

## 4. The cycle for EVERY issue (memorise this)

Example: Arjun working on issue **#9 (HMS-09)**.

**Step 1.** On the Project board, drag your card to **In Progress**.

**Step 2.** Start from the latest `main`:
```powershell
git checkout main
git pull
git checkout -b hms-09-blocks-rooms
```
Branch names are always `hms-<number>-<short-name>`.

**Step 3.** Write the code, **only inside your own app folder** where possible. Use the AI prompt from your guide, then read what it gives you before using it.

**Step 4.** Run the checks. All of them must pass:
```powershell
python manage.py makemigrations
python manage.py migrate
pytest
flake8
```

**Step 5.** Commit **only your files** (name them, never `git add .`):
```powershell
git status
git add allocation
git commit -m "HMS-09: blocks and rooms CRUD with availability counts"
git push -u origin hms-09-blocks-rooms
```

**Step 6.** Open the PR. Go to the repo on GitHub → yellow banner **"Compare & pull request"** → fill in the template. The description **must contain `Closes #9`** (your issue number); otherwise the `linked-issue` check fails. For several issues in one PR, write `Closes #4` and `Closes #5` on separate lines.

**Step 7.** Wait for the green ticks (`test`, `linked-issue`). If one goes red, click **Details**, fix the problem, commit and push again (same branch; the PR updates itself).

**Step 8.** Arjun reviews and merges. The issue closes and the card moves to **Done** automatically.

**Step 9.** Go back to Step 2 for your next issue. Always start from a fresh `git pull` on `main`.

**Rules (they're graded):**
- Only the person assigned an issue commits it and opens its PR. Never push someone else's issue.
- Only Arjun merges. Arjun's own PRs are approved by Arnav (you can't approve your own PR).
- Never push directly to `main` (branch protection blocks it anyway).
- If your work differs from the SRS/SAD/Test Plan, add a row to `docs/DEVIATIONS.md` in the same PR.
- When your requirement's tests pass, set its row in `docs/RTM.md` to **A** (once HMS-36 adds that file).

---

## 5. Merge conflicts (most likely in `config/settings.py`, `requirements.txt`, `templates/base.html`)

**Prevention:** when you must touch a shared file, **only add lines at the end** of it (settings, requirements) and keep the change small.

**If GitHub says "This branch has conflicts":**
```powershell
git checkout main
git pull
git checkout hms-09-blocks-rooms
git merge main
```
VS Code highlights each conflict. Click **"Accept Both Changes"** for settings and requirements lines (you almost always want both people's lines), then save. Then:
```powershell
pytest
git add config/settings.py
git commit -m "Merge main into hms-09"
git push
```

---

## 6. Integration contracts (names other modules rely on, so don't rename them)

Reports, seed data and dashboards are built against these names. If you really must change one, tell the person who depends on it.

**AllocationModule (Arjun), `allocation/models.py`**
- `Block`: `name` (unique), `gender_policy` (`"M"` / `"F"`)
- `Room`: `block` (FK Block), `floor` (int), `number`, `room_type` (`"SINGLE"` / `"SHARED"`), `capacity`, `occupancy`, `is_active`. Unique (`block`, `number`); CHECK `0 <= occupancy <= capacity`
- `Allocation`: `student` (FK User), `room` (FK Room), `start_date`, `end_date` (nullable), `status` (`"ACTIVE"` / `"ENDED"`)
- URL names: `allocation:my_room`, `allocation:room_list`, `allocation:student_list`, `allocation:allocate`, and (Sprint 2) `allocation:room_change_request`, `allocation:room_change_queue`

**FeeModule (Armaan), `fees/models.py`**
- `FeeStructure`: `term` (e.g. `"2026-ODD"`), `room_type` (`"SINGLE"` / `"SHARED"`), `amount`, `due_date`, `effective_from`
- `FeeStatement`: `student` (FK User), `term`, `amount_due`, `amount_paid`, `due_date`
- `Payment` (Sprint 2): `statement` (FK FeeStatement), `amount`, `status` (`"PENDING"` / `"SUCCESS"` / `"FAILED"`), `gateway_order_id`, `gateway_txn_id`, `created_at` (`auto_now_add`). **No card / CVV / PAN fields, ever.**
- URL names: `fees:my_fees`, `fees:structure_list`, and (Sprint 2) `fees:pay`, `fees:receipt`, `fees:reconciliation`

**AuthModule (Arjav), `accounts/`**: `User` (`role`, `roll_number`, `email`) and `StudentProfile` (`gender` etc.) already exist from HMS-01. URL names: `accounts:login`, `accounts:logout`, `accounts:register`, `accounts:profile`, `accounts:password_reset`.

**Already built (Arnav):** `audit.services.write_audit(actor, action, target, outcome="SUCCESS", details=None)`, plus URL names `complaints:my_complaints`, `complaints:create`, `complaints:queue` and `reports:index`.

**Shared helpers:** `core.decorators.role_required(User.Role.ADMIN, User.Role.WARDEN)` protects staff views. Pages extend `base.html` (Bootstrap 5).

**Rules everyone follows:**
- Every admin action (allocation, fee-structure edit, status change) calls `write_audit(...)` **inside** the same `transaction.atomic()` block.
- Never delete students or users. Deactivate them (`is_active = False`). Users with audit entries can't be deleted.
- Business rules go in `services.py`; views only call services.

---

## 7. AI prompt header (paste this before your own prompt)

> We are building a Django 5.1 Hostel Management System (Team 5). Custom user model `accounts.User` has `role` (STUDENT/WARDEN/ADMIN/TECHNICIAN), `roll_number`, `email`; `accounts.StudentProfile` has user (OneToOne, related_name="profile"), full_name, gender (M/F/O), phone, address, guardian_name, guardian_phone, emergency_contact. Use `core.decorators.role_required(User.Role.ADMIN, User.Role.WARDEN)` for staff-only views. Log admin actions with `audit.services.write_audit(actor, action, target, outcome="SUCCESS", details=None)` inside the same `transaction.atomic()`. Templates extend `base.html` (Bootstrap 5, mobile-first from 360px, every form field has a `<label>`). Business rules go in `services.py`, never in views. Write pytest-django tests in `<app>/tests/test_*.py` using the `client` fixture and `@pytest.mark.django_db`. Only modify files inside the `<app>/` folder unless told otherwise. Code must pass flake8 with max line length 120. Here are the existing files of my app: (paste them)

Read every line the AI gives you. You must be able to explain your code at the demo.
