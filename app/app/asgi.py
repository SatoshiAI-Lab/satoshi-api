"""
ASGI config for app project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from app.ws_middleware import TokenAuthMiddleware
from channels.security.websocket import AllowedHostsOriginValidator
from chat.routing import websocket_urlpatterns

os.environ.setdefault(key="DJANGO_SETTINGS_MODULE", value="app.settings")

application = ProtocolTypeRouter(
    application_mapping={
        "http": get_asgi_application(),
        "websocket": AllowedHostsOriginValidator(
            application=TokenAuthMiddleware(inner=URLRouter(routes=websocket_urlpatterns))
        ),
    }
)
