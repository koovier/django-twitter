from django.shortcuts import render
from requests import Response
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from tweets.api.serializers import TweetCreateSerializer, TweetSerializer
from tweets.models import Tweet


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
        return Response(TweetSerializer(tweet).data, status=201)





