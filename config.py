# Загрузка переменных окружения
import os
from dotenv import load_dotenv

load_dotenv()

# Глобальные переменные
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')
ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')
SENDER_ID = os.getenv('SENDER_ID')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = os.getenv('SMTP_PORT')

# Глобальные состояния
sending_memes = False
is_command_running = {}
SENT_MEMES = set()
MAX_SENT_MEMES = 500
