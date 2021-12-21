from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from comments.models import Comment
from comments.api.serializers import CommentSerializer, CommentSerializerForCreate


class CommentViewSet(viewsets.GenericViewSet):
    """
    methods include list, create, update, destroy
    methods do not include retrieve (pull single comment), since it is not a required function.
    """

    serializer_class = CommentSerializerForCreate
    queryset = Comment.objects.all()

    def get_permissions(self):
        # return an instance using AllowAny()/IsAuthenticated()
        if self.action == 'create':
            return [IsAuthenticated()]
        return [AllowAny()]

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







