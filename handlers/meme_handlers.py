from services.reddit_service import get_random_meme
from services.hentai_service import get_random_hentai_video
from telegram import Update
from telegram.ext import CallbackContext
from logging_setup import logger

is_command_running = False  # Глобальная переменная состояния
warhammer_command_running = False
hentai_command_running = False
dota_command_running = False

async def meme_command(update: Update, context: CallbackContext):
    global is_command_running
    if is_command_running:
        await update.message.reply_text("Пожалуйста, подождите, команда уже выполняется.")
        return

    is_command_running = True
    await update.message.reply_text("Подождите, идет обработка запроса...")  # Сообщение о ожидании
    try:
        await update.message.reply_text("Получение мема...")
        logger.info("Начало обработки команды /meme")
        meme = await get_random_meme()
        if meme:
            caption = f"{meme['title']}\n\nмда, шиз\n@sh1za1337_bot"
            await update.message.reply_photo(photo=meme['url'], caption=caption)
        else:
            await update.message.reply_text("❌ Не удалось получить мем.")
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /meme: {e}")
        await update.message.reply_text("❌ Произошла ошибка при получении мема")
    finally:
        is_command_running = False  # Сброс состояния после выполнения

async def warhammer_meme_command(update: Update, context: CallbackContext):
    global warhammer_command_running
    if warhammer_command_running:
        await update.message.reply_text("Пожалуйста, подождите, команда уже выполняется.")
        return

    warhammer_command_running = True
    await update.message.reply_text("Подождите, идет обработка запроса...")  # Сообщение о ожидании
    try:
        subreddit_names = ['WarhammerMemes']
        meme = await get_random_meme(subreddit_names=subreddit_names)
        if meme:
            caption = f"{meme['title']}\n\nмда, шиз\n@sh1za1337_bot"
            await update.message.reply_photo(photo=meme['url'], caption=caption)
        else:
            await update.message.reply_text("❌ Не удалось получить мем из Warhammer.")
    finally:
        warhammer_command_running = False  # Сброс состояния после выполнения

async def hentai_meme_command(update: Update, context: CallbackContext):
    global hentai_command_running
    if hentai_command_running:
        await update.message.reply_text("Пожалуйста, подождите, команда уже выполняется.")
        return

    hentai_command_running = True
    await update.message.reply_text("Подождите, идет обработка запроса...")  # Сообщение о ожидании
    try:
        subreddit_names = ['hentai']
        meme = await get_random_meme(subreddit_names=subreddit_names)
        if meme and meme['url'].endswith(('jpg', 'jpeg', 'png', 'gif')):
            caption = f"{meme['title']}\n\nмда, шиз\n@sh1za1337_bot"
            await update.message.reply_photo(photo=meme['url'], caption=caption)
        else:
            await update.message.reply_text(f"❌ Не удалось получить хентай мем, отправляю ссылку: {meme['url']}")
    finally:
        hentai_command_running = False  # Сброс состояния после выполнения

async def hentai_mp4_command(update: Update, context: CallbackContext):
    video = await get_random_hentai_video()  # Вызываем функцию получения Hentai видео
    if video:
        await context.bot.send_video(chat_id=update.effective_chat.id, video=video['url'], caption=video['title'])
    else:
        await update.message.reply_text("❌ Не удалось получить Hentai видео.")

async def dota_meme_command(update: Update, context: CallbackContext):
    global dota_command_running
    if dota_command_running:
        await update.message.reply_text("Пожалуйста, подождите, команда уже выполняется.")
        return

    dota_command_running = True
    await update.message.reply_text("Подождите, идет обработка запроса...")  # Сообщение о ожидании
    try:
        subreddit_names = ['dota2memes']
        meme = await get_random_meme(subreddit_names=subreddit_names)
        if meme:
            caption = f"{meme['title']}\n\nмда, шиз\n@sh1za1337_bot"
            await update.message.reply_photo(photo=meme['url'], caption=caption)
        else:
            await update.message.reply_text("❌ Не удалось получить Dota мем.")
    finally:
        dota_command_running = False  # Сброс состояния после выполнения
