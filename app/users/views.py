from datetime import datetime
from typing import Any, Literal, Never
import base58
import json
import os
from django.db.models.manager import BaseManager
import requests
import copy
import uuid
import asyncio

from eth_keys import keys
from nacl.signing import SigningKey

from rest_framework import generics
from rest_framework.utils.serializer_helpers import ReturnDict
from .models import User, Wallet, WalletLog
from .serializers import *
from django.shortcuts import get_object_or_404
from django.db import transaction
from . import forms
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from w3.wallet import WalletHandler
from w3.dex import DexTools
from utils import constants
from utils.response_util import ResponseUtil
from rest_framework.request import Request
from rest_framework.response import Response


class UserRegistrationView(generics.CreateAPIView):
    queryset: BaseManager[User] = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer: Never = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return ResponseUtil.field_error()
        self.perform_create(serializer=serializer)
        return ResponseUtil.success(data=serializer.data)


class MineView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]
    
    def get(self, request: Request, *args, **kwargs) -> Response:
        id, email = None, None
        if request.user.is_authenticated:
            id = request.user.id
            email = request.user.email
        return ResponseUtil.success(data={"id": id, "email": email})


class WalletAPIView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    # @method_decorator(cache_page(30))
    def get(self, request: Request) -> Response:
        chains: str | None = request.query_params.get('chain')
        all_chains: dict[str, dict[str, str]] = copy.deepcopy(x=constants.CHAIN_DICT)
        if not chains:
            chains: list[str] = all_chains.keys()
        else:
            chains: list[str] = [c.strip() for c in chains.split(sep=',') if c]
            for c in chains:
                if c not in all_chains:
                    return ResponseUtil.field_error(msg=f'Chain {c} error.')
        wallets: BaseManager[Wallet] = Wallet.objects.filter(user=request.user)
        serializer: WalletListSerializer = WalletListSerializer(wallets, many=True)
        wallet_handler: WalletHandler = WalletHandler()

        balance_for_account: dict[str, dict[str, dict]] = asyncio.run(main=wallet_handler.multi_get_balances(address_list=[s['address'] for s in serializer.data], chain_list=chains))
        data = dict()
        for k, v in balance_for_account.items():
            res: list = []
            s_data: ReturnDict = copy.deepcopy(x=serializer.data)
            for s in s_data:
                d: dict = v.get(s['address'])
                if not d:
                    continue
                s['value'] = d.get('value', 0)
                s['tokens'] = d.get('tokens', [])
                s['chain'] = d.get('chain')
                res.append(s)
            data[k] = res
        return ResponseUtil.success(data=data)

    def post(self, request: Request, *args, **kwargs) -> Response:
        data: dict[str, Any] = request.data
        data['platform'] = data.get('platform', constants.DEFAULT_PLATFORM)
        if data['platform'] not in constants.PLATFORM_LIST:
            return ResponseUtil.field_error(msg='Platform error.')
        
        wallet_handler: WalletHandler = WalletHandler()
        data['private_key'], data['public_key'], data['address'] = wallet_handler.create_wallet(platform=data['platform'])
        
        if not data['private_key']:
            return ResponseUtil.field_error()

        serializer: WalletSerializer = WalletSerializer(data=data, context={'request': request})
        if not serializer.is_valid():
            return ResponseUtil.field_error()
        
        serializer.save()
        return ResponseUtil.success(data=serializer.data)


class ImportPrivateKeyView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        data: dict[str, Any] = request.data.copy()
        private_key: str = data['private_key']
        platform: str = data.get('platform', constants.DEFAULT_PLATFORM)

        if platform not in constants.PLATFORM_LIST:
            return ResponseUtil.field_error(msg='Platform error.')

        if platform == 'EVM':
            if len(private_key) < 64 or len(private_key) > 66:
                return ResponseUtil.field_error()
            
            private_key_hex: str = "0x" + private_key if not private_key.startswith("0x") else private_key
            public_key: Any = keys.PrivateKey(bytes.fromhex(private_key_hex[2:])).public_key
            data['public_key'] = str(object=public_key)
            data['address'] = public_key.to_checksum_address()
        elif platform == 'SOL':
            if len(private_key) > 90 or len(private_key) < 85:
                return ResponseUtil.field_error()
            
            private_key_bytes: bytes = base58.b58decode(private_key)
            signing_key: SigningKey = SigningKey(seed=private_key_bytes[:32])
            public_key_bytes: bytes = signing_key.verify_key.encode()
            data['public_key'] = base58.b58encode(public_key_bytes).decode(encoding='utf-8')
            data['address'] = data['public_key']

        serializer: PrivateKeySerializer = PrivateKeySerializer(data=data)
        if serializer.is_valid():
            wallet: Wallet = Wallet.objects.create(**serializer.validated_data, user=request.user)
            return ResponseUtil.success(data=WalletSerializer(wallet).data)
        else:
            return ResponseUtil.field_error()


class ExportPrivateKeyView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def get(self, request: Request, pk: str) -> Response:
        try:
            uuid.UUID(hex=pk, version=4)
        except ValueError:
            return ResponseUtil.field_error()
        
        wallet: Wallet = get_object_or_404(klass=Wallet, pk=pk, user=request.user)
        if wallet.user == request.user:
            return ResponseUtil.success(data={"private_key": wallet.private_key})
        else:
            return ResponseUtil.field_error()


class UpdateWalletNameView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def get(self, request: Request, pk: str) -> Response:
        try:
            uuid.UUID(hex=pk, version=4)
        except ValueError:
            return ResponseUtil.field_error()
        
        res: bool = Wallet.objects.exclude(pk=pk).filter(user=request.user, name = request.query_params.get('name', default='')).exists()
        return ResponseUtil.success(data={"result": res})

    def patch(self, request: Request, pk: str) -> Response:
        try:
            uuid.UUID(hex=pk, version=4)
        except ValueError:
            return ResponseUtil.field_error()

        if Wallet.objects.exclude(pk=pk).filter(user=request.user, name = request.data.get('name', '')).exists():
            return ResponseUtil.data_exist()
        wallet: Wallet = get_object_or_404(klass=Wallet, pk=pk, user=request.user)
        serializer: WalletNameUpdateSerializer = WalletNameUpdateSerializer(wallet, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return ResponseUtil.success(data=serializer.data)
        else:
            return ResponseUtil.field_error()
        

class DeleteWalletView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def delete(self, request: Request, pk: str) -> Response:
        try:
            uuid.UUID(hex=pk, version=4)
        except ValueError:
            return ResponseUtil.field_error()
        
        wallet: Wallet = get_object_or_404(klass=Wallet, pk=pk, user=request.user)
        wallet.delete()
        return ResponseUtil.success()


class WalletBalanceAPIView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def get(self, request: Request, address: str) -> Response:
        chains: str | None = request.query_params.get('chain')
        all_chains: dict[str, dict[str, str]] = copy.deepcopy(constants.CHAIN_DICT)
        if not chains:
            chains: list[str] = all_chains.keys()
        else:
            chains: list[str] = [c.strip() for c in chains.split(',') if c]
            for c in chains:
                if c not in all_chains:
                    return ResponseUtil.field_error(msg=f'Chain error.')
        wallet_handler: WalletHandler = WalletHandler()
        balance_for_account: dict[str, Any] = asyncio.run(main=wallet_handler.multi_get_balances(address_list=[address], chain_list=chains))
        return ResponseUtil.success(data={k:v[address] if len(v) else v for k, v in balance_for_account.items()})


class UserSelectView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        form: forms.UserSelectForms = forms.UserSelectForms(data=request.data)
        if not form.is_valid():
            return ResponseUtil.field_error(msg=list(form.errors.values())[0][0])
        ids: list[dict] = form.data['ids']
        select_status: int = int(request.data['status'])
        
        user_obj: BaseManager[User] = User.objects.filter(id=request.user.id)
        existed_ids: list[dict] = json.loads(s=user_obj.first().ids) if isinstance(user_obj.first().ids, str) else user_obj.first().ids or []
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

        user_obj.update(ids=json.dumps(obj=existed_ids))
        return ResponseUtil.success(data={"ids": existed_ids})
    

class AccountTypeView(APIView):
    def get(self, request: Request) -> Response:
        chain: str = request.query_params.get('chain', default=constants.DEFAULT_CHAIN)
        if chain not in constants.CHAIN_DICT:
            return ResponseUtil.field_error(msg='Chain error.')
        
        if chain == 'solana':
            target_url: str = f"{os.getenv(key='WEB3_SOL_API')}/account/type"
            params: dict[str, Any] = request.GET.dict()
            headers: dict[str, Any] = dict(request.headers)

            response: requests.Response = requests.get(url=target_url, params=params, headers=headers)

            return ResponseUtil.success(data=json.loads(s=response.content).get('data', {}))
        else:
            address: str = request.query_params.get('address', default='')
            account_type: Literal['token'] | Literal['unknown'] | Literal['user'] = WalletHandler().account_type(address=address, chain=chain)
            return ResponseUtil.success(data={"type": account_type})
    

class HashStatusAPIView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        chain: str = request.query_params.get('chain', default=constants.DEFAULT_CHAIN)
        if chain not in constants.CHAIN_DICT:
            return ResponseUtil.field_error(msg='Chain error.')
        hash_tx: str | None = request.query_params.get('hash_tx')
        
        obj: WalletLog = get_object_or_404(klass=WalletLog, chain=chain, hash_tx=hash_tx, user = request.user)
        hash_status: int | None = obj.status
        created_at: datetime = obj.added_at
        if hash_status in [0, 2]:
            wallet_handler: WalletHandler = WalletHandler()
            check_res: list | None = wallet_handler.check_hash(chain=chain, data_list=[dict(trxHash=hash_tx, trxTimestamp=int(obj.added_at.timestamp()))])
            if check_res:
                check_res = check_res[0]
                if check_res.get('isPending') == False and check_res.get('isSuccess') == True: # succeed
                    hash_status = 1
                elif check_res.get('isPending') == False and check_res.get('isSuccess') == False: # failed
                    hash_status = 3
        if obj.status != hash_status:
            obj.status = hash_status
            obj.save()
        return ResponseUtil.success(data=dict(status=hash_status, created_at=created_at))
    

class WalletTransactionView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    @transaction.atomic
    def post(self, request: Request, pk: str) -> Response:
        try:
            uuid.UUID(hex=pk, version=4)
        except ValueError:
            return ResponseUtil.field_error()
        
        form: forms.WalletTransactionForms = forms.WalletTransactionForms(data=request.data)
        if not form.is_valid():
            return ResponseUtil.field_error(msg=list(form.errors.values())[0][0])
        form_data: dict[str, Any] = form.data
        chain: str=form_data.get('chain', constants.DEFAULT_CHAIN)

        if chain not in constants.CHAIN_DICT:
            return ResponseUtil.field_error(msg='Chain error.')
        
        wallet: Wallet = get_object_or_404(klass=Wallet, pk=pk, user=request.user)

        wallet_handler = WalletHandler()
        transaction_hash: str | None = wallet_handler.token_transaction(
            chain=chain, 
            private_key=wallet.private_key, 
            input_token=form_data['input_token'], 
            output_token=form_data['output_token'], 
            amount=form_data['amount'], 
            slippageBps=form_data.get('slippageBps', 10) * 100,
        )
        if not transaction_hash:
            return ResponseUtil.web3_error()
        
        log_obj: WalletLog = WalletLog.objects.create(
            chain=chain,
            input_token=form_data['input_token'],
            output_token=form_data['output_token'],
            amount=form_data['amount'],
            hash_tx=transaction_hash,
            type_id=0,
            status=0,
            user=wallet.user,
        )
        return ResponseUtil.success(data=dict(hash_tx=transaction_hash, url=constants.CHAIN_DICT[chain]['tx_url'] + transaction_hash, status = log_obj.status))
    

class CreateTokenView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    @transaction.atomic
    def post(self, request: Request, pk: str, *args, **kwargs) -> Response:
        try:
            uuid.UUID(hex=pk, version=4)
        except ValueError:
            return ResponseUtil.field_error()
        
        form: forms.CreateTokenForms = forms.CreateTokenForms(data=request.data)
        if not form.is_valid():
            return ResponseUtil.field_error(msg=list(form.errors.values())[0][0])
        form_data: dict[str, Any] = form.data
        chain: str=form_data.get('chain', constants.DEFAULT_CHAIN)

        if chain not in constants.CHAIN_DICT:
            return ResponseUtil.field_error(msg='Chain error.')
        
        wallet: Wallet = get_object_or_404(klass=Wallet, pk=pk, user=request.user)

        wallet_handler: WalletHandler = WalletHandler()

        # create token
        amount: float = form_data.get('amount') or 0
        created_hash, address = wallet_handler.create_token(
            chain=chain, 
            private_key=wallet.private_key, 
            name=form_data['name'], 
            symbol=form_data['symbol'], 
            desc=form_data.get('desc', ''), 
            decimals=str(object=form_data['decimals']), 
            amount=str(object=amount),
        )
        if not created_hash:
            return ResponseUtil.web3_error()
        
        log_obj: WalletLog = WalletLog.objects.create(
            chain=chain,
            input_token=address,
            output_token=None,
            amount=amount,
            hash_tx=created_hash,
            type_id=1,
            status=0,
            user=wallet.user,
        )
        return ResponseUtil.success(data=dict(hash_tx=created_hash, url=constants.CHAIN_DICT[chain]['tx_url'] + created_hash, status = log_obj.status, address = address))


class MintTokenView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    @transaction.atomic
    def post(self, request: Request, pk: str, *args, **kwargs) -> Response:
        try:
            uuid.UUID(hex=pk, version=4)
        except ValueError:
            return ResponseUtil.field_error()
        
        form: forms.MintTokenForms = forms.MintTokenForms(data=request.data)
        if not form.is_valid():
            return ResponseUtil.field_error(msg=list(form.errors.values())[0][0])
        form_data: dict[str, Any] = form.data
        chain: str=form_data.get('chain', constants.DEFAULT_CHAIN)
        created_hash: str = form_data['created_hash']

        if chain not in constants.CHAIN_DICT:
            return ResponseUtil.field_error(msg='Chain error.')

        created_log: WalletLog = get_object_or_404(klass=WalletLog, chain=chain, hash_tx=created_hash, user = request.user)

        wallet_handler: WalletHandler = WalletHandler()
        check_res: list | None = wallet_handler.check_hash(chain=chain, data_list=[dict(trxHash=created_hash, trxTimestamp=int(x=created_log.added_at.timestamp()))])
        if not (check_res and check_res[0].get('isPending') == False and check_res[0].get('isSuccess') == True): # succeed
            return ResponseUtil.web3_error(msg='Hash status error.')
        
        wallet: Wallet = get_object_or_404(klass=Wallet, pk=pk, user=request.user)

        wallet_handler = WalletHandler()
        address: None | str = wallet_handler.get_address_from_hash(chain=chain, hash_tx=created_hash)

        # mint token
        mint_hash: str | None = wallet_handler.mint_token(chain=chain, private_key=wallet.private_key, create_hash=created_hash, mint_amount=str(object=form_data['amount']))
        if not mint_hash:
            return ResponseUtil.web3_error()
        
        log_obj: WalletLog = WalletLog.objects.create(
            chain=chain,
            input_token=None,
            output_token=None,
            amount=form_data['amount'],
            hash_tx=mint_hash,
            type_id=2,
            status=0,
            user=wallet.user,
        )
        return ResponseUtil.success(data=dict(hash_tx=mint_hash, url=constants.CHAIN_DICT[chain]['tx_url'] + mint_hash, address=address, status = log_obj.status))


class CoinCrossQuoteView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def post(self, request: Request, *args, **kwargs) -> Response:    
        form: forms.CoinCrossQuoteForms = forms.CoinCrossQuoteForms(data=request.data)
        if not form.is_valid():
            return ResponseUtil.field_error(msg=list(form.errors.values())[0][0])
        form_data: dict = dict(form.data)

        wallet_handler: WalletHandler = WalletHandler()
        status, res = wallet_handler.token_cross_quote(form_data=form_data)
        data: dict = res.get('data', {})
        
        dex_tools: DexTools = DexTools()
        token_address: str = data.get('provider_data', {}).get('cross_chain_fee_token_address', '').replace('0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE', constants.ZERO_ADDRESS)
        data['provider_data']['cross_chain_fee_token'] = dex_tools.token_base(chain=form_data['fromData']['chain'], address=token_address)
        return Response(data=data, status=status)
        

class CoinCrossView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    @transaction.atomic
    def post(self, request: Request, pk: str, *args, **kwargs) -> Response:
        try:
            uuid.UUID(hex=pk, version=4)
        except ValueError:
            return ResponseUtil.field_error()
           
        form: forms.CoinCrossForms = forms.CoinCrossForms(data=request.data)
        if not form.is_valid():
            return ResponseUtil.field_error(msg=list(form.errors.values())[0][0])
        form_data: dict = dict(form.data)
        chain: str = form_data['fromData']['chain']

        if chain not in constants.CHAIN_DICT or form_data['toData']['chain'] not in constants.CHAIN_DICT:
            return ResponseUtil.field_error(msg='Chain error.')
        
        wallet: Wallet = get_object_or_404(klass=Wallet, pk=pk, user=request.user)
        form_data['fromData']['walletSecretKey'] = wallet.private_key
        form_data['fromData']['walletAddress'] = wallet.address

        wallet_handler: WalletHandler = WalletHandler()
        status, data = wallet_handler.token_cross(form_data=form_data)
        if status != 200:
            return ResponseUtil.no_data(msg = data['message'])
        hash_tx: str = data.get('data', {}).get('trx_hash')

        WalletLog.objects.create(
            chain=chain,
            input_token=form_data['fromData']['tokenAddress'],
            output_token=form_data['toData']['tokenAddress'],
            amount=form_data['crossAmount'],
            hash_tx=hash_tx,
            type_id=3,
            status=0,
            user=wallet.user,
        )
        return ResponseUtil.success(data=dict(hash_tx = hash_tx, url=constants.CHAIN_DICT[chain]['tx_url'] + hash_tx, provider = form_data.get('provider')))
    

class CoinCrossStatusView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    def get(self, request) -> Response:
        provider: str | None = request.query_params.get('provider')
        if not provider:
            return ResponseUtil.miss_field(msg = 'No provider.')
        if provider not in constants.CROSS_PROVIDERS:
            return ResponseUtil.field_error(msg = 'Provider error.')
        
        chain: str | None = request.query_params.get('chain')
        if not chain:
            return ResponseUtil.miss_field(msg = 'No chain.')
        if chain not in constants.CHAIN_DICT:
            return ResponseUtil.field_error(msg='Chain error.')

        hash_tx: str | None = request.query_params.get('hash_tx')
        if not hash_tx:
            return ResponseUtil.miss_field(msg = 'No hash.')

        if not WalletLog.objects.filter(hash_tx=hash_tx).exists():
            return ResponseUtil.no_data(msg = 'Hash does not exist.')
        
        wallet_handler: WalletHandler = WalletHandler()
        status_code, data = wallet_handler.token_cross_status(provider=provider, chain=chain, hash_tx=hash_tx)
        if status_code != 200:
            return ResponseUtil.no_data(msg = data['message'])
        
        status: str = data.get('data', {}).get('status')
        if provider == 'jumper':
            if status == 'DONE':
                status = 'SUCCESS'
            elif status == 'NOT_FOUND' or status == 'INVALID' or status == 'FAILED':
                status == 'FAILURE'
        
        return ResponseUtil.success(data=dict(status=status))
