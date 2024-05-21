from typing import Any, Literal
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from users.models import User

admin.site.site_header = "satoshi-api admin"


@admin.register(User)
class MainUserAdmin(UserAdmin):
    change_user_password_template = None
    list_display: tuple[Literal['email'], Literal['mobile'], Literal['added_at'], Literal['id']] = ("email", "mobile", "added_at", "id")
    list_filter: tuple[Literal['added_at']] = ("added_at",)
    search_fields: tuple[Literal['email']] = ("email",)
    ordering: tuple[Literal['-added_at']] = ("-added_at",)
    filter_horizontal: tuple[Literal['groups'], Literal['user_permissions']] = (
        "groups",
        "user_permissions",
    )
    readonly_fields: tuple[Literal['id']] = ("id",)

    fieldsets: Any = [
        ["User additional data", {"fields": ["id", "mobile"]}],
        ["Authorization", {"fields": ["is_superuser", "groups", "user_permissions"]}],
        ["Authentication", {"fields": ["email", "password"]}],
    ]
    add_fieldsets: Any = [
        ["Authorization", {"fields": ["is_superuser", "groups", "user_permissions"]}],
        ["Authenticated", {"fields": ["email", "password1", "password2"]}],
    ]
