from django.db import close_old_connections
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs
from channels.db import database_sync_to_async

import logging

logger = logging.getLogger(__name__)


class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send, *args, **kwargs):
        close_old_connections()
        token = parse_qs(scope["query_string"].decode("utf8"))["access_token"][0]

        try:
            UntypedToken(token)
        except (InvalidToken, TokenError) as e:
            logger.error(f'Auth error: {e}')
            return None
        else:
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user = await database_sync_to_async(get_user_model().objects.get)(
                id=decoded_data["user_id"]
            )
        return await self.inner(dict(scope, user=user), receive, send, *args, **kwargs)
