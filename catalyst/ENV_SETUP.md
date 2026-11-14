# Zoho Catalyst Environment & Cron Configuration Guide

> **Security Mandate**: Never commit real secret tokens to git repositories, pull requests, or issue comments. All values must be configured strictly in the Catalyst Console or CLI environment variables.

---

## 1. Required Environment Variables

Configure the following environment variables in the Zoho Catalyst Console for the `opi_trigger` serverless function (under **Serverless** -> **Functions** -> **Configuration** -> **Environment Variables**):

| Variable Name | Purpose | Sensitivity | Format / Example Pattern |
| :--- | :--- | :--- | :--- |
| `GITHUB_DISPATCH_TOKEN` | GitHub Personal Access Token (PAT) with `repo` and `workflow` permissions to invoke `workflow_dispatch` on `notify.yml`. | Confidential (Critical) | `ghp_...` or fine-grained `github_pat_...` |
| `TELEGRAM_BOT_TOKEN` | Bot API authentication token obtained from `@BotFather` for emergency trigger failure alerting. | Confidential (High) | `1234567890:ABCdef...` |
| `TELEGRAM_CHAT_ID` | Telegram chat or user ID receiving alert notifications. | Internal Identifier | `2006803662` |

---

## 2. Cron Schedules (Asia/Kolkata Timezone)

Create three scheduled Cron jobs in the Zoho Catalyst Console (**Serverless** -> **Cron**) targeting the `opi_trigger` function:

| Cron Name | Target Stage | Schedule (IST) | Standard 5-Field Cron Expression | Target Type |
| :--- | :--- | :--- | :--- | :--- |
| `opi_cron_announce` | `announce` | 09:00 & 20:00 IST daily | `0 9,20 * * *` | Function (`opi_trigger`) |
| `opi_cron_preview` | `preview` | 11:45 IST daily | `45 11 * * *` | Function (`opi_trigger`) |
| `opi_cron_listing` | `listing` | 11:30 & 16:30 IST daily | `30 11,16 * * *` | Function (`opi_trigger`) |

### Catalyst Cron Configuration Details
- **Execution Type**: Pre-defined / Periodic
- **Time Zone**: `Asia/Kolkata` (`IST`)
- **Concurrency & Retry**: 
  - Max retries: 2
  - Retry interval: 60 seconds
- **Payload Parameters**:
  - For `opi_cron_announce`: `{"stage": "announce", "dry_run": false}`
  - For `opi_cron_preview`: `{"stage": "preview", "dry_run": false}`
  - For `opi_cron_listing`: `{"stage": "listing", "dry_run": false}`

---

## 3. CLI Deployment Instructions

If deploying via the Zoho Catalyst CLI:

1. Log in to your Catalyst account:
   ```bash
   catalyst login --dc in
   ```
2. Link to the active Catalyst project:
   ```bash
   catalyst project:use Project-Rainfall
   ```
3. Set the environment variables in Catalyst:
   ```bash
   catalyst functions:config opi_trigger --env GITHUB_DISPATCH_TOKEN=<YOUR_PAT>
   catalyst functions:config opi_trigger --env TELEGRAM_BOT_TOKEN=<YOUR_BOT_TOKEN>
   catalyst functions:config opi_trigger --env TELEGRAM_CHAT_ID=2006803662
   ```
4. Deploy the function:
   ```bash
   catalyst deploy --only functions
   ```
