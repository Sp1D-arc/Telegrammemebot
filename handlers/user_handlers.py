# Обработчики пользовательских команд

from services.telegram_service import telegram_function
from services.user_service import get_user, create_user, update_user, delete_user
from models.user_model import User
from telegram import Update
from telegram.ext import CallbackContext
from logging_setup import logger
from config import sending_memes, is_command_running, SENT_MEMES, MAX_SENT_MEMES, SENDER_ID, SENDER_PASSWORD, SMTP_SERVER, SMTP_PORT
from utils.error_handlers import error_handler

async def handle_user_command(update: Update, context: CallbackContext):
    # Логика обработки пользовательских команд
    pass

async def handle_user_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Это пользовательская команда.")

async def start_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Добро пожаловать!")

def handle_user():
    pass  # Здесь будет код для обработки пользовательских команд
