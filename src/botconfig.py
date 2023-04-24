import uuid
import telebot
import os

SALT = "b9dd2d857993f0d2"  # Пускай остается
INFO_MESSAGE = """
Welcome to PythonLabs Bot.
Usage:
/register - Registration in our bot
/login - Sign in our bot
/predict - Try to classificate your image
/logout - Logout from our bot"""
REGISTER_MESSAGE = "Please enter your password to continue.."
LOGIN_MESSAGE = "Please enter your password to auth.."
BOT_FOLDER = "./tmp"
TOKEN = os.environ.get('BOT_TOKEN')
BOT = telebot.TeleBot(TOKEN)