def incr_comments_count(sender, instance, created, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F
    from utils.redis_helper import RedisHelper

    if not created:
        return

    # handle new comment
    Tweet.objects.update(comments_count=F('comments_count') + 1)
    RedisHelper.incr_count(instance.tweet, 'comments_count')


def decr_comments_count(sender, instance, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F
    from utils.redis_helper import RedisHelper

    # handle comment deletion
    Tweet.objects.update(comments_count=F('comments_count') - 1)
    RedisHelper.decr_count(instance.tweet, 'comments_count')
