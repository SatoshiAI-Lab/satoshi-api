# urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('chain/', ChainView.as_view(),  name='chain'),
    path("register/", UserRegistrationView.as_view(), name="user-registration"),
    path("mine/", MineView.as_view(), name="mine"),

    path('import-key/', ImportPrivateKeyView.as_view(), name='import-private-key'),
    path('export-key/<str:pk>/', ExportPrivateKeyView.as_view(), name='export-private-key'),
    path('update-wallet-name/<str:pk>/', UpdateWalletNameView.as_view(), name='update-wallet-name'),
    path('wallet-delete/<str:pk>/', DeleteWalletView.as_view(), name='wallet-delete'),
    path('wallet-balance/<str:address>/', WalletBalanceAPIView.as_view(), name='wallet-balance'),
    path('wallet/', WalletAPIView.as_view(), name='wallet-api'),

    path('account/type/', AccountTypeView.as_view(), name='account-type'),
    path('coin/select/', UserSelectView.as_view(),  name='coin-select'),

    path('hash/status/', HashStatusAPIView.as_view(),  name='hash-status'),
    path('wallet-transaction/<str:pk>/', WalletTransactionView.as_view(), name='wallet-transaction'),
    path('coin/create/<str:pk>/', CreateTokenView.as_view(),  name='coin-create'),
    path('coin/mint/<str:pk>/', MintTokenView.as_view(),  name='coin-mint'),
]
