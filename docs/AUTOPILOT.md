# OPI Autopilot: Autonomous Cloud Operations Guide

The India IPO Listing-Gain Predictor (OPI) operates fully autonomously in GitHub Actions. The system discovers new IPOs, generates pre-listing estimates, verifies post-listing outcomes, retrains models monthly, and evaluates prospective model promotions without human intervention.

The owner's primary interface is the live public dashboard:
👉 **[https://soul991.github.io/OPI/dashboard/](https://soul991.github.io/OPI/dashboard/)**

---

## 1. What Runs Automatically & When

OPI runs three scheduled cloud workflows on GitHub Actions:

| Workflow | Schedule | Automated Actions |
|---|---|---|
| **Daily Pipeline** (`daily.yml`) | Daily at 06:00 UTC (11:30 IST) & 14:00 UTC (19:30 IST) | • Discovers active and upcoming Mainboard IPOs.<br>• Ingests issue details and final subscription figures post-bidding close.<br>• Sanitizes research inputs and predicts listing gains using `champion` and `shadow` models.<br>• Records predictions to `predictions/prediction_log.csv` and `predictions/model_versions.csv`.<br>• Verifies listing-day opening prices per primary exchange policy (NSE first; BSE only for BSE-only listings).<br>• Regenerates and deploys the dashboard to GitHub Pages.<br>*(Note: GitHub Actions cron scheduling is subject to platform lag of ~4–5 hours; precise timing requires an external trigger).* |
| **Integrity Watchdog** (`watchdog.yml`) | Daily at 10:00 UTC (15:30 IST) | • Audits repository data integrity, feed coverage, and prediction timestamps.<br>• Tracks pending listing outcomes.<br>• Raises visible dashboard notices for outcomes pending 3–7 days.<br>• Fails the workflow and opens an issue only if an outcome is $\ge 8$ days overdue. |
| **Monthly Retraining** (`monthly_retrain.yml`) | 1st of every month at 00:00 UTC | • Trains a new candidate shadow model (`v4.X.0-YYYYMM`) on all verified rows except holdout.<br>• Registers the new model as `shadow` in `model/registry.json`.<br>• Evaluates pre-registered promotion rules on paired prospective forward predictions ($\ge 20$ pairs, $\Delta < 0$, 95% bootstrap CI upper bound $\le +0.5$ pp, Brier $\Delta \le 0.005$, 60-day cooldown).<br>• Logs promotion decisions to `model/promotions_log.csv`.<br>• Direct-pushes updates to `main` upon verification. |

---

## 2. What System Alerts Mean

Alerts are designed to be honest, transparent, and quiet:

* **Notice / Dashboard Banner (3 to 7 Days Overdue)**: An IPO has passed its expected listing date, but primary and second sources have not yet converged within 1.0% tolerance. This is normal when an exchange reschedules listing or holiday delays occur. The system preserves source snapshots under `data/evidence/actuals/pending/` and continues retrying daily without failing the build.
* **Critical Incident ($\ge 8$ Days Overdue or Step Failure)**: An outcome has remained unresolved for 8 or more days, or a core pipeline step failed (e.g. invalid git state, broken test). GitHub Actions fails the workflow, sending an email notification to the repository owner and opening a GitHub Issue.
* **Research Agent Alert**: If the LLM provider fails schema validation or returns an API error during pre-listing enrichment, the system logs `RESEARCH_AGENT_ALERT`, emits a prominent `[ALERT]` badge in the logs, and continues with deterministic baseline features so predictions are never dropped.

---

## 3. The Three Human Interventions

Under normal market conditions, zero manual actions are required. Human intervention is restricted to three operational events:

1. **API Key Expiry or Quota Exhaustion (`OPENROUTER_API_KEY`)**:
   * *Symptom*: Research agent logs show authentication or rate limit errors (`401`/`429`).
   * *Resolution*: Generate a new API key from OpenRouter and update repository secret `OPENROUTER_API_KEY` under GitHub **Settings → Secrets and variables → Actions**.
2. **Upstream Source Layout Changes**:
   * *Symptom*: Chittorgarh, BSE, or NSE alter their HTML/table layouts, causing scraper extractions to return unexpected formats.
   * *Resolution*: Update the HTML parsing functions in `opi/actuals.py` or `opi/ingest.py`, verify with fixture tests in `tests/`, and merge to `main`.
3. **GitHub Scheduled Workflow Pause (60-Day Inactivity Rule)**:
   * *Symptom*: GitHub Actions automatically disables scheduled cron workflows if a repository has received no git commits for 60 consecutive days.
   * *Resolution*: Visit the repository's **Actions** tab on GitHub and click **Enable workflow**, or push any commit to `main` to reset the 60-day timer.
