from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from users.models import User

admin.site.site_header = "satoshi-api admin"


@admin.register(User)
class MainUserAdmin(UserAdmin):
    change_user_password_template = None
    list_display = ("email", "mobile", "added_at", "id")
    list_filter = ("added_at",)
    search_fields = ("email",)
    ordering = ("-added_at",)
    filter_horizontal = (
        "groups",
        "user_permissions",
    )
    readonly_fields = ("id",)

    fieldsets = [
        ["User additional data", {"fields": ["id", "mobile"]}],
        ["Authorization", {"fields": ["is_superuser", "groups", "user_permissions"]}],
        ["Authentication", {"fields": ["email", "password"]}],
    ]
    add_fieldsets = [
        ["Authorization", {"fields": ["is_superuser", "groups", "user_permissions"]}],
        ["Authenticated", {"fields": ["email", "password1", "password2"]}],
    ]
