# Точка входа
import ctypes
import sys
import io
from dotenv import load_dotenv
import os

# Загружаем переменные окружения из .env файла
load_dotenv()

CHANNEL_ID = os.getenv('CHANNEL_ID')  # Получаем значение CHANNEL_ID

# Установить кодировку для консольного вывода
if sys.platform.startswith('win'):
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)  # Установить кодировку UTF-8

from telegram import Update
from telegram.ext import Application, CommandHandler
from config import TELEGRAM_TOKEN
from logging_setup import setup_logging, logger
from handlers.meme_handlers import meme_command, warhammer_meme_command, hentai_meme_command, dota_meme_command  # Импортируем все команды
from handlers.user_handlers import start_command  # Импортируем start_command
from handlers.utility_handlers import help_command, about_command  # Импортируем команды
from handlers.admin_handlers import start_memes, stop_memes, gomeme, time_command  # Импортируем команды администратора
from handlers.meme_handlers import hentai_mp4_command  # Обновленный импорт для hentai_mp4_command

def main():
    setup_logging()
    logger.info("Инициализация бота")  # Убрали эмодзи
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('meme', meme_command))
    app.add_handler(CommandHandler('warhammer', warhammer_meme_command))
    app.add_handler(CommandHandler('hentai', hentai_meme_command))
    app.add_handler(CommandHandler('dota', dota_meme_command))
    app.add_handler(CommandHandler('start', start_command))   # Добавляем обработчик для команды /start
    app.add_handler(CommandHandler('help', help_command))  # Добавляем обработчик для команды /help
    app.add_handler(CommandHandler('about', about_command))  # Добавляем обработчик для команды /about
    app.add_handler(CommandHandler('start_memes', start_memes))  # Добавляем обработчик для команды /start_memes
    app.add_handler(CommandHandler('stop_memes', stop_memes))    # Добавляем обработчик для команды /stop_memes
    app.add_handler(CommandHandler('gomeme', gomeme))            # Добавляем обработчик для команды /gomeme
    app.add_handler(CommandHandler('time', time_command))        # Добавляем обработчик для команды /time
    app.add_handler(CommandHandler('HentaiMP4', hentai_mp4_command))  # Добавляем обработчик для команды /HentaiMP4
    logger.info("Начало polling")  # Убрали эмодзи
    app.run_polling()
    logger.info("Бот запущен и готов к работе.")

if __name__ == '__main__':
    main()