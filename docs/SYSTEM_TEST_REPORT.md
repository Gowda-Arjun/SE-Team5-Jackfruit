# System Test Report: Team 5 HMS

STP v1.0 Section 5.2 **System** level and the course deliverable *System Validation: validation report* (Jackfruit guidelines, Phase 4). Black-box, end-to-end journeys through a real web browser, covering both actors of SRS Section 7.1 (Student; Warden/Admin, with the Technician sub-role), including negative paths and the error messages named in the acceptance criteria. Unit and integration results are in [UNIT_TEST_REPORT.md](UNIT_TEST_REPORT.md); the overall verdict is in [TEST_REPORT.md](TEST_REPORT.md).

| | |
|---|---|
| Build under test | `main` at `0c91b99` (frozen feature set) |
| Executed | 2026-11-16 09:06:29 (local time) |
| Browser | Chromium 159.0.8154.6 (Playwright, headless), 1280 x 800 (ST_30 at 360 x 740) |
| Server | Django 5.1.15 `runserver` on Windows 11, Python 3.12.7, fresh SQLite database; mock payment gateway (D8); file email backend standing in for MailHog |
| Executed by | Arnav Sharath Hanchanur (Test Lead), scripted run |
| Script and evidence | [`test-evidence/system/run_system_tests.py`](test-evidence/system/run_system_tests.py), [`results.json`](test-evidence/system/results.json), one screenshot per case in [`test-evidence/system/screenshots/`](test-evidence/system/screenshots/) |

## 1. Summary

| Metric | Result |
|---|---|
| System test cases executed | **33** of 33 planned (100%) |
| Passed | **33** |
| Failed | **0** |
| Functional requirements covered end to end | **20 of 20** |
| Also exercised | HMS-SR-003 (RBAC), HMS-SR-004 (audit), HMS-SR-005 (no card data), HMS-NF-003 (IDOR), HMS-NF-005 (360 px, partial), TC-Sec-08 (CSRF), TC-Sec-09 (uploads) |
| Defects raised | 1 new, Severity 4 (DEF-ST-01, Section 6); 0 Severity 1-3 |

## 2. Approach

- **Use-case based** (STP 5.4): each case is one actor journey from SRS Section 7.1, run through the UI exactly as a user would: open the page, fill the form, click the button, read what is shown. Negative cases try what a user should not be able to do (wrong password, foreign ticket id, typed admin URL, forged form post, a second admin taking the last bed).
- **Black-box.** Expected results come from the SRS acceptance criteria and the on-screen messages; the script reads the page, never the database. HTTP status codes are checked for denials (403/404).
- **Tool.** The STP planned Selenium WebDriver. The same journeys are driven with Playwright for Python (Chromium), which needs no separate driver binary. It is the same black-box browser automation; recorded as an update to [DEVIATIONS.md](DEVIATIONS.md) D13.
- **One shared dataset per run.** Cases run in a fixed order and later cases build on earlier ones (e.g. ST_11 downloads the receipt of the payment made in ST_10). The order is the `ORDER` list in the script.
- **Evidence.** Each case ends with a screenshot of the final screen (`screenshots/ST_nn.jpg`); the actual result recorded below is what the script read from the page at that moment.

## 3. Environment, test data and pre-conditions

The runner builds everything from scratch, so the run is repeatable (STP 6.3):

1. New SQLite database in a temp folder (`st_settings.py`), `migrate`.
2. `seed_demo`: `admin`, `warden`, `student01`-`student10` (01-05 male, 06-10 female), Block A (male) and Block B (female) with rooms x101 (single, capacity 1) and x102-x105 (shared, capacity 2), fee structures for term 2026-ODD (Single, Shared). All data synthetic; password `Hostel@Demo2026`.
3. [`setup_st_data.py`](test-evidence/system/setup_st_data.py): student01 and student04 in A103 (roommates), student03 in A102 with an overdue statement (a defaulter), Technician account `tech01`.
4. `runserver` with `PAYMENT_GATEWAY=mock` and emails written to files (read by the script for the OTP and complaint notifications, as a tester would read MailHog).

## 4. Traceability: requirement to system test case

| Req ID | Requirement | System test case(s) | Result |
|---|---|---|---|
| HMS-F-001 | Log in with role | ST_01, ST_02, ST_18, ST_19 | Pass |
| HMS-F-002 | Student profile update | ST_03 | Pass |
| HMS-F-003 | OTP password reset (10 min) | ST_04 | Pass |
| HMS-F-004 | Session timeout (20 min) | ST_05 | Pass |
| HMS-F-005 | RBAC: 403 and logged | ST_17, ST_18 | Pass |
| HMS-F-010 | View own room and roommates | ST_06 | Pass |
| HMS-F-011 | Admin CRUD on student records | ST_19 | Pass |
| HMS-F-012 | Allocate / reallocate room | ST_07, ST_22, ST_23 | Pass |
| HMS-F-013 | Room-change request and approval | ST_08, ST_29 | Pass |
| HMS-F-014 | Manage blocks, rooms, capacity | ST_20, ST_21 | Pass |
| HMS-F-015 | Prevent over-allocation | ST_22 | Pass |
| HMS-F-020 | Itemised fee statement | ST_09 | Pass |
| HMS-F-021 | Online fee payment (sandbox) | ST_10, ST_32 | Pass |
| HMS-F-022 | Fee structure per term | ST_24 | Pass |
| HMS-F-023 | PDF payment receipt | ST_11 | Pass |
| HMS-F-024 | Reconcile payments / defaulters | ST_12 | Pass |
| HMS-F-030 | Raise maintenance complaint | ST_13, ST_25 | Pass |
| HMS-F-031 | Complaint status workflow | ST_14, ST_27 | Pass |
| HMS-F-040 | Occupancy / vacancy / fee reports | ST_15, ST_28 | Pass |
| HMS-F-041 | CSV and PDF export | ST_16 | Pass |
| HMS-NF-003 | Data protection, no card data | ST_26 | Pass |
| HMS-NF-005 | Responsive, WCAG 2.1 AA | ST_30 | Pass |
| HMS-SR-003 | RBAC at view layer | ST_11, ST_17, ST_26 | Pass |
| HMS-SR-004 | Immutable audit log | ST_33 | Pass |
| HMS-SR-005 | Gateway only, no card data | ST_10 | Pass |

Not executed at system level: HMS-NF-001 and HMS-NF-006 (load and scale runs, see [TEST_REPORT.md](TEST_REPORT.md) Section 6), HMS-NF-002 (health check and restart policy, partial by design), HMS-NF-004 (archive/restore, integration level), HMS-SR-001 (no TLS host, D6), HMS-SR-002 (hash format is not visible in the UI; unit level).

## 5. Test cases and results

Course test-case template (Jackfruit Phase-3): Test Case ID, Name of Module, Test case description, Pre-conditions, Test Steps, Test data, Expected Results, Actual Result, Test Result.

### 5.1 AuthModule

| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |
|---|---|---|---|---|---|---|---|---|
| ST_01 | AuthModule | Student logs in with valid credentials and lands on the Student dashboard (HMS-F-001) | Seeded account student01 exists and is active | 1. Open /accounts/login/<br>2. Enter username and password<br>3. Click Log in | Username: student01, Password: Hostel@Demo2026 | Login succeeds; Student dashboard 'Welcome, Student 01' with My room, Fees and Complaints cards | Redirected to / with heading 'Welcome, Student 01'; cards shown: My room, Fees, Complaints | **[Pass](test-evidence/system/screenshots/ST_01.jpg)** |
| ST_02 | AuthModule | Login with a wrong password is refused (HMS-F-001) | Seeded account student01 exists | 1. Open /accounts/login/<br>2. Enter student01 with a wrong password<br>3. Click Log in | Username: student01, Password: WrongPass@1 | Stays on the login page with an error message; no session is created | Stayed on /accounts/login/; message: 'Please enter a correct username and password. Note that both fields may be case-sensitive.'; /fees/my/ still redirects to login | **[Pass](test-evidence/system/screenshots/ST_02.jpg)** |
| ST_03 | AuthModule | Student updates own profile (HMS-F-002) | Logged in as student01 | 1. Open My profile<br>2. Change phone and address<br>3. Click Save<br>4. Reload the page | Phone: 9123456780, Address: Room A103, PES Hostel, Bengaluru | 'Your profile was updated successfully.' shown; new values still there after reload | Message 'Your profile was updated successfully.'; after reload phone=9123456780, address='Room A103, PES Hostel, Bengaluru' | **[Pass](test-evidence/system/screenshots/ST_03.jpg)** |
| ST_04 | AuthModule | Password reset with emailed OTP; OTP is single use (HMS-F-003) | student05 has a registered email; email delivery captured to files (stands in for MailHog) | 1. Open Forgot password, enter email<br>2. Read the OTP from the email<br>3. Enter email, OTP and new password twice<br>4. Log in with the new password<br>5. Try the same OTP again<br>6. Try the old password | Email: student05@demo.hms.test, New password: Hostel@Reset2026 | OTP email received; reset succeeds; login works with new password; reused OTP refused; old password refused | OTP 033464 emailed; reset done and new password logs in; reusing the OTP shows 'Invalid or expired OTP. Request a new one and try again.' and the password is unchanged; old password refused | **[Pass](test-evidence/system/screenshots/ST_04.jpg)** |
| ST_05 | AuthModule | Session expires 20 minutes after the last request; logout ends it (HMS-F-004) | Logged in as student01 | 1. Log in<br>2. Inspect the session cookie expiry<br>3. Open a page and inspect again<br>4. Click Log out<br>5. Open /fees/my/ | student01 | Session cookie expires 20 min after each request (sliding); after logout the fee page redirects to login | Cookie TTL 1200s after login and 1200s after a later request (refreshed); HttpOnly; after logout /fees/my/ redirects to /accounts/login/?next=/fees/my/ | **[Pass](test-evidence/system/screenshots/ST_05.jpg)** |
| ST_17 | AuthModule | Student cannot open Warden/Admin pages (vertical escalation) (HMS-F-005, HMS-SR-003) | Logged in as student01 | 1. Log in as student01<br>2. Type each Admin/Warden URL into the address bar | /reports/, /allocation/rooms/, /allocation/students/, /allocation/allocate/, /fees/structures/, /fees/reconciliation/, /complaints/queue/, /allocation/room-change-queue/ | Every URL returns HTTP 403 Forbidden | All 8 URLs returned 403 | **[Pass](test-evidence/system/screenshots/ST_17.jpg)** |
| ST_18 | AuthModule | Each staff role lands on the right dashboard; Technician is kept out of admin pages (HMS-F-001, HMS-F-005) | Seeded admin, warden; tech01 created by setup_st_data.py | 1. Log in as admin, read the dashboard heading<br>2. Repeat as warden<br>3. Log in as tech01 and open /reports/, /allocation/rooms/ and /complaints/queue/ | admin, warden, tech01 / Hostel@Demo2026 | Admin and Warden see 'Warden / Admin dashboard'; Technician gets 403 on reports and rooms and 200 on the complaint queue | admin: 'Warden / Admin dashboard'; warden: 'Warden / Admin dashboard'; tech01 HTTP codes: {'/reports/': 403, '/allocation/rooms/': 403, '/complaints/queue/': 200} | **[Pass](test-evidence/system/screenshots/ST_18.jpg)** |
| ST_31 | AuthModule | A form post without a CSRF token is refused (TC-Sec-08) | Logged in as student01 | 1. Send POST /accounts/profile/ with the session cookie but no CSRF token | phone=0000000000 | HTTP 403; profile unchanged | HTTP 403; phone still 9123456780 | **[Pass](test-evidence/system/screenshots/ST_31.jpg)** |

### 5.2 AllocationModule

| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |
|---|---|---|---|---|---|---|---|---|
| ST_06 | AllocationModule | Student views own room and roommates (HMS-F-010) | student01 and student04 allocated to A103 (setup_st_data.py) | 1. Log in as student01<br>2. Open My room | student01 | Block A, Room A103, Shared, roommate 'Demo Student 04' | Shows 'Block A · Room A103', type Shared, roommate Demo Student 04 | **[Pass](test-evidence/system/screenshots/ST_06.jpg)** |
| ST_07 | AllocationModule | Admin allocates a room; occupancy updates (HMS-F-012) | Logged in as admin; student02 has no room; A104 empty | 1. Open Allocate room<br>2. Choose student and room<br>3. Click Allocate<br>4. Open Rooms | Student: Demo Student 02, Room: Block A Room A104 | 'Room A104 in Block A successfully allocated to Demo Student 02.'; A104 occupancy 1 of 2 | Message 'Room A104 in Block A successfully allocated to Demo Student 02.'; room list row: Block A A104 1 Shared 2 1 / 2 Active Edit Deactivate | **[Pass](test-evidence/system/screenshots/ST_07.jpg)** |
| ST_08 | AllocationModule | Student requests a room change; Warden approves it (HMS-F-013) | student01 in A103; A105 empty | 1. student01 opens Request Room Change, picks A105, gives a reason, submits<br>2. Warden opens the room-change queue and clicks Approve<br>3. student01 opens My room | Preferred room: Block A Room A105, Reason: Closer to the study hall | Request shown as Pending; Warden sees 'Room change request #n has been approved.'; student01 now in A105 | Student: 'Room change request submitted successfully.' (Pending). Warden: 'Room change request #1 has been approved.'. My room now shows Room A105 | **[Pass](test-evidence/system/screenshots/ST_08.jpg)** |
| ST_19 | AllocationModule | Admin creates, edits and deactivates student records; new student sets a password by OTP and logs in (HMS-F-011, HMS-F-001) | Logged in as admin | 1. Add Student with the data shown<br>2. Search by roll number<br>3. Edit phone<br>4. New student uses Forgot password to set a password and logs in<br>5. Admin deactivates student10<br>6. student10 tries to log in | Roll: ST2026001, Email: st.newstudent@demo.hms.test, Name: System Test Student, Gender: M, Phone (edit): 9988776655 | Record created and listed; edit saved; new student logs in to the Student dashboard; deactivated student10 is hidden from the list and cannot log in | 'Student record created for System Test Student (ST2026001).'; edit: 'Student record for System Test Student updated successfully.'; new student set a password by OTP and saw 'Welcome, ST2026001'; 'Student DEMO2026010 has been deactivated.'; student10 hidden from the list and login refused | **[Pass](test-evidence/system/screenshots/ST_19.jpg)** |
| ST_20 | AllocationModule | Admin creates a block and a room; invalid rooms are refused (HMS-F-014) | Logged in as admin | 1. Add Block<br>2. Add Room in the new block<br>3. Add the same room number again<br>4. Add a room with capacity 0 | Block C (Male); Room C201, floor 2, Shared, capacity 2; duplicate C201; C202 with capacity 0 | Block and room created with success messages; duplicate refused with 'A room with this number already exists in this block.'; capacity 0 refused | 'Block 'Block C' created successfully.'; 'Room C201 created successfully.'; duplicate: 'A room with this number already exists in this block.'; capacity 0: 'Capacity must be at least 1.' | **[Pass](test-evidence/system/screenshots/ST_20.jpg)** |
| ST_21 | AllocationModule | Admin deactivates a room; it is no longer offered for allocation (HMS-F-014) | Room C201 exists and is empty (ST_20) | 1. Open Rooms<br>2. Click Deactivate on C201 and confirm<br>3. Open Allocate room | Room C201 | 'Room C201 has been deactivated.'; C201 missing from the room choices | 'Room C201 has been deactivated.'; C201 not in the allocate form's room list | **[Pass](test-evidence/system/screenshots/ST_21.jpg)** |
| ST_22 | AllocationModule | Two admins race for the last bed; the second is refused (HMS-F-015, HMS-F-012) | Logged in as admin; single room A101 (capacity 1) is empty | 1. Admin opens Allocate room and selects student05 + A101<br>2. Before submitting, a second admin session allocates student02 to A101<br>3. First admin clicks Allocate<br>4. Open Rooms | Room A101 (Single, capacity 1); students Demo Student 05 and Demo Student 02 | Second allocation refused with a clear error; A101 shows occupancy 1 of 1, never 2 | Second submit refused: 'Select a valid choice. That choice is not one of the available choices.'. Room list: Block A A101 1 Single 1 1 / 1 Active Edit Deactivate. A101 no longer offered in the room list | **[Pass](test-evidence/system/screenshots/ST_22.jpg)** |
| ST_23 | AllocationModule | Allocation that breaks the block gender policy is refused (HMS-F-012) | Logged in as admin; Block B is Female only | 1. Open Allocate room<br>2. Choose a male student and a Block B room<br>3. Click Allocate | Student: Demo Student 05 [M], Room: Block B Room B102 | 'This block is not available for this student.'; no allocation made | Refused with 'This block is not available for this student.'; still on the allocate page | **[Pass](test-evidence/system/screenshots/ST_23.jpg)** |
| ST_29 | AllocationModule | Warden rejects a room-change request; allocation unchanged (HMS-F-013) | student04 in A103 | 1. student04 requests A104<br>2. Warden clicks Reject<br>3. student04 opens My room and the request page | Preferred room: Block A Room A104, Reason: Quieter floor | 'Room change request #n has been rejected.'; student04 still in A103; request shows Rejected | Warden: 'Room change request #2 has been rejected.'. student04 still in Room A103; request listed as Rejected | **[Pass](test-evidence/system/screenshots/ST_29.jpg)** |

### 5.3 FeeModule

| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |
|---|---|---|---|---|---|---|---|---|
| ST_09 | FeeModule | Student views an itemised fee statement (HMS-F-020) | student01 allocated (shared room); 2026-ODD fee structure seeded | 1. Log in as student01<br>2. Open Fees | student01 | Row for 2026-ODD 'Hostel fee (Shared)' with amount due, amount paid 0, balance = due - paid, due date | Term 2026-ODD, Hostel fee (Shared), due 65000.00, paid 0.00, balance 65000.00, due date Dec. 16, 2026 | **[Pass](test-evidence/system/screenshots/ST_09.jpg)** |
| ST_10 | FeeModule | Student pays the fee through the sandbox gateway (HMS-F-021, HMS-SR-005) | student01 has a balance | 1. Fees > Pay now<br>2. On the sandbox checkout click 'Pay (test)' (signed webhook returns to HMS)<br>3. Return to Fees | Mock gateway outcome: SUCCESS for the full balance | Checkout page has no card fields; amount paid = amount due; balance 0.00 | Checkout had 0 card inputs; after the signed webhook: paid 65000.00, balance 0.00 | **[Pass](test-evidence/system/screenshots/ST_10.jpg)** |
| ST_11 | FeeModule | Student downloads the PDF receipt; another student cannot (HMS-F-023, HMS-SR-003) | student01 has a successful payment (ST_10) | 1. Fees > Download receipt for the paid attempt<br>2. Log in as student02 and open the same receipt URL | Receipt URL of student01's successful payment | student01 gets a PDF file; student02 gets 404 (no information leak) | /fees/payments/2/receipt/ returned application/pdf (1867 bytes, starts with %PDF); student02 on the same URL: HTTP 404 | **[Pass](test-evidence/system/screenshots/ST_11.jpg)** |
| ST_12 | FeeModule | Admin reconciles payments against the gateway ledger and sees defaulters (HMS-F-024) | student01 paid (ST_10); student03 statement overdue (setup) | 1. Log in as admin<br>2. Open Reconciliation for this month | Date range 2026-11-01 to 2026-11-16 | Matched payments >= 1, no mismatches; Defaulters table lists DEMO2026003 | 'Matched payments: 1'; Defaulters table includes DEMO2026003 (student03) | **[Pass](test-evidence/system/screenshots/ST_12.jpg)** |
| ST_24 | FeeModule | Warden configures fee structures; invalid entries refused; existing statements keep their amount (HMS-F-022) | Logged in as warden; student03 already has a 2026-ODD statement | 1. Note student03's amount due<br>2. New fee structure for 2026-EVEN<br>3. Try a duplicate 2026-ODD Shared<br>4. Try amount 0<br>5. Edit 2026-ODD Shared amount +1000<br>6. student03 re-opens Fees | 2026-EVEN / Single / 52000 / due 2027-03-31 / from 2027-01-01; duplicate 2026-ODD Shared; amount 0 | 'Fee structure created.'; duplicate and zero amount refused with errors; 'Fee structure updated.'; student03's amount due unchanged | 'Fee structure created.'; duplicate refused: 'Fee structure with this Term and Room type already exists.'; amount 0 refused: 'Constraint “fees_structure_amount_positive” is violated.'; 'Fee structure updated.' (65000.00 -> 66000.00); student03 amount due stayed 65000.00 | **[Pass](test-evidence/system/screenshots/ST_24.jpg)** |
| ST_32 | FeeModule | A failed gateway payment leaves the balance unchanged (HMS-F-021) | student01 has a balance | 1. Fees > Pay now<br>2. On the sandbox checkout click 'Fail (test)'<br>3. Return to Fees | Mock gateway outcome: FAILED | Balance and amount paid unchanged; no receipt can be downloaded for the failed attempt | Balance stayed 65000.00, paid stayed 0.00; no 'Download receipt' link offered for the failed attempt | **[Pass](test-evidence/system/screenshots/ST_32.jpg)** |

### 5.4 ComplaintModule

| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |
|---|---|---|---|---|---|---|---|---|
| ST_13 | ComplaintModule | Student raises a maintenance complaint with a photo (HMS-F-030) | Logged in as student01 | 1. Complaints > New<br>2. Choose category, type description, attach photo<br>3. Submit<br>4. Open My complaints | Category: Plumbing, Description: Bathroom tap in A105 is leaking, Photo: tap.png (valid 1x1 PNG) | 'Complaint CMP-nnnnnn raised. Status: Open.' with a new ticket id; ticket listed as Open | 'Complaint CMP-000001 raised. Status: Open.'; My complaints row: CMP-000001 Plumbing Bathroom tap in A105 is leaking Open 16 Nov 2026, 09:06 | **[Pass](test-evidence/system/screenshots/ST_13.jpg)** |
| ST_14 | ComplaintModule | Warden moves a complaint Open -> In Progress -> Resolved; student is notified (HMS-F-031) | Ticket from ST_13 is Open | 1. Warden opens the complaint queue<br>2. Click Mark In Progress<br>3. Click Mark Resolved<br>4. student01 opens the ticket | Ticket from ST_13 | Each change shows '<ticket> updated. The student has been notified.'; ticket shows Resolved with a timestamped timeline Open, In Progress, Resolved; one email per change | Messages: ['CMP-000001 updated. The student has been notified.', 'CMP-000001 updated. The student has been notified.']; 2 notification emails; timeline: ['Open · 16 Nov 2026, 09:06', 'In Progress · 16 Nov 2026, 09:06', 'Resolved · 16 Nov 2026, 09:06'] | **[Pass](test-evidence/system/screenshots/ST_14.jpg)** |
| ST_25 | ComplaintModule | Unsafe complaint attachments are refused (HMS-F-030, TC-Sec-09) | Logged in as student01 | 1. Complaints > New<br>2. Attach each bad file<br>3. Submit | notes.png (text file renamed to .png); run.exe; photo.gif | Each upload refused with 'This file type or size is not allowed. Use a JPG or PNG image of 5 MB or less.' | notes.png: refused; run.exe: refused; photo.gif: refused (message: 'This file type or size is not allowed...') | **[Pass](test-evidence/system/screenshots/ST_25.jpg)** |
| ST_26 | ComplaintModule | Another student cannot open a complaint or its photo (IDOR) (HMS-NF-003, HMS-SR-003) | Ticket from ST_13 belongs to student01 | 1. Log in as student02<br>2. Open /complaints/<ticket>/ and /complaints/<ticket>/photo/ | Ticket id of student01's complaint | Both return 404 Not Found | /complaints/CMP-000001/ -> 404, /complaints/CMP-000001/photo/ -> 404 | **[Pass](test-evidence/system/screenshots/ST_26.jpg)** |
| ST_27 | ComplaintModule | A resolved complaint cannot go back to Open (HMS-F-031) | Ticket from ST_13 is Resolved (ST_14) | 1. Warden opens the queue: no buttons for the resolved ticket<br>2. Warden submits status=OPEN for the ticket directly (forged form post) | Ticket from ST_13, status OPEN | No transition buttons offered; forged request refused with 'This status change is not allowed.' | 0 transition buttons on the resolved ticket; forged post answered 'This status change is not allowed.' | **[Pass](test-evidence/system/screenshots/ST_27.jpg)** |

### 5.5 ReportingModule

| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |
|---|---|---|---|---|---|---|---|---|
| ST_15 | ReportingModule | Admin generates occupancy, vacancy and fee-collection reports (HMS-F-040) | Allocations and one successful payment exist | 1. Reports<br>2. For each report type pick this month's range and click Generate | Types: occupancy, vacancy, fee collection; 2026-11-01 to 2026-11-16 | Each report renders a titled table; the vacancy report does not list the full room A101; fee collection includes student01's 65000 payment | occupancy: 'Occupancy by block', 2 rows; vacancy: 'Vacant beds by room', 9 rows; fee-collection: 'Fee collection', 1 rows; defaulters: 'Fee defaulters', 1 rows; A101 absent from vacancy; fee collection shows the 65000 payment | **[Pass](test-evidence/system/screenshots/ST_15.jpg)** |
| ST_16 | ReportingModule | Report exports as CSV and PDF match the screen (HMS-F-041) | Occupancy report generated (ST_15) | 1. Click Export CSV<br>2. Click Export PDF<br>3. Compare with the on-screen table | Occupancy report, 2026-11-01 to 2026-11-16 | CSV rows equal the on-screen rows cell for cell; PDF downloads and opens | CSV header ['Block', 'Rooms', 'Beds', 'Occupied', 'Vacant', 'Occupancy %'] and all 2 data rows equal the on-screen table cell for cell; PDF 2143 bytes, application/pdf | **[Pass](test-evidence/system/screenshots/ST_16.jpg)** |
| ST_28 | ReportingModule | Report with an end date before the start date is refused (HMS-F-040) | Logged in as admin | 1. Reports<br>2. Set From after To<br>3. Generate | From 2026-11-16, To 2026-10-31 | 'The start date must be on or before the end date.'; no table shown | HTTP 400; message 'The start date must be on or before the end date.'; no report table | **[Pass](test-evidence/system/screenshots/ST_28.jpg)** |

### 5.6 Audit

| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |
|---|---|---|---|---|---|---|---|---|
| ST_33 | Audit | Admin actions from this run appear in the read-only audit log (HMS-SR-004) | ST_07, ST_08, ST_10, ST_14, ST_24 executed | 1. Log in as admin<br>2. Open Django admin > Audit logs<br>3. Look for the actions from this run<br>4. Look for Add / Delete controls | Audit log list | Entries for allocation, room-change approval, payment, complaint status and fee-structure edits, each with actor and timestamp; no Add or Delete control | 21 audit logs listed with actor and time, including allocation, room change, payment, complaint status, fee structure actions; no Add button (0) and no delete action | **[Pass](test-evidence/system/screenshots/ST_33.jpg)** |

### 5.7 Web UI

| Test Case ID | Name of Module | Test case description | Pre-conditions | Test Steps | Test data | Expected Results | Actual Result | Test Result |
|---|---|---|---|---|---|---|---|---|
| ST_30 | Web UI | Student pages fit a 360 px phone screen (partial check) (HMS-NF-005) | Logged in as student01 | 1. Set the browser to 360 x 740<br>2. Open dashboard, My room, Fees, New complaint<br>3. Measure page width | Viewport 360 px | No page wider than the viewport (no sideways scrolling); menu collapses to a toggle button | scrollWidth per page: {'/': 360, '/allocation/my-room/': 360, '/fees/my/': 360, '/complaints/new/': 360}; navbar toggle visible: True | **[Pass](test-evidence/system/screenshots/ST_30.jpg)** |

The Test Result links open the screenshot taken at the end of each case.

## 6. Defects and observations

| ID | Found in | Severity (STP 14.3) | Description | Status |
|---|---|---|---|---|
| DEF-ST-01 | ST_24 | 4 - Low | Creating a fee structure with amount 0 is correctly refused, but if the browser's `min=0.01` check is bypassed the Warden sees the raw database message *Constraint "fees_structure_amount_positive" is violated.* instead of a readable validation message such as "Amount must be greater than zero." Data stays correct; only the wording is wrong. Fix: a `clean_amount()` in `fees/forms.py` `FeeStructureForm` | Open: [MAINTENANCE_PLAN.md](MAINTENANCE_PLAN.md) M-01 |
| OBS-01 | HMS-37 demo recording (15 Nov) | 4 - Low | After a room change into a different room type, My fees labels the existing statement with the new room type but keeps the original amount. The amount is correct by design (HMS-F-022: issued statements are not re-priced); the label is misleading | Open: [MAINTENANCE_PLAN.md](MAINTENANCE_PLAN.md) M-02 |

Two problems seen during the first dry run were in the test script, not the application (error text read from the wrong CSS class; the fee report prints `65000` without decimals). They were fixed in the script before the recorded run.

## 7. Limits of this run

- **Cross-testing rule (STP 9.2).** The STP assigns system testing of each module to a member who did not build it. This recorded run was executed by the Test Lead with a script; the script and its expected results are reviewed through the pull request that adds this report, and any member can re-run it with one command (Section 8).
- **Session timeout (ST_05)** is verified by the session cookie's 20-minute sliding expiry and server-side logout, not by waiting 20 idle minutes. The idle-expiry redirect itself is covered by `test_expired_session_redirects_to_login`.
- **Payment** uses the mock gateway with HMAC-signed webhooks (D8). The Razorpay test-mode checkout was not part of this run.
- **Email** is captured by Django's file backend rather than MailHog; the HMS side (the send call and message content) is the same.
- **Responsiveness (ST_30)** checks layout width at 360 px only. The full TC-UX-01 audit (three viewports, axe, keyboard-only pass) is still not recorded, so HMS-NF-005 stays **P** in the RTM.
- SQLite and the Django development server, not PostgreSQL behind Gunicorn/Nginx (D4, D6). Database-specific behaviour (capacity constraint, audit trigger) is verified on PostgreSQL by the CI suite.

## 8. How to reproduce

```bash
pip install playwright && playwright install chromium   # once; any virtual environment
python docs/test-evidence/system/run_system_tests.py --server-python .venv/Scripts/python.exe
```

`--server-python` is the interpreter that has `requirements.txt` installed (on Linux/macOS: `.venv/bin/python`). The run takes about 90 seconds, prints one line per case, and rewrites `results.json` and `screenshots/`. It never touches the project's own `db.sqlite3` or `media/`.
