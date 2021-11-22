from comments.models import Comment
from django.contrib.auth.models import User
from django.core.cache import caches
from django.test import TestCase as DjangoTestCase
from django_hbase.models import HBaseModel
from friendships.services import FriendshipService
from newsfeeds.services import NewsFeedService
from rest_framework.test import APIClient
from tweets.models import Tweet
from utils.redis_client import RedisClient

cache = caches['testing']


class TestCase(DjangoTestCase):

    def setUp(self):
        RedisClient.clear()
        cache.clear()
        try:
            for hbase_model_class in HBaseModel.__subclasses__():
                hbase_model_class.create_table()
        except Exception:
            self.tearDown()
            raise

    def tearDown(self):
        for hbase_model_class in HBaseModel.__subclasses__():
            hbase_model_class.drop_table()

    @property
    def anonymous_client(self):
        if hasattr(self, '_anonymous_client'):
            return self._anonymous_client
        self._anonymous_client = APIClient()
        return self._anonymous_client

    def createUser(self, username, email=None, password=None):
        if password is None:
            password = 'generic password'
        if email is None:
            email = '{}@jiuzhang.com'.format(username)
        # 不能写成 User.objects.create()
        # 因为 password 需要被加密, username 和 email 需要进行一些 normalize 处理
        return User.objects.create_user(username, email, password)

    def createUserAndClient(self, *args, **kwargs):
        user = self.createUser(*args, **kwargs)
        client = APIClient()
        client.force_authenticate(user)
        return user, client

    def createTweet(self, user, content=None):
        if content is None:
            content = 'default tweet content'
        return Tweet.objects.create(user=user, content=content)

    def createComment(self, user, tweet, content=None):
        if content is None:
            content = 'default comment content'
        return Comment.objects.create(user=user, tweet=tweet, content=content)

    def createNewsFeed(self, owner, tweet=None, user=None, content=None):
        if not tweet:
            tweet = self.createTweet(user, content)
        return NewsFeedService.create(user_id=owner.id, tweet_id=tweet.id)

    def createFriendship(self, from_user, to_user):
        return FriendshipService.follow(from_user.id, to_user.id)
