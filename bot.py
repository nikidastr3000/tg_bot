import os
import json
import requests
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dateutil import parser

# Configuration from environment variables (GitHub Secrets)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GOOGLE_TOKEN_JSON = os.environ.get('GOOGLE_TOKEN_JSON')

# Calendars to ignore (exact names or keywords)
SKIP_CALENDARS = ["Christian Holidays", "Holidays in Germany", "Holidays in Ukraine", "Jewish Holidays"]

def get_google_service(name, version, credentials_dict, token_dict):
    creds = Credentials.from_authorized_user_info(token_dict)
    return build(name, version, credentials=creds)

def get_today_range():
    now = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = now + timedelta(days=1)
    return now.isoformat(), end.isoformat()

def fetch_calendar_events(service):
    now_iso, end_iso = get_today_range()
    all_events = []
    
    # Get all calendars
    calendar_list = service.calendarList().list().execute().get('items', [])
    
    for calendar in calendar_list:
        summary = calendar.get('summary', '')
        if any(skip_name.lower() in summary.lower() for skip_name in SKIP_CALENDARS):
            continue
            
        events_result = service.events().list(
            calendarId=calendar['id'],
            timeMin=now_iso,
            timeMax=end_iso,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        for e in events:
            all_events.append({
                'summary': e.get('summary', 'No Title'),
                'start': e['start'].get('dateTime', e['start'].get('date')),
                'location': e.get('location', '')
            })
    
    # Sort all events by start time
    all_events.sort(key=lambda x: x['start'])
    return all_events

def fetch_tasks(service):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    due_today = []
    overdue = []
    other_tasks = []
    
    tasklists = service.tasklists().list().execute().get('items', [])
    for tl in tasklists:
        tasks = service.tasks().list(tasklist=tl['id'], showCompleted=False, showHidden=True).execute().get('items', [])
        for t in tasks:
            due_str = t.get('due')
            title = t.get('title', 'No Title')
            
            if not due_str:
                other_tasks.append(title)
                continue
            
            due_date = parser.isoparse(due_str).astimezone(timezone.utc)
            
            if today_start <= due_date < today_end:
                due_today.append(title)
            elif due_date < today_start:
                overdue.append(title)
            else:
                # Due in the future
                other_tasks.append(title)
                
    return due_today, overdue, other_tasks

def format_agenda_message(events, due_today):
    lines = ["\U0001F305 *Today's Agenda* \U0001F305\n"]
    
    # Calendar Section
    lines.append("\U0001F4C5 *Today's Events:*")
    if not events:
        lines.append("_Nothing here_")
    else:
        for e in events:
            time_str = ""
            if 'T' in e['start']: # DateTime
                dt = parser.isoparse(e['start'])
                time_str = dt.strftime('%H:%M')
            else: # All day
                time_str = "All Day"
            
            loc = f" (@ {e['location']})" if e['location'] else ""
            lines.append(f"\u2022 {time_str}: {e['summary']}{loc}")
    
    # Due Today Section
    lines.append("\n\u2705 *Tasks Due Today:*")
    if not due_today:
        lines.append("_Nothing here_")
    else:
        for t in due_today:
            lines.append(f"\u2022 {t}")
            
    return "\n".join(lines)

def format_backlog_message(overdue, other_tasks):
    lines = ["\U0001F5D2 *Task Backlog* \U0001F5D2\n"]
            
    # Overdue Section
    lines.append("\U0001F6A8 *Overdue Tasks:*")
    if not overdue:
        lines.append("_Nothing here_")
    else:
        for t in overdue:
            lines.append(f"\u2022 {t}")

    # All Other Tasks Section
    lines.append("\n\U0001F308 *Other Pending Tasks:*")
    if not other_tasks:
        lines.append("_Nothing here_")
    else:
        for t in other_tasks:
            lines.append(f"\u2022 {t}")
            
    return "\n".join(lines)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()

def main():
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GOOGLE_TOKEN_JSON]):
        print("Missing required environment variables.")
        return

    token_dict = json.loads(GOOGLE_TOKEN_JSON)
    
    cal_service = get_google_service('calendar', 'v3', None, token_dict)
    tasks_service = get_google_service('tasks', 'v1', None, token_dict)
    
    events = fetch_calendar_events(cal_service)
    due_today, overdue, other_tasks = fetch_tasks(tasks_service)
    
    # Message 1: Today's Agenda
    agenda_msg = format_agenda_message(events, due_today)
    send_telegram(agenda_msg)
    
    # Message 2: Task Backlog
    backlog_msg = format_backlog_message(overdue, other_tasks)
    send_telegram(backlog_msg)
    
    print("Both digest messages sent successfully!")

if __name__ == '__main__':
    main()
