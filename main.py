from __future__ import print_function
import datetime
from datetime import datetime as dt
import pickle
import os.path
import sys
import pandas as pd
import calendar
from collections import defaultdict
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def main():
    mydict = defaultdict(lambda: datetime.timedelta(minutes=0))
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    year, month, user_email = get_args()
    start_day = datetime.datetime(year, month, 1).isoformat() + 'Z'
    end_day = datetime.datetime(year, month+1, 1).isoformat() + 'Z'
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    events_result = service.events().list(calendarId=user_email, timeMin=start_day,
                                        timeMax=end_day,
                                        maxResults=100, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = get_datetime(event['start'])
        end = get_datetime(event['end'])
        if start:
            getUserEvent(event, user_email, start, end, mydict)
        else:
            pass
    df_attend = pd.DataFrame.from_dict(mydict.items())
    print(df_attend)
    df_attend.columns = ['event', 'datetime']
    df_attend = df_attend.set_index('event')
    print( df_attend.sort_values(by='datetime', ascending=False) )

def getUserEvent(event, user_email, start, end, mydict):
    if event['organizer'].get('email')==user_email:
        getEventMinutes(event, start, end, mydict)
    else:
        getAttendeeEvent(event, user_email, start, end, mydict)

def getAttendeeEvent(event, user_email, start, end, mydict):
    for attendees in event['attendees']:
        if user_email in attendees.values():
            if attendees['responseStatus']=='accepted':
                getEventMinutes(event, start, end, mydict)

def getEventMinutes(event, start, end, mydict):
    seconds = (end-start).seconds
    minutes = datetime.timedelta(seconds=seconds)
    mydict[event['summary']] += minutes

def get_datetime(event):
    d = event.get('dateTime')
    if d:
        return dt.fromisoformat(str(d))

def get_args():
    args = sys.argv
    year = int( args[1] )
    month = int( args[2] )
    email = str( args[3] )
    return year, month, email

if __name__ == '__main__':
    main()
