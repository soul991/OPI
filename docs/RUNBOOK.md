# OPI Production Operational Runbook

> **Audience**: Repository maintainer and operator.  
> **Purpose**: Concise, plain-language operating manual for maintaining, monitoring, and operating the automated OPI system.  
> **Golden Rule**: Decision aid and empirical benchmark only. Never use this system for investment or financial advice.

---

## 1. What the System Does

OPI (Online Predictor for IPOs) is a fully autonomous machine learning pipeline that monitors Indian Mainboard Initial Public Offerings (NSE and BSE).
Every day, running in GitHub Actions cloud infrastructure (independent of any personal workstation):
- **Discovers** newly closed Mainboard IPOs before they list.
- **Extracts & Grounded Scores** features (issue parameters, subscription levels, market macro indices, and pre-listing grey market quotes).
- **Prospectively Logs Predictions** in `predictions/prediction_log.csv` strictly before listing.
- **Records Actual Outcomes** from verified official exchange opening price notices.
- **Publishes the Live Audit Dashboard** at [https://soul991.github.io/OPI/dashboard/](https://soul991.github.io/OPI/dashboard/).

---

## 2. The Three Places to Look

When checking system health, look at these three sources:
1. **GitHub Actions Tab** (`https://github.com/soul991/OPI/actions`):
   - Shows the status of the twice-daily automated runs (`Daily Forward Test & Verification`), the daily watchdog health check, and weekly canary builds.
2. **The Public Web Dashboard** (`https://soul991.github.io/OPI/dashboard/`):
   - Visualizes live running model MAE, GMP MAE, conformal prediction bounds, recent IPO outcomes, and cloud run timestamps.
3. **The Defect Ledger** (`DEFECTS.md`):
   - Comprehensive audit register of all identified anomalies, open/closed issues, and regression test proofs.

---

## 3. What Each Alert Issue Means and First Steps

When an automated workflow fails, an issue titled `Daily run failed: <run_id>` or `Watchdog run failed: <run_id>` is opened in the GitHub repository.

| Alert Title / Reason | Meaning | Immediate Action |
|---|---|---|
| `Daily run failed: <id>` (Verification) | Pytest or `scripts/verify_all.py` detected a data integrity violation. | Click the Actions run URL in the issue. Inspect the step failure. If an IPO entry had an invalid date or formatting anomaly, fix the input. |
| `Daily run failed: <id>` (SKIPPED_BLOCKED_SOURCE) | Upstream exchange (NSE/BSE) or data aggregator blocked cloud scraping. | Run the manual outcome recording flow using a local browser snapshot (Section 5). |
| `Watchdog run failed: <id>` (Scheduled Run Staleness) | No scheduled run succeeded in the last 36 hours. | Check GitHub Actions tab for disabled workflows or runner outage. Manually trigger `daily.yml`. |
| `Watchdog run failed: <id>` (Dashboard Staleness) | The GitHub Pages dashboard rendered timestamp is older than 36 hours. | Verify GitHub Pages deployment under Settings > Pages. Manually dispatch `daily.yml` to trigger Pages rebuild. |
| `Watchdog run failed: <id>` (OpenRouter Model Unavailability) | None of the free models in `config/research_models.json` are listed on OpenRouter. | Follow Section 6 to update the free model list. |

*Note: Open alert issues automatically close upon the next successful green scheduled run.*

---

## 4. How to Rotate the OpenRouter API Key

The OpenRouter API key is stored exclusively as a repository secret and is never stored in repository code or logs.
To rotate the key:
1. Go to repository **Settings** > **Secrets and variables** > **Actions**.
2. Locate `OPENROUTER_API_KEY`.
3. Click the pencil icon (Edit) or update secret.
4. Paste your new OpenRouter API key and save.
5. **No code change, commit, or repository edit is required.**

---

## 5. How to Re-Run a Failed Day Manually

If a scheduled cloud run failed or missed an IPO because of temporary site downtime:
1. Go to the **Actions** tab on GitHub.
2. Select **Daily Forward Test & Verification** in the left sidebar.
3. Click the **Run workflow** dropdown button, select branch `main`, and click **Run workflow**.
4. To record a listed IPO outcome manually when automated exchange access is blocked:
   - Save the official BSE or NSE listing page from your desktop browser as HTML.
   - Run:
     ```bash
     python scripts/update_actuals.py --company "<Exact Company Name>" --source-url "<Official URL>" --actual-listing-price <Price> --page-date <YYYY-MM-DD> --company-quote "<Excerpt>" --price-quote "<Excerpt>" --evidence-file "<Path to HTML>"
     ```
   - Commit the generated snapshot under `data/evidence/actuals/` and push.

---

## 6. How to Add or Change a Free Model

Model configurations are defined in `config/research_models.json`.
1. Check currently active free models at [https://openrouter.ai/models?q=free](https://openrouter.ai/models?q=free).
2. Edit `config/research_models.json`:
   ```json
   {
     "models": [
       "google/gemma-4-31b-it:free",
       "nvidia/nemotron-3.5-super-vl:free",
       "meta-llama/llama-3.3-70b-instruct:free"
     ]
   }
   ```
3. Commit and push. The daily research runner will automatically prioritize models in the order listed.

---

## 7. How to Read the Final Evaluation ($n = 30$)

When 30 genuine forward IPOs have listed with verified exchange actuals:
1. `scripts/final_evaluation.py` will automatically execute in the daily workflow.
2. Review the generated report at `phases/Final Evaluation/report.md`.
3. **Key Numbers**:
   - **Model MAE vs. GMP MAE**: Compare point accuracy across rows with grey market quotes.
   - **Mean Paired $\Delta$**: Difference in absolute error.
   - **95% Bootstrap Confidence Interval**:
     - If the interval is strictly positive ($> 0$), the model statistically outperformed GMP.
     - If the interval includes zero, the model is **statistically indistinguishable** from GMP.
   - **90% Conformal Coverage Rate**: Expected nominal coverage is 90% (evaluated with Wilson 95% CI).

---

## 8. Monthly 10-Minute Maintainer Checklist

Perform this 10-minute audit on the 1st of every month:
- [ ] **Dashboard Freshness**: Open [https://soul991.github.io/OPI/dashboard/](https://soul991.github.io/OPI/dashboard/); confirm the "Last Cloud Run" badge is within 24 hours.
- [ ] **Issues Tab Empty**: Check repository Issues; confirm zero open alert issues.
- [ ] **Defect Counter**: Confirm dashboard defect counter equals the count of open/partial rows in `DEFECTS.md`.
- [ ] **Scheduled Runs**: Verify the last 5 scheduled runs in Actions tab are green.
- [ ] **Secret Verified**: Confirm `OPENROUTER_API_KEY` exists in `gh secret list`.
- [ ] **Data Completeness**: Check `predictions/prediction_log.csv` to ensure no recently listed Mainboard IPOs were skipped without logged reasons.

---

## 9. Disclaimer and Prohibited Usage

**What this system must NEVER be used for**:
- This software is strictly an academic quantitative research aid and empirical forecasting benchmark.
- **It is NOT financial advice, investment advice, trading advice, or a recommendation to subscribe to any security.**
- IPO investments in Indian securities markets involve substantial capital risk, market volatility, and unpredictable institutional demand. Always consult a SEBI-registered investment advisor before making financial decisions.
