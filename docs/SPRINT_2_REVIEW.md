# Sprint 2 Review: Team 5 HMS (final)

**Window:** 26-30 Oct 2026 (planned) · feature work completed mid-November 2026 (see [DEVIATIONS](DEVIATIONS.md) D3)
**Development frozen:** on merge of HMS-36 and HMS-37, tag `v1.0`
**Demo video:** [`docs/videos/final_demo.mp4`](videos/final_demo.mp4), Part 2 (1:20 to the end). One combined video covers both sprints (DEVIATIONS D7).

## Goal

The complete product: password reset, room changes, online payment with receipts and reconciliation, the complaint workflow, reports with export, and the non-functional and security requirements.

## Completed items

| ID | Item | Owner | SP | PR |
|---|---|---|---|---|
| HMS-21 | OTP password reset | Arjav | 3 | #59 |
| HMS-22 | Responsive / accessible UI | Arjav | 3 | #62 |
| HMS-23 | HTTPS-only security settings | Arjav | 2 | #63 |
| HMS-24 | Health check + restart policy | Arjav | 1 | #65 |
| HMS-25 | Room change request and approval | Arjun | 5 | #64 |
| HMS-26 | Performance: indexes, pagination, Locust | Arjun | 3 | #67 |
| HMS-27 | Scale test (5,000 students / 2,000 rooms) | Arjun | 2 | #66 |
| HMS-28 | Online payment (sandbox gateway) | Armaan | 8 | #68 |
| HMS-29 | PDF receipt | Armaan | 3 | #69 |
| HMS-30 | Reconciliation and defaulters | Armaan | 5 | #70 |
| HMS-31 | Complaint status workflow | Arnav | 3 | #52 |
| HMS-32 | Occupancy / vacancy / fee reports | Arnav | 5 | #58 |
| HMS-33 | CSV / PDF export | Arnav | 3 | #60 |
| HMS-34 | Data protection | Arnav | 2 | #61 |
| HMS-35 | Audit retention and archive | Arnav | 2 | #57 |
| HMS-36 | Final documentation | Arnav | 2 | #71 |
| HMS-37 | Final demo video (both sprints) | Arnav | 2 | this PR |

**Velocity:** 54 of 54 story points (Arjav 9, Arjun 10, Armaan 16, Arnav 19). **Project total:** 109 of 109 across both sprints, 37 of 37 backlog items.

## What the demo shows (video Part 2)

Password reset by email OTP; a room-change request approved by the Warden; a sandbox payment and the PDF receipt; reconciliation and the defaulters list; a complaint moving through its statuses with the student notified; reports for a date range exported to CSV and PDF; the read-only audit log.

## Not completed / known limitations

From [TEST_REPORT.md](TEST_REPORT.md), section 10:

- HMS-NF-001: the 200-user Locust target (p95 <= 2 s) was not met on the local SQLite run (D9)
- No login / OTP rate limiting (D14)
- Accessibility audit (TC-UX-01) not recorded
- Django 5.1.15 has open security advisories; upgrade to 5.2 LTS recommended
- Branch coverage below the Test Plan targets for AllocationModule and FeeModule

## Review and retrospective

- **Went well:** every backlog item delivered with tests; security cases (webhook signatures, upload safety, PII masking, RBAC) automated and running in CI.
- **Blockers:** the late Sprint 1 pushed Sprint 2 into November. Parallel PRs touching `config/settings.py`, `fees/views.py` and the fee migrations caused merge conflicts, including two migrations both numbered `0003`, resolved when merging HMS-26.
- **Process:** PRs were raised by the assigned member with a linked issue and green CI.

## Final state

- RTM: [RTM.md](RTM.md), 27 A / 4 P / 0 N
- Test Summary Report: [TEST_REPORT.md](TEST_REPORT.md)
- Deviations: [DEVIATIONS.md](DEVIATIONS.md)
- CI: all checks green on `main` at tag `v1.0`
