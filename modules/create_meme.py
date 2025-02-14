# Модуль для создания мемов

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import logging
import os

logger = logging.getLogger(__name__)

TEXT, PHOTO = range(2)

async def create_meme(update, context):
    # Логика создания мема
    pass

async def creatememe_command(update: Update, context: CallbackContext):
    logger.info("Вызвана команда /creatememe")
    await update.message.reply_text("📝 Отправь текст для демотиватора.")
    return TEXT

async def handle_text(update: Update, context: CallbackContext):
    logger.info("Вызвана функция handle_text")
    context.user_data['meme_text'] = update.message.text
    logger.info(f"Получен текст для мема: {update.message.text}")
    await update.message.reply_text("📸 Теперь отправь изображение для демотиватора.")
    context.user_data['awaiting_meme_image'] = True
    logger.info("Состояние 'awaiting_meme_image' установлено в True")
    return PHOTO

async def handle_photo(update: Update, context: CallbackContext):
    logger.info("Вызвана функция handle_photo")
    try:
        if update.message.photo:
            logger.info("Получено сообщение с изображением")
            photo = update.message.photo[-1]
            logger.info(f"Получено изображение: {photo.file_id}")
            file = await context.bot.get_file(photo.file_id)
            logger.info(f"Файл изображения получен: {file.file_id}")
            image_path = f"temp_{update.effective_user.id}.jpg"
            await file.download_to_drive(image_path)
            logger.info(f"Изображение сохранено: {image_path}")
            logger.info("Начинаем обработку изображения...")
            meme_text = context.user_data.get('meme_text', 'Мем без текста')
            output_path = f"demotivator_{update.effective_user.id}.jpg"
            logger.info(f"Начинаем создание демотиватора с текстом: {meme_text}")
            create_demotivator(image_path, meme_text, output_path)
            logger.info(f"Демотиватор успешно создан: {output_path}")
            logger.info("Отправляем демотиватор пользователю...")
            with open(output_path, 'rb') as photo:
                await update.message.reply_photo(photo=photo)
            logger.info(f"Демотиватор отправлен пользователю: {update.effective_user.id}")
            logger.info("Очищаем временные файлы...")
            os.remove(image_path)
            os.remove(output_path)
            logger.info(f"Временные файлы удалены")
        else:
            logger.warning("Нет изображения в сообщении.")
            await update.message.reply_text("❌ Пожалуйста, отправьте изображение для демотиватора.")
    except Exception as e:
        logger.error(f"Ошибка в handle_photo: {e}")
        await update.message.reply_text("❌ Произошла ошибка при создании демотиватора. Попробуйте еще раз.")

    return ConversationHandler.END
