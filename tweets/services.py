from django.contrib.auth.models import User
from tweets.models import Tweet
from twitter.cache import USER_TWEETS_PATTERN
from utils.redis_helper import RedisHelper


class TweetService:

    @classmethod
    def get_cached_tweets(cls, user_id):
        def load_db_objects(limit):
            return Tweet.objects.filter(user_id=user_id).order_by('-created_at')[:limit]

        key = USER_TWEETS_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(key, load_db_objects)

    @classmethod
    def push_tweet_to_cache(cls, tweet):
        key = USER_TWEETS_PATTERN.format(user_id=tweet.user_id)
        RedisHelper.push_object(key, tweet)
