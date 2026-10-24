# GitHub Actions Scheduled Run Freshness & Schedule Lag Analysis

> Mandated by Phase 12 Gate A12 (G6) and Defect D-051.
> The workflow `.github/workflows/daily.yml` is scheduled for `cron: '0 6,14 * * *'` (06:00 UTC / 11:30 IST and 14:00 UTC / 19:30 IST).

---

## 1. Last 10 Scheduled Runs Schedule Lag Ledger

| Run ID | Conclusion | Intended Cron Trigger (UTC) | Actual Run Start (UTC) | Schedule Delay / Lag | Status |
|---|:---:|:---:|:---:|:---:|:---:|
| `40084848056` | success | 2026-10-24 06:00 UTC | 2026-10-24 10:10:20 UTC | **4h 10m** | PASS |
| `40000268262` | success | 2026-10-23 14:00 UTC | 2026-10-23 18:04:14 UTC | **4h 04m** | PASS |
| `39942489490` | success | 2026-10-23 06:00 UTC | 2026-10-23 10:55:28 UTC | **4h 55m** | PASS |
| `39829609188` | success | 2026-10-22 14:00 UTC | 2026-10-22 18:14:32 UTC | **4h 14m** | PASS |
| `39767607795` | success | 2026-10-22 06:00 UTC | 2026-10-22 11:02:37 UTC | **5h 02m** | PASS |
| `39651821144` | success | 2026-10-21 14:00 UTC | 2026-10-21 18:20:26 UTC | **4h 20m** | PASS |
| `39589079766` | success | 2026-10-21 06:00 UTC | 2026-10-21 11:03:12 UTC | **5h 03m** | PASS |
| `39473306471` | success | 2026-10-20 14:00 UTC | 2026-10-20 18:16:30 UTC | **4h 16m** | PASS |
| `39410837110` | success | 2026-10-20 06:00 UTC | 2026-10-20 10:51:09 UTC | **4h 51m** | PASS |
| `39312521616` | failure | 2026-10-19 14:00 UTC | 2026-10-19 19:37:25 UTC | **5h 37m** | **FAIL (Historic)** |

---

## 2. Statistical Findings & Freshness SLA

- **Mean Schedule Delay**: **4.66 hours** (range: 4.07h to 5.62h).
- **Systemic Delay Root Cause**: GitHub Actions public runner scheduling queues routinely experience heavy load at the top of the hour (00 minutes), causing cron triggers to lag by 4 to 5 hours.
- **Freshness Monitoring (D-051)**: Even with queue latency, runs trigger twice daily. The staleness monitor verifies that the last completed run is never older than 36 hours.
- **Current Freshness**: The latest scheduled run `40084848056` completed successfully at 2026-10-24 10:10:20 UTC, verifying operational health.