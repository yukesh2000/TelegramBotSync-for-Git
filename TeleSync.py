from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

## Set up Telegram Bot
import telebot
TOKEN = ""
bot = telebot.TeleBot(TOKEN, parse_mode=None)

## Set up Google API
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = None
song_name = ""

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

service = build('calendar', 'v3', credentials=creds)

## List of Commands
@bot.message_handler(commands=['start'])
def send_welcome(message):
    reply = bot.send_message(message.chat.id, "Hello, can you type song name?")
    def get_song_name(message):
        global song_name
        song_name = message.text
        print(song_name)

    bot.register_next_step_handler(reply, get_song_name)

@bot.message_handler(commands=['create'])
def create_event(message):
    bot.send_message(message.chat.id, "adding")
    service = build('calendar', 'v3', credentials=creds)
    bot.send_message(message.chat.id, "servicing")
    event = {
        'summary': 'event1?',
        'description': 'sb cmi',
        'start': {
            'dateTime': '2023-06-30T21:00:00+08:00',
            'timeZone': 'Asia/Singapore',
        },
        'end': {
            'dateTime': '2023-06-30T22:00:00+08:00',
            'timeZone': 'Asia/Singapore',
        },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    bot.send_message(message.chat.id, "Event added")

@bot.message_handler(commands=['delete'])
def delete_event(message):
    reply = bot.send_message(message.chat.id, "Which song title you want to delete from?")
    
    def handle_song_name_reply(message):
        global service
        try:
            # Call the Calendar API
            events_result = service.events().list(calendarId='primary',
                                                maxResults=100, singleEvents=True,
                                                orderBy='startTime').execute()
            events = events_result.get('items', [])

            if not events:
                print('No upcoming events found.')
                return

            message_list = ""
            filtered_id_list  = []

            for i in range(len(events)):
                if (events[i]['summary'].lower().replace(" ", "") == message.text.lower().replace(" ","")):
                    message_list += str(i+1) + ") " + rfc3339_to_GMT_converter(events[i]['start'].get('dateTime', events[i]['start'].get('date')), events[i]['end'].get('dateTime', events[i]['end'].get('date')))+ "\n"
                    filtered_id_list.append(events[i]['id'])
            
            if (len(filtered_id_list) == 0):
                bot.send_message(message.chat.id, "Sorry song name not found :( pls type /delete again")
                return

            bot.send_message(message.chat.id, message_list)
            reply_index = bot.send_message(message.chat.id, "Which number do you want to delete?")

            # Deletes the event
            def delete_event_handler(message):
                if (int(message.text) - 1 < 0):
                    bot.send_message(message.chat.id, "Sorry number not found :( pls type /delete again")
                    return

                try:
                    service.events().delete(calendarId='primary', eventId=filtered_id_list[int(message.text)-1]).execute()
                    bot.send_message(message.chat.id, "Okai deleted")
                except:
                    bot.send_message(message.chat.id, "Sorry number not found :( pls type /delete again")

            bot.register_next_step_handler(reply_index, delete_event_handler)

        except HttpError as error:
            print('An error occurred: %s' % error)
        
    bot.register_next_step_handler(reply, handle_song_name_reply)
    

def rfc3339_to_GMT_converter(start, end):
    date = start[8:10]+"/"+start[5:7]
    return date + " at " + time_check(start) + " - " + time_check(end)

def time_check(s):
    time24hr_hr = int(s.split("T")[1].split(":")[0])
    time_min = s.split("T")[1].split(":")[1]
    if (time24hr_hr >= 12):
        time24hr_hr -= 12
        return str(time24hr_hr) + "." + time_min + "pm"
    return str(time24hr_hr) + "." + time_min + "am" 

@bot.message_handler(func=lambda message: True)
def echo_message(message):
  if ("Date" in message.text):
    handle_message(message.text)

def handle_message(text):
    lines = text.splitlines()
    event_list = []
    dict = {}
    for i in range(len(lines)):
        if (len(lines[i]) > 1):
            arr = lines[i].split(":")
            dict[arr[0].rstrip()] = arr[1].strip()

        # Next event/Exit
        if (len(lines[i]) <= 1 or i == len(lines) - 1):
            event_list.append(Event(dict["Date"], dict["Time"], dict["CMI"], dict["Agenda"]))
            dict = {}

    global service
    for e in event_list:
        global song_name

        time_converted = date_converter(e.date, e.time)
        event = {
            'summary': '{}'.format(song_name) ,
            'description': 'CMI: {}\nAgenda: {}'.format(e.cmi, e.agenda),
            'start': {
                'dateTime': '{}'.format(time_converted[0]),
                'timeZone': 'Asia/Singapore',
            },
            'end': {
                'dateTime': '{}'.format(time_converted[1]),
                'timeZone': 'Asia/Singapore',
            },
        }
        service.events().insert(calendarId='primary', body=event).execute()
        print(event)

def date_converter(date, time):
    spliced_day = date[:2]
    spliced_month = date[3:5]

    time_arr = handle_time(time)
    start_time = time_arr[0]
    end_time = time_arr[1]

    start_string = "2023-{}-{}T{}:{}:00+08:00".format(spliced_month, spliced_day, start_time[0], start_time[1])
    end_string = "2023-{}-{}T{}:{}:00+08:00".format(spliced_month, spliced_day, end_time[0], end_time[1])

    return [start_string, end_string]

def handle_time(s):
    arr = s.strip().split("-")
    return [parse_time(arr[0]), parse_time(arr[1])]

def parse_time(time):
    am_pm = time.strip()[-2:]
    arr = time.strip()[:-2].split(".")
    mins = arr[1]
    hr = arr[0]

    if (len(hr) < 2):
        hr = "0" + hr

    if (am_pm == "pm"):
        hr = str(int(hr) + 12)

    return [hr, mins]

class Event:
    def __init__(self, date, time, cmi, agenda):
        self.date = date
        self.time = time
        self.cmi = cmi
        self.agenda = agenda

    def to_string(self):
        print(self.date, self.time, self.cmi, self.agenda)

bot.infinity_polling()