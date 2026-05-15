from google_auth_oauthlib.flow import InstalledAppFlow
import json

scopes = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/tasks.readonly']
flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', scopes)

# access_type='offline' ensures we get a refresh_token
# prompt='consent' ensures the user is asked for permission even if they already granted it before, 
# which is sometimes necessary to get a new refresh_token.
creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')

creds_json = creds.to_json()
creds_dict = json.loads(creds_json)

if 'refresh_token' not in creds_dict:
    print("WARNING: No refresh_token found. The bot will only work for 1 hour.")
    print("Try revoking access in your Google Account settings and run this script again.")
else:
    print("SUCCESS: Refresh token obtained.")

print("\nCopy the following JSON string into your GitHub Secret GOOGLE_TOKEN_JSON:\n")
print(creds_json)