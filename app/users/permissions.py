from rest_framework.permissions import BasePermission, SAFE_METHODS


class OptionalAuthentication(BasePermission):
    def has_permission(self, request, view):
        authorization = request.headers.get('Authorization')
        if authorization:
            return True
        return True
