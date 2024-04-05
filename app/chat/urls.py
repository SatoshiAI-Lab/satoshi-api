from django.urls import path
from .views import ChatRoomDetailView

urlpatterns = [
    path(
        "chat/<str:room_name>/",
        ChatRoomDetailView.as_view(),
        name="chat-room-detail-or-create",
    ),
]
