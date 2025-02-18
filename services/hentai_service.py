import asyncpraw
import random
from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
from logging_setup import logger

async def get_random_hentai_video():
    try:
        logger.info("Начало процесса получения Hentai видео")
        reddit = asyncpraw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )

        subreddit = await reddit.subreddit('hentai')
        hot_posts = []
        async for post in subreddit.hot(limit=50):
            if post.url.endswith(('.mp4', '.webm')):
                hot_posts.append(post)

        if hot_posts:
            selected_video = random.choice(hot_posts)
            return {
                'url': selected_video.url,
                'title': selected_video.title
            }
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении Hentai видео: {e}")
        return None
