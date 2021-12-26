from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from comments.models import Comment
from comments.api.serializers import CommentSerializer, CommentSerializerForCreate, CommentSerializerForUpdate
from comments.api.permissions import IsObjectOwner
from utils.decorators import required_params


class CommentViewSet(viewsets.GenericViewSet):
    """
    methods include list, create, update, destroy
    methods do not include retrieve (pull single comment), since it is not a required function.
    """

    serializer_class = CommentSerializerForCreate
    queryset = Comment.objects.all()
    # can add other filter set in the future.
    filterset_fields = ('tweet_id',)

    def get_permissions(self):
        # return an instance using AllowAny()/IsAuthenticated()
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ['destroy', 'update']:
            return [IsAuthenticated(), IsObjectOwner()]
        return [AllowAny()]

    @required_params(params=['tweet_id'])
    def list(self, request, *args, **kwargs):
        """
        GET: query_params
        POST: data
        default: use query_params
        """
        if 'tweet_id' not in request.query_params:
            return Response({
                'message': 'missing tweet_id in request',
                'success': False,
            }, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.get_queryset()
        # use prefetch_related to reduce sql query
        # comments = self.filter_queryset(queryset).prefetch_related('user').order_by('created_at')
        comments = self.filter_queryset(queryset).order_by('created_at')
        serializer = CommentSerializer(comments, many=True)
        return Response({
            'comments': serializer.data,
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        data = {
            'user_id': request.user.id,
            'tweet_id': request.data.get('tweet_id'),
            'content': request.data.get('content'),
        }

        serializer = CommentSerializerForCreate(data=data)
        # the first para is an instance by default. Therefore 'data=' is required.

        if not serializer.is_valid():
            return Response({
                'message': 'Please check input.',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        comment = serializer.save()
        # save() method triggers create() method.

        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        serializer = CommentSerializerForUpdate(
            instance=self.get_object(),
            data=request.data
        )
        if not serializer.is_valid():
            raise Response({
                'message': 'Please check input.'
            }, status=status.HTTP_400_BAD_REQUEST)

        comment = serializer.save()
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        # default response code is 204
        return Response({
            'success': True,
        }, status=status.HTTP_200_OK)








