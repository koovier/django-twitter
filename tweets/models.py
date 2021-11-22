from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save
from likes.models import Like
from photos.models import Photo
from tweets.listeners import push_tweet_to_cache
from utils.listeners import invalidate_object_cache
from utils.memcached_helper import MemcachedHelper


class Tweet(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    photos = models.ManyToManyField(Photo, blank=True)
    # 为什么使用 BigInteger? (2^64)，了解一下鸟叔如何搞挂 youtube 的
    # https://www.youtube.com/watch?v=9bZkp7q19f0
    likes_count = models.BigIntegerField(default=0, null=True)
    comments_count = models.BigIntegerField(default=0, null=True)

    class Meta:
        index_together = (('user', 'created_at'),)

    def __str__(self):
        # 这里是你执行 print(tweet instance) 的时候会显示的内容
        return '{} {}: {}'.format(self.created_at, self.user, self.content)

    @property
    def like_set(self):
        return Like.objects.filter(
            content_type=ContentType.objects.get_for_model(Tweet),
            object_id=self.id,
        ).order_by('-created_at')

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.user_id)

    @property
    def created_at_as_int(self):
        return int(self.created_at.timestamp() * 1000000)


post_save.connect(push_tweet_to_cache, sender=Tweet)
post_save.connect(invalidate_object_cache, sender=Tweet)
