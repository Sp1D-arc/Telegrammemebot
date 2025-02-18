import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='bot_debug.log',
        filemode='a'
    )
    logger = logging.getLogger()

    # Консольный вывод логов
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    console_handler.stream = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1, errors='replace')  # Игнорировать ошибки кодировки
    logger.addHandler(console_handler)

    # Отключаем логи сторонних библиотек
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)

    return logger

logger = setup_logging()
logger.info("Настройка логирования завершена")  # Убрали эмодзи
