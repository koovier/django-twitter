from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from tweets.api.serializers import TweetCreateSerializer, TweetSerializer
from tweets.models import Tweet
from newsfeeds.services import NewsFeedService


class TweetViewSet(viewsets.GenericViewSet,
                   viewsets.mixins.CreateModelMixin,
                   viewsets.mixins.ListModelMixin):
    '''
    API endpoint that allows users to create, list tweets
    '''
    queryset = Tweet.objects.all()
    serializer_class = TweetCreateSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        # override create method
        serializer = TweetCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Please check input.',
                'errors': serializer.errors,
            }, status=400)
        tweet = serializer.save()
        NewsFeedService.fanout_to_followers(tweet)
        return Response(TweetSerializer(tweet).data, status=201)

    def list(self, request, *args, **kwargs):
        # override list method. add filter with user_id.
        if 'user_id' not in request.query_params:
            return Response('missing user_id', status=400)

        tweets = Tweet.objects.filter(
            user_id=request.query_params['user_id']
        ).order_by('-created_at')
        serializer = TweetSerializer(tweets, many=True)
        return Response({'tweets': serializer.data})

    def retrieve(self, request, *args, **kwargs):
        # use query & param: with_all_comments to determine whether to get all comments #TODO
        # query & param: with_preview_comments to determine whether to get first 3 comments #TODO
        tweet = self.get_object()
        return Response(TweetSerializerWithComments(tweet).data)






