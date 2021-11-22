from accounts.api.serializers import UserSerializerForTweet
from comments.api.serializers import CommentSerializer
from likes.api.serializers import LikeSerializer
from photos.services import PhotoService
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from tweets.constants import TWEET_PHOTOS_UPLOAD_LIMIT
from tweets.models import Tweet
from utils.redis_helper import RedisHelper


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet(source='cached_user')
    comments_count = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    photo_urls = serializers.SerializerMethodField()

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'comments_count',
            'likes_count',
            'photo_urls',
        )

    def get_likes_count(self, obj):
        return RedisHelper.get_count(obj, 'likes_count')

    def get_comments_count(self, obj):
        return RedisHelper.get_count(obj, 'comments_count')

    def get_photo_urls(self, obj):
        photo_urls = []
        for photo in obj.photos.all():
            photo_urls.append(photo.file.url)
        return photo_urls


class TweetSerializerForDetail(TweetSerializer):
    # <HOMEWORK> 使用 serializers.SerializerMethodField 的方式实现 comments
    comments = CommentSerializer(source='comment_set', many=True)
    likes = LikeSerializer(source='like_set', many=True)

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'comments',
            'created_at',
            'content',
            'likes',
            'comments',
            'likes_count',
            'comments_count',
            'photo_urls',
        )


class TweetCreateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(max_length=140)
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = Tweet
        fields = ('content', 'files')

    def validate(self, data):
        if len(data.get('files', [])) > TWEET_PHOTOS_UPLOAD_LIMIT:
            raise ValidationError({'message': 'You can upload 9 photos at most'})
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
        if validated_data.get('files'):
            photos = PhotoService.create_photos_from_files(
                user,
                validated_data['files'],
            )
            tweet.photos.add(*photos)
        return tweet
