from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User
from tweets.models import Tweet
from comments.models import Comment
from rest_framework.test import APIClient


class TestCase(DjangoTestCase):

    def create_user(self, username, email=None, password=None):
        if email is None:
            email = '{}@gmail.com'.format(username)
        if password is None:
            password = 'generic password'
        # password should be encrypted, therefore should not be passed in plain text.
        # username and password require to be normalized.
        return User.objects.create_user(username, email, password)

    def create_tweet(self, user, content=None):
        if content is None:
            content = 'default tweet content'
        return Tweet.objects.create(user=user, content=content)

    def create_comment(self, user, tweet, content=None):
        if content is None:
            content = 'default comment content.'
        return Comment.objects.create(user=user, tweet=tweet, content=content)


