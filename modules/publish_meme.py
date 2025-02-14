# Модуль для обработки публикации мемов

from datetime import datetime
from telegram import Update
from telegram.ext import CallbackContext
from dotenv import load_dotenv
import os

load_dotenv()
CHANNEL_ID = os.getenv('CHANNEL_ID')

async def publish_meme_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    current_time = datetime.now()
    last_publish_time = context.user_data.get('last_publish_time', None)

    # Ограничение по времени: 60 секунд между публикациями
    if last_publish_time:
        time_diff = (current_time - last_publish_time).total_seconds()
        if time_diff < 60:  # 60 секунд
            await update.message.reply_text("❌ Вы можете отправить только одно изображение каждые 60 секунд.")
            return

    await update.message.reply_text("Теперь отправьте мне одно изображение или GIF.")
    context.user_data['awaiting_meme'] = True

async def handle_publish_meme(update: Update, context: CallbackContext):
    if context.user_data.get('awaiting_meme'):
        if update.message.photo:
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            meme_url = file.file_id
        elif update.message.animation:
            animation = update.message.animation
            file = await context.bot.get_file(animation.file_id)
            meme_url = file.file_id
        else:
            await update.message.reply_text("❌ Пожалуйста, отправьте изображение или GIF.")
            return

        # Получаем текст мема из user_data
        meme_text = context.user_data.get('meme_text', 'посмейтесь хоть чуть-чуть')

        # Публикуем мем в канал
        if update.message.photo:
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=meme_url,
                caption=f"{meme_text}\n\nМда, шиз @sh1za1337_bot. Додумался @{update.effective_user.username}"
            )
        elif update.message.animation:
            await context.bot.send_animation(
                chat_id=CHANNEL_ID,
                animation=meme_url,
                caption=f"{meme_text}\n\nМда, шиз @sh1za1337_bot. Додумался @{update.effective_user.username}"
            )

        await update.message.reply_text(f"✅ Мем успешно опубликован в канал @Sp1DShiz")
        context.user_data['last_publish_time'] = datetime.now()
        context.user_data['awaiting_meme'] = False

async def publish_meme(update, context):
    # Логика публикации мема
    pass
