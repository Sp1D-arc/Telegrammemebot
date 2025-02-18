# Работа с Telegram API
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler


def telegram_function():
    pass  # Здесь будет код для работы с Telegram API

def send_message(bot: Bot, chat_id: int, text: str):
    bot.send_message(chat_id=chat_id, text=text)
