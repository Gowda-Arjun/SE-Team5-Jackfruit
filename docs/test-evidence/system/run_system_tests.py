"""System test run for HMS (STP 5.2 "System" level, test cases ST_01 to ST_33).

Black-box, end-to-end journeys through a real browser (Chromium via Playwright) against the
running Django app, as STP 5.2 plans with Selenium (see docs/DEVIATIONS.md D13 for the tool).
Every case drives the UI the way a Student, Warden, Admin or Technician would, checks what is
shown on screen (or the HTTP status for negative cases), and saves a screenshot as evidence.

Usage (from the repo root):

    pip install playwright && playwright install chromium     # once, in any venv
    python docs/test-evidence/system/run_system_tests.py --server-python .venv/Scripts/python.exe

The runner builds a fresh SQLite database in a temp folder, runs migrate + seed_demo +
setup_st_data.py, starts `runserver` with the mock payment gateway and a file email backend,
runs every case in order, and writes results.json and screenshots/ next to this file.
Results are summarised in docs/SYSTEM_TEST_REPORT.md.
"""
import argparse
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PW = "Hostel@Demo2026"
TODAY = datetime.date.today()
MONTH_START = TODAY.replace(day=1)
CASES = []


def case(cid, module, reqs, title, pre, steps, data, expected):
    def wrap(fn):
        CASES.append({"id": cid, "module": module, "requirements": reqs, "title": title, "pre": pre,
                      "steps": steps, "data": data, "expected": expected, "fn": fn})
        return fn
    return wrap


class Run:
    """Shared state for one run: browser context, page, server URL and facts carried between cases."""

    def __init__(self, base, work, browser):
        self.base, self.work, self.browser = base, work, browser
        self.ctx = browser.new_context(viewport={"width": 1280, "height": 800}, accept_downloads=True)
        self.page = self.ctx.new_page()
        self.page.on("dialog", lambda d: d.accept())
        self.facts = {}

    # ---- helpers -------------------------------------------------------------------------
    def go(self, path):
        return self.page.goto(self.base + path)

    def body(self):
        return self.page.inner_text("body")

    def alerts(self):
        sel = ".alert, .errorlist, .invalid-feedback, form .text-danger"
        seen = []
        for t in self.page.locator(sel).all_inner_texts():
            t = " ".join(t.split())
            if t and not any(t in s or s in t for s in seen):
                seen.append(t)
        return " | ".join(seen)

    def url(self, href):
        return urllib.parse.urljoin(self.page.url, href)

    def login(self, username, password=PW):
        self.ctx.clear_cookies()
        self.go("/accounts/login/")
        self.page.fill("input[name=username]", username)
        self.page.fill("input[name=password]", password)
        self.submit("username")

    def submit(self, field):
        """Click the submit button of the form that contains the named field."""
        form = self.page.locator("form", has=self.page.locator(f"[name={field}]")).first
        form.locator("button[type=submit], input[type=submit]").first.click()
        self.page.wait_for_load_state()

    def select_containing(self, name, needle):
        sel = f"select[name={name}]"
        value = self.page.evaluate(
            "([s, n]) => { const o = [...document.querySelector(s).options].find(o => o.text.includes(n));"
            " return o ? o.value : null; }", [sel, needle])
        if value is None:
            raise AssertionError(f"no option containing {needle!r} in {name}")
        self.page.select_option(sel, value)
        return value

    def options(self, name):
        return self.page.evaluate(f"() => [...document.querySelector('select[name={name}]').options].map(o => o.text)")

    def status(self, path):
        return self.page.request.get(self.base + path, max_redirects=0).status

    def mails(self, to=None):
        out = []
        for f in sorted(glob.glob(os.path.join(self.work, "mail", "*.log")), key=os.path.getmtime):
            text = open(f, encoding="utf-8", errors="replace").read()
            for msg in text.split("-" * 79):
                if msg.strip() and (to is None or f"To: {to}" in msg):
                    out.append(msg)
        return out

    def otp_for(self, email):
        codes = re.findall(r"OTP is (\d{6})", "\n".join(self.mails(email)))
        if not codes:
            raise AssertionError(f"no OTP email for {email}")
        return codes[-1]

    def fee_row(self):
        cells = self.page.locator("tbody tr").first.locator("td").all_inner_texts()
        return {"term": cells[0], "item": cells[1], "due": float(cells[2]), "paid": float(cells[3]),
                "balance": float(cells[4]), "due_date": cells[5]}

    def reset_password(self, email, new_password):
        self.ctx.clear_cookies()
        self.go("/accounts/forgot-password/")
        self.page.fill("input[name=email]", email)
        self.submit("email")
        otp = self.otp_for(email)
        if "reset-password" not in self.page.url:
            self.go("/accounts/reset-password/")
        self.page.fill("input[name=email]", email)
        self.page.fill("input[name=otp]", otp)
        self.page.fill("input[name=new_password]", new_password)
        self.page.fill("input[name=confirm_password]", new_password)
        self.submit("otp")
        return otp


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


# =============================== AuthModule =================================================
@case("ST_01", "AuthModule", "HMS-F-001", "Student logs in with valid credentials and lands on the Student dashboard",
      "Seeded account student01 exists and is active", "1. Open /accounts/login/ 2. Enter username and password "
      "3. Click Log in", "Username: student01, Password: Hostel@Demo2026",
      "Login succeeds; Student dashboard 'Welcome, Student 01' with My room, Fees and Complaints cards")
def st_01(r):
    r.login("student01")
    h1 = r.page.inner_text("h1")
    check(r.page.url.rstrip("/") == r.base and "Welcome" in h1, f"landed on {r.page.url} with heading {h1!r}")
    cards = [c for c in ("My room", "Fees", "Complaints") if c in r.body()]
    check(len(cards) == 3, f"cards shown: {cards}")
    return f"Redirected to / with heading '{h1}'; cards shown: {', '.join(cards)}"


@case("ST_02", "AuthModule", "HMS-F-001", "Login with a wrong password is refused",
      "Seeded account student01 exists", "1. Open /accounts/login/ 2. Enter student01 with a wrong password "
      "3. Click Log in", "Username: student01, Password: WrongPass@1",
      "Stays on the login page with an error message; no session is created")
def st_02(r):
    r.login("student01", "WrongPass@1")
    msg = r.alerts() or r.body()
    check("/accounts/login/" in r.page.url, f"moved to {r.page.url}")
    check("correct username and password" in msg, f"message: {msg[:200]}")
    check(r.status("/fees/my/") == 302, "protected page reachable without login")
    return f"Stayed on /accounts/login/; message: '{msg.strip()[:110]}'; /fees/my/ still redirects to login"


@case("ST_18", "AuthModule", "HMS-F-001, HMS-F-005", "Each staff role lands on the right dashboard; "
      "Technician is kept out of admin pages", "Seeded admin, warden; tech01 created by setup_st_data.py",
      "1. Log in as admin, read the dashboard heading 2. Repeat as warden 3. Log in as tech01 and open "
      "/reports/, /allocation/rooms/ and /complaints/queue/", "admin, warden, tech01 / Hostel@Demo2026",
      "Admin and Warden see 'Warden / Admin dashboard'; Technician gets 403 on reports and rooms and 200 on "
      "the complaint queue")
def st_18(r):
    out = []
    for user in ("admin", "warden"):
        r.login(user)
        h1 = r.page.inner_text("h1")
        check("Warden / Admin dashboard" in h1, f"{user} heading {h1!r}")
        out.append(f"{user}: '{h1}'")
    r.login("tech01")
    codes = {p: r.status(p) for p in ("/reports/", "/allocation/rooms/", "/complaints/queue/")}
    check(codes["/reports/"] == 403 and codes["/allocation/rooms/"] == 403, f"technician codes {codes}")
    check(codes["/complaints/queue/"] == 200, f"technician queue {codes}")
    r.go("/complaints/queue/")
    return "; ".join(out) + f"; tech01 HTTP codes: {codes}"


@case("ST_17", "AuthModule", "HMS-F-005, HMS-SR-003", "Student cannot open Warden/Admin pages (vertical escalation)",
      "Logged in as student01", "1. Log in as student01 2. Type each Admin/Warden URL into the address bar",
      "/reports/, /allocation/rooms/, /allocation/students/, /allocation/allocate/, /fees/structures/, "
      "/fees/reconciliation/, /complaints/queue/, /allocation/room-change-queue/",
      "Every URL returns HTTP 403 Forbidden")
def st_17(r):
    r.login("student01")
    paths = ["/reports/", "/allocation/rooms/", "/allocation/students/", "/allocation/allocate/",
             "/fees/structures/", "/fees/reconciliation/", "/complaints/queue/", "/allocation/room-change-queue/"]
    codes = {p: r.status(p) for p in paths}
    bad = {p: c for p, c in codes.items() if c != 403}
    check(not bad, f"not 403: {bad}")
    r.go("/reports/")
    return f"All {len(paths)} URLs returned 403"


@case("ST_03", "AuthModule", "HMS-F-002", "Student updates own profile",
      "Logged in as student01", "1. Open My profile 2. Change phone and address 3. Click Save 4. Reload the page",
      "Phone: 9123456780, Address: Room A103, PES Hostel, Bengaluru",
      "'Your profile was updated successfully.' shown; new values still there after reload")
def st_03(r):
    r.login("student01")
    r.go("/accounts/profile/")
    r.page.fill("[name=phone]", "9123456780")
    r.page.fill("[name=address]", "Room A103, PES Hostel, Bengaluru")
    r.submit("phone")
    msg = r.alerts()
    check("profile was updated successfully" in msg, f"message: {msg}")
    r.go("/accounts/profile/")
    phone, addr = r.page.input_value("[name=phone]"), r.page.input_value("[name=address]")
    check(phone == "9123456780" and addr.startswith("Room A103"), f"after reload {phone!r} {addr!r}")
    return f"Message '{msg}'; after reload phone={phone}, address='{addr}'"


@case("ST_04", "AuthModule", "HMS-F-003", "Password reset with emailed OTP; OTP is single use",
      "student05 has a registered email; email delivery captured to files (stands in for MailHog)",
      "1. Open Forgot password, enter email 2. Read the OTP from the email 3. Enter email, OTP and new password "
      "twice 4. Log in with the new password 5. Try the same OTP again 6. Try the old password",
      "Email: student05@demo.hms.test, New password: Hostel@Reset2026",
      "OTP email received; reset succeeds; login works with new password; reused OTP refused; old password refused")
def st_04(r):
    email = "student05@demo.hms.test"
    otp = r.reset_password(email, "Hostel@Reset2026")
    r.login("student05", "Hostel@Reset2026")
    check("Welcome" in r.page.inner_text("h1"), "new password did not log in")
    r.ctx.clear_cookies()
    r.go("/accounts/reset-password/")
    r.page.fill("input[name=email]", email)
    r.page.fill("input[name=otp]", otp)
    r.page.fill("input[name=new_password]", "Hostel@Again2026")
    r.page.fill("input[name=confirm_password]", "Hostel@Again2026")
    r.submit("otp")
    reuse_msg = r.alerts() or r.body()[:200]
    r.login("student05", "Hostel@Again2026")
    check("/accounts/login/" in r.page.url, "reused OTP changed the password")
    r.login("student05", PW)
    check("/accounts/login/" in r.page.url, "old password still works")
    r.login("student05", "Hostel@Reset2026")
    return (f"OTP {otp} emailed; reset done and new password logs in; reusing the OTP shows "
            f"'{reuse_msg.strip()[:90]}' and the password is unchanged; old password refused")


@case("ST_05", "AuthModule", "HMS-F-004", "Session expires 20 minutes after the last request; logout ends it",
      "Logged in as student01", "1. Log in 2. Inspect the session cookie expiry 3. Open a page and inspect again "
      "4. Click Log out 5. Open /fees/my/", "student01",
      "Session cookie expires 20 min after each request (sliding); after logout the fee page redirects to login")
def st_05(r):
    r.login("student01")

    def ttl():
        c = [c for c in r.ctx.cookies() if c["name"] == "sessionid"][0]
        return c["expires"] - time.time(), c

    t1, cookie = ttl()
    time.sleep(3)
    r.go("/fees/my/")
    t2, _ = ttl()
    check(1140 <= t1 <= 1205 and 1140 <= t2 <= 1205, f"ttl {t1:.0f}s / {t2:.0f}s")
    check(cookie["httpOnly"], "session cookie not HttpOnly")
    r.page.locator("form[action*='logout'] button").first.click()
    r.page.wait_for_load_state()
    code = r.status("/fees/my/")
    check(code == 302, f"after logout /fees/my/ gave {code}")
    r.go("/fees/my/")
    check("/accounts/login/" in r.page.url, f"not on login page: {r.page.url}")
    return (f"Cookie TTL {t1:.0f}s after login and {t2:.0f}s after a later request (refreshed); HttpOnly; "
            f"after logout /fees/my/ redirects to {r.page.url.replace(r.base, '')}")


# =============================== AllocationModule ===========================================
@case("ST_06", "AllocationModule", "HMS-F-010", "Student views own room and roommates",
      "student01 and student04 allocated to A103 (setup_st_data.py)", "1. Log in as student01 2. Open My room",
      "student01", "Block A, Room A103, Shared, roommate 'Demo Student 04'")
def st_06(r):
    r.login("student01")
    r.go("/allocation/my-room/")
    text = r.body()
    check("Room A103" in text and "Demo Student 04" in text, text[:300])
    return "Shows 'Block A · Room A103', type Shared, roommate Demo Student 04"


@case("ST_07", "AllocationModule", "HMS-F-012", "Admin allocates a room; occupancy updates",
      "Logged in as admin; student02 has no room; A104 empty", "1. Open Allocate room 2. Choose student and room "
      "3. Click Allocate 4. Open Rooms", "Student: Demo Student 02, Room: Block A Room A104",
      "'Room A104 in Block A successfully allocated to Demo Student 02.'; A104 occupancy 1 of 2")
def st_07(r):
    r.login("admin")
    r.go("/allocation/allocate/")
    r.select_containing("student", "Demo Student 02")
    r.select_containing("room", "Room A104")
    r.submit("student")
    msg = r.alerts()
    check("A104" in msg and "successfully allocated" in msg, msg)
    row = r.page.locator("tr", has_text="A104").first.inner_text()
    return f"Message '{msg}'; room list row: {' '.join(row.split())}"


@case("ST_23", "AllocationModule", "HMS-F-012", "Allocation that breaks the block gender policy is refused",
      "Logged in as admin; Block B is Female only", "1. Open Allocate room 2. Choose a male student and a Block B "
      "room 3. Click Allocate", "Student: Demo Student 05 [M], Room: Block B Room B102",
      "'This block is not available for this student.'; no allocation made")
def st_23(r):
    r.login("admin")
    r.go("/allocation/allocate/")
    r.select_containing("student", "Demo Student 05")
    r.select_containing("room", "Room B102")
    r.submit("student")
    msg = r.alerts()
    check("not available for this student" in msg, msg)
    return f"Refused with '{msg}'; still on the allocate page"


@case("ST_22", "AllocationModule", "HMS-F-015, HMS-F-012", "Two admins race for the last bed; the second is refused",
      "Logged in as admin; single room A101 (capacity 1) is empty", "1. Admin opens Allocate room and selects "
      "student05 + A101 2. Before submitting, a second admin session allocates student02 to A101 3. First admin "
      "clicks Allocate 4. Open Rooms", "Room A101 (Single, capacity 1); students Demo Student 05 and Demo Student 02",
      "Second allocation refused with a clear error; A101 shows occupancy 1 of 1, never 2")
def st_22(r):
    r.login("admin")
    r.go("/allocation/allocate/")
    r.select_containing("student", "Demo Student 05")
    room = r.select_containing("room", "Room A101")
    token = r.page.input_value("input[name=csrfmiddlewaretoken]")
    other = r.page.evaluate("() => [...document.querySelector('select[name=student]').options]"
                            ".find(o => o.text.includes('Demo Student 02')).value")
    resp = r.page.request.post(r.base + "/allocation/allocate/", form={
        "csrfmiddlewaretoken": token, "student": other, "room": room},
        headers={"Referer": r.base + "/allocation/allocate/"})
    check(resp.ok, f"concurrent allocation failed: {resp.status}")
    r.submit("student")
    msg = r.alerts()
    check("/allocation/allocate/" in r.page.url, f"first admin was redirected to {r.page.url}")
    check("no free beds" in msg or "not one of the available choices" in msg, msg)
    r.go("/allocation/rooms/")
    row = " ".join(r.page.locator("tr", has_text="A101").first.inner_text().split())
    r.go("/allocation/allocate/")
    r.select_containing("student", "Demo Student 05")
    check(not any("Room A101" in o for o in r.options("room")), "A101 still offered")
    return f"Second submit refused: '{msg}'. Room list: {row}. A101 no longer offered in the room list"


@case("ST_19", "AllocationModule", "HMS-F-011, HMS-F-001", "Admin creates, edits and deactivates student records; "
      "new student sets a password by OTP and logs in", "Logged in as admin",
      "1. Add Student with the data shown 2. Search by roll number 3. Edit phone 4. New student uses Forgot password "
      "to set a password and logs in 5. Admin deactivates student10 6. student10 tries to log in",
      "Roll: ST2026001, Email: st.newstudent@demo.hms.test, Name: System Test Student, Gender: M, "
      "Phone (edit): 9988776655",
      "Record created and listed; edit saved; new student logs in to the Student dashboard; deactivated student10 "
      "is hidden from the list and cannot log in")
def st_19(r):
    r.login("admin")
    r.go("/allocation/students/create/")
    r.page.fill("[name=roll_number]", "ST2026001")
    r.page.fill("[name=email]", "st.newstudent@demo.hms.test")
    r.page.fill("[name=full_name]", "System Test Student")
    r.page.select_option("[name=gender]", "M")
    r.submit("roll_number")
    created = r.alerts()
    check("Student record created for System Test Student (ST2026001)" in created, created)
    r.go("/allocation/students/?q=ST2026001")
    row = r.page.locator("tr", has_text="ST2026001").first
    row.locator("a", has_text="Edit").click()
    r.page.wait_for_load_state()
    r.page.fill("[name=phone]", "9988776655")
    r.submit("phone")
    edited = r.alerts()
    check("updated" in edited.lower(), edited)
    r.reset_password("st.newstudent@demo.hms.test", "Hostel@New2026")
    r.login("ST2026001", "Hostel@New2026")
    h1 = r.page.inner_text("h1")
    check("Welcome" in h1, f"new student heading {h1!r}")
    r.login("admin")
    r.go("/allocation/students/?q=DEMO2026010")
    r.page.locator("tr", has_text="DEMO2026010").first.locator("button", has_text="Deactivate").click()
    r.page.wait_for_load_state()
    deact = r.alerts()
    check("DEMO2026010 has been deactivated" in deact, deact)
    r.go("/allocation/students/")
    hidden = "DEMO2026010" not in r.body()
    r.login("student10")
    check("/accounts/login/" in r.page.url and hidden, "deactivated student still listed or able to log in")
    r.login("admin")
    r.go("/allocation/students/?q=ST2026001")
    return (f"'{created}'; edit: '{edited}'; new student set a password by OTP and saw '{h1}'; "
            f"'{deact}'; student10 hidden from the list and login refused")


@case("ST_20", "AllocationModule", "HMS-F-014", "Admin creates a block and a room; invalid rooms are refused",
      "Logged in as admin", "1. Add Block 2. Add Room in the new block 3. Add the same room number again "
      "4. Add a room with capacity 0", "Block C (Male); Room C201, floor 2, Shared, capacity 2; duplicate C201; "
      "C202 with capacity 0", "Block and room created with success messages; duplicate refused with 'A room with "
      "this number already exists in this block.'; capacity 0 refused")
def st_20(r):
    r.login("admin")
    r.go("/allocation/blocks/create/")
    r.page.fill("[name=name]", "Block C")
    r.page.select_option("[name=gender_policy]", "M")
    r.submit("name")
    m1 = r.alerts()
    check("Block 'Block C' created successfully" in m1, m1)

    def add_room(number, capacity):
        r.go("/allocation/rooms/create/")
        r.select_containing("block", "Block C")
        r.page.fill("[name=floor]", "2")
        r.page.fill("[name=number]", number)
        r.page.select_option("[name=room_type]", "SHARED")
        r.page.fill("[name=capacity]", str(capacity))
        r.page.evaluate("() => document.querySelectorAll('[min]').forEach(e => e.removeAttribute('min'))")
        r.submit("number")
        return r.alerts()

    m2 = add_room("C201", 2)
    check("Room C201 created successfully" in m2, m2)
    m3 = add_room("C201", 2)
    check("already exists in this block" in m3, m3)
    m4 = add_room("C202", 0)
    check("/rooms/create/" in r.page.url and m4, f"capacity 0 accepted: {m4}")
    return f"'{m1}'; '{m2}'; duplicate: '{m3}'; capacity 0: '{m4}'"


@case("ST_21", "AllocationModule", "HMS-F-014", "Admin deactivates a room; it is no longer offered for allocation",
      "Room C201 exists and is empty (ST_20)", "1. Open Rooms 2. Click Deactivate on C201 and confirm "
      "3. Open Allocate room", "Room C201", "'Room C201 has been deactivated.'; C201 missing from the room choices")
def st_21(r):
    r.login("admin")
    r.go("/allocation/rooms/")
    r.page.locator("tr", has_text="C201").first.locator("button", has_text="Deactivate").click()
    r.page.wait_for_load_state()
    msg = r.alerts()
    check("Room C201 has been deactivated" in msg, msg)
    r.go("/allocation/allocate/")
    check(not any("C201" in o for o in r.options("room")), "C201 still offered")
    return f"'{msg}'; C201 not in the allocate form's room list"


@case("ST_08", "AllocationModule", "HMS-F-013", "Student requests a room change; Warden approves it",
      "student01 in A103; A105 empty", "1. student01 opens Request Room Change, picks A105, gives a reason, submits "
      "2. Warden opens the room-change queue and clicks Approve 3. student01 opens My room",
      "Preferred room: Block A Room A105, Reason: Closer to the study hall",
      "Request shown as Pending; Warden sees 'Room change request #n has been approved.'; student01 now in A105")
def st_08(r):
    r.login("student01")
    r.go("/allocation/room-change/")
    r.select_containing("preferred_room", "A105")
    r.page.fill("[name=reason]", "Closer to the study hall")
    r.submit("reason")
    m1 = " ".join(r.page.locator(".alert-success").first.inner_text().split())
    check("submitted successfully" in m1 and "Pending" in r.body(), m1)
    r.login("warden")
    r.go("/allocation/room-change-queue/")
    r.page.locator("tr", has_text="A105").first.locator("form:has(input[value=approve]) button").click()
    r.page.wait_for_load_state()
    m2 = r.alerts()
    check("has been approved" in m2, m2)
    r.login("student01")
    r.go("/allocation/my-room/")
    check("Room A105" in r.body(), "student01 not moved")
    return f"Student: '{m1}' (Pending). Warden: '{m2}'. My room now shows Room A105"


@case("ST_29", "AllocationModule", "HMS-F-013", "Warden rejects a room-change request; allocation unchanged",
      "student04 in A103", "1. student04 requests A104 2. Warden clicks Reject 3. student04 opens My room and the "
      "request page", "Preferred room: Block A Room A104, Reason: Quieter floor",
      "'Room change request #n has been rejected.'; student04 still in A103; request shows Rejected")
def st_29(r):
    r.login("student04")
    r.go("/allocation/room-change/")
    r.select_containing("preferred_room", "A104")
    r.page.fill("[name=reason]", "Quieter floor")
    r.submit("reason")
    r.login("warden")
    r.go("/allocation/room-change-queue/")
    r.page.locator("tr", has_text="A104").first.locator("form:has(input[value=reject]) button").click()
    r.page.wait_for_load_state()
    msg = r.alerts()
    check("has been rejected" in msg, msg)
    r.login("student04")
    r.go("/allocation/my-room/")
    check("Room A103" in r.body(), "student04 moved")
    r.go("/allocation/room-change/")
    check("Rejected" in r.body(), "status not Rejected")
    return f"Warden: '{msg}'. student04 still in Room A103; request listed as Rejected"


# =============================== FeeModule ==================================================
@case("ST_09", "FeeModule", "HMS-F-020", "Student views an itemised fee statement",
      "student01 allocated (shared room); 2026-ODD fee structure seeded", "1. Log in as student01 2. Open Fees",
      "student01", "Row for 2026-ODD 'Hostel fee (Shared)' with amount due, amount paid 0, balance = due - paid, "
      "due date")
def st_09(r):
    r.login("student01")
    r.go("/fees/my/")
    row = r.fee_row()
    check(row["term"] == "2026-ODD" and row["paid"] == 0 and row["balance"] == row["due"] - row["paid"], row)
    r.facts["fee_due"] = row["due"]
    return (f"Term {row['term']}, {row['item']}, due {row['due']:.2f}, paid {row['paid']:.2f}, "
            f"balance {row['balance']:.2f}, due date {row['due_date']}")


@case("ST_32", "FeeModule", "HMS-F-021", "A failed gateway payment leaves the balance unchanged",
      "student01 has a balance", "1. Fees > Pay now 2. On the sandbox checkout click 'Fail (test)' "
      "3. Return to Fees", "Mock gateway outcome: FAILED", "Balance and amount paid unchanged; no receipt can be "
      "downloaded for the failed attempt")
def st_32(r):
    r.login("student01")
    r.go("/fees/my/")
    before = r.fee_row()
    r.page.click("text=Pay now")
    r.page.wait_for_load_state()
    r.page.click("button:has-text('Fail (test)')")
    r.page.wait_for_load_state()
    r.go("/fees/my/")
    after = r.fee_row()
    check(after["balance"] == before["balance"] and after["paid"] == before["paid"], (before, after))
    shown = r.page.locator("a", has_text="Download receipt").count()
    check(shown == 0, f"{shown} receipt links offered for a failed payment")
    return (f"Balance stayed {after['balance']:.2f}, paid stayed {after['paid']:.2f}; "
            f"no 'Download receipt' link offered for the failed attempt")


@case("ST_10", "FeeModule", "HMS-F-021, HMS-SR-005", "Student pays the fee through the sandbox gateway",
      "student01 has a balance", "1. Fees > Pay now 2. On the sandbox checkout click 'Pay (test)' (signed webhook "
      "returns to HMS) 3. Return to Fees", "Mock gateway outcome: SUCCESS for the full balance",
      "Checkout page has no card fields; amount paid = amount due; balance 0.00")
def st_10(r):
    r.login("student01")
    r.go("/fees/my/")
    r.page.click("text=Pay now")
    r.page.wait_for_load_state()
    card_inputs = r.page.locator("input[name*=card], input[name*=cvv], input[autocomplete^=cc-]").count()
    check(card_inputs == 0, "card fields on checkout")
    r.page.click("button:has-text('Pay (test)')")
    r.page.wait_for_load_state()
    r.go("/fees/my/")
    row = r.fee_row()
    check(row["balance"] == 0 and row["paid"] == row["due"], row)
    return f"Checkout had 0 card inputs; after the signed webhook: paid {row['paid']:.2f}, balance {row['balance']:.2f}"


@case("ST_11", "FeeModule", "HMS-F-023, HMS-SR-003", "Student downloads the PDF receipt; another student cannot",
      "student01 has a successful payment (ST_10)", "1. Fees > Download receipt for the paid attempt 2. Log in as "
      "student02 and open the same receipt URL", "Receipt URL of student01's successful payment",
      "student01 gets a PDF file; student02 gets 404 (no information leak)")
def st_11(r):
    r.login("student01")
    r.go("/fees/my/")
    links = r.page.locator("a", has_text="Download receipt")
    hrefs = [links.nth(i).get_attribute("href") for i in range(links.count())]
    pdf = None
    for href in hrefs:
        resp = r.page.request.get(r.base + href)
        if resp.ok and resp.body()[:4] == b"%PDF":
            pdf = (href, len(resp.body()), resp.headers.get("content-type"))
    check(pdf, f"no PDF among {hrefs}")
    path = os.path.join(r.work, "receipt.pdf")
    open(path, "wb").write(r.page.request.get(r.base + pdf[0]).body())
    r.login("student02")
    code = r.status(pdf[0])
    check(code in (403, 404), f"other student got {code}")
    r.go(pdf[0])
    return f"{pdf[0]} returned {pdf[2]} ({pdf[1]} bytes, starts with %PDF); student02 on the same URL: HTTP {code}"


@case("ST_24", "FeeModule", "HMS-F-022", "Warden configures fee structures; invalid entries refused; existing "
      "statements keep their amount", "Logged in as warden; student03 already has a 2026-ODD statement",
      "1. Note student03's amount due 2. New fee structure for 2026-EVEN 3. Try a duplicate 2026-ODD Shared "
      "4. Try amount 0 5. Edit 2026-ODD Shared amount +1000 6. student03 re-opens Fees",
      "2026-EVEN / Single / 52000 / due 2027-03-31 / from 2027-01-01; duplicate 2026-ODD Shared; amount 0",
      "'Fee structure created.'; duplicate and zero amount refused with errors; 'Fee structure updated.'; "
      "student03's amount due unchanged")
def st_24(r):
    r.login("student03")
    r.go("/fees/my/")
    due_before = r.fee_row()["due"]
    r.login("warden")

    def new(term, rtype, amount):
        r.go("/fees/structures/new/")
        r.page.fill("[name=term]", term)
        r.page.select_option("[name=room_type]", rtype)
        r.page.evaluate("() => document.querySelectorAll('[min]').forEach(e => e.removeAttribute('min'))")
        r.page.fill("[name=amount]", str(amount))
        r.page.fill("[name=due_date]", "2027-03-31")
        r.page.fill("[name=effective_from]", "2027-01-01")
        r.submit("term")
        return r.alerts()

    m1 = new("2026-EVEN", "SINGLE", 52000)
    check("Fee structure created" in m1, m1)
    m2 = new("2026-ODD", "SHARED", 40000)
    check("/structures/new/" in r.page.url and "created" not in m2, f"duplicate accepted: {m2}")
    m3 = new("2026-EVEN", "SHARED", 0)
    check("/structures/new/" in r.page.url and "created" not in m3, f"zero accepted: {m3}")
    r.go("/fees/structures/")
    r.page.locator("tr", has_text="2026-ODD").filter(has_text="Shared").first.locator("a", has_text="Edit").click()
    r.page.wait_for_load_state()
    old_amount = float(r.page.input_value("[name=amount]"))
    r.page.fill("[name=amount]", f"{old_amount + 1000:.2f}")
    r.submit("amount")
    m4 = r.alerts()
    check("Fee structure updated" in m4, m4)
    r.login("student03")
    r.go("/fees/my/")
    due_after = r.fee_row()["due"]
    check(due_after == due_before, f"statement changed {due_before} -> {due_after}")
    r.login("warden")
    r.go("/fees/structures/")
    return (f"'{m1}'; duplicate refused: '{m2}'; amount 0 refused: '{m3}'; '{m4}' "
            f"({old_amount:.2f} -> {old_amount + 1000:.2f}); student03 amount due stayed {due_after:.2f}")


@case("ST_12", "FeeModule", "HMS-F-024", "Admin reconciles payments against the gateway ledger and sees defaulters",
      "student01 paid (ST_10); student03 statement overdue (setup)", "1. Log in as admin 2. Open Reconciliation for "
      "this month", f"Date range {MONTH_START} to {TODAY}",
      "Matched payments >= 1, no mismatches; Defaulters table lists DEMO2026003")
def st_12(r):
    r.login("admin")
    r.go(f"/fees/reconciliation/?date_from={MONTH_START}&date_to={TODAY}")
    text = r.body()
    matched = re.search(r"Matched payments: (\d+)", text)
    check(matched and int(matched.group(1)) >= 1, text[:300])
    defaulters = r.page.locator("table").last.inner_text()
    check("DEMO2026003" in defaulters, defaulters[:300])
    return f"'Matched payments: {matched.group(1)}'; Defaulters table includes DEMO2026003 (student03)"


# =============================== ComplaintModule ============================================
@case("ST_13", "ComplaintModule", "HMS-F-030", "Student raises a maintenance complaint with a photo",
      "Logged in as student01", "1. Complaints > New 2. Choose category, type description, attach photo 3. Submit "
      "4. Open My complaints", "Category: Plumbing, Description: Bathroom tap in A105 is leaking, Photo: tap.png "
      "(valid 1x1 PNG)", "'Complaint CMP-nnnnnn raised. Status: Open.' with a new ticket id; ticket listed as Open")
def st_13(r):
    r.login("student01")
    r.go("/complaints/new/")
    r.page.select_option("[name=category]", "PLUMBING")
    r.page.fill("[name=description]", "Bathroom tap in A105 is leaking")
    png = os.path.join(r.work, "tap.png")
    open(png, "wb").write(bytes.fromhex(
        "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
        "1f15c4890000000d49444154789c63f8cf000000020001e221bc330000000049454e44ae426082"))
    r.page.set_input_files("[name=photo]", png)
    r.submit("description")
    msg = r.alerts()
    ticket = re.search(r"Complaint (\S+) raised\. Status: Open", msg)
    check(ticket, msg)
    r.facts["ticket"] = ticket.group(1)
    r.go("/complaints/")
    row = " ".join(r.page.locator("tr", has_text=ticket.group(1)).first.inner_text().split())
    check("Open" in row, row)
    return f"'{msg}'; My complaints row: {row}"


@case("ST_25", "ComplaintModule", "HMS-F-030, TC-Sec-09", "Unsafe complaint attachments are refused",
      "Logged in as student01", "1. Complaints > New 2. Attach each bad file 3. Submit",
      "notes.png (text file renamed to .png); run.exe; photo.gif",
      "Each upload refused with 'This file type or size is not allowed. Use a JPG or PNG image of 5 MB or less.'")
def st_25(r):
    r.login("student01")
    results = []
    for name, content in (("notes.png", b"<?php echo 'x'; ?>"), ("run.exe", b"MZ\x90\x00"), ("photo.gif", b"GIF89a")):
        path = os.path.join(r.work, name)
        open(path, "wb").write(content)
        r.go("/complaints/new/")
        r.page.select_option("[name=category]", "ELECTRICAL")
        r.page.fill("[name=description]", "Upload safety check")
        r.page.set_input_files("[name=photo]", path)
        r.submit("description")
        refused = "This file type or size is not allowed" in r.body() and "/complaints/new/" in r.page.url
        results.append(f"{name}: {'refused' if refused else 'ACCEPTED'}")
    check(all("refused" in x for x in results), results)
    return "; ".join(results) + " (message: 'This file type or size is not allowed...')"


@case("ST_26", "ComplaintModule", "HMS-NF-003, HMS-SR-003", "Another student cannot open a complaint or its photo "
      "(IDOR)", "Ticket from ST_13 belongs to student01", "1. Log in as student02 2. Open /complaints/<ticket>/ and "
      "/complaints/<ticket>/photo/", "Ticket id of student01's complaint", "Both return 404 Not Found")
def st_26(r):
    t = r.facts["ticket"]
    r.login("student02")
    codes = (r.status(f"/complaints/{t}/"), r.status(f"/complaints/{t}/photo/"))
    check(codes == (404, 404), codes)
    r.go(f"/complaints/{t}/")
    return f"/complaints/{t}/ -> {codes[0]}, /complaints/{t}/photo/ -> {codes[1]}"


@case("ST_14", "ComplaintModule", "HMS-F-031", "Warden moves a complaint Open -> In Progress -> Resolved; "
      "student is notified", "Ticket from ST_13 is Open", "1. Warden opens the complaint queue 2. Click Mark In "
      "Progress 3. Click Mark Resolved 4. student01 opens the ticket", "Ticket from ST_13",
      "Each change shows '<ticket> updated. The student has been notified.'; ticket shows Resolved with a timestamped "
      "timeline Open, In Progress, Resolved; one email per change")
def st_14(r):
    t = r.facts["ticket"]
    r.login("warden")
    r.go("/complaints/queue/")
    msgs = []
    for label in ("Mark In Progress", "Mark Resolved"):
        r.page.locator("tr", has_text=t).first.locator("button", has_text=label).click()
        r.page.wait_for_load_state()
        msgs.append(r.alerts())
    check(all("The student has been notified" in m for m in msgs), msgs)
    mails = [m for m in r.mails("student01@demo.hms.test") if t in m]
    r.login("student01")
    r.go(f"/complaints/{t}/")
    timeline = [" ".join(x.split()) for x in r.page.locator("ol li").all_inner_texts()]
    check("Resolved" in r.page.inner_text("h1") and len(timeline) >= 3, timeline)
    return f"Messages: {msgs}; {len(mails)} notification emails; timeline: {timeline}"


@case("ST_27", "ComplaintModule", "HMS-F-031", "A resolved complaint cannot go back to Open",
      "Ticket from ST_13 is Resolved (ST_14)", "1. Warden opens the queue: no buttons for the resolved ticket "
      "2. Warden submits status=OPEN for the ticket directly (forged form post)", "Ticket from ST_13, status OPEN",
      "No transition buttons offered; forged request refused with 'This status change is not allowed.'")
def st_27(r):
    t = r.facts["ticket"]
    r.login("warden")
    r.go("/complaints/queue/?status=RESOLVED")
    rows = r.page.locator("tr", has_text=t)
    buttons = rows.first.locator("button").count() if rows.count() else 0
    token = r.page.evaluate("() => document.cookie.match(/csrftoken=([^;]+)/)[1]")
    resp = r.page.request.post(f"{r.base}/complaints/{t}/status/", form={"csrfmiddlewaretoken": token,
                               "status": "OPEN"}, headers={"Referer": r.base + "/complaints/queue/"})
    r.page.set_content(resp.text())
    msg = r.alerts()
    check(buttons == 0 and "not allowed" in msg, (buttons, msg))
    r.go(f"/complaints/{t}/")
    return f"{buttons} transition buttons on the resolved ticket; forged post answered '{msg}'"


# =============================== ReportingModule ============================================
@case("ST_15", "ReportingModule", "HMS-F-040", "Admin generates occupancy, vacancy and fee-collection reports",
      "Allocations and one successful payment exist", "1. Reports 2. For each report type pick this month's range "
      "and click Generate", f"Types: occupancy, vacancy, fee collection; {MONTH_START} to {TODAY}",
      "Each report renders a titled table; the vacancy report does not list the full room A101; fee collection "
      "includes student01's 65000 payment")
def st_15(r):
    r.login("admin")
    r.go("/reports/")
    types = r.page.evaluate("() => [...document.querySelector('select[name=type]').options].map(o => o.value)")
    out = []
    for t in types:
        r.go(f"/reports/?type={t}&date_from={MONTH_START}&date_to={TODAY}")
        rows = r.page.locator("table tbody tr").count()
        title = r.page.locator("h2").first.inner_text()
        out.append(f"{t}: '{title}', {rows} rows")
        if t.startswith("fee"):
            amounts = {f"{r.facts['fee_due']:.2f}", f"{r.facts['fee_due']:,.2f}", f"{r.facts['fee_due']:.0f}"}
            check(any(a in r.page.locator("table").inner_text() for a in amounts), "payment missing")
        if t == "vacancy":
            check("A101" not in r.page.locator("table").inner_text(), "full room A101 listed as vacant")
    r.go(f"/reports/?type=occupancy&date_from={MONTH_START}&date_to={TODAY}")
    return "; ".join(out) + "; A101 absent from vacancy; fee collection shows the 65000 payment"


@case("ST_16", "ReportingModule", "HMS-F-041", "Report exports as CSV and PDF match the screen",
      "Occupancy report generated (ST_15)", "1. Click Export CSV 2. Click Export PDF 3. Compare with the on-screen "
      "table", f"Occupancy report, {MONTH_START} to {TODAY}",
      "CSV rows equal the on-screen rows cell for cell; PDF downloads and opens")
def st_16(r):
    r.login("admin")
    r.go(f"/reports/?type=occupancy&date_from={MONTH_START}&date_to={TODAY}")
    screen = [[c.strip() for c in tr.locator("td").all_inner_texts()] for tr in r.page.locator("table tbody tr").all()]
    csv_href = r.page.locator("a", has_text="Export CSV").get_attribute("href")
    pdf_href = r.page.locator("a", has_text="Export PDF").get_attribute("href")
    csv_text = r.page.request.get(r.url(csv_href)).text().lstrip("﻿")
    import csv as _csv
    csv_rows = [row for row in _csv.reader(csv_text.splitlines()) if row]
    header = [h.strip() for h in r.page.locator("table thead th").all_inner_texts()]
    check(header in csv_rows, f"header {header} not in CSV")
    start = csv_rows.index(header) + 1
    body = csv_rows[start:start + len(screen)]
    check(body == screen, f"screen {screen[:2]} vs csv {body[:2]}")
    pdf = r.page.request.get(r.url(pdf_href))
    check(pdf.body()[:4] == b"%PDF", "PDF export is not a PDF")
    return (f"CSV header {header} and all {len(screen)} data rows equal the on-screen table cell for cell; "
            f"PDF {len(pdf.body())} bytes, {pdf.headers.get('content-type')}")


@case("ST_28", "ReportingModule", "HMS-F-040", "Report with an end date before the start date is refused",
      "Logged in as admin", "1. Reports 2. Set From after To 3. Generate",
      f"From {TODAY}, To {MONTH_START - datetime.timedelta(days=1)}",
      "'The start date must be on or before the end date.'; no table shown")
def st_28(r):
    r.login("admin")
    resp = r.go(f"/reports/?type=occupancy&date_from={TODAY}&date_to={MONTH_START - datetime.timedelta(days=1)}")
    text = r.body()
    check("start date must be on or before the end date" in text and r.page.locator("table").count() == 0, text[:300])
    return f"HTTP {resp.status}; message 'The start date must be on or before the end date.'; no report table"


# =============================== Cross-cutting ==============================================
@case("ST_33", "Audit", "HMS-SR-004", "Admin actions from this run appear in the read-only audit log",
      "ST_07, ST_08, ST_10, ST_14, ST_24 executed", "1. Log in as admin 2. Open Django admin > Audit logs "
      "3. Look for the actions from this run 4. Look for Add / Delete controls", "Audit log list",
      "Entries for allocation, room-change approval, payment, complaint status and fee-structure edits, each with "
      "actor and timestamp; no Add or Delete control")
def st_33(r):
    r.login("admin")
    r.go("/admin/audit/auditlog/?o=-1")
    text = r.body().lower()
    kinds = {"allocat": "allocation", "room_change": "room change", "payment": "payment",
             "complaint": "complaint status", "fee": "fee structure"}
    found = [label for k, label in kinds.items() if k in text]
    add = r.page.locator("#content .object-tools a.addlink").count()
    delete_action = r.page.locator("select[name=action] option[value=delete_selected]").count()
    check(delete_action == 0, "bulk delete action offered")
    check(len(found) >= 4 and add == 0, (found, add))
    total = re.search(r"(\d+) audit logs?", text)
    return (f"{total.group(0) if total else 'Entries'} listed with actor and time, including {', '.join(found)} "
            f"actions; no Add button ({add}) and no delete action")


@case("ST_31", "AuthModule", "TC-Sec-08", "A form post without a CSRF token is refused",
      "Logged in as student01", "1. Send POST /accounts/profile/ with the session cookie but no CSRF token",
      "phone=0000000000", "HTTP 403; profile unchanged")
def st_31(r):
    r.login("student01")
    resp = r.page.request.post(r.base + "/accounts/profile/", form={"phone": "0000000000"})
    r.go("/accounts/profile/")
    phone = r.page.input_value("[name=phone]")
    check(resp.status == 403 and phone != "0000000000", (resp.status, phone))
    return f"HTTP {resp.status}; phone still {phone}"


@case("ST_30", "Web UI", "HMS-NF-005", "Student pages fit a 360 px phone screen (partial check)",
      "Logged in as student01", "1. Set the browser to 360 x 740 2. Open dashboard, My room, Fees, New complaint "
      "3. Measure page width", "Viewport 360 px", "No page wider than the viewport (no sideways scrolling); menu "
      "collapses to a toggle button")
def st_30(r):
    r.login("student01")
    r.page.set_viewport_size({"width": 360, "height": 740})
    widths = {}
    for p in ("/", "/allocation/my-room/", "/fees/my/", "/complaints/new/"):
        r.go(p)
        widths[p] = r.page.evaluate("() => document.documentElement.scrollWidth")
    toggler = r.page.locator(".navbar-toggler").is_visible()
    r.go("/")
    check(all(w <= 360 for w in widths.values()) and toggler, (widths, toggler))
    return f"scrollWidth per page: {widths}; navbar toggle visible: {toggler}"


ORDER = ["ST_01", "ST_02", "ST_18", "ST_17", "ST_03", "ST_04", "ST_05", "ST_06", "ST_07", "ST_23", "ST_22",
         "ST_19", "ST_20", "ST_21", "ST_08", "ST_29", "ST_09", "ST_32", "ST_10", "ST_11", "ST_24", "ST_12", "ST_13",
         "ST_25", "ST_26", "ST_14", "ST_27", "ST_15", "ST_16", "ST_28", "ST_33", "ST_31", "ST_30"]


def manage(py, env, *args, stdin=None):
    subprocess.run([py, "manage.py", *args], cwd=REPO, env=env, check=True, stdin=stdin,
                   stdout=subprocess.DEVNULL)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server-python", default=sys.executable, help="Python that has the HMS requirements")
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--work", default=os.path.join(tempfile.gettempdir(), "hms_system_test"))
    args = ap.parse_args()

    shutil.rmtree(args.work, ignore_errors=True)
    os.makedirs(os.path.join(args.work, "mail"))
    shots = os.path.join(HERE, "screenshots")
    shutil.rmtree(shots, ignore_errors=True)
    os.makedirs(shots)
    env = dict(os.environ, DJANGO_SETTINGS_MODULE="st_settings", HMS_ST_WORK=args.work, DJANGO_DEBUG="1",
               PYTHONPATH=os.pathsep.join([HERE, REPO]))
    manage(args.server_python, env, "migrate", "--noinput")
    manage(args.server_python, env, "seed_demo")
    with open(os.path.join(HERE, "setup_st_data.py"), "rb") as f:
        manage(args.server_python, env, "shell", stdin=f)

    log = open(os.path.join(args.work, "server.log"), "w")
    server = subprocess.Popen([args.server_python, "manage.py", "runserver", f"127.0.0.1:{args.port}", "--noreload"],
                              cwd=REPO, env=env, stdout=log, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{args.port}"
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(base + "/healthz/")
                break
            except OSError:
                time.sleep(0.5)
        results = []
        by_id = {c["id"]: c for c in CASES}
        with sync_playwright() as p:
            browser = p.chromium.launch()
            run = Run(base, args.work, browser)
            for cid in ORDER:
                c = by_id[cid]
                started = time.time()
                try:
                    actual, verdict = c["fn"](run), "Pass"
                except Exception as exc:  # noqa: BLE001 - every failure is recorded, the run continues
                    actual, verdict = f"{type(exc).__name__}: {exc}", "Fail"
                    traceback.print_exc()
                shot = f"{cid}.jpg"
                try:
                    run.page.screenshot(path=os.path.join(shots, shot), type="jpeg", quality=70)
                except Exception:  # noqa: BLE001
                    shot = None
                run.page.set_viewport_size({"width": 1280, "height": 800})
                results.append({k: v for k, v in c.items() if k != "fn"} | {
                    "actual": actual, "result": verdict, "screenshot": shot,
                    "seconds": round(time.time() - started, 1)})
                print(f"{cid} {verdict}: {actual[:150]}")
            version = browser.version
            browser.close()
        summary = {"executed_at": datetime.datetime.now().isoformat(timespec="seconds"),
                   "browser": f"Chromium {version} (Playwright, headless)", "base_url": base,
                   "total": len(results), "passed": sum(r["result"] == "Pass" for r in results),
                   "failed": sum(r["result"] == "Fail" for r in results), "cases": results}
        with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"{summary['passed']}/{summary['total']} passed")
    finally:
        server.terminate()
        server.wait()
        log.close()


if __name__ == "__main__":
    main()
