# Системные библиотеки
import os
import re
import sys
import random
import logging
import asyncio
import pytz
import asyncio
from datetime import datetime, timedelta

# Глобальная переменная для отслеживания состояния отправки мемов
sending_memes = False

# Глобальная переменная для отслеживания состояния выполнения команд
is_command_running = {}  # Глобальная переменная для отслеживания состояния выполнения команд

# Библиотеки для сетевых запросов
import aiohttp
import aiofiles

# Библиотеки для Telegram
import telegram
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, JobQueue, CallbackQueryHandler, ConversationHandler
from telegram.error import Conflict, RetryAfter, TimedOut

# Библиотеки для Reddit
import asyncpraw
import asyncprawcore

# Библиотека для перевода текста
from deep_translator import GoogleTranslator

# Работа с окружением и логированием
from dotenv import load_dotenv
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot_debug.log',
    filemode='a'
)
logger = logging.getLogger()

# Загрузка переменных окружения
load_dotenv()

# Точная настройка логирования
logger.setLevel(logging.DEBUG)
logger.handlers.clear()

# Консольный вывод логов
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Обработка сетевых ошибок Telegram
async def error_handler(update: object, context: CallbackContext):
    try:
        raise context.error
    except Conflict:
        logger.error("Конфликт при получении обновлений. Другой экземпляр бота активен.")
        # Можно добавить логику перезапуска или ожидания
    except RetryAfter as e:
        logger.warning(f"Превышен лимит. Ожидание {e.retry_after} секунд.")
        await asyncio.sleep(e.retry_after)
    except TimedOut:
        logger.error("Превышено время ожидания ответа от Telegram.")
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}", exc_info=True)

# Функция проверки URL
async def check_url_availability(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=10) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f"Ошибка проверки URL {url}: {e}")
        return False

# Работа с окружением и логированием
from dotenv import load_dotenv
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot_debug.log',
    filemode='a'
)
logger = logging.getLogger()

# Загрузка переменных окружения
load_dotenv()

# Точная настройка логирования
logger.setLevel(logging.DEBUG)
logger.handlers.clear()

# Файловый обработчик
file_handler = logging.FileHandler('bot_debug.log', mode='w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Добавляем обработчики
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Отключаем логи сторонних библиотек
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

# Получение токена из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Чтение данных из .env
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')

# Глобальный список для отслеживания отправленных мемов
SENT_MEMES = set()
MAX_SENT_MEMES = 500  # Максимальное количество мемов в истории

async def get_random_meme(subreddit_names=None, limit=200):
    """
    Асинхронное получение случайного мема с использованием AsyncPRAW
    """
    try:
        logger.info("🚀 Начало процесса получения мема")
        
        # Расширенная диагностика сети
        import socket
        import ssl
        
        def check_internet_connection():
            try:
                # Проверка DNS
                socket.gethostbyname('www.reddit.com')
                
                # Проверка SSL-соединения
                context = ssl.create_default_context()
                with socket.create_connection(("www.reddit.com", 443)) as sock:
                    with context.wrap_socket(sock, server_hostname="www.reddit.com") as secure_sock:
                        logger.info("✅ Успешное SSL-соединение с Reddit")
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка подключения: {e}")
                return False
        
        if not check_internet_connection():
            logger.warning("❌ Нет доступа к Reddit")
            return None
        
        # Расширенная отладка Reddit API
        logger.info(f"Reddit Client ID: {os.getenv('REDDIT_CLIENT_ID', 'НЕ УСТАНОВЛЕН')[:5]}...")
        logger.info(f"Reddit Client Secret: {'*' * 10}")
        logger.info(f"Reddit User Agent: {os.getenv('REDDIT_USER_AGENT', 'TelegramMemeBot/1.5')}")
        
        try:
            reddit = asyncpraw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent=os.getenv('REDDIT_USER_AGENT', 'TelegramMemeBot/1.5')
            )
        except Exception as auth_error:
            logger.critical(f"❌ Ошибка аутентификации Reddit: {auth_error}")
            return None
        
        if not subreddit_names:
            subreddit_names = [
                'memes', 'dankmemes', 'funny', 'ru_memes', 'Pikabu'
            ]
        
        logger.info(f"Список суб-реддитов для поиска: {subreddit_names}")
        
        all_memes = []
        for subreddit_name in subreddit_names:
            try:
                subreddit = await reddit.subreddit(subreddit_name)
                hot_memes = []
                async for post in subreddit.hot(limit=limit):
                    if post.url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        hot_memes.append(post)
                
                all_memes.extend(hot_memes)
                logger.info(f"Получено {len(hot_memes)} мемов из {subreddit_name}")
            except asyncprawcore.exceptions.Forbidden as forbidden_error:
                logger.error(f"❌ Доступ запрещен к {subreddit_name}: {forbidden_error}")
            except asyncprawcore.exceptions.NotFound as not_found_error:
                logger.error(f"❌ Суб-реддит не найден {subreddit_name}: {not_found_error}")
            except asyncprawcore.exceptions.RequestException as request_error:
                logger.error(f"❌ Ошибка запроса к {subreddit_name}: {request_error}")
            except Exception as e:
                logger.error(f"❌ Ошибка при получении мемов из {subreddit_name}: {e}", exc_info=True)
        
        logger.info(f"Всего собрано мемов: {len(all_memes)}")
        
        valid_memes = [
            meme for meme in all_memes 
            if meme.url not in SENT_MEMES
        ]
        
        logger.info(f"Найдено валидных мемов: {len(valid_memes)}")
        
        if not valid_memes:
            logger.warning("Очистка истории отправленных мемов")
            SENT_MEMES.clear()
            valid_memes = all_memes
        
        if not valid_memes:
            logger.warning("❌ Не удалось найти подходящие мемы")
            return None
        
        selected_meme = random.choice(valid_memes)
        
        # Перевод заголовка, если он на иностранном языке
        title = selected_meme.title
        translated_title = GoogleTranslator(source='auto', target='ru').translate(title)

        selected_meme.title = translated_title  # Обновляем заголовок на русский
        
        SENT_MEMES.add(selected_meme.url)
        
        if len(SENT_MEMES) > MAX_SENT_MEMES:
            logger.info("Достигнут максимум отправленных мемов, очистка истории")
            SENT_MEMES.clear()
        
        logger.info(f"✅ Выбран мем: {selected_meme.title} из {selected_meme.subreddit}")
        
        return {
            'title': selected_meme.title,
            'url': selected_meme.url,
            'author': selected_meme.author,
            'subreddit': selected_meme.subreddit
        }
    except Exception as e:
        logger.critical(f"❌ Критическая ошибка в get_random_meme: {e}", exc_info=True)
        return None
    finally:
        # Закрываем сессию Reddit
        try:
            await reddit.close()
        except Exception:
            pass

async def send_meme_to_channel(context: CallbackContext):
    try:
        logger.info("🚀 Начало процесса отправки мема")
        meme = await get_random_meme()  # Получение мема
        logger.info(f"Отправка мема с URL: {meme['url']}")  # Логирование URL
        
        # Формируем подпись
        caption = f"{meme['title']}\n\nмда, шиз\n@sh1za1337_bot"  # Подпись для мема
        
        # Отправляем мем в канал с подписью
        await context.bot.send_photo(
            chat_id=CHANNEL_ID, 
            photo=meme['url'], 
            caption=caption
        )
        
        logger.info("✅ Мем успешно отправлен")
    except Exception as e:
        logger.error(f"Ошибка при отправке мема: {e}", exc_info=True)

async def start_command(update: Update, context: CallbackContext):
    try:
        if update.message.text.startswith('/start'):
            keyboard = [
                ["/Hentai", "/Warhammer"],
                ["/Dota"],
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Добро пожаловать! Выберите команду:", reply_markup=reply_markup)
    except Exception as e:
        logger.critical(f"❌ Критическая ошибка в start_command для {update.effective_user.id}: {e}", exc_info=True)

async def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'get_meme':
        await meme_command(query.message, context)
    elif query.data == 'stats':
        await stats_command(query.message, context)

def setup_meme_job(application: Application):
    # Удаляем автоматическую отправку мемов
    pass

async def help_command(update: Update, context: CallbackContext):
    """
    Обработчик команды /help
    """
    logger.info("Received /help command")
    
    try:
        # Отладочный вывод типа чата
        logger.debug(f"Chat type: {update.effective_chat.type}")
        
        # Проверяем тип чата
        if update.effective_chat.type != "private":
            logger.warning("Command /help only in private messages")
            await update.message.reply_text("🚫 Command /help is only available in private messages.")
            return

        help_text = (
            "📋 Список команд:\n\n"
            "🤖 /start - Запустить бота\n"
            "🤣 /meme - Получить случайный мем\n"
            "📋 /help - Список всех команд\n"
            "🌐 /about - Информация о боте\n"
            "📊 /stats - Статистика мемов\n\n"
            "🖼️ Мемы публикуются в канале: @Sp1DShiz\n\n"
            "Команды для администраторов:\n"
            "/start_memes - Начать отправку мемов в канал (только для администраторов).\n"
            "/stop_memes - Остановить отправку мемов (только для администраторов)."
        )
        
        await update.message.reply_text(help_text)
    
    except Exception as e:
        logger.error(f"Error in help_command: {e}", exc_info=True)

async def about_command(update: Update, context: CallbackContext):
    await update.message.reply_text("🤖 *Мем-Бот* 🚀\n\n" 
    "✨ Версия бота: 2.0\n" 
    "👨‍💻 Разработчик: @sp1dpwnzero\n\n" 
    "📜 Этот бот предназначен для поиска и отправки мемов из Reddit.\n" 
    "🎉 Функции:\n" 
    "• Отправка случайных мемов в личные сообщения\n" 
    "• Отправка мемов в канал для администратора\n" 
    "• Интерактивные команды для пользователей\n\n" 
    "😄 Приятного использования! \n\n"
    "⚠️ Внимание! Некоторые функции могут не работать как ожидается, но это их вина.")

async def stats_command(update: Update, context: CallbackContext):
    """
    Обработчик команды /stats
    """
    logger.info("Received /stats command")
    
    try:
        # Отладочный вывод типа чата
        logger.debug(f"Chat type: {update.effective_chat.type}")
        
        # Проверяем тип чата
        if update.effective_chat.type != "private":
            logger.warning("Command /stats only in private messages")
            await update.message.reply_text("🚫 Command /stats is only available in private messages.")
            return

        # Отправляем статистику
        await update.message.reply_text(
            "📊 Meme statistics:\n\n"
            "🚧 Functionality in development\n"
            "🤖 Bot is in testing stage"
        )
    
    except Exception as e:
        logger.error(f"Error in stats_command: {e}", exc_info=True)

import random

async def meme_command(update: Update, context: CallbackContext):
    try:
        chat_type = update.message.chat.type
        if chat_type == 'group' or chat_type == 'supergroup':
            messages = [
                "🔒 Подготовка к запуску мемов..."
            ]
            await update.message.reply_text(random.choice(messages))
        else:
            await update.message.reply_text("Мем будет отправлен в личные сообщения!")
        meme = await get_random_meme()  # Получение мема
        if meme:
            if not meme['url'].endswith(('.png', '.jpg', '.jpeg', '.gif')):
                await update.message.reply_text("❌ Полученный URL не является изображением.")
                return
            caption = f"{meme['title']}\n\nмда, шиз\n@sh1za1337_bot"
            await update.message.reply_photo(
                photo=meme['url'],
                caption=caption
            )
            if chat_type != 'group' and chat_type != 'supergroup':
                await update.message.reply_text("✅ Мем успешно отправлен в личные сообщения!")
        else:
            await update.message.reply_text("❌ Не удалось получить мем.")
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /meme: {e}", exc_info=True)
        await update.message.reply_text("❌ Произошла ошибка при получении мема")

async def handle_command(update: Update, context: CallbackContext):
    """
    Универсальный обработчик неизвестных команд
    """
    logger.info(f"Unhandled command from {update.effective_user}")
    
    try:
        if update.message.text.startswith('/start'):
            await update.message.reply_text("Добро пожаловать! Я бот для мемов. Пожалуйста, используйте команду /meme для получения мемов.")
        elif update.message.text.startswith('/stop_memes'):
            await stop_memes_command(update, context)
        elif update.message.text.startswith('/start_memes'):
            await start_memes_command(update, context)
        else:
            await update.message.reply_text(
                "❓ Неизвестная команда. Используйте /help для списка команд."
            )
    
    except Exception as e:
        logger.error(f"Error in handle_command: {e}", exc_info=True)

async def handle_user_meme(update: Update, context: CallbackContext):
    """
    Обработчик для пользовательских мемов
    Принимает картинку от пользователя и публикует её в канале
    """
    try:
        if not update.message.photo:
            await update.message.reply_text("❌ Пожалуйста, отправь мем в виде изображения")
            return
        
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        sender = update.effective_user
        sender_name = sender.username or f"{sender.first_name} {sender.last_name}".strip()
        
        caption_parts = []
        caption_parts.append(f"Додумался @{sender_name}")
        
        if update.message.caption:
            caption_parts.append(f"\n{update.message.caption}")
        
        caption_parts.extend([
            "\nмда, шиз",
            "@sh1za1337_bot"
        ])
        
        caption = "\n".join(caption_parts)
        
        await context.bot.send_photo(
            chat_id=CHANNEL_ID, 
            photo=file.file_id, 
            caption=caption
        )
        
        await update.message.reply_text("✅ Мем опубликован в канале!")
        
        logger.info(f"Пользовательский мем от {sender_name} опубликован в канале")
    
    except Exception as e:
        logger.error(f"❌ Ошибка при публикации пользовательского мема: {e}", exc_info=True)
        await update.message.reply_text("😱 Произошла ошибка при публикации мема")

async def time_command(update: Update, context: CallbackContext):
    try:
        if str(update.effective_user.id) != os.getenv('ADMIN_USER_ID'):
            await update.message.reply_text("🚫 У вас нет прав для выполнения этой команды.")
            return
        
        jobs = context.job_queue.jobs()
        meme_job = next((job for job in jobs if job.name == 'send_meme'), None)
        
        if meme_job:
            next_run_time = meme_job.data.get('next_run_time', datetime.now(pytz.utc))
            
            remaining_time = next_run_time - datetime.now(pytz.utc)
            
            hours, remainder = divmod(remaining_time.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            message = (
                f"⏰ До следующего мема:\n"
                f"🕒 Осталось: {int(hours)} ч. {int(minutes)} мин. {int(seconds)} сек.\n"
                f"🔜 Следующая отправка: {next_run_time.astimezone(pytz.timezone('Europe/Moscow'))}"
            )
            
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("❌ Задача отправки мемов не найдена")
    except Exception as e:
        logger.error(f"Ошибка в команде /time: {e}", exc_info=True)
        await update.message.reply_text("❌ Произошла ошибка при получении времени")

async def gomeme_command(update: Update, context: CallbackContext):
    try:
        if str(update.effective_user.id) != os.getenv('ADMIN_USER_ID'):
            warning_message = (
                "⚠️ ВНИМАНИЕ! НЕСАНКЦИОНИРОВАННАЯ ПОПЫТКА ДОСТУПА! ⚠️\n\n"
                "🔒 Эта команда строго конфиденциальна и предназначена ТОЛЬКО для администратора.\n"
                "👀 Все ваши действия ЛОГИРУЮТСЯ и будут НЕМЕДЛЕННО ДОЛОЖЕНЫ.\n"
                "💀 Повторные попытки могут привести к БЛОКИРОВКЕ и УГОЛОВНОЙ ОТВЕТСТВЕННОСТИ!\n\n"
                "🚨 НЕМЕДЛЕННО ПРЕКРАТИТЕ ПОПЫТКИ НЕСАНКЦИОНИРОВАННОГО ДОСТУПА! 🚨"
            )
            logger.warning(
                f"ВНИМАНИЕ! Несанкционированная попытка доступа к /gomeme. "
                f"Пользователь: {update.effective_user.username} (ID: {update.effective_user.id})"
            )
            await update.message.reply_text(warning_message)
            return
        meme = await get_random_meme()
        if not meme:
            await update.message.reply_text("❌ Не удалось получить мем")
            return
        caption = f"{meme['title']}\n\nмда, шиз\n@sh1za1337_bot"
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=meme['url'],
            caption=caption
        )
        await update.message.reply_text("✅ Мем успешно отправлен в канал!")
    except Exception as e:
        logger.error(f"Ошибка в команде /gomeme: {e}", exc_info=True)
        await update.message.reply_text("❌ Не удалось отправить мем")

async def send_memes(context: CallbackContext):
    global sending_memes
    logger.info("Запуск отправки мемов...")
    while sending_memes:
        meme = await get_random_meme()  # Получение мема
        if meme:
            caption = f"{meme['title']}\n\nмда, шиз\n@sh1za1337_bot"  # Подпись для мема
            logger.info(f"Отправка мема: {meme['title']}")
            await context.bot.send_photo(
                chat_id=CHANNEL_ID, 
                photo=meme['url'], 
                caption=caption
            )
            logger.info(f"Мем отправлен: {meme['title']}")
        await asyncio.sleep(random.randint(3600, 14400))  # Отправка мема каждые 1-4 часа

async def start_memes_command(update: Update, context: CallbackContext):
    global sending_memes
    admin_id = os.getenv('ADMIN_USER_ID')  # ID администратора
    if update.effective_user.id != int(admin_id):
        warning_message = (
            "⚠️ ВНИМАНИЕ! НЕСАНКЦИОНИРОВАННАЯ ПОПЫТКА ДОСТУПА! ⚠️\n\n"
            "🔒 Эта команда строго конфиденциальна и предназначена ТОЛЬКО для администратора.\n"
            "👀 Все ваши действия ЛОГИРУЮТСЯ и будут НЕМЕДЛЕННО ДОЛОЖЕНЫ.\n"
            "💀 Повторные попытки могут привести к БЛОКИРОВКЕ и УГОЛОВНОЙ ОТВЕТСТВЕННОСТИ!\n\n"
            "🚨 НЕМЕДЛЕННО ПРЕКРАТИТЕ ПОПЫТКИ НЕСАНКЦИОНИРОВАННОГО ДОСТУПА! 🚨"
        )
        logger.warning(
            f"ВНИМАНИЕ! Несанкционированная попытка доступа к /start_memes. "
            f"Пользователь: {update.effective_user.username} (ID: {update.effective_user.id})"
        )
        await update.message.reply_text(warning_message)
        return

    if not sending_memes:
        sending_memes = True
        await update.message.reply_text("Начинаю отправку мемов!")
        asyncio.create_task(send_memes(context))  # Запускаем отправку мемов в отдельной задаче
    else:
        await update.message.reply_text("Отправка мемов уже активна.")

async def stop_memes_command(update: Update, context: CallbackContext):
    global sending_memes
    admin_id = os.getenv('ADMIN_USER_ID')  # ID администратора
    if update.effective_user.id != int(admin_id):
        warning_message = (
            "⚠️ ВНИМАНИЕ! НЕСАНКЦИОНИРОВАННАЯ ПОПЫТКА ДОСТУПА! ⚠️\n\n"
            "🔒 Эта команда строго конфиденциальна и предназначена ТОЛЬКО для администратора.\n"
            "👀 Все ваши действия ЛОГИРУЮТСЯ и будут НЕМЕДЛЕННО ДОЛОЖЕНЫ.\n"
            "💀 Повторные попытки могут привести к БЛОКИРОВКЕ и УГОЛОВНОЙ ОТВЕТСТВЕННОСТИ!\n\n"
            "🚨 НЕМЕДЛЕННО ПРЕКРАТИТЕ ПОПЫТКИ НЕСАНКЦИОНИРОВАННОГО ДОСТУПА! 🚨"
        )
        logger.warning(
            f"ВНИМАНИЕ! Несанкционированная попытка доступа к /stop_memes. "
            f"Пользователь: {update.effective_user.username} (ID: {update.effective_user.id})"
        )
        await update.message.reply_text(warning_message)
        return

    sending_memes = False
    await update.message.reply_text("Остановил отправку мемов.")

async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "📋 Список команд:\n\n"
        "🤖 /start - Запустить бота\n"
        "🤣 /meme - Получить случайный мем\n"
        "📋 /help - Список всех команд\n"
        "🌐 /about - Информация о боте\n"
        "📊 /stats - Статистика мемов\n\n"
        "🖼️ Мемы публикуются в канале: @Sp1DShiz\n\n"
        "Команды для администраторов:\n"
        "/start_memes - Начать отправку мемов в канал (только для администраторов).\n"
        "/stop_memes - Остановить отправку мемов (только для администраторов)."
    )
    await update.message.reply_text(help_text)

import random

async def create_meme_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Отправьте текст для демотиватора:")
    context.user_data['awaiting_meme_text'] = True

async def handle_message(update: Update, context: CallbackContext):
    if context.user_data.get('awaiting_meme_text'):
        meme_text = update.message.text
        context.user_data['meme_text'] = meme_text
        await update.message.reply_text("Теперь отправьте изображение для демотиватора:")
        context.user_data['awaiting_meme_text'] = False
        context.user_data['awaiting_meme_image'] = True
    elif context.user_data.get('awaiting_meme_image'):
        image_file = update.message.photo[-1].file_id
        new_file = await context.bot.get_file(image_file)
        await new_file.download_to_drive('temp_image.jpg')

        # Создаем демотиватор
        meme_text = context.user_data['meme_text']
        image = Image.open('temp_image.jpg')
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        draw.text((10, 10), meme_text, fill="white", font=font)
        image.save('demotivator.jpg')

        await update.message.reply_photo(photo=open('demotivator.jpg', 'rb'))
        context.user_data['awaiting_meme_image'] = False
        os.remove('temp_image.jpg')
        os.remove('demotivator.jpg')

async def fun_fact_command(update: Update, context: CallbackContext):
    fact = random.choice(fun_facts)
    await update.message.reply_text(f"Вот случайный факт: {fact}")

async def discuss_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Какой ваш любимый мем? Поделитесь с нами!")

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from telegram import ReplyKeyboardMarkup

# Состояния для ConversationHandler
TEXT, PHOTO = range(2)

async def creatememe_command(update: Update, context: CallbackContext):
    await update.message.reply_text("📝 Отправь текст для демотиватора.")
    return TEXT

async def handle_text(update: Update, context: CallbackContext):
    context.user_data['meme_text'] = update.message.text
    await update.message.reply_text("🖼️ Теперь отправь изображение для демотиватора.")
    return PHOTO

async def handle_photo(update: Update, context: CallbackContext):
    # Получаем изображение
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    
    # Скачиваем изображение
    image_path = f"temp_{update.effective_user.id}.jpg"
    await file.download_to_drive(image_path)
    
    # Создаём демотиватор
    meme_text = context.user_data.get('meme_text', 'Мем без текста')
    output_path = f"demotivator_{update.effective_user.id}.jpg"
    create_demotivator(image_path, meme_text, output_path)
    
    # Отправляем демотиватор пользователю
    with open(output_path, 'rb') as photo:
        await update.message.reply_photo(photo=photo)
    
    # Очищаем временные файлы
    os.remove(image_path)
    os.remove(output_path)
    
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("❌ Создание демотиватора отменено.")
    return ConversationHandler.END

# Добавление ConversationHandler в приложение
def setup_creatememe_handler(application):
    creatememe_handler = ConversationHandler(
        entry_points=[CommandHandler('creatememe', creatememe_command)],
        states={
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
            PHOTO: [MessageHandler(filters.PHOTO, handle_photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(creatememe_handler)

async def publish_meme_command(update: Update, context: CallbackContext):
    try:
        # Получаем текст мема из user_data
        meme_text = context.user_data.get('meme_text', 'Мем без текста')
        
        # Получаем URL мема из user_data или другого источника
        meme_url = context.user_data.get('meme_url', None)
        
        if not meme_url:
            await update.message.reply_text("❌ Изображение не найдено. Сначала создайте мем с помощью /creatememe.")
            return
        
        # Публикуем мем в канал
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=meme_url,
            caption=meme_text
        )
        
        await update.message.reply_text("✅ Мем успешно опубликован!")
    
    except Exception as e:
        logger.error(f"Ошибка при публикации мема: {e}", exc_info=True)
        await update.message.reply_text("❌ Произошла ошибка при публикации мема.")

async def warhammer_meme_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id in is_command_running and is_command_running[chat_id]:
        await update.message.reply_text("❌ Команда уже выполняется. Пожалуйста, подождите.")
        return

    is_command_running[chat_id] = True
    try:
        await update.message.reply_text("Подождите минуту...")
        meme = await get_random_meme(subreddit_names=['Warhammer'])
        if meme:
            caption = f"{meme.get('title', 'За Императора?')}\n\nмда, шиз\n@sh1za1337_bot"
            await update.message.reply_photo(
                photo=meme['url'],
                caption=caption
            )
        else:
            await update.message.reply_text("❌ Не удалось получить мем из сабреддита.")
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /warhammer_meme: {e}", exc_info=True)
        await update.message.reply_text("😱 Произошла ошибка при получении мема.")
    finally:
        is_command_running[chat_id] = False

async def hentai_meme_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id in is_command_running and is_command_running[chat_id]:
        await update.message.reply_text("❌ Команда уже выполняется. Пожалуйста, подождите.")
        return

    is_command_running[chat_id] = True
    try:
        await update.message.reply_text("Сейчас найду для вас самое вкусное...")
        meme = await get_random_meme(subreddit_names=['Hentai'])
        if isinstance(meme, dict) and 'url' in meme:
            caption = f"{meme.get('title', 'Уф, вот это хентай! 😏')}\n\nмда, шиз\n@sh1za1337_bot"
            await update.message.reply_photo(photo=meme['url'], caption=caption)
        else:
            await update.message.reply_text("❌ Не удалось получить мем из сабреддита Hentai.")
    except Exception as e:
        logger.error(f"Ошибка при получении мема: {e}", exc_info=True)

        # Удаляем сообщение с ошибкой (если оно было отправлено)
        try:
            await update.message.delete()
        except Exception as delete_error:
            logger.error(f"Ошибка при удалении сообщения: {delete_error}")

        # Отправляем нейтральное сообщение
        await update.message.reply_text("Что-то пошло не так. Попробуйте позже!")
    finally:
        is_command_running[chat_id] = False

async def dota_meme_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if chat_id in is_command_running and is_command_running[chat_id]:
        await update.message.reply_text("❌ Команда уже выполняется. Пожалуйста, подождите.")
        return

    is_command_running[chat_id] = True
    try:
        await update.message.reply_text("Подождите минуту...")
        meme = await get_random_meme(subreddit_names=['dota'])
        if meme:
            caption = f"{meme.get('title', '5 мажоров выйграл?')}\n\nмда, шиз\n@sh1za1337_bot"  # Описание для Dota
            try:
                await update.message.reply_photo(
                    photo=meme['url'],
                    caption=caption
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке фото: {e}", exc_info=True)
                if update.message:
                    await update.message.delete()
                await update.message.reply_text("Что-то пошло не так. Попробуйте позже!")
        else:
            await update.message.reply_text("❌ Не удалось получить мем из сабреддита Dota.")
    except Exception as e:
        logger.error(f"Ошибка при получении мема: {e}", exc_info=True)
        if update.message:
            try:
                await update.message.delete()
            except Exception as delete_error:
                logger.error(f"Ошибка при удалении сообщения: {delete_error}", exc_info=True)
        await update.message.reply_text("Что-то пошло не так. Попробуйте позже!")
    finally:
        is_command_running[chat_id] = False

async def reff_command(update: Update, context: CallbackContext):
    pass

import textwrap
from PIL import Image, ImageDraw, ImageFont

def create_demotivator(image_path, text, output_path):
    # Загружаем изображение
    image = Image.open(image_path)
    width, height = image.size
    
    # Создаём новое изображение для демотиватора с увеличенными рамками
    demotivator = Image.new('RGB', (width + 80, height + 180), color='black')
    
    # Вставляем оригинальное изображение
    demotivator.paste(image, (40, 40))  # Увеличиваем отступы для изображения
    
    # Добавляем текст
    draw = ImageDraw.Draw(demotivator)
    font_path = "fonts/Roboto-BlackItalic.ttf"  # Указываем имя шрифта
    font = ImageFont.truetype(font_path, 56)  # Размер шрифта 56
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]  # Ширина текста
    text_height = text_bbox[3] - text_bbox[1]  # Высота текста
    
    # Проверка на длину текста
    if text_width > (width - 80):
        wrapped_text = textwrap.fill(text, width=30)  # 30 символов на строку
    else:
        wrapped_text = text
    
    # Рисуем текст
    draw.text(
        ((width + 80 - text_width) // 2, height + 60),  # Увеличиваем отступ для текста
        wrapped_text,
        fill="white",
        font=font
    )
    
    # Сохраняем демотиватор
    demotivator.save(output_path)

def main():
    logger.info("🤖 Инициализация бота...")
    if not TELEGRAM_TOKEN:
        logger.critical("❌ TELEGRAM_TOKEN не установлен!")
        raise ValueError("Токен Telegram не найден")
    logger.info("Bot token status: PRESENT")
    logger.info("Telegram Bot starting...")
    application = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .build()
    )
    logger.info(f"✅ Приложение создано с токеном: {TELEGRAM_TOKEN[:10]}...")
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('about', about_command))
    application.add_handler(CommandHandler('stats', stats_command))
    application.add_handler(CommandHandler('meme', meme_command))
    application.add_handler(CommandHandler('time', time_command))
    application.add_handler(CommandHandler('gomeme', gomeme_command))
    application.add_handler(CommandHandler('start_memes', start_memes_command))
    application.add_handler(CommandHandler('stop_memes', stop_memes_command))
    
    # Добавляем обработчик для создания демотиватора
    setup_creatememe_handler(application)
    
    # Добавляем обработчик для публикации мема
    application.add_handler(CommandHandler('publishmeme', publish_meme_command))
    
    application.add_handler(CommandHandler('hentai', hentai_meme_command))
    application.add_handler(CommandHandler('warhammer', warhammer_meme_command))
    application.add_handler(CommandHandler('dota', dota_meme_command))

    application.add_error_handler(error_handler)
    logger.info("🚀 Начало polling...")
    application.run_polling(
        drop_pending_updates=True,
        stop_signals=None
    )

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("🛑 Работа бота прервана пользователем")
    except Exception as e:
        print(f"❌ Непредвиденная ошибка: {e}")
        import traceback
        traceback.print_exc()
