from rest_framework import serializers
from notifications.models import Notification
from accounts.api.serializers import UserSerializer


class NotificationSerializer(serializers.ModelSerializer):
    recipient = UserSerializer()

    class Meta:
        model = Notification
        fields = (
            'id',
            'recipient',
            'actor_content_type',
            'actor_object_id',
            'verb',
            'action_object_content_type',
            'action_object_object_id',
            'target_content_type',
            'target_object_id',
            'timestamp',
            'unread',
        )


class NotificationSerializerForUpdate(serializers.ModelSerializer):
    # BooleanField 会自动兼容 unread=true, false, "true", "false", "True", "1", "0"
    # 等情况，并都转换为 python 的 boolean 类型的 True / False
    unread = serializers.BooleanField()

    class Meta:
        model = Notification
        fields = ('unread',)

    def update(self, instance, validated_data):
        instance.unread = validated_data['unread']
        instance.save()
        return instance
