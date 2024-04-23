from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from .models import User, Wallet, WalletLog
from .serializers import *
from django.shortcuts import get_object_or_404
from django.db import transaction
from . import forms
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from eth_keys import keys
from nacl.signing import SigningKey
import base58
import json
import re
import os
import requests
import time

from w3.wallet import WalletHandler
from utils.constants import *


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
    

class ChainView(APIView):
    # permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(5 * 60))
    def get(self, request, *args, **kwargs):
        return Response(dict(data={"chains": [dict(name=c, logo=f"{os.getenv('S3_DOMAIN')}/chains/logo/{c}.png") for c in CHAIN_DICT], "platforms": PLATFORM_LIST}), status=status.HTTP_200_OK)


class WalletAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # @method_decorator(cache_page(30))
    def get(self, request):
        chain = request.query_params.get('chain', DEFAULT_CHAIN)
        if not chain:
            wallets = Wallet.objects.filter(user=request.user)
        else:
            if chain not in CHAIN_DICT:
                return Response(dict(data={'error': 'Chain error.'}),status=status.HTTP_400_BAD_REQUEST)
            wallets = Wallet.objects.filter(user=request.user, platform = CHAIN_DICT.get(chain, {}).get('platform'))
        serializer = WalletListSerializer(wallets, many=True)
        wallet_handler = WalletHandler()
        balance_dict = wallet_handler.multi_get_balances(chain, [s['address'] for s in serializer.data])
        for s in serializer.data:
            data = balance_dict.get(s['address'], dict())
            s['value'] = data.get('value', 0)
            s['tokens'] = data.get('tokens', [])
            s['chain'] = data.get('chain')
        return Response(dict(data=serializer.data))

    def post(self, request, *args, **kwargs):
        data = request.data
        data['platform'] = data.get('platform', DEFAULT_PLATFORM)
        if data['platform'] not in PLATFORM_LIST:
            return Response(dict(data={'error': 'Platform error.'}),status=status.HTTP_400_BAD_REQUEST)
        
        wallet_handler = WalletHandler()
        data['private_key'], data['public_key'], data['address'] = wallet_handler.create_wallet(data['platform'])
        
        if not data['private_key']:
            return Response(dict(data={'error': 'Create the private key failed.'}),status=status.HTTP_400_BAD_REQUEST)

        serializer = WalletSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(dict(data=serializer.data), status=status.HTTP_200_OK)
        return Response(dict(error=list(serializer.errors.values())[0][0]), status=status.HTTP_400_BAD_REQUEST)


class ImportPrivateKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        private_key = data['private_key']
        platform = data.get('platform', DEFAULT_PLATFORM)

        if platform not in PLATFORM_LIST:
            return Response(dict(data={'error': 'Platform error.'}),status=status.HTTP_400_BAD_REQUEST)

        if platform == 'EVM':
            if len(private_key) < 64 or len(private_key) > 66:
                return Response(dict(data={'error': 'Import the private key failed.'}),status=status.HTTP_400_BAD_REQUEST)

            # pattern = re.compile(r"^[0-9a-fA-F]+$")
            # if not re.match(pattern, private_key):
            #     return Response(dict(data={'error': 'Import the private key failed.'}),status=status.HTTP_400_BAD_REQUEST)
            
            private_key_hex = "0x" + private_key if not private_key.startswith("0x") else private_key
            public_key = keys.PrivateKey(bytes.fromhex(private_key_hex[2:])).public_key
            data['public_key'] = str(public_key)
            data['address'] = public_key.to_checksum_address()
        elif platform == 'SOL':
            if len(private_key) > 90 or len(private_key) < 85:
                return Response(dict(data={'error': 'Import the private key failed.'}),status=status.HTTP_400_BAD_REQUEST)
            
            private_key_bytes = base58.b58decode(private_key)
            signing_key = SigningKey(seed=private_key_bytes[:32])
            public_key_bytes = signing_key.verify_key.encode()
            data['public_key'] = base58.b58encode(public_key_bytes).decode('utf-8')
            data['address'] = data['public_key']

        serializer = PrivateKeySerializer(data=data)
        if serializer.is_valid():
            wallet = Wallet.objects.create(**serializer.validated_data, user=request.user)
            return Response(dict(data=WalletSerializer(wallet).data), status=status.HTTP_200_OK)
        else:
            return Response(dict(error=list(serializer.errors.values())[0][0]), status=status.HTTP_400_BAD_REQUEST)


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
            return Response(dict(error=list(serializer.errors.values())[0][0]), status=status.HTTP_400_BAD_REQUEST)
        

class DeleteWalletView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        wallet = get_object_or_404(Wallet, pk=pk, user=request.user)
        wallet.delete()
        return Response(dict(data=dict(msg='ok')), status=status.HTTP_200_OK)


class WalletBalanceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        chain = request.query_params.get('chain', DEFAULT_CHAIN)
        if chain not in CHAIN_DICT:
            return Response(dict(data={'error': 'Chain error.'}),status=status.HTTP_400_BAD_REQUEST)
        wallet_handler = WalletHandler()
        data = wallet_handler.get_balances(chain, pk)
        return Response(dict(data=dict(address=pk,value=data.get('value', 0),tokens=data.get('tokens', []), chain=data.get('chain'))))


class UserSelectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        form = forms.UserSelectForms(request.data)
        if not form.is_valid():
            return Response(dict(error=list(form.errors.values())[0][0]), status=status.HTTP_400_BAD_REQUEST)
        ids = form.data['ids']
        select_status = int(request.data['status'])
        
        user_obj = User.objects.filter(id=request.user.id)
        existed_ids = user_obj.first().ids or []
        for id in ids:
            # add
            if select_status == 1:
                if id not in existed_ids:
                    existed_ids.insert(0,id)
            # remove
            elif select_status == 2:
                if id in existed_ids:
                    existed_ids.remove(id)
            # top
            elif select_status == 3:
                if id in existed_ids:
                    existed_ids.remove(id)
                    existed_ids.insert(0,id)
        while len(existed_ids) > 300:
            del existed_ids[0]

        user_obj.update(ids=json.dumps(existed_ids))
        return Response(dict(data=dict(ids=existed_ids)), status=status.HTTP_200_OK)
    

class AccountTypeView(APIView):
    def get(self, request):
        chain = request.query_params.get('chain', DEFAULT_CHAIN)
        if chain not in CHAIN_DICT:
            return Response(dict(data={'error': 'Chain error.'}),status=status.HTTP_400_BAD_REQUEST)
        
        if chain == 'Solana':
            target_url = f"{os.getenv('WEB3_SOL_API')}/account/type"
            params = request.GET.dict()
            headers = dict(request.headers)

            response = requests.get(target_url, params=params, headers=headers)
            return Response(json.loads(response.content), status=response.status_code)
        else:
            address = request.query_params.get('address', '')
            account_type = WalletHandler().account_type(chain, address)
            return Response(dict(data=dict(type=account_type)), status=status.HTTP_200_OK)
    

class HashStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        chain = request.query_params.get('chain', DEFAULT_CHAIN)
        if chain not in CHAIN_DICT:
            return Response(dict(data={'error': 'Chain error.'}),status=status.HTTP_400_BAD_REQUEST)
        hash_tx = request.query_params.get('hash_tx')
        
        obj = get_object_or_404(WalletLog, chain=chain, hash_tx=hash_tx, user = request.user)
        hash_status = obj.status
        created_at = obj.added_at
        if hash_status in [0, 2]:
            wallet_handler = WalletHandler()
            check_res = wallet_handler.check_hash(chain, [dict(trxHash=hash_tx, trxTimestamp=int(obj.added_at.timestamp()))])
            if check_res:
                check_res = check_res[0]
                if check_res.get('isPending') == False and check_res.get('isSuccess') == True: # succeed
                    hash_status = 1
                elif check_res.get('isPending') == False and check_res.get('isSuccess') == True: # failed
                    hash_status = 3
        return Response(dict(data=dict(status=hash_status, created_at=created_at)), status=status.HTTP_200_OK)
    

class WalletTransactionView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        form = forms.WalletTransactionForms(request.data)
        if not form.is_valid():
            return Response(dict(error=list(form.errors.values())[0][0]), status=status.HTTP_400_BAD_REQUEST)
        form_data = form.data
        chain=form_data.get('chain', DEFAULT_CHAIN)
        
        wallet = get_object_or_404(Wallet, pk=pk, user=request.user)

        wallet_handler = WalletHandler()
        transaction_hash = wallet_handler.token_transaction(chain, wallet.private_key, form_data['input_token'], form_data['output_token'], form_data['amount'], form_data.get('slippageBps', 10) * 100)
        if not transaction_hash:
            return Response(dict(data={'error': 'No hash, transaction failed.'}), status=status.HTTP_400_BAD_REQUEST)
        
        log_obj = WalletLog.objects.create(
            chain=chain,
            input_token=form_data['input_token'],
            output_token=form_data['output_token'],
            amount=form_data['amount'],
            hash_tx=transaction_hash,
            type_id=0,
            status=0,
            user=wallet.user,
        )

        return Response(dict(data=dict(hash_tx=transaction_hash, url=CHAIN_DICT[chain]['tx_url'] + transaction_hash, status = log_obj.status)), status=status.HTTP_200_OK)
    

class CreateTokenView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, *args, **kwargs):
        form = forms.CreateTokenForms(request.data)
        if not form.is_valid():
            return Response(dict(error=list(form.errors.values())[0][0]), status=status.HTTP_400_BAD_REQUEST)
        form_data = form.data
        chain=form_data.get('chain', DEFAULT_CHAIN)
        
        wallet = get_object_or_404(Wallet, pk=pk, user=request.user)

        wallet_handler = WalletHandler()

        # create token
        amount = form_data.get('amount', 0)
        created_hash, address = wallet_handler.create_token(chain, wallet.private_key, form_data['name'], form_data['symbol'], form_data.get('desc', ''), str(form_data['decimals']), str(amount))
        if not created_hash:
            return Response(dict(data={'error': 'No hash, create token failed.'}), status=status.HTTP_400_BAD_REQUEST)
        log_obj = WalletLog.objects.create(
            chain=chain,
            input_token=address,
            output_token=None,
            amount=amount,
            hash_tx=created_hash,
            type_id=1,
            status=0,
            user=wallet.user,
        )

        return Response(dict(data=dict(hash_tx=created_hash, url=CHAIN_DICT[chain]['tx_url'] + created_hash, status = log_obj.status, address = address)), status=status.HTTP_200_OK)


class MintTokenView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, *args, **kwargs):
        form = forms.MintTokenForms(request.data)
        if not form.is_valid():
            return Response(dict(error=list(form.errors.values())[0][0]), status=status.HTTP_400_BAD_REQUEST)
        form_data = form.data
        chain=form_data.get('chain', 'Solana')
        created_hash = form_data['created_hash']

        created_log = get_object_or_404(WalletLog, chain=chain, hash_tx=created_hash, user = request.user)

        wallet_handler = WalletHandler()
        check_res = wallet_handler.check_hash(chain, [dict(trxHash=created_hash, trxTimestamp=int(created_log.added_at.timestamp()))])
        if not (check_res and check_res[0].get('isPending') == False and check_res[0].get('isSuccess') == True): # succeed
            return Response(dict(data={'error': 'Hash status error.'}), status=status.HTTP_400_BAD_REQUEST) 
        
        wallet = get_object_or_404(Wallet, pk=pk, user=request.user)

        wallet_handler = WalletHandler()
        address = wallet_handler.get_address_from_hash(chain, created_hash)

        # mint token
        mint_hash = wallet_handler.mint_token(chain, wallet.private_key, created_hash, str(form_data['amount']))
        if not mint_hash:
            return Response(dict(data={'error': 'No hash, mint token failed.'}), status=status.HTTP_400_BAD_REQUEST)
        
        log_obj = WalletLog.objects.create(
            chain=chain,
            input_token=None,
            output_token=None,
            amount=form_data['amount'],
            hash_tx=mint_hash,
            type_id=2,
            status=0,
            user=wallet.user,
        )
        
        return Response(dict(data=dict(hash_tx=mint_hash, url=CHAIN_DICT[chain]['tx_url'] + mint_hash, address=address, status = log_obj.status)), status=status.HTTP_200_OK)

