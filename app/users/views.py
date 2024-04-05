from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from .models import User, Wallet, WalletLog
from .serializers import UserSerializer, WalletSerializer, WalletNameUpdateSerializer, PrivateKeySerializer
from django.shortcuts import get_object_or_404
from django.db import transaction
from . import forms

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from eth_keys import keys
from solders.keypair import Keypair
import base58

from w3.wallet import WalletHandler


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            dict(data=serializer.data), status=status.HTTP_200_OK, headers=headers
        )


class MineView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        id, email = None, None
        if request.user.is_authenticated:
            id = request.user.id
            email = request.user.email
        return Response(dict(data={"id": id, "email": email}), status=status.HTTP_200_OK)


class WalletAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        platform = request.query_params.get('platform')
        if not platform:
            wallets = Wallet.objects.filter(user=request.user)
        else:
            wallets = Wallet.objects.filter(user=request.user, platform = platform)
        serializer = WalletSerializer(wallets, many=True)
        return Response(dict(data=serializer.data))

    def post(self, request, *args, **kwargs):
        data = request.data
        data['platform'] = data.get('platform', 'SOL')
        wallet_handler = WalletHandler(data['platform'])
        data['private_key'], data['public_key'] = wallet_handler.create_wallet()
        if not data['private_key']:
            return Response(dict(data={'error': 'Create the private key failed.'}))

        serializer = WalletSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(dict(data=serializer.data), status=status.HTTP_200_OK)
        return Response(dict(data=serializer.errors), status=status.HTTP_400_BAD_REQUEST)


class ImportPrivateKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        private_key = data['private_key']
        platform = data.get('platform', 'SOL')

        if platform == 'EVM':
            private_key_hex = "0x" + private_key_hex if not private_key.startswith("0x") else private_key
            data['public_key'] = keys.PrivateKey(bytes.fromhex(private_key_hex[2:])).public_key
        elif platform == 'SOL':
            private_key_bytes = base58.b58decode(private_key)
            keypair = Keypair.from_bytes(private_key_bytes)
            data['public_key'] = str(keypair.pubkey())

        serializer = PrivateKeySerializer(data=data)
        if serializer.is_valid():
            wallet = Wallet.objects.create(**serializer.validated_data, user=request.user)
            return Response(dict(data=WalletSerializer(wallet).data), status=status.HTTP_200_OK)
        else:
            return Response(dict(data=serializer.errors), status=status.HTTP_400_BAD_REQUEST)


class ExportPrivateKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        wallet = get_object_or_404(Wallet, pk=pk, user=request.user)
        if wallet.user == request.user:
            return Response(dict(data={'private_key': wallet.private_key}))
        else:
            return Response(dict(data={'error': 'You do not have permission to view this private key.'}), status=status.HTTP_403_FORBIDDEN)


class UpdateWalletNameView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        wallet = get_object_or_404(Wallet, pk=pk, user=request.user)
        serializer = WalletNameUpdateSerializer(wallet, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(dict(data=serializer.data))
        else:
            return Response(dict(data=serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        

class DeleteWalletView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        wallet = get_object_or_404(Wallet, pk=pk, user=request.user)
        wallet.delete()
        return Response(dict(data=dict(msg='ok')), status=status.HTTP_200_OK)


class WalletBalanceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        platform = request.query_params.get('platform', 'SOL')
        wallet_handler = WalletHandler(platform)
        data = wallet_handler.get_balances(pk)
        return Response(dict(data=dict(address=pk,token=data.get('value', 0),tokens=data.get('tokens', []))))


class WalletTransactionView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        form = forms.WalletTransactionForms(request.data)
        if not form.is_valid():
            return Response(dict(data={'error': 'Parameter error.'}), status=status.HTTP_400_BAD_REQUEST)
        form_data = form.data
        platform=form_data.get('platform', 'SOL')
        
        wallet = get_object_or_404(Wallet, pk=pk, user=request.user)

        wallet_handler = WalletHandler(platform)
        hash_tx = wallet_handler.token_transaction(wallet.private_key, form_data['input_token'], form_data['output_token'], form_data['amount'], form_data.get('slippageBps', 10) * 100)
        if not hash_tx:
            return Response(dict(data={'error': 'Transaction failed.'}), status=status.HTTP_400_BAD_REQUEST)
        
        WalletLog.objects.create(
            platform=platform,
            input_token=form_data['input_token'],
            output_token=form_data['output_token'],
            amount=form_data['amount'],
            hash_tx=hash_tx,
            type_id=0,
            status=0,
            user=wallet.user,
        )

        return Response(dict(data=dict(hash_tx=hash_tx)), status=status.HTTP_200_OK)
    