from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

## Set up Telegram Bot
import telebot
from telebot import types
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

# List of Commands
@bot.message_handler(commands=['add'])
def create_event(message):
    reply = bot.send_message(message.chat.id, "What is the song title to add?")
    def get_song_name(message):
        global song_name
        song_name = message.text
        print(song_name)
        bot.send_message(message.chat.id, "Okai adding for song title: {}\n\nPlease type in the dates in the proper format\nDate: DD/MM _(day)_\nTime: HH.MMam/pm - HH.MMam/pm\nCMI:\nAgenda:\n\nYou may leave CMI or Agenda empty.\nThe (day) is optional, doesnt affect the bot, just for your ez ref if want to paste in grpchat.\nIf you need an example enter /eg and go back to /add again to continue.\nYou can copy the below message to get started.".format(song_name), parse_mode="Markdown")
        bot.send_message(message.chat.id, "Date:\nTime:\nCMI:\nAgenda:\n ")
    bot.register_next_step_handler(reply, get_song_name)

@bot.message_handler(commands=['start'])
def welcome_message(message):
    bot.send_message(message.chat.id, "Hello, welcome to N.Trance Sync, enter /menu to begin :>")

@bot.message_handler(commands=['menu'])
def handle_m(message):

    keyboard = telebot.types.InlineKeyboardMarkup()
    b1 = telebot.types.InlineKeyboardButton('/add: Add Date(s)', callback_data='add')
    b2 = telebot.types.InlineKeyboardButton('/eg: Example Format', callback_data='eg')
    b3 = telebot.types.InlineKeyboardButton('/delete: Delete Date', callback_data='delete')
    keyboard.row(b1)
    keyboard.row(b2)
    keyboard.row(b3)
    commands = "Here are the commands :)\n/start   : Welcome message\n\n/add     : Prompts user for song title and dates to add to calendar\n\n/eg       : Provides an example in proper format/delete : Prompts user to choose which song title to delete from and will be given a list of song dates currently registered in calendar\n\n/delete : Prompts user to choose which song title to delete from and will be given a list of song dates currently registered in calendar\n"

    bot.send_message(message.chat.id, commands,reply_markup=keyboard)

@bot.callback_query_handler(func=lambda c:True)
def handle_menu_click(c):
    if (c.data == "add"):
        create_event(c.message)
    elif (c.data == "eg"):
        example_message(c.message)
    elif (c.data == "delete"):
        delete_event(c.message)

# @bot.message_handler(commands=['help'])
# def help_message(message):
#     bot.send_message(message.chat.id, "/start   : Welcome message\n/add     : Prompts user for song title and dates to add to calendar\n/delete : Prompts user to choose which song title to delete from and will be given a list of song dates currently registered in calendar\n/eg       : Provides an example in proper format")

@bot.message_handler(commands=['eg'])
def example_message(message):
    bot.send_message(message.chat.id, "Date: 01/02\nTime: 9.00am - 10.30pm\nCMI: IU :/ she'll come after 8pm (hopefully)\nAgenda: Clean till chorus\n\nDate: 02/02\nTime: 10.00am - 12.00pm\nCMI: Full crew\nAgenda: Filming at MBS")

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
            counter = 0
            for i in range(len(events)):
                if (events[i]['summary'].lower().replace(" ", "") == message.text.lower().replace(" ","")):
                    message_list += str(counter+1) + ") " + rfc3339_to_GMT_converter(events[i]['start'].get('dateTime', events[i]['start'].get('date')), events[i]['end'].get('dateTime', events[i]['end'].get('date')))+ "\n"
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

# Prepares given input events from user
@bot.message_handler(func=lambda message: True)
def event_handler(message):
  if ("Date" in message.text):
    handle_message(message.text, message)
  else:
      bot.send_message(message.chat.id, "Sorry me no understand :( Please type in correct command")

# Handles given input events from user
def handle_message(text, message):
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
            # print(dict)
            dict = {}

    global service
    try:
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
            bot.send_message(message.chat.id, "Okay added into calendar")
            print(event)
    except (HttpError, IndexError) as error:
        bot.send_message(message.chat.id, "Sorry incorrect format. Please check again and start from /add")

# Converts date-time to rf3339 format
def date_converter(date, time):
    spliced_day = date[:2]
    spliced_month = date[3:5]

    time_arr = handle_time(time)
    start_time = time_arr[0]
    end_time = time_arr[1]

    start_string = "2023-{}-{}T{}:{}:00+08:00".format(spliced_month, spliced_day, start_time[0], start_time[1])
    end_string = "2023-{}-{}T{}:{}:00+08:00".format(spliced_month, spliced_day, end_time[0], end_time[1])

    return [start_string, end_string]

# Splices given date-time
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