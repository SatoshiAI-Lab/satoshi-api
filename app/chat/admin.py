from typing import Literal
from django.contrib import admin
from chat.models import Message, ChatRoom


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display: tuple[Literal['id'], Literal['show_members']] = ("id", "show_members")

    def show_members(self, obj: ChatRoom) -> str:
        output: str = ", ".join(
            f"{str(object=member)} == {str(object=member.id)}" for member in obj.members.all()
        )
        return output

    show_members.short_description = "Members of the chat room"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display: tuple[Literal['user'], Literal['room'], Literal['id'], Literal['created_at']] = ("user", "room", "id", "created_at")
