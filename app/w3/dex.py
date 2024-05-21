import os
from typing import Any
import requests
from django.core.cache import cache

from utils.fetch import MultiFetch
from subscribe import models as subscribe_models


class DexTools():
    domain: str | None = os.getenv(key='DEX_DOMAIN')
    headers: dict[str, str | None] = {
        'x-api-key': os.getenv(key='DEX_KEY'),
        'accept': 'application/json',
    }

    @classmethod
    def token_info(cls, chain: str, address: str) -> dict:
        urls: list[str] = [
            f'{cls.domain}/token/{chain}/{address}/info',
        ]
        res: dict[str, Any] = MultiFetch.fetch_multiple_urls(headers=cls.headers, urls=urls)
        data: dict[str, Any] = res[urls[0]].get('data') or dict()
        return data
    

class GeckoAPI():
    domain: str | None = os.getenv(key='GECKO_DOMAIN')
    app_domain: str | None = os.getenv(key='GECKO_APP_DOMAIN')
    headers: dict[str, str] = {
        'Accept': 'application/json;version=20230302',
    }

    @classmethod
    def search(cls, kw: str) -> dict | None:
        url: str = f'{cls.app_domain}/search?query={kw}'
        payload: dict[str, Any] = {}
        headers: dict[str, str] = {'User-Agent': 'PostmanRuntime/7.37.3'}
        response: requests.Response = requests.request(method="GET", url=url, headers=headers, data=payload)
        if response.status_code != 200:
            return {}
        res: dict[str, Any] | None = response.json().get('data', {}).get('attributes', {})
        return res

    @classmethod
    def token_info(cls, chain: str, address: str) -> dict:
        urls: list[str] = [
            f'{cls.domain}/networks/{chain}/tokens/{address}',
            f'{cls.domain}/networks/{chain}/tokens/{address}/info',
            f'{cls.domain}/networks/{chain}/tokens/{address}/pools'
        ]
        res: dict[str, Any] = MultiFetch.fetch_multiple_urls(headers=cls.headers, urls=urls)
        if not res:
            return dict()
        base: dict[str, Any] = res[urls[0]].get('data', {}).get('attributes', {})
        info: dict[str, Any] = res[urls[1]].get('data', {}).get('attributes', {})
        pools: list[dict] = res[urls[2]].get('data', {})
        pool: dict[str, Any] = pools[0].get('attributes', {}) if len(pools) > 0 else {}
        data: dict[str, Any] = dict(
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
    domain: str | None = os.getenv(key='AVE_DOMAIN')

    @staticmethod
    def get_auth() -> str | None:
        ave_cache_key: str = f'satoshi:ave_auth'
        ave_auth: str | None = cache.get(key=ave_cache_key)
        if not ave_auth:
            ave_auth = subscribe_models.Config.objects.filter(id=1).first().ave_auth
        else:
            cache.set(key=ave_cache_key, value=1, timeout=600)
        return ave_auth

    @classmethod
    def search(cls, kw: str) -> list[dict]:
        url: str = f'{cls.domain}/tokens/query?keyword={kw}'
        payload: dict[str, Any] = {}
        headers: dict[str, str | None] = {"X-Auth": cls.get_auth()}
        response: requests.Response = requests.request(method="GET", url=url, headers=headers, data=payload)
        if response.status_code != 200:
            return []
        res: list[dict] = response.json().get('data', {}).get('token_list', [])
        return res