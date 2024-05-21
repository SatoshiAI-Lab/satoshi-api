from typing import Any, Literal
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request, HttpRequest
from rest_framework.views import APIView


class OptionalAuthentication(BasePermission):
    def has_permission(self, request: HttpRequest, view: APIView) -> Literal[True]:
        authorization: Any = request.headers.get('Authorization')
        if authorization:
            return True
        return True
