# urls.py
from django.urls import path
from django.urls.resolvers import URLPattern
from .views import *

urlpatterns: list[URLPattern] = [
    path(route="coin/list/", view=CoinListView.as_view(), name="coin-list-api"),
    path(route="coin/info/", view=CoinInfoView.as_view(), name="coin-info-api"),
    path(route="coin/search/", view=CoinSearchView.as_view(), name="coin-search-api"),
    path(route="coin/query/", view=CoinQueryView.as_view(), name="coin-query-api"),
    path(route="address/query/", view=AddressQueryView.as_view(), name="address-query-api"),
]