# urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="user-registration"),
    path("mine/", MineView.as_view(), name="mine"),

    path('wallet/', WalletAPIView.as_view(), name='wallet-api'),
    path('import-key/', ImportPrivateKeyView.as_view(), name='import-private-key'),
    path('export-key/<str:pk>/', ExportPrivateKeyView.as_view(), name='export-private-key'),
    path('update-wallet-name/<str:pk>/', UpdateWalletNameView.as_view(), name='update-wallet-name'),
    path('wallet-delete/<str:pk>/', DeleteWalletView.as_view(), name='wallet-delete'),
    path('wallet-balance/<str:pk>/', WalletBalanceAPIView.as_view(), name='wallet-balance'),
    path('wallet-transaction/<str:pk>/', WalletTransactionView.as_view(), name='wallet-transaction'),

    path('coin/select/', UserSelect.as_view(),  name='coin-select'),
]
