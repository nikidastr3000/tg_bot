# Morning Digest Telegram Bot

A Python-based Telegram bot that sends a personalized morning digest of your Google Calendar events and Google Tasks. Designed to run for free using GitHub Actions.

## Features
- **Google Calendar:** Summarizes all events for today from all your calendars.
- **Google Tasks:** Lists all tasks due today and all overdue tasks from all your task lists.
- **Scheduled:** Runs automatically via GitHub Actions at a configurable time.
- **Zero Cost:** Uses GitHub Actions' free tier.

## Setup Instructions

### 1. Telegram Setup
1. Create a bot using [@BotFather](https://t.me/botfather) and save the **Bot Token**.
2. Get your **Chat ID** by sending a message to your bot and then visiting `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`.

### 2. Google API Setup
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable **Google Calendar API** and **Google Tasks API**.
4. Go to **APIs & Services > OAuth consent screen**. Configure it as "External" and add yourself as a test user. Add scopes: `.../auth/calendar.readonly` and `.../auth/tasks.readonly`.
5. Go to **APIs & Services > Credentials**. Create **OAuth 2.0 Client IDs** (Application type: Desktop app).
6. Download the JSON file and rename it to `client_secret.json`.

### 3. Generate Refresh Token
Since this bot runs on GitHub Actions, it needs a persistent refresh token.
1. Install requirements locally: `pip install google-auth-oauthlib`.
2. Run a small script to authorize and generate `token.json`:
   ```python
   from google_auth_oauthlib.flow import InstalledAppFlow
   scopes = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/tasks.readonly']
   flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', scopes)
   creds = flow.run_local_server(port=0)
   print(creds.to_json()) # This is your GOOGLE_TOKEN_JSON
   ```
3. Copy the output JSON string.

### 4. GitHub Secrets
Add the following secrets to your GitHub repository (**Settings > Secrets and variables > Actions**):
- `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token.
- `TELEGRAM_CHAT_ID`: Your Telegram Chat ID.
- `GOOGLE_TOKEN_JSON`: The full JSON string of your `token.json` (generated in step 3).

## Adjusting Send Time
The bot is scheduled in `.github/workflows/morning_digest.yml`. 
Find the `cron` line and adjust it (time is in UTC):
```yaml
on:
  schedule:
    - cron: '0 7 * * *' # 07:00 UTC
```

## Local Development
1. Clone the repo.
2. Install dependencies: `pip install -r requirements.txt`.
3. Set environment variables (or create a `.env` file):
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `GOOGLE_TOKEN_JSON`
4. Run: `python bot.py`.
