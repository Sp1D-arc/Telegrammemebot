import praw
from decouple import config

# Чтение данных из .env
REDDIT_CLIENT_ID = config('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = config('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = config('REDDIT_USER_AGENT')

# Инициализация Reddit API
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

def test_reddit_api():
    try:
        # Получаем 5 горячих постов из сабреддита 'memes'
        subreddit = reddit.subreddit('memes')
        hot_posts = subreddit.hot(limit=5)
        
        for post in hot_posts:
            print(f"Title: {post.title}")
            print(f"URL: {post.url}")
            print("---")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_reddit_api()
