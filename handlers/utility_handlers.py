# Обработчики утилит (help, about, stats)

from telegram import Update
from telegram.ext import CallbackContext
from logging_setup import logger
from services.telegram_service import telegram_function
from services.utility_service import get_help, get_about, get_stats
from utils.error_handlers import error_handler

async def handle_utility():
    await handle_help()
    await handle_about()

async def handle_help(update: Update, context: CallbackContext):
    await update.message.reply_text("Это справка по командам бота.")

async def handle_about(update: Update, context: CallbackContext):
    await update.message.reply_text("Я бот для получения мемов!")

async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "Доступные команды:\n"
        "/start - Начать взаимодействие с ботом\n"
        "/meme - Получить случайный мем\n"
        "/Warhammer - Получить мемы на тему Warhammer\n"
        "/Hentai - Получить hentai\n"
        "/Dota - Получить мемы на тему Dota"
    )
    await update.message.reply_text(help_text)

async def about_command(update: Update, context: CallbackContext):
    about_text = "Это бот для получения мемов из различных источников, включая Reddit."
    await update.message.reply_text(about_text)

async def stats_command(update: Update, context: CallbackContext):
    # Логика команды статистики
    pass
