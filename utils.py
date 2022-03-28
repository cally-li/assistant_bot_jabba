from __future__ import print_function

import datetime
import os
import os.path
import smtplib
import ssl
from email.message import EmailMessage
from secrets import API_KEY, EMAIL_ADDRESS, EMAIL_PASSWORD

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']


# weather API call
def get_weather():
    city = 'Toronto'
    request_url = f'https://api.openweathermap.org/data/2.5/weather?appid={API_KEY}&q={city}'
    response = requests.get(request_url)
    if response.status_code == 200:
        data = response.json()  #decode json response object - return data as dict
        weather = data['weather'][0]['description']
        temp = round(data['main']['temp'] - 273.15, 1)
        feels_like = round(data['main']['feels_like'] - 273.15, 1)
        print(f"Today's weather in {city} is >> {weather}, {temp} celsius but feels like {feels_like} celsius")
    else:
        print("Sorry, an error occurred.")


def send_email():
    send_to = input("Please input whose email to send to >> ")
    subject = input("Please input the email subject >> ")
    content = input("Please write your message >> ")
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = send_to
    msg.set_content(content)
    context = ssl.create_default_context()

    print(f"...Sending email...")
    try:
        # connect to gmail server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f" Your email was sent to '{send_to}'!")

    except:
        print("Sorry, an error occurred.")


def open_notes():
    path = '/System/Applications/Notes.app'
    command = f'open {path}'
    os.system(command)


def show_calendar():
    """
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print('...Getting your upcoming 10 events...')
        now_time = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M")
        print(f'Current Time: {now_time}')
        
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=10, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        # Prints the start and name of the next 10 events
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            formatted_datetime_obj= datetime.datetime.strptime(start,'%Y-%m-%dT%H:%M:%S-04:00').strftime('%Y-%m-%d %H:%M')
            print(formatted_datetime_obj, event['summary'])

    except HttpError as error:
        print('An error occurred: %s' % error)




# convert user input time to RFC format
def convert_to_RFC_datetime(year, month, day, hour, minute):
    dt = datetime.datetime(year, month, day, hour, minute, 0).isoformat() + 'Z'
    return dt


def add_calendar():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    summary = input("Please input a summary of the event >> ")
    location = input("Please input location of the event >> ")
    description = input("Please input description of event >> ")
    year, month, day, hour, minute = [int(numb) for numb in input(
        "Enter the START date and time of the event in the format [year-month-day-hour-minute] >> ").split("-")]
    endyear, endmonth, endday, endhour, endminute = [int(numb) for numb in input(
        "Enter the END date and time of the event in the format [year-month-day-hour-minute] >> ").split("-")]

    hour_adjustment = 4 #GMT to Toronto time

    event = {
        'summary': summary,
        'location': location,
        'description': description,
        'start': {
            'dateTime': convert_to_RFC_datetime(year, month, day, hour + hour_adjustment, minute),
            'timeZone': 'America/Toronto',
        },
        'end': {
            'dateTime': convert_to_RFC_datetime(endyear, endmonth, endday, endhour + hour_adjustment, endminute),
            'timeZone': 'America/Toronto',
        }
    }

    try:
        service = build('calendar', 'v3', credentials=creds)
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")

    except:
        print("Something went wrong. Please try to add your event again.")
