# urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path("coin/search/", CoinSearchView.as_view(), name="coin-search-api"),
    path("coin/list/", CoinListView.as_view(), name="coin-list-api"),
    path("coin/info/", CoinInfoView.as_view(), name="coin-info-api"),
]