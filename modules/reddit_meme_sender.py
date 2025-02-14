import praw
import random

class RedditMemeSender:
    def __init__(self, reddit_client_id, reddit_client_secret, reddit_user_agent):
        self.reddit = praw.Reddit(
            client_id=reddit_client_id,
            client_secret=reddit_client_secret,
            user_agent=reddit_user_agent
        )

    def get_memes_from_subreddit(self, subreddit_name, limit=10):
        subreddit = self.reddit.subreddit(subreddit_name)
        memes = [submission.url for submission in subreddit.top(limit=limit) if submission.url.endswith(('jpg', 'jpeg', 'png', 'gif'))]
        return memes

    def send_random_meme(self, subreddit_name):
        memes = self.get_memes_from_subreddit(subreddit_name)
        if memes:
            return random.choice(memes)
        return None

# Пример использования:
# reddit_sender = RedditMemeSender('client_id', 'client_secret', 'user_agent')
# meme_url = reddit_sender.send_random_meme('memes')
