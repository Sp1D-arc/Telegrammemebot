import os
import asyncio
import logging
import sys
import praw
import random
import re
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, JobQueue

# Загрузка переменных окружения
from dotenv import load_dotenv
load_dotenv()  # Загружаем переменные из .env

# Точная настройка логирования
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.handlers.clear()

# Создаем форматтер
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Файловый обработчик
file_handler = logging.FileHandler('bot_debug.log', mode='w', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Консольный обработчик
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

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

# Настройка Reddit API
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

# Отладочный вывод токена
print(f"🕹️ Токен бота: {TELEGRAM_TOKEN[:5]}...{TELEGRAM_TOKEN[-5:] if TELEGRAM_TOKEN else 'ТОКЕН НЕ НАЙДЕН'}")
logger.info(f"Bot token status: {'PRESENT' if TELEGRAM_TOKEN else 'MISSING'}")

def get_random_meme(subreddit_names=None, limit=200):
    """
    Получение случайного мема
    """
    if subreddit_names is None:
        subreddit_names = [
            'ru_memes', 'memes', 'dankmemes', 'funny', 
            'anime_irl', 'hornymemes', 'Warhammer40k', 
            'animememes', 'waifuism', 'grimdank'
        ]
    
    try:
        all_memes = []
        
        # Собираем мемы из разных сабреддитов
        for subreddit_name in subreddit_names:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                memes = list(subreddit.hot(limit=limit//len(subreddit_names)))
                
                # Фильтрация мемов (только картинки)
                filtered_memes = [
                    meme for meme in memes 
                    if (meme.url.endswith(('.jpg', '.png', '.jpeg', '.gif')) 
                        and not meme.over_18
                    )
                ]
                
                all_memes.extend(filtered_memes)
            
            except Exception as e:
                logger.warning(f"Ошибка при получении мемов из {subreddit_name}: {e}")
        
        if not all_memes:
            logger.warning("Не найдено подходящих мемов")
            return None
        
        # Выбираем мем с учетом вероятностного отбора
        selected_meme = random.choices(
            all_memes[:50],  # Берем топ-50 мемов
            weights=[1 / (i + 1) for i in range(50)]  # Вероятность выбора уменьшается
        )[0]
        
        return {
            'title': selected_meme.title,
            'url': selected_meme.url,
            'author': selected_meme.author.name,
            'subreddit': selected_meme.subreddit.display_name
        }
    
    except Exception as e:
        logger.error(f"Ошибка получения мема: {e}", exc_info=True)
        return None

async def send_meme_to_channel(context: CallbackContext):
    """
    Отправка случайного мема в канал
    """
    try:
        meme = get_random_meme()
        
        if not meme:
            logger.warning("Не удалось получить мем")
            return
        
        caption = f"{meme['title']}\n\nмда, шиз\n@sh1za1337_bot"
        
        await context.bot.send_photo(
            chat_id=CHANNEL_ID, 
            photo=meme['url'], 
            caption=caption
        )
        
        logger.info(f"Отправлен мем из {meme['subreddit']}")
    
    except Exception as e:
        logger.error(f"Ошибка отправки мема: {e}", exc_info=True)

async def start_command(update: Update, context: CallbackContext):
    """
    Обработчик команды /start
    """
    print("🔍 Команда /start получена")
    logger.info("Received /start command")
    
    try:
        # Отладочный вывод типа чата
        print(f"💬 Тип чата: {update.effective_chat.type}")
        logger.debug(f"Chat type: {update.effective_chat.type}")
        
        # Проверяем тип чата
        if update.effective_chat.type != "private":
            print("❌ Команда /start только в личных сообщениях")
            await update.message.reply_text("🚫 Команда /start доступна только в личных сообщениях.")
            return

        # Отправляем приветственное сообщение
        user_name = update.effective_user.first_name
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
    
    except Exception as e:
        print(f"❌ Ошибка в start_command: {e}")
        logger.error(f"Error in start_command: {e}", exc_info=True)

async def help_command(update: Update, context: CallbackContext):
    """
    Обработчик команды /help
    """
    print("🔍 Команда /help получена")
    logger.info("Received /help command")
    
    try:
        # Отладочный вывод типа чата
        print(f"💬 Тип чата: {update.effective_chat.type}")
        logger.debug(f"Chat type: {update.effective_chat.type}")
        
        # Проверяем тип чата
        if update.effective_chat.type != "private":
            print("❌ Команда /help только в личных сообщениях")
            await update.message.reply_text("🚫 Команда /help доступна только в личных сообщениях.")
            return

        help_text = (
            '📋 Список команд:\n\n'
            '🤖 /start - Запуск бота\n'
            '🤣 /meme - Получить случайный мем\n'
            '📋 /help - Список всех команд\n'
            '🌐 /about - Информация о боте\n'
            '📊 /stats - Статистика мемов\n\n'
            '🖼️ Отправь картинку боту - опубликовать мем в канале'
        )
        
        await update.message.reply_text(help_text)
    
    except Exception as e:
        print(f"❌ Ошибка в help_command: {e}")
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
    print("🔍 Команда /stats получена")
    logger.info("Received /stats command")
    
    try:
        # Отладочный вывод типа чата
        print(f"💬 Тип чата: {update.effective_chat.type}")
        logger.debug(f"Chat type: {update.effective_chat.type}")
        
        # Проверяем тип чата
        if update.effective_chat.type != "private":
            print("❌ Команда /stats только в личных сообщениях")
            await update.message.reply_text("🚫 Команда /stats доступна только в личных сообщениях.")
            return

        # Отправляем статистику
        await update.message.reply_text(
            "📊 Статистика мемов:\n\n"
            "🚧 Функция статистики в разработке\n"
            "🤖 Бот находится в стадии тестирования"
        )
    
    except Exception as e:
        print(f"❌ Ошибка в stats_command: {e}")
        logger.error(f"Error in stats_command: {e}", exc_info=True)

async def meme_command(update: Update, context: CallbackContext):
    """
    Команда /meme для получения случайного мема
    """
    try:
        meme = get_random_meme()
        
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
    print("🔍 Получена неизвестная команда")
    logger.info(f"Unhandled command from {update.effective_user}")
    
    try:
        await update.message.reply_text(
            "❓ Неизвестная команда. Используйте /help для списка команд."
        )
    
    except Exception as e:
        print(f"❌ Ошибка в handle_command: {e}")
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

def setup_meme_job(application: Application):
    """
    Настройка периодической отправки мемов со случайным интервалом
    """
    try:
        # Создаем функцию для отправки мема
        async def send_meme_callback(context: CallbackContext):
            await send_meme_to_channel(context)
            
            # Планируем следующую отправку с рандомным интервалом
            interval_hours = random.uniform(1, 4)
            context.job_queue.run_once(send_meme_callback, interval_hours * 3600)
            
            logger.info(f"Следующий мем будет отправлен через {interval_hours:.1f} часов")
        
        # Запускаем первую задачу через 10 секунд
        application.job_queue.run_once(send_meme_callback, 10)
        
        logger.info("Джоб для отправки мемов настроен успешно")
    except Exception as e:
        logger.error(f"Ошибка настройки джоба для мемов: {e}", exc_info=True)

def main():
    """
    Основная функция для запуска бота
    """
    print("🚀 Запуск бота...")
    logger.info("Telegram Bot starting...")

    if not TELEGRAM_TOKEN:
        logger.critical("❌ Telegram bot token is missing! Please set TELEGRAM_TOKEN in .env")
        sys.exit(1)

    # Создаем приложение
    try:
        # Включаем максимально подробное логирование для библиотек
        logging.getLogger('telegram').setLevel(logging.DEBUG)
        logging.getLogger('httpx').setLevel(logging.DEBUG)
        logging.getLogger('httpcore').setLevel(logging.DEBUG)

        application = (
            Application.builder()
            .token(TELEGRAM_TOKEN)
            .get_updates_read_timeout(30)
            .get_updates_write_timeout(30)
            .get_updates_connect_timeout(30)
            .job_queue(JobQueue())  # Добавляем job queue
            .build()
        )
        logger.info(f"✅ Приложение создано с токеном: {TELEGRAM_TOKEN[:5]}...")
    except Exception as e:
        logger.critical(f"❌ Ошибка создания приложения: {e}", exc_info=True)
        sys.exit(1)

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("meme", meme_command))
    application.add_handler(MessageHandler(filters.COMMAND, handle_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_user_meme))

    # Устанавливаем команды меню
    commands = [
        BotCommand("start", "Запуск бота"),
        BotCommand("meme", "Получить случайный мем"),
        BotCommand("help", "Список всех команд"),
        BotCommand("about", "Информация о боте"),
        BotCommand("stats", "Статистика мемов")
    ]

    setup_meme_job(application)

    # Запускаем бота
    print("🤖 Бот запускается...")
    logger.info("🚀 Начало polling...")
    
    try:
        # Используем блокирующий запуск с максимально подробным логированием
        application.run_polling(
            drop_pending_updates=True, 
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            poll_interval=1.0  # Увеличиваем частоту опроса
        )
    except Exception as e:
        logger.critical(f"❌ Критическая ошибка при запуске бота: {e}", exc_info=True)
        print(f"❌ Критическая ошибка: {e}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("🛑 Работа бота прервана пользователем")
    except Exception as e:
        print(f"❌ Непредвиденная ошибка: {e}")
        import traceback
        traceback.print_exc()
