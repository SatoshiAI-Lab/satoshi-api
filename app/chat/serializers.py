from rest_framework import serializers
from .models import ChatRoom, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["user", "id", "content", "created_at", "room"]


class ChatRoomSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ["id", "members", "created_at", "messages"]

    def get_messages(self, obj):
        messages = Message.objects.filter(room=obj).order_by('-created_at')[:10]
        return MessageSerializer(messages, many=True, context=self.context).data

