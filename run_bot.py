import os
import sys
import asyncio

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем основную функцию из бота
from bot import main

if __name__ == '__main__':
    # Запускаем асинхронную функцию main()
    asyncio.run(main())
