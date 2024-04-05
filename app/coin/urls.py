# urls.py
from django.urls import path
from .views import SearchView

urlpatterns = [
    path("coin/search/", SearchView.as_view(), name="search-api"),
]