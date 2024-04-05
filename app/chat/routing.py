from django.urls import re_path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>[A-Za-z0-9_-]+)/$", ChatConsumer.as_asgi()),
]
