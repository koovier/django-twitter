from dateutil import parser
from newsfeeds.hbase_models import HBaseNewsFeed
from newsfeeds.tasks import fanout_newsfeeds_main_task
from twitter.cache import USER_NEWSFEEDS_PATTERN
from utils.redis_helper import RedisHelper
from utils.redis_serializer import HBaseModelSerializer


class NewsFeedService(object):

    @classmethod
    def fanout_to_followers(cls, tweet):
        # 这句话的作用是，在 celery 配置的 message queue 中创建一个 fanout 的任务
        # 参数是 tweet。任意一个在监听 message queue 的 worker 进程都有机会拿到这个任务
        # worker 进程中会执行 fanout_newsfeeds_task 里的代码来实现一个异步的任务处理
        # 如果这个任务需要处理 10s 则这 10s 会花费在 worker 进程上，而不是花费在用户发 tweet
        # 的过程中。所以这里 .delay 操作会马上执行马上结束从而不影响用户的正常操作。
        # （因为这里只是创建了一个任务，把任务信息放在了 message queue 里，并没有真正执行这个函数）
        # 要注意的是，delay 里的参数必须是可以被 celery serialize 的值，因为 worker 进程是一个独立
        # 的进程，甚至在不同的机器上，没有办法知道当前 web 进程的某片内存空间里的值是什么。所以
        # 我们只能把 tweet.id 作为参数传进去，而不能把 tweet 传进去。因为 celery 并不知道
        # 如何 serialize Tweet。
        # 将 tweet 的创建时间作为 newsfeed 的创建时间，这样的好处是，即便我们重复创建对象
        # hbase 中也会因为 row key(user_id+created_at) 相同而被覆盖，不会像 mysql 一样
        # 产生冗余数据
        fanout_newsfeeds_main_task.delay(tweet.id, tweet.created_at_as_int, tweet.user_id)

    @classmethod
    def get_cached_newsfeeds(cls, user_id):
        def load_db_objects(limit):
            return HBaseNewsFeed.filter(prefix=(user_id, None), limit=limit, reverse=True)
        key = USER_NEWSFEEDS_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(key, load_db_objects, HBaseModelSerializer)

    @classmethod
    def push_newsfeed_to_cache(cls, newsfeed):
        key = USER_NEWSFEEDS_PATTERN.format(user_id=newsfeed.user_id)
        RedisHelper.push_object(key, newsfeed)

    @classmethod
    def create(cls, **kwargs):
        newsfeed = HBaseNewsFeed.create(**kwargs)
        cls.push_newsfeed_to_cache(newsfeed)
        return newsfeed
