# urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path("coin/search/", CoinSearchView.as_view(), name="search-api"),
    path("coin/list/", CoinListView.as_view(), name="search-api"),
]