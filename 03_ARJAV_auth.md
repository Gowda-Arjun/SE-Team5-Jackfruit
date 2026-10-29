# Arjav: AuthModule + Accessibility (complete instructions)

Read `00_TEAM_WORKFLOW_read_first.md` first: install, clone, the per-issue git cycle, conflicts, and the **AI prompt header** you paste before every prompt below.

**Your issues:**
- **Sprint 1:** HMS-04, 05, 06, 07, 08 (13 points)
- **Sprint 2:** HMS-21, 22, 23, 24 (9 points)

Your code lives in **`accounts/`**. A few issues also need small additions to shared files; those are marked **SHARED** below. Only **append** to those files.

What already exists (from Arjun's HMS-01):
- `accounts.User` with `role`, `roll_number` and `email`
- `accounts.StudentProfile` with `gender`, `phone` and so on
- A basic login/logout at `accounts/urls.py`
- `core/decorators.py` with `role_required`
- `templates/base.html`

---

## PART A: Day 1 morning (while Arjun and Arnav set up)

1. **Accept the repo invite.** Check your email or https://github.com/notifications. Until you accept it you can't push or be assigned issues.
2. **Install** Python 3.12, Git and VS Code, then run the `git config` commands. All of this is in Section 2 of the shared guide.
3. Wait for **"main is ready"** from Arjun, then clone and set up (Section 3 of the shared guide).
4. Open the Project board (repo → **Projects** tab → *HMS - Team 5 Backlog*) and find your cards.

---

## PART B: Sprint 1 (Day 1 afternoon). Do them in this order

### B1. HMS-04 + HMS-05 (#4, #5): Register and log in; password hashing. Branch `hms-04-register-login`
One PR whose description contains both **`Closes #4`** and **`Closes #5`**.

**AI prompt:**
> In the `accounts` app: (1) A student self-registration page at URL name `accounts:register` (link it from the login page). Fields: full name, email, roll number, gender (M/F/O), phone, password and confirm password. Validate the roll number format with a small `IdVerifier.check(roll_number)` function in `accounts/services.py` (for now: regex `^PES[12]UG\d{2}[A-Z]{2}\d{3}$`, case-insensitive, stored upper-case). Reject duplicate email or roll number with a clear message. Use Django password validators. In one `transaction.atomic()`, create `User(username=roll_number, email, roll_number, role=STUDENT)` with `set_password` plus a `StudentProfile`, then log the user in and redirect to `core:home`. (2) Login with **username or roll number**: add `accounts/backends.py` with a backend that looks up `User` by `username` or `roll_number` (case-insensitive) and checks the password. (3) Show "The email/roll number or password is incorrect." on a failed login. Tests: register success creates User + StudentProfile with role STUDENT; duplicate roll/email rejected; bad roll format rejected; login with roll number works; wrong password fails; the stored password starts with `pbkdf2_sha256$` and never contains the plain password (HMS-SR-002). (HMS-F-001, TC-Auth-01, TC-Sec-03)

**SHARED, append at the end of `config/settings.py`:**
```python
# HMS-F-001: log in with username or roll number
AUTHENTICATION_BACKENDS = ["accounts.backends.UsernameOrRollNumberBackend"]
```
`git add accounts templates config/settings.py` (`templates` only if you changed `base.html`).

### B2. HMS-06 (#6): RBAC and logging denied access. Branch `hms-06-rbac`
**Start this only after Arnav's HMS-18 (audit log) is merged.** Run `git pull` and check that `audit/services.py` exists.

**AI prompt:**
> (1) Update `core/decorators.py` `role_required` so that when a logged-in user's role isn't allowed, it calls `audit.services.write_audit(request.user, "ACCESS_DENIED", None, outcome="DENIED", details={"path": request.path})` and logs a warning, then raises `PermissionDenied`. (2) Create `templates/403.html` extending `base.html`: "You do not have permission to open this page." plus a link back to home. (3) Make sure every staff page uses `role_required(...)` and every student page uses `role_required(User.Role.STUDENT)`. Tests: a student opening a staff URL gets 403 and an AuditLog row with outcome DENIED; an admin opening a student-only URL gets 403; an anonymous user is redirected to login. (HMS-F-005, HMS-SR-003, TC-Auth-05, TC-Sec-04)

`git add core/decorators.py templates/403.html accounts`

### B3. HMS-07 (#7): 20-minute session timeout. Branch `hms-07-session-timeout`
**SHARED, append at the end of `config/settings.py`:**
```python
# HMS-F-004: end inactive sessions after 20 minutes
SESSION_COOKIE_AGE = 20 * 60
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
```
Test (`accounts/tests/test_session.py`):
> Test that after logging in, `request.session.get_expiry_age()` is 1200; that a request made while the session is still active refreshes the expiry; and that once the session expires (use `freezegun` or set `SESSION_COOKIE_AGE=1` with `time.sleep(2)`), visiting `core:home` redirects to `accounts:login`. (TC-Auth-04)

If you use `freezegun`, add `freezegun>=1.4` at the end of `requirements.txt`.
`git add accounts config/settings.py` (plus `requirements.txt` if you changed it).

### B4. HMS-08 (#8): Profile update. Branch `hms-08-profile`
**AI prompt:**
> A student-only page at URL name `accounts:profile` where the logged-in student edits **only their own** `StudentProfile` fields: phone, address, guardian_name, guardian_phone, emergency_contact (not name, gender or roll number). Phone must be 10 digits. On save, show a success message. Tests: the update persists and is shown after logging in again; a student cannot edit another student's profile (there is no id in the URL; it always uses `request.user`); a non-student gets 403. (HMS-F-002, TC-Auth-02)

`git add accounts`

### B5. Check your Sprint 1 PRs
All four PRs merged → cards in **Done**. Be ready to show registration and the 403 in the Sprint 1 video (Arnav records it).

---

## PART C: Sprint 2 (Day 2)

### C1. HMS-21 (#21): OTP password reset. Branch `hms-21-otp-reset`
**AI prompt:**
> Model `OTPToken(user FK, code_hash, created_at, expires_at, used_at null)`. Page `accounts:password_reset` takes an email and **always** shows the same message: "If that email is registered, a code has been sent." If the email exists, generate a 6-digit code with `secrets.randbelow`, store only `make_password(code)`, set expiry to now + 10 minutes, and email it with `send_mail`. Then a page `accounts:password_reset_confirm` takes email + code + new password + confirm. It works only if an unused, unexpired token exists and `check_password` matches; it marks the token used and sets the new password. Throttle: at most 5 code requests and 5 wrong attempts per email per 15 minutes (use Django's cache) → "Too many attempts. Please wait a few minutes and try again." Write `write_audit` entries for successful resets. Tests: valid code resets the password; expired code (11 minutes) is rejected; used code is rejected; wrong code is rejected; the same reply is given for an unknown email; throttling kicks in. (HMS-F-003, TC-Auth-03, TC-Sec-12)

In development, emails print in the `runserver` terminal (console email backend), which is how you read the code during the demo.
`git add accounts`

### C2. HMS-22 (#22): Responsive and accessible UI. Branch `hms-22-accessibility`
1. Run `python manage.py seed_demo`, then `runserver`. In Chrome, open each page (login, register, student dashboard, my room, fees, complaints, admin dashboard, reports).
2. Press **F12** → **Lighthouse** → *Accessibility* → **Analyze**. Also press **Ctrl+Shift+M** (device toolbar) and check the page at **360 px**, **768 px** and **1366 px** wide.
3. Keyboard-only test: **Tab** through every form. Focus must be visible, and every field needs a label.
4. Fix what you find. Usually that's `templates/base.html` (nav, contrast) or your own templates. For bugs in other modules' templates, tell the owner instead of editing their files.
5. Write `docs/a11y/ACCESSIBILITY_AUDIT.md`: a table of page, Lighthouse score, issues found and fixes, plus screenshots at 360 px.

`git add templates docs/a11y accounts` (TC-UX-01, HMS-NF-005)

### C3. HMS-23 (#23): HTTPS-only settings. Branch `hms-23-https-settings`
**SHARED, append at the end of `config/settings.py`:**
```python
# HMS-SR-001: HTTPS only in production (set DJANGO_SECURE=1 on the server)
if os.environ.get("DJANGO_SECURE") == "1":
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
```
Test: with `DJANGO_SECURE=1`, `DJANGO_DEBUG=0` and a long `DJANGO_SECRET_KEY` set, run `python manage.py check --deploy` and paste the output into `docs/security/check_deploy.txt` (warnings explained). Add a pytest that uses `override_settings(SECURE_SSL_REDIRECT=True)` and checks that an `http` request gets a 301 to `https`. (TC-Sec-02)

Add a DEVIATIONS row: "TLS 1.2 is enforced at Nginx in the SAD; no staging server in this project, so verified with Django settings and `check --deploy`."
`git add config/settings.py docs/security accounts docs/DEVIATIONS.md`

### C4. HMS-24 (#24): Health check + restart policy. Branch `hms-24-health-restart`
- `/healthz/` already exists (`core/views.py`). Add a test that it returns `{"status": "ok"}` in under 200 ms.
- **SHARED** `docker-compose.yml`: add `restart: unless-stopped` under both `db:` and `web:`.
- Write `docs/ops/UPTIME.md` (5 lines): an uptime monitor (e.g. UptimeRobot) calls `/healthz/` every minute; containers restart automatically; targets HMS-NF-002 (99.5%).

`git add docker-compose.yml docs/ops core/tests` (HMS-NF-002)

### C5. Update the RTM
After Arnav's HMS-36 is merged: in your last PR, set your rows (F-001 to F-005, SR-001, SR-002, SR-003, NF-002, NF-005) in `docs/RTM.md` to **A** (or **P** with a reason).

---

## If you get stuck
- A red ✗ on the PR: click **Details** and read the last red lines. `flake8` errors show the file and line to fix; `pytest` errors show which test failed.
- Merge conflict in `config/settings.py`: **Accept Both Changes** (shared guide, Section 5).
- Ask in the group before editing any file outside `accounts/`, other than the SHARED ones listed here.
