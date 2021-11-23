from django.contrib.auth.models import User
from rest_framework import serializers, exceptions


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=20, min_length=6)
    password = serializers.CharField(max_length=20, min_length=6)
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    # called when is_validated is
    def validate(self, data):
        # User.objects.filter(username_iexact=data['username']).exists() # Very slow to process
        if User.objects.filter(username=data['username'].lower()).exists():  # store data in lower case
            raise exceptions.ValidationError({
                'message': 'This username address has been occupied.'
            })
        if User.objects.filter(email=data['email'].lower()).exists():
            raise exceptions.ValidationError({
                'message': 'This email address has been occupied.'
            })
        return data

    def create(self, validated_data):
        username = validated_data['username'].lower()
        password = validated_data['password'].lower()
        email = validated_data['email'].lower()

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        return user
