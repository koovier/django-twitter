"""
Deprecated
use newsfeeds.hbase_models.HBaseNewsFeed instead
"""
from django.contrib.auth.models import User
from django.db import models
from tweets.models import Tweet
from utils.memcached_helper import MemcachedHelper


class NewsFeed(models.Model):
    # 注意这个 user 不是存储谁发了这条 tweet，而是谁可以看到这条 tweet
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (('user', 'created_at'),)
        unique_together = (('user', 'tweet'),)
        ordering = ('user', '-created_at',)

    def __str__(self):
        return '{} inbox of {}: {}'.format(self.created_at, self.user, self.tweet)

    @property
    def cached_tweet(self):
        return MemcachedHelper.get_object_through_cache(Tweet, self.tweet_id)
