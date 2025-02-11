# Telegram Meme Bot v1.7

## Деплой на PythonAnywhere

### Подготовка окружения

1. Создайте виртуальное окружение:
```bash
python3 -m venv myenv
source myenv/bin/activate
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

### Настройка .env

1. Создайте файл `.env` в корневой директории
2. Заполните следующие переменные:
```
TELEGRAM_TOKEN=ваш_токен_телеграм_бота
REDDIT_CLIENT_ID=ваш_reddit_client_id
REDDIT_CLIENT_SECRET=ваш_reddit_client_secret
REDDIT_USER_AGENT=ваш_user_agent
CHANNEL_ID=@ваш_канал
ADMIN_USER_ID=ваш_telegram_id
```

### Запуск на PythonAnywhere

1. В настройках Web App:
   - Выберите "Manual configuration (WSGI)"
   - Python версии 3.11
   - Путь к WSGI-файлу: `/home/yourusername/myapp/wsgi.py`

2. Создайте `wsgi.py`:
```python
import sys
import os

# Путь к директории проекта
path = '/home/yourusername/myapp'
if path not in sys.path:
    sys.path.append(path)

# Импорт и запуск бота
from run_bot import main
import asyncio

def application(env, start_response):
    asyncio.run(main())
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b'Bot started']
```

### Troubleshooting

- Проверьте логи в `bot_debug.log`
- Убедитесь, что все переменные окружения корректны
- Проверьте права доступа бота к каналу

## Версия 1.7 Changelog

- Асинхронная работа с Reddit API
- Улучшенное логирование
- Случайный интервал отправки мемов
- Расширенная обработка ошибок
