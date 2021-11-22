from django.utils.decorators import method_decorator
from newsfeeds.api.serializers import NewsFeedSerializer
from newsfeeds.hbase_models import HBaseNewsFeed
from newsfeeds.services import NewsFeedService
from ratelimit.decorators import ratelimit
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from utils.paginations import EndlessPagination


class NewsFeedViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = EndlessPagination

    @method_decorator(ratelimit(key='user', rate='5/s', method='GET', block=True))
    def list(self, request):
        cached_list = NewsFeedService.get_cached_newsfeeds(request.user.id)
        page = self.paginator.paginate_cached_list(cached_list, request)
        if page is None:
            page = self.paginator.paginate_hbase(HBaseNewsFeed, (request.user.id,), request)
        serializer = NewsFeedSerializer(page, many=True)
        return self.paginator.get_paginated_response(serializer.data)
