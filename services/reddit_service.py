import asyncpraw
import random
from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, SENT_MEMES, MAX_SENT_MEMES
from deep_translator import GoogleTranslator
from logging_setup import logger

async def get_random_meme(subreddit_names=None, limit=200):
    try:
        logger.info("Начало процесса получения мема")
        reddit = asyncpraw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )

        if not subreddit_names:
            subreddit_names = ['memes', 'dankmemes', 'funny', 'ru_memes', 'Pikabu']

        all_memes = []
        for subreddit_name in subreddit_names:
            try:
                subreddit = await reddit.subreddit(subreddit_name)
                hot_memes = []
                async for post in subreddit.hot(limit=limit):
                    if post.url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        hot_memes.append(post)
                all_memes.extend(hot_memes)
            except Exception as e:
                logger.error(f"Ошибка при получении мемов из {subreddit_name}: {e}")

        valid_memes = [meme for meme in all_memes if meme.url not in SENT_MEMES]
        if not valid_memes:
            SENT_MEMES.clear()
            valid_memes = all_memes

        if not valid_memes:
            logger.warning("Не удалось найти подходящие мемы")
            return None

        selected_meme = random.choice(valid_memes)
        title = selected_meme.title
        translated_title = GoogleTranslator(source='auto', target='ru').translate(title)
        selected_meme.title = translated_title

        SENT_MEMES.add(selected_meme.url)
        if len(SENT_MEMES) > MAX_SENT_MEMES:
            SENT_MEMES.clear()

        return {
            'title': selected_meme.title,
            'url': selected_meme.url,
            'author': selected_meme.author,
            'subreddit': selected_meme.subreddit
        }
    except Exception as e:
        logger.critical(f"Критическая ошибка в get_random_meme: {e}")
        return None
    finally:
        await reddit.close()
