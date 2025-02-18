# Обработчики для администраторов

import logging
from telegram import Update
from telegram.ext import CallbackContext
from services.telegram_service import telegram_function
from logging_setup import logger
from config import sending_memes, is_command_running, SENT_MEMES, MAX_SENT_MEMES, CHANNEL_ID
from utils.error_handlers import error_handler
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import random
from services.reddit_service import get_random_meme
from services.hentai_service import get_random_hentai_video

scheduler = AsyncIOScheduler()

async def handle_admin_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Это администраторская команда.")

async def start_memes_command(update: Update, context: CallbackContext):
    # Логика команды для начала отправки мемов
    pass

async def stop_memes_command(update: Update, context: CallbackContext):
    # Логика команды для остановки отправки мемов
    pass

async def start_memes(update: Update, context: CallbackContext):
    global sending_memes
    sending_memes = True
    try:
        # Сначала отправляем случайный мем
        meme = await get_random_meme()
        if meme:
            caption = f"{meme['title']}\n\nмда, шиз\n@sh1za1337_bot"
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=meme['url'],
                caption=caption
            )
        else:
            await update.message.reply_text("❌ Не удалось получить мем.")
            return

        # Затем планируем отправку мемов раз в 1-4 часа
        interval = random.randint(3600, 14400)  # Интервал в секундах (1-4 часа)
        context.job_queue.run_repeating(
            send_random_meme,
            interval=interval,
            data={'channel_id': CHANNEL_ID}
        )
        await update.message.reply_text("✅ Отправка мемов запущена!")
    except Exception as e:
        logger.error(f"Ошибка при запуске отправки мемов: {e}")
        await update.message.reply_text("❌ Произошла ошибка при запуске отправки мемов.")

async def stop_memes(update: Update, context: CallbackContext):
    global sending_memes
    sending_memes = False
    if context.job:
        context.job.schedule_removal()
        await update.message.reply_text("Отправка мемов остановлена.")
    else:
        await update.message.reply_text("Нет активных задач отправки мемов.")

async def send_random_meme(context: CallbackContext):
    try:
        meme = await get_random_meme()
        if meme:
            caption = f"{meme['title']}\n\nмда, шиз\n@sh1za1337_bot"
            await context.bot.send_photo(
                chat_id=context.job.data['channel_id'],
                photo=meme['url'],
                caption=caption
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке мема: {e}")

async def gomeme(update: Update, context: CallbackContext):
    if sending_memes:
        # Логика для немедленной отправки мема
        await update.message.reply_text("Отправка мема...")
    else:
        await update.message.reply_text("Отправка мемов не запущена.")

async def time_command(update: Update, context: CallbackContext):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"Текущее время: {current_time}")

async def hentai_mp4_command(update: Update, context: CallbackContext):
    video = await get_random_hentai_video()  # Вызываем функцию получения Hentai видео
    if video:
        await context.bot.send_video(chat_id=CHANNEL_ID, video=video['url'], caption=video['title'])
    else:
        await update.message.reply_text("❌ Не удалось получить Hentai видео.")

def handle_admin():
    pass  # Здесь будет код для обработки администраторских команд
