from django.urls import re_path
from django.urls.resolvers import URLPattern
from .consumers import ChatConsumer

websocket_urlpatterns: list[URLPattern] = [
    re_path(route=r"ws/chat/(?P<room_name>[A-Za-z0-9_-]+)/$", view=ChatConsumer.as_asgi()),
]
