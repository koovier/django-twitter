def incr_likes_count(sender, instance, created, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F
    from utils.redis_helper import RedisHelper

    if not created:
        return

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        # TODO 给 Comment 使用类似的 Dernomalization 的方法进行 likes_count 的统计
        return

    # handle tweet likes
    tweet = instance.content_object
    Tweet.objects.update(likes_count=F('likes_count') + 1)
    RedisHelper.incr_count(tweet, 'likes_count')


def decr_likes_count(sender, instance, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F
    from utils.redis_helper import RedisHelper

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        # TODO 给 Comment 使用类似的 Dernomalization 的方法进行 likes_count 的统计
        return

    # handle tweet likes cancel
    tweet = instance.content_object
    Tweet.objects.update(likes_count=F('likes_count') - 1)
    RedisHelper.decr_count(tweet, 'likes_count')
