from django.contrib.auth.models import User
from django_hbase.models import HBaseModel, HBaseField
from tweets.models import Tweet
from utils.memcached_helper import MemcachedHelper


class HBaseNewsFeed(HBaseModel):
    # 注意这个 user 不是存储谁发了这条 tweet，而是谁可以看到这条 tweet
    user_id = HBaseField(field_type='int', reverse=True)
    created_at = HBaseField(field_type='timestamp', auto_now_add=True)
    tweet_id = HBaseField(field_type='int', column_family='cf')

    class Meta:
        table_name = 'twitter_newsfeeds'
        row_key = ('user_id', 'created_at')

    def __str__(self):
        return '{} inbox of {}: {}'.format(self.created_at, self.user_id, self.tweet_id)

    @property
    def cached_tweet(self):
        return MemcachedHelper.get_object_through_cache(Tweet, self.tweet_id)

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.user_id)
