from google_auth_oauthlib.flow import InstalledAppFlow
scopes = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/tasks.readonly']
flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', scopes)
creds = flow.run_local_server(port=0)
print(creds.to_json()) # This is your GOOGLE_TOKEN_JSON