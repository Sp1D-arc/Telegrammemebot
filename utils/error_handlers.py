# Обработка ошибок

import logging
from telegram import Update
from telegram.ext import CallbackContext
from logging_setup import logger

async def handle_error(update: Update, context: CallbackContext):
    try:
        raise context.error
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

def error_handler(update, context):
    logging.error(f"Update {update} caused error {context.error}")
    context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Произошла ошибка. Попробуйте снова.")
