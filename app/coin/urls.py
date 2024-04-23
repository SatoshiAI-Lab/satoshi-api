# urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path("coin/list/", CoinListView.as_view(), name="coin-list-api"),
    path("coin/info/", CoinInfoView.as_view(), name="coin-info-api"),
    path("coin/search/", CoinSearchView.as_view(), name="coin-search-api"),
    path("coin/query/", CoinQueryView.as_view(), name="coin-query-api"),
    path("address/query/", AddressQueryView.as_view(), name="address-query-api"),
]