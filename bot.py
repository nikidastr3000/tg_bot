import os
import json
import requests
import sys
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dateutil import parser

# Configuration from environment variables (GitHub Secrets)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GOOGLE_TOKEN_JSON = os.environ.get('GOOGLE_TOKEN_JSON')

# Calendars to ignore (exact names or keywords)
SKIP_CALENDARS = ["Christian Holidays", "Holidays in Germany", "Holidays in Ukraine", "Jewish Holidays"]

def escape_markdown(text):
    """
    Helper to escape characters that might break Telegram Markdown.
    Note: We are using legacy Markdown for simplicity as per existing code.
    """
    if not text:
        return ""
    # In legacy Markdown, * _ ` [ are the main ones. 
    # But since we use them for formatting, we only escape if they are likely to be "naked".
    # For now, let's just do a basic cleanup to prevent crashes.
    return text.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`').replace('[', '\\[')

def get_google_service(name, version, token_dict):
    print(f"Initializing {name} {version} service...")
    creds = Credentials.from_authorized_user_info(token_dict)
    
    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        print(f"Refreshing Google {name} credentials...")
        creds.refresh(Request())
        
    return build(name, version, credentials=creds)

def get_today_range():
    now = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = now + timedelta(days=1)
    return now.isoformat(), end.isoformat()

def fetch_calendar_events(service):
    print("Fetching calendar events...")
    now_iso, end_iso = get_today_range()
    all_events = []
    
    # Get all calendars
    try:
        calendar_list_result = service.calendarList().list().execute()
        calendar_list = calendar_list_result.get('items', [])
    except Exception as e:
        print(f"Error fetching calendar list: {e}")
        return []
    
    for calendar in calendar_list:
        summary = calendar.get('summary', '')
        if any(skip_name.lower() in summary.lower() for skip_name in SKIP_CALENDARS):
            print(f"Skipping calendar: {summary}")
            continue
            
        print(f"Processing calendar: {summary}")
        try:
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
        except Exception as e:
            print(f"Error fetching events for {summary}: {e}")
    
    # Sort all events by start time
    all_events.sort(key=lambda x: x['start'])
    return all_events

def fetch_tasks(service):
    print("Fetching tasks...")
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    due_today = []
    overdue = []
    other_tasks = []
    
    try:
        tasklists = service.tasklists().list().execute().get('items', [])
    except Exception as e:
        print(f"Error fetching task lists: {e}")
        return [], [], []

    for tl in tasklists:
        print(f"Processing task list: {tl['title']}")
        try:
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
        except Exception as e:
            print(f"Error fetching tasks for {tl['title']}: {e}")
                
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
            
            loc = f" (@ {escape_markdown(e['location'])})" if e['location'] else ""
            lines.append(f"\u2022 {time_str}: {escape_markdown(e['summary'])}{loc}")
    
    # Due Today Section
    lines.append("\n\u2705 *Tasks Due Today:*")
    if not due_today:
        lines.append("_Nothing here_")
    else:
        for t in due_today:
            lines.append(f"\u2022 {escape_markdown(t)}")
            
    return "\n".join(lines)

def format_backlog_message(overdue, other_tasks):
    lines = ["\U0001F5D2 *Task Backlog* \U0001F5D2\n"]
            
    # Overdue Section
    lines.append("\U0001F6A8 *Overdue Tasks:*")
    if not overdue:
        lines.append("_Nothing here_")
    else:
        for t in overdue:
            lines.append(f"\u2022 {escape_markdown(t)}")

    # All Other Tasks Section
    lines.append("\n\U0001F308 *Other Pending Tasks:*")
    if not other_tasks:
        lines.append("_Nothing here_")
    else:
        for t in other_tasks:
            lines.append(f"\u2022 {escape_markdown(t)}")
            
    return "\n".join(lines)

def send_telegram(text):
    print("Sending message to Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Telegram API Error: {response.text}")
    response.raise_for_status()

def main():
    print(f"Starting Morning Digest Bot at {datetime.now(timezone.utc)}")
    
    missing_vars = []
    if not TELEGRAM_BOT_TOKEN: missing_vars.append('TELEGRAM_BOT_TOKEN')
    if not TELEGRAM_CHAT_ID: missing_vars.append('TELEGRAM_CHAT_ID')
    if not GOOGLE_TOKEN_JSON: missing_vars.append('GOOGLE_TOKEN_JSON')
    
    if missing_vars:
        print(f"CRITICAL ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    try:
        token_dict = json.loads(GOOGLE_TOKEN_JSON)
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to parse GOOGLE_TOKEN_JSON: {e}")
        sys.exit(1)
    
    try:
        cal_service = get_google_service('calendar', 'v3', token_dict)
        tasks_service = get_google_service('tasks', 'v1', token_dict)
        
        events = fetch_calendar_events(cal_service)
        due_today, overdue, other_tasks = fetch_tasks(tasks_service)
        
        # Message 1: Today's Agenda
        agenda_msg = format_agenda_message(events, due_today)
        send_telegram(agenda_msg)
        
        # Message 2: Task Backlog
        backlog_msg = format_backlog_message(overdue, other_tasks)
        send_telegram(backlog_msg)
        
        print("Both digest messages sent successfully!")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
