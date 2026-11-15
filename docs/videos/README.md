# Final demo video (HMS-37, also covers HMS-20)

[`final_demo.mp4`](final_demo.mp4) is 2:20 at 1280×720 (H.264). It is one combined video for both sprints instead of a separate 1-minute Sprint 1 video (HMS-20) and 2-minute Sprint 2 video. See [DEVIATIONS D7](../DEVIATIONS.md).

## Chapters

| Time | Sprint | Shows | Backlog |
|---|---|---|---|
| 0:00 | 1 | Role-based login, Admin dashboard with live occupancy | HMS-04, 06, 16 |
| 0:12 | 1 | Blocks and rooms with availability | HMS-09 |
| 0:20 | 1 | Allocating the last bed in single room A101: a concurrent allocation is refused (no free beds) | HMS-11, 12 |
| 0:34 | 1 | Fee structure; student's itemised fee statement | HMS-14, 15 |
| 0:44 | 1 | Student raises a complaint with a photo | HMS-19 |
| 0:52 | 1 | Student gets 403 on `/reports/` | HMS-06 |
| **0:58** | **2** | Password reset with an emailed OTP | HMS-21 |
| 1:10 | 2 | Sandbox payment, signed webhook, PDF receipt | HMS-28, 29 |
| 1:26 | 2 | Room and roommates; room-change request approved by the Warden | HMS-13, 25 |
| 1:42 | 2 | Reconciliation and defaulters | HMS-30 |
| 1:48 | 2 | Complaint status workflow with email notification | HMS-31 |
| 1:58 | 2 | Occupancy report, CSV and PDF export | HMS-32, 33 |
| 2:10 | 2 | Append-only audit log | HMS-18, 35 |
| 2:16 | - | End card | - |

## How it was recorded

The recording is of the real application from `main`, running locally on SQLite with the `seed_demo` data (synthetic accounts only). A Playwright script drove Chromium through the pages and recorded the browser viewport; the captions and the sprint tag are an overlay added by that script, not part of the application. Before recording, one fee statement was given a past due date so the defaulters list has an entry. The complaint photo is a 1×1 PNG.
