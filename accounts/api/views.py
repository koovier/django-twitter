from accounts.api.serializers import SignupSerializer, LoginSerializer
from accounts.api.serializers import UserSerializer
from django.contrib.auth.models import User
from django.contrib.auth import (
    authenticate as django_authenticate,
    login as django_login,
    logout as django_logout,
)
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class AccountViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    serializer_class = SignupSerializer

    def get_serializer_class(self):
        if self.action == 'signup':
            return SignupSerializer
        return LoginSerializer

    @action(methods=['POST'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='POST', block=True))
    def login(self, request):
        """
        vagrant 中设置的默认admin登录账号密码
        {
            "username": "admin",
            "password": "admin"
        }
        """
        serializer = self.get_serializer_class()(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Please check input",
                "errors": serializer.errors,
            })
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = django_authenticate(username=username, password=password)
        if not user or user.is_anonymous:
            return Response({
                "success": False,
                "message": "username and password does not match",
            }, status=400)
        django_login(request, user)
        return Response({
            "success": True,
            "user": UserSerializer(instance=user).data,
        })

    @action(methods=['POST'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='POST', block=True))
    def logout(self, request):
        django_logout(request)
        return Response({"success": True})

    @action(methods=['POST'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='POST', block=True))
    def signup(self, request):
        """
        # 不太优雅的写法
        username = request.data.get('username')
        if not username:
            return Response("username required", status=400)
        password = request.data.get('password')
        if not password:
            return Response("password required", status=400)
        if User.objects.filter(username=username).exists():
            return Response("password required", status=400)
        """
        serializer = self.get_serializer_class()(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': "Please check input",
                'errors': serializer.errors,
            }, status=400)

        user = serializer.save()
        # call user.profile to auto create a UserProfile object
        user.profile
        django_login(request, user)
        return Response({
            "success": True,
            "user": UserSerializer(instance=user).data,
        }, status=201)

    @action(methods=['GET'], detail=False)
    @method_decorator(ratelimit(key='ip', rate='3/s', method='GET', block=True))
    def login_status(self, request):
        return Response({
            'has_logged_in': request.user.is_authenticated,
        })
