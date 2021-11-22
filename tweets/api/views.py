from django.utils.decorators import method_decorator
from newsfeeds.services import NewsFeedService
from ratelimit.decorators import ratelimit
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from tweets.api.serializers import (
    TweetSerializer,
    TweetCreateSerializer,
    TweetSerializerForDetail,
)
from tweets.models import Tweet
from tweets.services import TweetService
from utils.decorators import required_params
from utils.paginations import EndlessPagination

class TweetViewSet(viewsets.GenericViewSet):
    """
    API endpoint that allows users to create, list tweets
    """
    queryset = Tweet.objects.all()
    serializer_class = TweetCreateSerializer
    pagination_class = EndlessPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @method_decorator(ratelimit(key='user_or_ip', rate='5/s', method='GET', block=True))
    def retrieve(self, request, *args, **kwargs):
        # <HOMEWORK> 通过某个 query 参数 with_comments 来决定是否需要带上 comments
        tweet = self.get_object()
        return Response(
            TweetSerializerForDetail(tweet).data,
            status=status.HTTP_200_OK,
        )

    @required_params(params=['user_id'])
    @method_decorator(ratelimit(key='user_or_ip', rate='3/s', method='GET', block=True))
    @method_decorator(ratelimit(key='user_or_ip', rate='10/m', method='GET', block=True))
    def list(self, request, *args, **kwargs):
        user_id = request.query_params['user_id']
        cached_tweets = TweetService.get_cached_tweets(user_id)
        page = self.paginator.paginate_cached_list(cached_tweets, request)
        if page is None:
            queryset = Tweet.objects.filter(user_id=user_id).order_by('-created_at')
            page = self.paginator.paginate_queryset(queryset, request)
        serializer = TweetSerializer(page, many=True)
        return self.paginator.get_paginated_response(serializer.data)

    @method_decorator(ratelimit(key='user', rate='1/s', method='POST', block=True))
    @method_decorator(ratelimit(key='user', rate='5/m', method='POST', block=True))
    def create(self, request, *args, **kwargs):
        serializer = TweetCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': "Please check input",
                'errors': serializer.errors,
            }, status=400)
        tweet = serializer.save()
        NewsFeedService.fanout_to_followers(tweet)
        return Response(
            TweetSerializer(tweet).data,
            status=status.HTTP_201_CREATED,
        )

    # <HOMEWORK> 增加一个 like 的方法让用户可以通过 /api/tweets/<id>/like/ 点赞
    # <HOMEWORK> 增加一个 unlike 的方法让用户可以通过 /api/tweets/<id>/unlike/ 取消点赞
