from django.conf import settings
from django.core.cache import caches
from friendships.hbase_models import HBaseFollowing, HBaseFollower
from twitter.cache import FOLLOWING_HASH_PATTERN
from utils.redis_client import RedisClient


import time

cache = caches['testing'] if settings.TESTING else caches['default']


class FriendshipService(object):

    @classmethod
    def follow(cls, from_user_id, to_user_id):
        if from_user_id == to_user_id:
            return None

        # update db
        now = int(time.time() * 1000000)
        instance = HBaseFollowing.create(from_user_id=from_user_id, to_user_id=to_user_id, created_at=now)
        HBaseFollower.create(from_user_id=from_user_id, to_user_id=to_user_id, created_at=now)

        # update cache
        conn = RedisClient.get_connection()
        key = FOLLOWING_HASH_PATTERN.format(user_id=from_user_id)
        conn.hset(key, str(to_user_id), now)
        return instance

    @classmethod
    def unfollow(cls, from_user_id, to_user_id):
        if from_user_id == to_user_id:
            return 0

        # update db
        cls.cache_following_hash(from_user_id)
        conn = RedisClient.get_connection()
        key = FOLLOWING_HASH_PATTERN.format(user_id=from_user_id)
        timestamp = conn.hget(key, str(to_user_id))
        if timestamp is None:
            return 0
        HBaseFollowing.delete(from_user_id=from_user_id, created_at=timestamp)
        HBaseFollower.delete(to_user_id=to_user_id, created_at=timestamp)

        # update cache
        return conn.hdel(key, str(to_user_id))

    @classmethod
    def get_follower_user_ids(cls, to_user_id):
        # 获取 followers 的时候不需要经过 cache，因为数据可能会很大，没有太多意义
        # 而且获取 A 是否关注 B的信息的时候查的是 A 的 following 列表而不是 B 的 follower 列表
        # <HOMEWORK> 对于大 V 一口气取 100 万条数据会很慢也没有意义，应该在 fanout 的时候分批次取
        friendships = HBaseFollower.filter(prefix=(to_user_id, None))
        return [friendship.from_user_id for friendship in friendships]

    @classmethod
    def get_following_user_ids(cls, from_user_id):
        cls.cache_following_hash(from_user_id)
        conn = RedisClient.get_connection()
        key = FOLLOWING_HASH_PATTERN.format(user_id=from_user_id)
        # 把自己关注自己的信息拿掉
        return [int(key) for key in conn.hkeys(key) if key != str(from_user_id)]

    @classmethod
    def cache_following_hash(cls, from_user_id):
        conn = RedisClient.get_connection()
        key = FOLLOWING_HASH_PATTERN.format(user_id=from_user_id)
        if conn.hlen(key) > 0:
            return

        followings = HBaseFollowing.filter(prefix=(from_user_id, None))
        mapping = {
            str(f.to_user_id): f.created_at
            for f in followings
        }
        # redis 有一个毛病，如果 mapping 是空的，就不会写到 redis 里，但是我们又需要 cache
        # 这种情况，因此我们增加一个自己 follow 了自己的信息，确保即便是空的 mapping 也会被写入
        mapping[str(from_user_id)] = 0
        conn.hmset(key, mapping)
        conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)

    @classmethod
    def has_followed(cls, from_user_id, to_user_id):
        if from_user_id == to_user_id:
            return False
        conn = RedisClient.get_connection()
        cls.cache_following_hash(from_user_id)
        key = FOLLOWING_HASH_PATTERN.format(user_id=from_user_id)
        return conn.hexists(key, str(to_user_id))

    @classmethod
    def get_following_count(cls, from_user_id):
        conn = RedisClient.get_connection()
        cls.cache_following_hash(from_user_id)
        key = FOLLOWING_HASH_PATTERN.format(user_id=from_user_id)
        # -1 是因为有一条自己关注了自己的信息
        return conn.hlen(key) - 1
