import json
import copy

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Q

from rest_framework.views import APIView, Request
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from . import forms, models, serializers
import os
from urllib.parse import urljoin
from users import models as user_models
from users.permissions import OptionalAuthentication
from utils.constants import *
from w3.dex import GeckoAPI, DexTools, AveAPI
from w3.wallet import WalletHandler


class CoinSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(5 * 60))
    def get(self, request):
        form = forms.CoinSearchForms(request.query_params)
        if not form.is_valid():
            return Response(dict(error=list(form.errors.values())[0][0]), status=status.HTTP_400_BAD_REQUEST)
        kw = request.query_params['kw']

        reserved_chars = r'''?&|!{}[]()^~*:\\"'+-'''
        replace = ['\\' + l for l in reserved_chars]
        trans = str.maketrans(dict(zip(reserved_chars, replace)))
        kw = str(kw).strip().translate(trans).replace('%', '')
        
        num = 10
        data = dict()

        sql = f"""
        select id,name,symbol,logo from token where symbol ilike %s 
        order by char_length(symbol) asc, strpos('{kw}',symbol) asc, market_cap desc limit {num};
        """
        objs = models.Coin.objects.using('coin_source').raw(sql, [f'%{kw}%'])
        ser = serializers.CoinSearch(objs, many=True)
        ser_data = ser.data
        tokens = [t['id'] for t in ser_data]

        full_objs = models.Coin.objects.using('coin_source').filter(Q(name__icontains = kw) | Q(slug__icontains = kw)).order_by('-market_cap')[:num]
        full_ser = serializers.CoinSearch(full_objs, many=True)
        for fs in full_ser.data:
            if fs['id'] in tokens:
                continue
            tokens.append(fs['id'])
            ser_data.append(fs)

        chain_objs = models.CoinChainData.objects.using('coin_source').filter(address__icontains = kw)[:num]
        for chain_obj in chain_objs:
            try:
                token = chain_obj.token
                if token.id in tokens:
                    continue
                tokens.append(token.id)
                ser_data.append(dict(id=token.id,name=token.name,symbol=token.symbol,logo=urljoin(os.getenv('IMAGE_DOMAIN'), token.logo)))
            except:
                continue
        data['coin'] = ser_data[:num]
        return Response(dict(data=data), status=status.HTTP_200_OK)

class CoinListView(APIView):
    permission_classes = [OptionalAuthentication]

    # @method_decorator(cache_page(60 * 10))
    def post(self, request):
        form = forms.CoinListForms(request.data)
        if not form.is_valid():
            return Response(dict(error=list(form.errors.values())[0][0]), status=status.HTTP_400_BAD_REQUEST)

        uid = request.user.id
        if uid:
            ids = user_models.User.objects.filter(id=uid).first().ids
        else:
            ids = request.data.get('ids')
        if not ids:
            return Response(dict(data=dict(list=[])), status=status.HTTP_200_OK)

        if isinstance(ids, str):
            try:
                ids = json.loads(ids)
            except:
                return Response(dict(error=list(form.errors.values())[0][0]), status=status.HTTP_400_BAD_REQUEST)
        token_ids = [i['id'] for i in ids if i['type'] == 1]
        t_models = models.Coin.objects.using('coin_source').filter(id__in=token_ids)
        token_data = serializers.CoinListSerializer(t_models, many=True).data

        return Response(dict(data=dict(list=token_data)), status=status.HTTP_200_OK)
    

class CoinInfoView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(1 * 60))
    def get(self, request):
        form = forms.CoinInfoForms(request.query_params)
        if not form.is_valid():
            return Response(dict(error=list(form.errors.values())[0][0]), status=status.HTTP_400_BAD_REQUEST)
        address = request.query_params['address']
        chain = request.query_params.get('chain', DEFAULT_CHAIN)
        if chain not in CHAIN_DICT:
            return Response(dict(data={'error': 'Chain error.'}),status=status.HTTP_400_BAD_REQUEST)

        data = dict()
        chain_gecko = CHAIN_DICT.get(chain, {}).get('gecko')
        chain_dex_tools = CHAIN_DICT.get(chain, {}).get('dex_tools')
        if chain_gecko:
            gecko_data = GeckoAPI.token_info(chain_gecko, address)
            data = dict(data, **gecko_data)
        else:
            return Response(dict(data=data), status=status.HTTP_200_OK)
        if chain_dex_tools:
            dex_tools_data = DexTools.token_info(chain_dex_tools, address)
            data['holders'] = dex_tools_data.get('holders')
        else:
            data['holders'] = None
        return Response(dict(data=data), status=status.HTTP_200_OK)
    

class PoolSearchView(APIView):
    # permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(1 * 60))
    def get(self, request):
        form = forms.CoinSearchForms(request.query_params)
        if not form.is_valid():
            return Response(dict(error=list(form.errors.values())[0][0]), status=status.HTTP_400_BAD_REQUEST)
        kw = request.query_params['kw']

        data = GeckoAPI.search(kw).get('pools', [])
        for d in data:
            network = d['network']
            chain = GECKO_CHAIN_DICT.get(network.get('identifier', ''))
            if not chain:
                continue
            d['network'] = dict(chain=chain, logo = f"{os.getenv('S3_DOMAIN')}/chains/logo/{chain}.png")
        
        return Response(dict(data=data), status=status.HTTP_200_OK)
    

class CoinQueryView(APIView):
    # permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(1 * 60))
    def get(self, request):
        form = forms.CoinSearchForms(request.query_params)
        if not form.is_valid():
            return Response(dict(error=list(form.errors.values())[0][0]), status=status.HTTP_400_BAD_REQUEST)
        kw = request.query_params['kw']

        data = []
        ave_data = AveAPI.search(kw)
        for d in ave_data:
            coin_data = dict(
                logo = urljoin(os.getenv('AVE_LOGO_DOMAIN'), d['logo_url']) if d.get('logo_url') else d.get('logo_url'),
                address = d['token'],
                name = d.get('name'),
                symbol = d.get('symbol'),
                decimals = d.get('decimal'),
                price_usd = d.get('current_price_usd'),
                price_change = d.get('price_change'),
            )
            chain = AVE_CHAIN_DICT.get(d.get('chain', ''))
            if not chain:
                coin_data['chain'] = dict(name=d.get('chain'), id = None, logo = None)
                coin_data['is_supported'] = False
                continue
            else:
                coin_data['chain'] = dict(name=chain, id = str(CHAIN_DICT[chain]['id']), logo = f"{os.getenv('S3_DOMAIN')}/chains/logo/{chain}.png")
                coin_data['is_supported'] = True
            data.append(coin_data)
        
        return Response(dict(data=data), status=status.HTTP_200_OK)
    

class AddressQueryView(APIView):
    # permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(1 * 60))
    def get(self, request):
        form = forms.AddressQueryForms(request.query_params)
        if not form.is_valid():
            return Response(dict(error=list(form.errors.values())[0][0]), status=status.HTTP_400_BAD_REQUEST)
        address = request.query_params['address']
        addr_type = request.query_params.get('type')
        chains = copy.deepcopy(CHAIN_DICT)
        excluded_chains = chains
        token_data = dict()
        account_data = dict()

        if not addr_type or addr_type == 'token':
            ave_data = AveAPI.search(address)
            for d in ave_data:
                coin_data = dict(
                    logo = urljoin(os.getenv('AVE_LOGO_DOMAIN'), d['logo_url']) if d.get('logo_url') else d.get('logo_url'),
                    address = d['token'],
                    name = d.get('name'),
                    symbol = d.get('symbol'),
                    decimals = d.get('decimal'),
                    price_usd = d.get('current_price_usd'),
                    price_change = d.get('price_change'),
                )
                chain = AVE_CHAIN_DICT.get(d.get('chain', ''))
                if not chain:
                    chain = d.get('chain')
                    coin_data['chain'] = dict(name=chain, id = None, logo = None)
                    coin_data['is_supported'] = False
                    continue
                else:
                    coin_data['chain'] = dict(name=chain, id = str(CHAIN_DICT[chain]['id']), logo = f"{os.getenv('S3_DOMAIN')}/chains/logo/{chain}.png")
                    coin_data['is_supported'] = True
                    if chain in excluded_chains:
                        excluded_chains.pop(chain)
                token_data[chain] = coin_data
        
        if not addr_type or addr_type == 'account':
            wallet_handler = WalletHandler()
            address_type_res = wallet_handler.multi_account_type_exclude_token(address, excluded_chains)

            chains_for_account = [k for k, v in address_type_res.items() if v == 'user']
            balance_for_account = wallet_handler.multi_get_balances([address], chains_for_account)
            account_data = {k:v[address] if len(v) else v for k, v in balance_for_account.items()}

        return Response(dict(data=dict(tokens=token_data, accounts=account_data)), status=status.HTTP_200_OK)