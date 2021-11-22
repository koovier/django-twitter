from django.conf import settings
from django_hbase.models import HBaseModel
from utils.redis_client import RedisClient
from utils.redis_serializer import HBaseModelSerializer, DjangoModelSerializer


class RedisHelper:

    @classmethod
    def load_objects(cls, key, load_db_objects, serializer=DjangoModelSerializer):
        conn = RedisClient.get_connection()

        # 如果在 cache 里存在，则直接拿出来，然后返回
        if conn.exists(key):
            # 这句话可加可不加，如果用户经常访问自己的 Newsfeed, 就在每次访问时延长 cache
            # 超时时间。如果一个用户一定时间之后不访问了，就释放掉。如果每次访问都延长的话
            # EXPIRE_TIME 不适合设置太长，比如 2-3 天。如果是在创建的时候设置过期时间的话
            # 可以设置得长一些，比如 7-14 天，让所有 keys 的 expire 时间错开，避免对数据库
            # 产生过大影响。
            # 每次都延长的方法必须保证代码中没有任何造成一致性错误的 bug 存在
            # 否则一个用户越是访问频繁，越是可能出错且消除不掉。后者至少保证一定时间之后能够和
            # 数据库发生一次同步来保证数据的一致性。
            # 我更倾向于后者。
            # conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)

            serialized_list = conn.lrange(key, 0, -1)
            objects = []
            for serialized_data in serialized_list:
                deserialized_obj = serializer.deserialize(serialized_data)
                objects.append(deserialized_obj)
            return objects

        serialized_list = []
        # 最多只 cache REDIS_LIST_LENGTH_LIMIT 那么多个 objects
        objects = load_db_objects(settings.REDIS_LIST_LENGTH_LIMIT)
        for obj in objects:
            # Django 的 serializer 默认要求传入一个 list/queryset of objects
            serialized_data = serializer.serialize(obj)
            serialized_list.append(serialized_data)

        if serialized_list:
            conn.rpush(key, *serialized_list)
            conn.expire(key, settings.REDIS_KEY_EXPIRE_TIME)

        # 转换为 list 的原因是保持返回类型的统一，因为存在 redis 里的数据是 list 的形式
        return list(objects)

    @classmethod
    def push_object(cls, key, obj):
        if isinstance(obj, HBaseModel):
            serializer = HBaseModelSerializer
        else:
            serializer = DjangoModelSerializer
        conn = RedisClient.get_connection()
        serialized_data = serializer.serialize(obj)
        conn.lpush(key, serialized_data)
        conn.ltrim(key, 0, settings.REDIS_LIST_LENGTH_LIMIT - 1)
        # 不需要延长 key 的超时时间，因为 push 是被动的，不是需要读取 newsfeed 的人主动调用的

    @classmethod
    def get_count_key(cls, obj, attr):
        return '{}.{}:{}'.format(obj.__class__.__name__, attr, obj.id)

    @classmethod
    def incr_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        return conn.incr(key)

    @classmethod
    def decr_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        return conn.decr(key)

    @classmethod
    def get_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        key = cls.get_count_key(obj, attr)
        count = conn.get(key)
        if count is not None:
            return int(count)

        obj.refresh_from_db()
        count = getattr(obj, attr)
        conn.set(key, count)
        return count
