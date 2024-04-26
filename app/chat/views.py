from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import ChatRoom, Message
from .serializers import ChatRoomSerializer
from users.models import User

from utils.response_util import ResponseUtil


class ChatRoomDetailView(generics.RetrieveAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        receiver_id = self.kwargs.get("room_name")
        self.receiver = User.objects.get(id=receiver_id)

        chat_room = ChatRoom.objects.filter(
            members__in=[self.request.user, self.receiver]
        ).first()

        if not chat_room:
            chat_room = ChatRoom.objects.create()
            chat_room.members.add(self.request.user, self.receiver)

        return chat_room
