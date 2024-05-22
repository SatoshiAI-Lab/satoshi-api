# urls.py
from django.urls import path
from django.urls.resolvers import URLPattern
from .views import *

urlpatterns: list[URLPattern] = [
    path(route="register/", view=UserRegistrationView.as_view(), name="user-registration"),
    path(route="mine/", view=MineView.as_view(), name="mine"),

    path(route='import-key/', view=ImportPrivateKeyView.as_view(), name='import-private-key'),
    path(route='export-key/<str:pk>/', view=ExportPrivateKeyView.as_view(), name='export-private-key'),
    path(route='update-wallet-name/<str:pk>/', view=UpdateWalletNameView.as_view(), name='update-wallet-name'),
    path(route='wallet-delete/<str:pk>/', view=DeleteWalletView.as_view(), name='wallet-delete'),
    path(route='wallet-balance/<str:address>/', view=WalletBalanceAPIView.as_view(), name='wallet-balance'),
    path(route='wallet/', view=WalletAPIView.as_view(), name='wallet-api'),

    path(route='account/type/', view=AccountTypeView.as_view(), name='account-type'),
    path(route='coin/select/', view=UserSelectView.as_view(),  name='coin-select'),

    path(route='hash/status/', view=HashStatusAPIView.as_view(),  name='hash-status'),
    path(route='wallet-transaction/<str:pk>/', view=WalletTransactionView.as_view(), name='wallet-transaction'),
    path(route='coin/create/<str:pk>/', view=CreateTokenView.as_view(),  name='coin-create'),
    path(route='coin/mint/<str:pk>/', view=MintTokenView.as_view(),  name='coin-mint'),

    path(route='coin/cross-quote/', view=CoinCrossQuoteView.as_view(), name='coin-cross-quote'),
    path(route='coin/cross/<str:pk>/', view=CoinCrossView.as_view(), name='coin-cross'),
    path(route='coin/cross-status/', view=CoinCrossStatusView.as_view(), name='coin-cross-status'),
]
