from typing import Any
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework import permissions
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view: Any = get_schema_view(
    info=openapi.Info(
        title="REST APIs",
        default_version="v1",
        description="API documentation",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns: list = [
    # Prometheus
    path(route="", view=include(arg="django_prometheus.urls")),
    # Include DRF-Swagger URLs
    path(
        route="swagger<format>/", view=schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        route="swagger/",
        view=schema_view.with_ui(renderer="swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(route="redoc/", view=schema_view.with_ui(renderer="redoc", cache_timeout=0), name="schema-redoc"),
    # API URLs
    path(route="admin/", view=admin.site.urls),
    path(route="api/v1/token/", view=TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path(route="api/v1/token/refresh/", view=TokenRefreshView.as_view(), name="token_refresh"),
    path(route="api/v1/", view=include(arg="users.urls")),
    path(route="api/v1/", view=include(arg="subscribe.urls")),
    path(route="api/v1/", view=include(arg="chat.urls")),
    path(route="api/v1/", view=include(arg="coin.urls")),
] + static(prefix=settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
