from typing import Any
from django.db import close_old_connections
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs
from channels.db import database_sync_to_async

import logging

logger: logging.Logger = logging.getLogger(name=__name__)


class TokenAuthMiddleware:
    def __init__(self, inner) -> None:
        self.inner: Any = inner

    async def __call__(self, scope, receive, send, *args, **kwargs) -> None | Any:
        close_old_connections()
        token: Any = parse_qs(qs=scope["query_string"].decode("utf8"))["access_token"][0]

        try:
            UntypedToken(token=token)
        except (InvalidToken, TokenError) as e:
            logger.error(msg=f'Auth error: {e}')
            return None
        else:
            decoded_data: Any = jwt_decode(jwt=token, key=settings.SECRET_KEY, algorithms=["HS256"])
            user: Any = await database_sync_to_async(get_user_model().objects.get)(
                id=decoded_data["user_id"]
            )
        return await self.inner(dict(scope, user=user), receive, send, *args, **kwargs)
