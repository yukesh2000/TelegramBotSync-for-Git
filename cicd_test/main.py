## Set up Telegram Bot
import telebot
from telebot import types
TOKEN = "6202926078:AAFT8f1aoe7cW9zeOFpfHXjXySsYalzqgoc"
bot = telebot.TeleBot(TOKEN, parse_mode=None)

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

# @bot.message_handler(commands=['help'])
# def help_message(message):
#     bot.send_message(message.chat.id, "/start   : Welcome message\n/add     : Prompts user for song title and dates to add to calendar\n/delete : Prompts user to choose which song title to delete from and will be given a list of song dates currently registered in calendar\n/eg       : Provides an example in proper format")

@bot.message_handler(commands=['eg'])
def example_message(message):
    bot.send_message(message.chat.id, "Date: 01/02\nTime: 9.00am - 10.30pm\nCMI: IU :/ she'll come after 8pm (hopefully)\nAgenda: Clean till chorus\n\nDate: 02/02\nTime: 10.00am - 12.00pm\nCMI: Full crew\nAgenda: Filming at MBS")

bot.infinity_polling()