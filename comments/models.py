from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from likes.models import Like
from tweets.models import Tweet
from utils.memcached_helper import MemcachedHelper
from django.db.models.signals import post_save, pre_delete
from comments.listeners import incr_comments_count, decr_comments_count


class Comment(models.Model):
    """
    这个版本中，我们先实现一个比较简单的评论
    评论只评论在某个Tweet上，不能评论别人的评论
    """
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    tweet = models.ForeignKey(Tweet, null=True, on_delete=models.SET_NULL)
    content = models.TextField(max_length=140)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # 有在某个 tweet 下排序所有 comments 的需求
        index_together = (('tweet', 'created_at'),)

    def __str__(self):
        return '{} - {} says {} at tweet {}'.format(
            self.created_at,
            self.user,
            self.content,
            self.tweet_id,
        )

    @property
    def like_set(self):
        return Like.objects.filter(
            content_type=ContentType.objects.get_for_model(Comment),
            object_id=self.id,
        ).order_by('-created_at')

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_through_cache(User, self.user_id)


post_save.connect(incr_comments_count, sender=Comment)
pre_delete.connect(decr_comments_count, sender=Comment)
