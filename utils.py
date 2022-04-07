from __future__ import print_function

import datetime
import os
import os.path
import smtplib
import ssl
import webbrowser
from email.message import EmailMessage
from secrets import API_KEY, EMAIL_ADDRESS, EMAIL_PASSWORD

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

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
        print(f"Today's weather in {city} is : {weather}, {temp} Celsius but feels like {feels_like} Celsius")
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

        # Prints the next 10 events
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            try:
                formatted_datetime_obj= datetime.datetime.strptime(start,'%Y-%m-%dT%H:%M:%S-04:00').strftime('%Y-%m-%d %H:%M')
                print(formatted_datetime_obj, event['summary'])
            except: #for events with no time scheduled
                print(start, event['summary'])

    except HttpError as error:
        print(f'An error occurred: {error}')




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



def google():
    
    search=input("What would you like to search for? ")

    #selenium - set up web driver
    s = Service('/Users/callyli/Documents/chromedriver')
    driver = webdriver.Chrome(service=s)
    url = 'https://www.google.ca/search?q=' + search

    print(f'Googling "{search}"...')

    try:  
        driver.get(url)

        print("Here are the top 5 results from your search... ")
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        linkdivs=soup.find_all('div', class_='yuRUbf')[:5] #find_all returns python list (first 5 elements)
        for i, div in enumerate(linkdivs):
            print(f"({i+1}) {div.find('a')['href']}")
            
    except Exception as e:
        print(f"Sorry, an error occurred:{e}")


def maps():
    choice=input("Do you want to look up a location(l) or directions (d)? ")
    # try:

    if choice=='l':
        location=input("What's the location/address you want to look up? ")
        print(f"Searching for {location}...")
        url="https://www.google.com/maps/search/?api=1&query=" + location
        webbrowser.open(url, new=2)

    elif choice=='d':
        start=input("Input starting point: ")
        destination=input("Input destination: ")
        print(f"Retrieving directions from {start} to {destination}...")
        url=f"https://www.google.com/maps/dir/?api=1&origin={start}&destination={destination}&travelmode=driving" 
        webbrowser.open(url, new=2)

def music():
    print("Opening Spotify...")
    
    #open spotify desktop app
    path = '/Applications/Spotify.app'
    command = f'open {path}'
    os.system(command)



    
