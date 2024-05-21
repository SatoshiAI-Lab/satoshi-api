from django.urls import path
from django.urls.resolvers import URLPattern
from .views import ChatRoomDetailView

urlpatterns: list[URLPattern] = [
    path(
        route="chat/<str:room_name>/",
        view=ChatRoomDetailView.as_view(),
        name="chat-room-detail-or-create",
    ),
]
