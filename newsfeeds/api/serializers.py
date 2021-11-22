from rest_framework import serializers
from tweets.api.serializers import TweetSerializer


class NewsFeedSerializer(serializers.Serializer):
    tweet = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def get_tweet(self, obj):
        return TweetSerializer(obj.cached_tweet).data

    def get_created_at(self, obj):
        return obj.created_at
