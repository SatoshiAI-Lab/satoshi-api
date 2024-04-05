# urls.py
from django.urls import path
from .views import UserRegistrationView, MineView, WalletAPIView, ImportPrivateKeyView, ExportPrivateKeyView, UpdateWalletNameView, DeleteWalletView, WalletBalanceAPIView, WalletTransactionView

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="user-registration"),
    path("mine/", MineView.as_view(), name="mine"),
    path('wallet/', WalletAPIView.as_view(), name='wallet_api'),
    path('import-key/', ImportPrivateKeyView.as_view(), name='import_private_key'),
    path('export-key/<str:pk>/', ExportPrivateKeyView.as_view(), name='export_private_key'),
    path('update-wallet-name/<str:pk>/', UpdateWalletNameView.as_view(), name='update_wallet_name'),
    path('wallet-delete/<str:pk>/', DeleteWalletView.as_view(), name='wallet_delete'),
    path('wallet-balance/<str:pk>/', WalletBalanceAPIView.as_view(), name='wallet_balance'),
    path('wallet-transaction/<str:pk>/', WalletTransactionView.as_view(), name='wallet_transaction'),
]
