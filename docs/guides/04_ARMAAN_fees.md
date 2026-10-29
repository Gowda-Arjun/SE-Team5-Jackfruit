# Armaan: FeeModule + Payment Gateway (complete instructions)

Read `00_TEAM_WORKFLOW_read_first.md` first: install, clone, the per-issue git cycle, conflicts, the **AI prompt header** you paste before every prompt below, and the **integration contracts** (Section 6), which your model and field names must follow exactly. Arnav's reports and seed data read them.

**Your issues:**
- **Sprint 1:** HMS-14, 15, 16, 17 (10 points)
- **Sprint 2:** HMS-28, 29, 30 (16 points)

Your code lives in **`fees/`**. HMS-16 (dashboards) touches `core/` and `templates/base.html`, which are marked **SHARED**.

---

## PART A: Day 1 morning

1. Install Python 3.12, Git and VS Code, then run the `git config` commands (Section 2 of the shared guide).
2. **Start the Razorpay test account now** (needed on Day 2, and approval can take a while). Sign up at https://dashboard.razorpay.com → switch to **Test Mode** → **Settings → API Keys** → **Generate Test Key**. Keep the Key ID and Key Secret **private**: never commit them, never paste them in the group chat. They go in your local `.env` file only.
   If the signup is blocked or slow, use the **mock gateway** (C1 explains it). The demo works fully without Razorpay.
3. Wait for **"main is ready"** from Arjun, then clone and set up (Section 3 of the shared guide).

---

## PART B: Sprint 1 (Day 1 afternoon)

### B1. HMS-14 + HMS-17 (#14, #17): Fee structure; no card data. Branch `hms-14-fee-structure`
One PR whose description contains **`Closes #14`** and **`Closes #17`**.

**AI prompt:**
> In the `fees` app create `FeeStructure(term CharField e.g. "2026-ODD", room_type choices "SINGLE"/"SHARED", amount DecimalField(10,2) > 0 (CheckConstraint), due_date, effective_from)` with `UniqueConstraint(term, room_type)`. Warden/Admin pages at URL name `fees:structure_list` (list + create + edit) using `core.decorators.role_required(User.Role.ADMIN, User.Role.WARDEN)`. Every create/edit calls `audit.services.write_audit(request.user, "FEE_STRUCTURE_SAVED", structure)` inside `transaction.atomic()`. Editing a structure must **not** change any statement that is already paid (statements copy the amount when created). Register it in Django admin. Tests: create works; a duplicate term + room type is rejected; amount <= 0 is rejected; a student gets 403; an audit row is written; and **a schema test proving no model field in any HMS app is named like card, cvv, pan or expiry** (HMS-SR-005). (HMS-F-022, TC-Fee-03, TC-Sec-06)

`git add fees`

### B2. HMS-15 (#15): Itemised fee statement. Branch `hms-15-fee-statement`
Start after Arjun's HMS-11 (Allocation) is merged, because the statement needs the student's room type. Before that, you can still build it and test it with a student who has no allocation.

**AI prompt:**
> Create `FeeStatement(student FK User PROTECT, term, amount_due DecimalField, amount_paid DecimalField default 0, due_date)` with `UniqueConstraint(student, term)` and `CheckConstraint amount_paid >= 0`. In `fees/services.py` write `get_or_create_statement(student, term)`: it finds the student's ACTIVE `allocation.Allocation` (`status="ACTIVE"`), takes its `room.room_type`, finds the `FeeStructure` for that term and room type, and creates the statement with `amount_due` copied from the structure (it stays fixed after that). It raises `NoFeeStructure` if there's none. Student page at URL name `fees:my_fees` showing term, itemised lines (hostel fee for room type), amount due, amount paid, **balance = due - paid** and due date. If the student has no room yet: "No fee statement yet. You have not been allocated a room." Tests: balance is correct; it uses the right room type; a later fee-structure edit doesn't change the existing statement; a student sees only their own statement. (HMS-F-020, TC-Fee-01)

The current term can be a constant `CURRENT_TERM = "2026-ODD"` in `fees/services.py`.
`git add fees`

### B3. HMS-16 (#16): Dashboards with live data. Branch `hms-16-dashboards`
**Do this last in Sprint 1**, after Arjun's allocation, Arnav's complaints and your fee PRs are merged (`git pull` first).

**SHARED files:**
- `core/views.py` (`home` view context)
- `core/templates/core/student_dashboard.html`
- `core/templates/core/admin_dashboard.html`
- `templates/base.html` (nav links)

**AI prompt:**
> Update `core/views.py` `home` so the student dashboard gets: the active allocation (block, room, number of roommates), the current fee statement (balance, due date) and the count of the student's OPEN/IN_PROGRESS complaints. The admin dashboard gets: total beds, occupied, vacant and occupancy %, number of pending room-change requests (if that model exists), number of open complaints, and number of students with balance > 0 past the due date. Each dashboard card links to its page. In `templates/base.html`, fill `{% block nav_links %}` with role-based links: students get My room (`allocation:my_room`), Fees (`fees:my_fees`), Complaints (`complaints:my_complaints`) and Profile (`accounts:profile`); Warden/Admin get Rooms (`allocation:room_list`), Students (`allocation:student_list`), Allocate (`allocation:allocate`), Fees (`fees:structure_list`), Complaints (`complaints:queue`) and Reports (`reports:index`). Only include links whose URL names exist. Keep it mobile-friendly (360 px). Tests: the student dashboard shows the room and balance; the admin dashboard shows the occupancy numbers; the nav shows the correct links per role.

`git add core templates`

---

## PART C: Sprint 2 (Day 2)

### C1. HMS-28 (#28): Online payment through a sandbox gateway (8 SP, your biggest item). Branch `hms-28-online-payment`
Design (SAD 4.2.2): HMS never sees card data. It creates an order, the student pays on the gateway's page, and **only a verified webhook** marks the payment as successful.

**AI prompt:**
> Create `Payment(statement FK FeeStatement PROTECT, amount Decimal, status choices "PENDING"/"SUCCESS"/"FAILED", gateway_order_id unique, gateway_txn_id unique null, created_at auto_now_add, updated_at auto_now)`. Create `fees/gateway.py` with an adapter interface `PaymentGateway` with `create_order(amount, payment_id) -> (order_id, checkout_url)`, `verify_signature(body: bytes, signature: str) -> bool` and `fetch_ledger(date_from, date_to) -> list`. Give it two implementations chosen by setting `PAYMENT_GATEWAY` ("mock" or "razorpay"): **MockGateway** (default) returns a local checkout URL `fees:mock_checkout` that shows "Pay (test)" / "Fail (test)" buttons. These post a webhook to our own endpoint signed with HMAC-SHA256 using `PAYMENT_WEBHOOK_SECRET`. **RazorpayGateway** uses the `razorpay` package in test mode with keys from environment variables `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` and verifies the `X-Razorpay-Signature` header. Student "Pay now" (URL name `fees:pay`, POST) creates a PENDING Payment for the balance and redirects to the checkout URL; if the balance is 0, show "There are no dues to pay for this term." The webhook view `fees:webhook` (csrf_exempt, POST only) does: invalid signature → 400 and audit DENIED; unknown order → 404; amount mismatch → 400; an already-SUCCESS order → 200 and changes nothing (idempotent); otherwise, in one transaction with `select_for_update`, set SUCCESS + txn id, add to `statement.amount_paid`, and write an audit entry; then after commit, email a confirmation. Tests: happy path updates the balance; bad signature is rejected; a replayed webhook credits only once; amount mismatch is rejected; a FAILED webhook leaves the balance unchanged; no card fields exist. (HMS-F-021, TC-Fee-02, TC-Sec-10)

**SHARED, append at the end of `config/settings.py`:**
```python
# HMS-F-021: payment gateway (mock by default; "razorpay" uses test-mode keys from .env)
PAYMENT_GATEWAY = os.environ.get("PAYMENT_GATEWAY", "mock")
PAYMENT_WEBHOOK_SECRET = os.environ.get("PAYMENT_WEBHOOK_SECRET", "dev-webhook-secret")
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
```
**SHARED, append at the end of `requirements.txt`:** `razorpay>=1.4`. Also add the four variable *names* (no real values) to `.env.example`.
Add a DEVIATIONS row: "ADR-05 (gateway) decided: Razorpay test mode, with a mock gateway as the default for development and CI."
`git add fees config/settings.py requirements.txt .env.example docs/DEVIATIONS.md`

### C2. HMS-29 (#29): PDF receipt. Branch `hms-29-receipt`
`reportlab` is already in `requirements.txt` once Arnav's HMS-33 is merged. If it isn't yet, add `reportlab>=4.2` at the end (and on conflict, keep just one copy of the line).

**AI prompt:**
> Create `Receipt(payment OneToOne, receipt_no unique e.g. "RCPT-000123", created_at)`, created once when a payment becomes SUCCESS (inside the webhook transaction). View `fees:receipt` (GET `/fees/payments/<id>/receipt/`) returns a ReportLab PDF as an attachment with receipt number, transaction id, amount, date, and student name + roll number + term. Only the payment's own student or a Warden/Admin can download it; others get 404. A non-successful payment gives 404. Add a "Download receipt" link on `fees:my_fees` for each successful payment. Tests: the owner downloads a PDF (`%PDF` header); another student gets 404; a pending payment gets 404. (HMS-F-023, TC-Fee-04)

`git add fees requirements.txt`

### C3. HMS-30 (#30): Reconciliation and defaulters. Branch `hms-30-reconciliation`
**AI prompt:**
> Admin/Warden page `fees:reconciliation` with a date range. It calls `gateway.fetch_ledger(from, to)` (MockGateway returns our own SUCCESS payments, so everything matches; also add a test double that returns a mismatched entry) and lists **matched** count, **mismatched** rows (in our DB but not in the ledger, or with a different amount/status), and **defaulters** = statements with `amount_paid < amount_due` and `due_date < today` (student, roll number, balance, due date). If the gateway is down, show "Payment service is not available right now." Tests: the mismatch is detected; the defaulter list matches the statements; a student gets 403. (HMS-F-024, TC-Fee-05)

`git add fees`

### C4. Update the RTM
After Arnav's HMS-36 is merged: in your last PR, set your rows (F-020 to F-024, SR-005) in `docs/RTM.md` to **A** (or **P** with a reason).

---

## Demo prep (for Arnav's videos)
- Sprint 1: the fee structure page as admin, and the fee statement as `student01`.
- Sprint 2: Pay now → mock checkout → "Pay (test)" → the balance drops to 0 → download the receipt PDF; then the admin reconciliation page.
