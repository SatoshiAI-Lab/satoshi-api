import json
import copy
import asyncio
from typing import Any

from django.db.models.manager import BaseManager
from django.db.models.query import RawQuerySet
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Q

from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from . import forms, models, serializers
import os
from urllib.parse import urljoin
from users import models as user_models
from users.permissions import OptionalAuthentication

from utils import constants
from utils.response_util import ResponseUtil

from w3.dex import GeckoAPI, DexTools, AveAPI, DefinedAPI
from w3.wallet import WalletHandler

from rest_framework.request import Request
from rest_framework.response import Response


class ChainView(APIView):
    @method_decorator(decorator=cache_page(timeout=5 * 60))
    def get(self, request: Request, *args, **kwargs) -> Response:
        data: dict[str, list[dict] | list[str]] = {
            "chains": [dict(
                name=c, 
                logo=f"{os.getenv(key='S3_DOMAIN')}/chains/logo/{c}.png", 
                platform = constants.CHAIN_DICT[c]['platform'],
                token = constants.CHAIN_DICT[c]['token'],
            ) for c in constants.CHAIN_DICT], 
            "platforms": constants.PLATFORM_LIST,
        }
        return ResponseUtil.success(data=data)


class CoinSearchView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    @method_decorator(decorator=cache_page(timeout=5 * 60))
    def get(self, request: Request) -> Response:
        form: forms.CoinSearchForms = forms.CoinSearchForms(data=request.query_params)
        if not form.is_valid():
            return ResponseUtil.field_error(msg=list(form.errors.values())[0][0])
        kw: str = request.query_params['kw']

        reserved_chars = r'''?&|!{}[]()^~*:\\"'+-'''
        replace: list[str] = ['\\' + l for l in reserved_chars]
        trans: dict[int, str] = str.maketrans(dict(zip(reserved_chars, replace)))
        kw = str(object=kw).strip().translate(trans).replace('%', '')
        
        num: int = 10
        data: dict = dict()

        sql: str = f"""
        select id,name,symbol,logo 
        from token 
        where symbol ilike %s 
        order by char_length(symbol) asc, strpos('{kw}',symbol) asc, market_cap desc 
        limit {num};
        """
        objs: RawQuerySet[Any] = models.Coin.objects.using(alias='coin_source').raw(raw_query=sql, params=[f'%{kw}%'])
        ser: serializers.CoinSearch = serializers.CoinSearch(objs, many=True)
        ser_data: ReturnList | Any | ReturnDict = ser.data
        tokens: list[int] = [t['id'] for t in ser_data]

        full_objs: BaseManager[models.Coin] = models.Coin.objects.using(alias='coin_source').filter(Q(name__icontains = kw) | Q(slug__icontains = kw)).order_by('-market_cap')[:num]
        full_ser: serializers.CoinSearch = serializers.CoinSearch(full_objs, many=True)
        for fs in full_ser.data:
            if fs['id'] in tokens:
                continue
            tokens.append(fs['id'])
            ser_data.append(fs)

        chain_objs: BaseManager[models.CoinChainData] = models.CoinChainData.objects.using(alias='coin_source').filter(address__icontains = kw)[:num]
        for chain_obj in chain_objs:
            try:
                token: models.Coin = chain_obj.token
                if token.id in tokens:
                    continue
                tokens.append(token.id)
                ser_data.append(dict(id=token.id,name=token.name,symbol=token.symbol,logo=urljoin(base=os.getenv(key='IMAGE_DOMAIN'), url=token.logo)))
            except:
                continue
        data['coin'] = ser_data[:num]
        return ResponseUtil.success(data=data)


class CoinListView(APIView):
    permission_classes: list[type[OptionalAuthentication]] = [OptionalAuthentication]

    # @method_decorator(cache_page(60 * 10))
    def post(self, request: Request) -> Response:
        form: forms.CoinListForms = forms.CoinListForms(data=request.data)
        if not form.is_valid():
            return ResponseUtil.field_error(msg=list(form.errors.values())[0][0])

        uid: str | None = request.user.id
        if uid:
            ids: None | str = user_models.User.objects.filter(id=uid).first().ids
        else:
            ids: None | str = request.data.get('ids')
        if not ids:
            return ResponseUtil.success(data=dict(list=[]))

        if isinstance(ids, str):
            try:
                ids = json.loads(s=ids)
            except:
                return ResponseUtil.field_error(msg=list(form.errors.values())[0][0])
        token_ids: list[int] = [i['id'] for i in ids if i['type'] == 1]
        t_models: BaseManager[models.Coin] = models.Coin.objects.using(alias='coin_source').filter(id__in=token_ids)
        token_data: ReturnList | Any | ReturnDict = serializers.CoinListSerializer(t_models, many=True).data

        return ResponseUtil.success(data=dict(list=token_data))
    

class CoinInfoView(APIView):
    permission_classes: list[type[IsAuthenticated]] = [IsAuthenticated]

    @method_decorator(decorator=cache_page(timeout=1 * 60))
    def get(self, request: Request) -> Response:
        form: forms.CoinInfoForms = forms.CoinInfoForms(data=request.query_params)
        if not form.is_valid():
            return ResponseUtil.field_error(msg=list(form.errors.values())[0][0])
        address: str = request.query_params['address']
        chain: str = request.query_params.get('chain', default=constants.DEFAULT_CHAIN)
        if chain not in constants.CHAIN_DICT:
            return ResponseUtil.field_error(msg='Chain error.')

        data: dict[str, Any] = dict()
        chain_gecko: str | None = constants.CHAIN_DICT.get(chain, {}).get('gecko')
        chain_dex_tools: str | None = constants.CHAIN_DICT.get(chain, {}).get('dex_tools')
        if chain_gecko:
            gecko_data: dict = GeckoAPI.token_info(chain=chain_gecko, address=address)
            data = dict(data, **gecko_data)
        else:
            return ResponseUtil.success(data=data)
        if chain_dex_tools:
            dex_tools_data: dict = DexTools.token_info(chain=chain_dex_tools, address=address)
            data['holders'] = dex_tools_data.get('holders')
        else:
            data['holders'] = None
        return ResponseUtil.success(data=data)
    

class PoolSearchView(APIView):
    @method_decorator(decorator=cache_page(timeout=1 * 60))
    def get(self, request: Request) -> Response:
        form: forms.CoinSearchForms = forms.CoinSearchForms(data=request.query_params)
        if not form.is_valid():
            return ResponseUtil.field_error(msg=list(form.errors.values())[0][0])
        kw: str = request.query_params['kw']

        data: list[dict[str, Any]] = GeckoAPI.search(kw=kw).get('pools', [])
        for d in data:
            network: str = d['network']
            chain: str | None = constants.GECKO_CHAIN_DICT.get(network.get('identifier', ''))
            if not chain:
                continue
            d['network'] = dict(chain=chain, logo = f"{os.getenv(key='S3_DOMAIN')}/chains/logo/{chain}.png")
        
        return ResponseUtil.success(data=data)
    

class CoinQueryView(APIView):
    # @method_decorator(decorator=cache_page(timeout=1 * 60))
    def get(self, request: Request) -> Response:
        form: forms.CoinSearchForms = forms.CoinSearchForms(data=request.query_params)
        if not form.is_valid():
            return ResponseUtil.field_error(msg=list(form.errors.values())[0][0])
        kw: str = request.query_params['kw']

        data: list[dict] = DefinedAPI.search(kw=kw)
        return ResponseUtil.success(data=data)
    

class AddressQueryView(APIView):
    @method_decorator(decorator=cache_page(timeout=1 * 60))
    def get(self, request: Request) -> Response:
        form: forms.AddressQueryForms = forms.AddressQueryForms(data=request.query_params)
        if not form.is_valid():
            return ResponseUtil.field_error(msg=list(form.errors.values())[0][0])
        address: str = request.query_params['address']
        addr_type: str | None = request.query_params.get('type')
        chains: dict[str, dict[str, str]] = copy.deepcopy(constants.CHAIN_DICT)
        excluded_chains: dict[str, dict[str, str]] = chains
        token_data: dict[str, Any] = dict()
        account_data: dict[str, Any] = dict()
        
        if not addr_type or addr_type == 'token':
            token_data: list[dict] = DefinedAPI.search(kw=address)
        
        if not addr_type or addr_type == 'account':
            wallet_handler: WalletHandler = WalletHandler()
            address_type_res: dict = asyncio.run(main=wallet_handler.multi_account_type_exclude_token(address=address, chain_list=excluded_chains))

            chains_for_account: list = [k for k, v in address_type_res.items() if v == 'user']
            balance_for_account: dict = asyncio.run(main=wallet_handler.multi_get_balances(address_list=[address], chain_list=chains_for_account))
            account_data = {k:v[address] if len(v) else v for k, v in balance_for_account.items()}

        return ResponseUtil.success(data=dict(tokens=token_data, accounts=account_data))
