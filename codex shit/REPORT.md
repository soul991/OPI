# OPI Session Report

**Date:** 2026-10-17
**Repository:** `/Users/istakahamed06/Documents/OPI`
**Archive:** `codex shit/`

## Goal

Bring the local OPI repository up to date, then prepare an honest comparison between IPO model predictions and listing outcomes without retraining. Keep genuine future predictions separate from retrospective analysis and make the dashboard refresh when new official actuals are recorded.

## Work completed

1. The local `main` branch was fast-forwarded from GitHub to commit `e17520a` (`origin/main`). No push or new commit was made in this session.
2. Confirmed that the registered champion is `v4.0.0-champion`, trained on the 2010-01-01 through 2021-12-31 window; its artifact SHA-256 matches `model/registry.json`. **No training, retraining, or model promotion was run.**
3. Scored the post-training rows already in `data/ipo_master.csv` with the existing champion. The master has 333 rows through 2021 and 398 rows from 2022 onward. After the Mainboard eligibility gate excluded the InvIT and REIT rows, the replay contains 396 IPOs, from 2022-01-31 to 2026-10-08. Replay MAE is 7.98 percentage points; predicted positive/non-positive direction matched actual direction for 84.3%.
4. Saved the inference results to `predictions/champion_replay_v4.0.0-champion.csv`, including model and input-data hashes. The replay is explicitly retrospective: historical feature values are not all backed by pre-listing snapshots, so it is exploratory and is not the live forward track record.
5. Added a predicted-versus-actual historical replay chart and a separate live champion chart to `dashboard/index.html`. The live chart includes pending predictions and will fill in actuals after the official exchange evidence workflow records them.
6. Replaced the stale `new_ipo.csv` candidate with Fusion CX Limited, using the final post-close subscription figures and issue information. Scored and logged it before its scheduled 2026-10-22 listing: predicted gain +4.33%; calibrated P(gain > 10%) 30.1%. No GMP was entered. HD Fire Protect's existing +26.12% prediction remains pending its scheduled 2026-10-21 listing.
7. Added dashboard regeneration after a successful official NSE/BSE actual update, and retained daily dashboard regeneration in the forward runner. Newly completed SME listings found past the master cutoff were not added to the Mainboard model; for example, R.K. Fashion Accessories is listed on NSE as SME.
8. Updated the README to document the champion replay, its limits, the live prediction status, and dashboard refresh behavior.
9. Python syntax compilation and `git diff --check` passed. The test suite was not run, per the user's instruction.

## Market references used

- NSE Fusion CX issue information: https://www.nseindia.com/market-data/issue-information?series=EQ&symbol=FUSIONCX&type=Active
- Final Fusion CX subscription figures compiled from exchange data: https://www.ipoji.com/ipo-subscription/fusion-cx-ipo
- Fusion CX listing calendar: https://www.moneycontrol.com/ipo/
- HD Fire Protect issue and listing dates: https://www.indmoney.com/ipo/hd-fire-protect-ltd-ipo
- NSE R.K. Fashion Accessories quote (SME segment): https://www.nseindia.com/get-quote/equity/RKFAL/R.K.-Fashion-Accessories-Limited

## Archived files

Copies of the changed/generated project files and the key model/data inputs used for the replay are stored below `files/`, preserving their original relative paths. Originals remain in their working locations so the project continues to run.

- `README.md` — SHA-256 `77e999f658f3fa2fa31eddf9cd9f70606bf01345df5e008130c5951483457ca1`
- `dashboard/index.html` — SHA-256 `7a172dc0830c6e93315310d93fb8f18f4f262a8582d9519657af663e1a18f026`
- `new_ipo.csv` — SHA-256 `61233b2f0da4ed7094408631407ce9dfb0746e9d6d91adc80d4aaa12f9b9fbfb`
- `data/ipo_master.csv` — SHA-256 `1428fca4369fbcf2a29a88696c07dc03bbcc4d755766803444eca54441e553ae`
- `model/registry.json` — SHA-256 `dcc1bc39c9f19a8e4683e06100fd664acf6b0dd2bcc62e3c52134327d83cb064`
- `model/ipo_model_phase4.joblib` — SHA-256 `335dd32d3ab3127de378316d64690b1a9bd6c2e8377859671916b1347e9b9069`
- `opi/actuals.py` — SHA-256 `1743df850c9c8be357cf5aa88ff396620b526a893983fbbcf110c35b954bf681`
- `opi/log.py` — SHA-256 `b3bb2415feb62601d07950e01954c95064c084dd5bd707b2508f08c08db89a02`
- `opi/report.py` — SHA-256 `664eb5ad2a9c00eacd347ac1d40fe1a7f9aba1e207a0d4c906b5f0e371261cf1`
- `opi/run_daily.py` — SHA-256 `4b3187c327db1dd1ce80c03d75a50ed8a930861b0c2db5f84bfa467889960805`
- `opi/score.py` — SHA-256 `933296bbb674b38f1a4b609896c4c8535fb1ce9d8b6333cd165efbc8c0867e53`
- `opi/validate.py` — SHA-256 `67b89ef955f4da595d231e6c006a21ac30428d4bc2d0fc3e295d1d8030e16bd4`
- `predictions/champion_replay_v4.0.0-champion.csv` — SHA-256 `f2a9ebd1bafed57247dffa38e71651fb5d8bb26db2103b0b72cf08ea20282a8b`
- `predictions/prediction_log.csv` — SHA-256 `0968f33253db2b76718a8febc9b00a8484ccd06054d219afd7ac92425926726c`
- `scripts/update_actuals.py` — SHA-256 `22cf73176466c8201d646eb4f0cc0b7cffa6bb5d0e040f9c596b2e34ddfd3f34`
