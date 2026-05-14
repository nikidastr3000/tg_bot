# Morning Digest Bot - Project Context

## Project Overview
This project is a Telegram bot designed to provide a daily "Morning Digest" by aggregating data from Google Calendar and Google Tasks. It is optimized to run as a scheduled task on GitHub Actions, eliminating the need for a dedicated server.

### Core Technologies
- **Language:** Python 3.10+
- **APIs:** 
  - Google Calendar API (v3)
  - Google Tasks API (v1)
  - Telegram Bot API
- **Infrastructure:** GitHub Actions (Scheduler & Runner)

### Architecture
- `bot.py`: The main script that authenticates with Google, fetches events/tasks, formats the message, and sends it to Telegram.
- `.github/workflows/morning_digest.yml`: Defines the CI/CD pipeline that triggers the bot on a cron schedule.
- `requirements.txt`: Lists the necessary Python libraries.

## Building and Running

### Commands
- **Install Dependencies:** `pip install -r requirements.txt`
- **Run Locally:** `python bot.py` (Requires environment variables to be set)
- **Test Workflow:** Trigger the "Morning Digest Bot" workflow manually from the GitHub Actions tab.

### Configuration
- **Delivery Time:** Controlled via the `cron` expression in `.github/workflows/morning_digest.yml`.
- **Secrets:** Managed through GitHub Actions Secrets:
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`
  - `GOOGLE_TOKEN_JSON` (OAuth2 refresh token JSON)

## Development Conventions
- **Authentication:** Uses OAuth2 refresh tokens for persistent access to user-specific Google Tasks data.
- **Error Handling:** Minimal; relies on script failure to notify in GitHub Actions if a run fails.
- **Formatting:** Uses Telegram's Markdown for clean message presentation.
- **Privacy:** Credentials must NEVER be hardcoded and should only be passed via environment variables/secrets.
