# Системные библиотеки
import os
import sys
import random
import logging
import asyncio
import pytz
from datetime import datetime, timedelta

# Библиотеки для сетевых запросов
import aiohttp
import aiofiles

# Библиотеки для Telegram
import telegram
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, JobQueue
from telegram.error import Conflict, RetryAfter, TimedOut

# Библиотеки для Reddit
import asyncpraw
import asyncprawcore

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
        logger.info(f"Reddit User Agent: {os.getenv('REDDIT_USER_AGENT', 'НЕ УСТАНОВЛЕН')}")
        
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
    """
    Отправка случайного мема в канал с расширенной отладкой
    """
    try:
        logger.info("🚀 Начало процесса отправки мема")
        
        # Проверка прав доступа к каналу
        try:
            channel_info = await context.bot.get_chat(CHANNEL_ID)
            logger.info(f"Информация о канале: {channel_info}")
        except Exception as channel_error:
            logger.error(f"❌ Ошибка получения информации о канале: {channel_error}")
            return
        
        meme = await get_random_meme()
        
        if not meme:
            logger.warning("❌ Не удалось получить мем")
            return
        
        caption = f"{meme['title']}\n\nмда, шиз\n@sh1za1337_bot"
        
        try:
            logger.info(f"📸 Попытка отправить мем в канал: {CHANNEL_ID}")
            logger.info(f"🔗 URL мема: {meme['url']}")
            
            # Проверка доступности URL-изображения
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(meme['url']) as response:
                        if response.status != 200:
                            logger.error(f"❌ Недоступное изображение: {meme['url']} (статус: {response.status})")
                            return
            except Exception as url_error:
                logger.error(f"❌ Ошибка проверки URL: {url_error}")
                return
            
            await context.bot.send_photo(
                chat_id=CHANNEL_ID, 
                photo=meme['url'], 
                caption=caption
            )
            
            logger.info(f"✅ Мем успешно отправлен из {meme['subreddit']}")
        except Exception as send_error:
            logger.error(f"❌ Ошибка отправки мема в канал: {send_error}")
            
            # Попытка отправить в личные сообщения администратора
            try:
                admin_id = os.getenv('ADMIN_USER_ID')
                logger.info(f"📧 Попытка уведомить администратора: {admin_id}")
                
                await context.bot.send_message(
                    chat_id=admin_id, 
                    text=f"❌ Не удалось отправить мем в канал:\n{send_error}\n\n"
                         f"Мем: {meme['url']}\n"
                         f"Суб-реддит: {meme['subreddit']}"
                )
            except Exception as admin_error:
                logger.critical(f"❌ Критическая ошибка уведомления администратора: {admin_error}")
    
    except Exception as e:
        logger.critical(f"❌ Критическая ошибка в send_meme_to_channel: {e}", exc_info=True)

async def start_command(update: Update, context: CallbackContext):
    """
    Обработчик команды /start с расширенной отладкой
    """
    logger.info(f"🔍 Получена команда /start от пользователя: {update.effective_user.id}")
    
    try:
        # Отладочный вывод всей информации о чате
        logger.debug(f"Полная информация о чате: {update.effective_chat}")
        logger.debug(f"Информация о пользователе: {update.effective_user}")
        
        # Проверяем тип чата с логированием
        chat_type = update.effective_chat.type
        logger.info(f"Тип чата: {chat_type}")
        
        if chat_type != "private":
            logger.warning(f"Команда /start вне личных сообщений от {update.effective_user.id}")
            await update.message.reply_text("🚫 Команда /start доступна только в личных сообщениях.")
            return

        # Отправляем приветственное сообщение
        user_name = update.effective_user.first_name or "Друг"
        start_text = (
            f'👋 Привет, {user_name}!\n\n'
            '🤣 Я бот, который будет присылать мемы.\n\n'
            '📋 Доступные команды:\n'
            '• /start - Запуск бота\n'
            '• /meme - Получить случайный мем\n'
            '• /help - Список всех команд\n'
            '• /about - Информация о боте\n'
            '• /stats - Статистика мемов\n\n'
            f'🚀 Мемы публикуются в канале: {CHANNEL_ID}'
        )
        
        await update.message.reply_text(start_text)
        logger.info(f"✅ Приветственное сообщение отправлено пользователю: {update.effective_user.id}")
    
    except Exception as e:
        logger.critical(f"❌ Критическая ошибка в start_command для {update.effective_user.id}: {e}", exc_info=True)

def setup_meme_job(application: Application):
    """
    Настройка периодической отправки мемов с расширенной отладкой
    """
    try:
        async def send_meme_callback(context: CallbackContext):
            """
            Колбэк для отправки мема с логированием
            """
            logger.info("🕒 Запуск send_meme_callback для отправки мема")
            try:
                await send_meme_to_channel(context)
                
                # Планируем следующую отправку с рандомным интервалом
                interval_hours = random.uniform(1, 4)
                next_run_time = datetime.now(pytz.utc) + timedelta(hours=interval_hours)
                
                context.job_queue.run_once(
                    send_meme_callback, 
                    interval_hours * 3600, 
                    name='send_meme',  
                    data={'next_run_time': next_run_time}  
                )
                
                logger.info(f"⏰ Следующий мем будет отправлен через {interval_hours:.1f} часов")
            except Exception as e:
                logger.error(f"❌ Ошибка в send_meme_callback: {e}", exc_info=True)
        
        # Запускаем первую задачу через 10 секунд
        application.job_queue.run_once(
            send_meme_callback, 
            10, 
            name='send_meme',  
            data={'next_run_time': datetime.now(pytz.utc) + timedelta(seconds=10)}
        )
        
        logger.info("✅ Джоб для отправки мемов настроен успешно")
    except Exception as e:
        logger.critical(f"❌ Ошибка настройки джоба для мемов: {e}", exc_info=True)

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
            '📋 List of commands:\n\n'
            '🤖 /start - Start the bot\n'
            '🤣 /meme - Get a random meme\n'
            '📋 /help - List of all commands\n'
            '🌐 /about - Information about the bot\n'
            '📊 /stats - Meme statistics\n\n'
            f'🖼️ Memes are published in the channel: {CHANNEL_ID}'
        )
        
        await update.message.reply_text(help_text)
    
    except Exception as e:
        logger.error(f"Error in help_command: {e}", exc_info=True)

async def about_command(update: Update, context: CallbackContext):
    """
    Обработчик команды /about - информация о боте
    """
    try:
        def escape_markdown_v2(text):
            """
            Корректное экранирование текста для Markdown V2
            Экранирует специальные символы с учетом всех требований Telegram
            """
            if not text:
                return ''
            
            # Список символов, которые нужно экранировать
            escape_chars = '_*[]()~`>#+-=|{}.!'
            
            # Экранируем каждый символ
            escaped_text = ''.join('\\' + char if char in escape_chars else char for char in str(text))
            
            # Дополнительно обрабатываем точки в начале и середине слов
            escaped_text = re.sub(r'(?<=\w)\.', r'\\.', escaped_text)
            
            return escaped_text
        
        about_text = (
            "🤖 *Мем\\-Бот* 🚀\n\n"
            "*Версия:* 1\\.0\\.0\n"
            "*Разработчик:* @sp1dpwnzero\n\n"
            "Бот создан по приколу для генерации случайных мемов\\.\n"
            "Функционал:\n"
            "• Отправка случайных мемов\n"
            "• Статистика мемов\n"
            "• Быстрые команды\n\n"
            "Не ухахатайся\\! 😄"
        )
        
        await update.message.reply_markdown_v2(
            about_text, 
            disable_web_page_preview=True
        )
        
        logger.info(f"About command used by {update.effective_user.username}")
    
    except Exception as e:
        logger.error(f"Ошибка в about_command: {e}", exc_info=True)
        await update.message.reply_text("Извините, возникла ошибка при выполнении команды.")

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

async def meme_command(update: Update, context: CallbackContext):
    """
    Команда /meme для получения случайного мема
    """
    try:
        meme = await get_random_meme()
        
        if not meme:
            await update.message.reply_text("😱 Не удалось получить мем")
            return
        
        caption = f"{meme['title']}\n\nмда, шиз\n@sh1za1337_bot"
        
        await update.message.reply_photo(
            photo=meme['url'], 
            caption=caption
        )
        
        logger.info(f"Отправлен мем по команде /meme из {meme['subreddit']}")
    
    except Exception as e:
        logger.error(f"❌ Ошибка команды /meme: {e}", exc_info=True)
        await update.message.reply_text("😱 Произошла ошибка при получении мема")

async def handle_command(update: Update, context: CallbackContext):
    """
    Универсальный обработчик неизвестных команд
    """
    logger.info(f"Unhandled command from {update.effective_user}")
    
    try:
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
        # Проверяем, что это изображение
        if not update.message.photo:
            await update.message.reply_text("❌ Пожалуйста, отправь мем в виде изображения")
            return
        
        # Получаем последнее (самое большое) изображение
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        # Получаем информацию об отправителе
        sender = update.effective_user
        sender_name = sender.username or f"{sender.first_name} {sender.last_name}".strip()
        
        # Формируем подпись с учетом текста, если он есть
        caption_parts = []
        caption_parts.append(f"Додумался @{sender_name}")
        
        # Добавляем текст к картинке, если он есть
        if update.message.caption:
            caption_parts.append(f"\n{update.message.caption}")
        
        # Добавляем стандартные теги
        caption_parts.extend([
            "\nмда, шиз",
            "@sh1za1337_bot"
        ])
        
        # Объединяем части подписи
        caption = "\n".join(caption_parts)
        
        # Отправляем мем в канал
        await context.bot.send_photo(
            chat_id=CHANNEL_ID, 
            photo=file.file_id, 
            caption=caption
        )
        
        # Уведомляем пользователя об успешной отправке
        await update.message.reply_text("✅ Мем опубликован в канале!")
        
        logger.info(f"Пользовательский мем от {sender_name} опубликован в канале")
    
    except Exception as e:
        logger.error(f"❌ Ошибка при публикации пользовательского мема: {e}", exc_info=True)
        await update.message.reply_text("😱 Произошла ошибка при публикации мема")

async def time_command(update: Update, context: CallbackContext):
    """
    Команда /time для получения времени до следующего мема с расширенной отладкой
    """
    logger.info(f"Вызов /time от пользователя {update.effective_user.username} (ID: {update.effective_user.id})")
    
    try:
        # Проверяем, что команда от администратора
        if str(update.effective_user.id) != os.getenv('ADMIN_USER_ID'):
            warning_message = (
                "⚠️ ВНИМАНИЕ! НЕСАНКЦИОНИРОВАННАЯ ПОПЫТКА ДОСТУПА! ⚠️\n\n"
                "🔒 Эта команда строго конфиденциальна и предназначена ТОЛЬКО для администратора.\n"
                "👀 Все ваши действия ЛОГИРУЮТСЯ и будут НЕМЕДЛЕННО ДОЛОЖЕНЫ.\n"
                "💀 Повторные попытки могут привести к БЛОКИРОВКЕ и УГОЛОВНОЙ ОТВЕТСТВЕННОСТИ!\n\n"
                "🚨 НЕМЕДЛЕННО ПРЕКРАТИТЕ ПОПЫТКИ НЕСАНКЦИОНИРОВАННОГО ДОСТУПА! 🚨"
            )
            
            logger.warning(
                f"ВНИМАНИЕ! Несанкционированная попытка доступа к /time. "
                f"Пользователь: {update.effective_user.username} "
                f"(ID: {update.effective_user.id})"
            )
            
            await update.message.reply_text(warning_message)
            return
        
        logger.info(f"Администратор {update.effective_user.username} вызвал /time")
        
        # Находим задачу отправки мема
        jobs = context.job_queue.jobs()
        meme_job = next((job for job in jobs if job.name == 'send_meme'), None)
        
        if meme_job:
            # Получаем время следующего запуска из данных джоба
            next_run_time = meme_job.data.get('next_run_time') if meme_job.data else datetime.now(pytz.utc)
            
            # Вычисляем оставшееся время
            remaining_time = next_run_time - datetime.now(pytz.utc)
            
            # Форматируем сообщение с более подробной информацией
            hours, remainder = divmod(remaining_time.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            message = (
                f"⏰ До следующего мема:\n"
                f"🕒 Осталось: {int(hours)} ч. {int(minutes)} мин. {int(seconds)} сек.\n"
                f"🔜 Следующая отправка: {next_run_time.astimezone(pytz.timezone('Europe/Moscow'))}"
            )
            
            logger.info(f"Отправка времени следующего мема: {message}")
            await update.message.reply_text(message)
        else:
            logger.warning("Задача отправки мемов не найдена")
            await update.message.reply_text("❌ Задача отправки мемов не найдена")
    
    except Exception as e:
        logger.error(f"Ошибка в команде /time: {e}", exc_info=True)
        await update.message.reply_text("❌ Произошла ошибка при получении времени")

async def gomeme_command(update: Update, context: CallbackContext):
    """
    Команда /gomeme для принудительной отправки мема и обновления расписания
    """
    logger.info(f"Вызов /gomeme от пользователя {update.effective_user.username} (ID: {update.effective_user.id})")
    
    try:
        # Проверяем, что команда от администратора
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
                f"Пользователь: {update.effective_user.username} "
                f"(ID: {update.effective_user.id})"
            )
            
            await update.message.reply_text(warning_message)
            return
        
        logger.info(f"Администратор {update.effective_user.username} вызвал /gomeme")
        
        # Отправляем мем в канал
        await send_meme_to_channel(context)
        
        # Перепланируем следующую отправку
        setup_meme_job(context.application)
        
        logger.info("Мем отправлен, расписание обновлено")
        await update.message.reply_text("✅ Мем отправлен. Расписание обновлено.")
    
    except Exception as e:
        logger.error(f"Ошибка в команде /gomeme: {e}", exc_info=True)
        await update.message.reply_text("❌ Не удалось отправить мем")

def main():
    """
    Основная функция для запуска бота
    """
    try:
        logger.info("🤖 Инициализация бота...")
        
        # Проверка токена
        if not TELEGRAM_TOKEN:
            logger.critical("❌ TELEGRAM_TOKEN не установлен!")
            raise ValueError("Токен Telegram не найден")
        
        logger.info("Bot token status: PRESENT")
        logger.info("Telegram Bot starting...")
        
        # Создание приложения
        application = (
            Application.builder()
            .token(TELEGRAM_TOKEN)
            .build()
        )
        
        logger.info(f"✅ Приложение создано с токеном: {TELEGRAM_TOKEN[:10]}...")
        
        # Регистрация команд
        application.add_handler(CommandHandler('start', start_command))
        application.add_handler(CommandHandler('help', help_command))
        application.add_handler(CommandHandler('about', about_command))
        application.add_handler(CommandHandler('stats', stats_command))
        application.add_handler(CommandHandler('meme', meme_command))
        application.add_handler(CommandHandler('time', time_command))
        application.add_handler(CommandHandler('gomeme', gomeme_command))
        
        # Обработчик неизвестных команд
        application.add_handler(MessageHandler(filters.COMMAND, handle_command))
        
        # Обработчик пользовательских мемов
        application.add_handler(MessageHandler(filters.PHOTO, handle_user_meme))
        
        # Настройка джоба для отправки мемов
        setup_meme_job(application)
        
        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        logger.info("🚀 Начало polling...")
        
        # Запуск бота
        application.run_polling(
            drop_pending_updates=True,
            stop_signals=None
        )
    
    except Exception as e:
        logger.critical(f"❌ Критическая ошибка при запуске бота: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("🛑 Работа бота прервана пользователем")
    except Exception as e:
        print(f"❌ Непредвиденная ошибка: {e}")
        import traceback
        traceback.print_exc()
