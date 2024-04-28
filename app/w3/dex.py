from utils.fetch import MultiFetch
import os
import json
import requests
from django.core.cache import cache

from subscribe import models as subscribe_models


class DexTools():
    domain = os.getenv('DEX_DOMAIN')
    headers = {
        'x-api-key': os.getenv('DEX_KEY'),
        'accept': 'application/json',
    }

    @classmethod
    def token_info(cls, chain, address):
        urls = [
            # f'{cls.domain}/token/{chain}/{address}',
            f'{cls.domain}/token/{chain}/{address}/info',
            # f'{cls.domain}/token/{chain}/{address}/pools?sort=creationBlock&order=asc&from=0&to=9999999999'
        ]
        res = MultiFetch.fetch_multiple_urls(cls.headers, urls)

        # pools_data = json.loads(res[urls[2]]).get('data', {}).get('results', [])
        # pools_price_urls = []
        # pools_liquidity_urls = []
        # for p in pools_data:
        #     pools_price_urls.append(f"{cls.domain}/pool/{chain}/{p['address']}/price")
        #     pools_liquidity_urls.append(f"{cls.domain}/pool/{chain}/{p['address']}/liquidity")
        # pool_res = MultiFetch.fetch_multiple_urls(cls.headers, pools_price_urls + pools_liquidity_urls)
        return json.loads(res[urls[0]]).get('data') or dict()
    

class GeckoAPI():
    domain = os.getenv('GECKO_DOMAIN')
    app_domain = os.getenv('GECKO_APP_DOMAIN')
    headers = {
        'Accept': 'application/json;version=20230302',
    }

    @classmethod
    def search(cls, kw):
        url = f'{cls.app_domain}/search?query={kw}'
        payload = {}
        headers = {'User-Agent': 'PostmanRuntime/7.37.3'}
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code != 200:
            return {}
        res = json.loads(response.text).get('data', {}).get('attributes', {})
        return res

    @classmethod
    def token_info(cls, chain, address):
        urls = [
            f'{cls.domain}/networks/{chain}/tokens/{address}',
            f'{cls.domain}/networks/{chain}/tokens/{address}/info',
            f'{cls.domain}/networks/{chain}/tokens/{address}/pools'
        ]
        res = MultiFetch.fetch_multiple_urls(cls.headers, urls)
        if not res:
            return dict()
        base = json.loads(res[urls[0]]).get('data', {}).get('attributes', {})
        info = json.loads(res[urls[1]]).get('data', {}).get('attributes', {})
        pools = json.loads(res[urls[2]]).get('data', {})
        pool = pools[0].get('attributes', {}) if len(pools) > 0 else {}
        data = dict(
            address = base.get('address'),
            logo = base['image_url'] if base.get('image_url') and base['image_url'] != 'missing.png' else None,
            name = base.get('name'),
            symbol = base.get('symbol'),
            decimals = base.get('decimals'),
            description = info.get('description'),
            price = base.get('price_usd'),
            liquidity = base.get('total_reserve_in_usd'),
            market_cap = base.get('market_cap_usd'),
            volume = base.get('volume_usd', {}).get('h24'),
            twitter = info.get('twitter_handle'),
            telegram = info.get('telegram_handle'),
            websites = info.get('websites'),
            price_change = pool.get('price_change_percentage', {}).get('h24'),
        )

        return data
    

class AveAPI():
    domain = os.getenv('AVE_DOMAIN')

    @staticmethod
    def get_auth():
        ave_cache_key = f'satoshi:ave_auth'  # 重复检测
        ave_auth = cache.get(ave_cache_key)
        if not ave_auth:
            ave_auth = subscribe_models.Config.objects.filter(id=1).first().ave_auth
        else:
            cache.set(ave_cache_key, 1, 600)
        return ave_auth

    @classmethod
    def search(cls, kw):
        url = f'{cls.domain}/tokens/query?keyword={kw}'
        payload = {}
        headers = {"X-Auth": cls.get_auth()}
        response = requests.request("GET", url, headers=headers, data=payload)
        if response.status_code != 200:
            return {}
        res = json.loads(response.text).get('data', {}).get('token_list', [])
        return res