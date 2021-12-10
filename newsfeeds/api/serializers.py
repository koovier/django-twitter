from rest_framework import serializers
from newsfeeds.models import NewsFeed
from tweets.api.serializers import TweetSerializer


class NewsFeedSerializer(serializers.ModelSerializer):
    tweet = TweetSerializer()

    class Meta:
        model = NewsFeed
        fields = ('id', 'created_at', 'user', 'tweet')

