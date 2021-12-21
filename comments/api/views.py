from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from comments.models import Comment
from comments.api.serializers import CommentSerializer, CommentSerializerForCreate, CommentSerializerForUpdate
from comments.api.permissions import IsObjectOwner


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
        if self.action in ['destroy', 'update']:
            return [IsAuthenticated(), IsObjectOwner()]
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






