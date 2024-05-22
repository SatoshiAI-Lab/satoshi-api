import os
import json
from typing import Any
import requests
from django.core.cache import cache
from utils import constants
from urllib.parse import urljoin

from utils.fetch import MultiFetch
from subscribe import models as subscribe_models


class DexTools():
    domain: str | None = os.getenv(key='DEX_DOMAIN')
    headers: dict[str, str | None] = {
        'x-api-key': os.getenv(key='DEX_KEY'),
        'accept': 'application/json',
    }

    @classmethod
    def token_base(cls, chain: str, address: str) -> dict | None:
        if address == constants.ZERO_ADDRESS:
            return constants.CHAIN_DICT[chain]['token']
        urls: list[str] = [
            f'{cls.domain}/token/{chain}/{address}',
        ]
        res: dict[str, Any] = MultiFetch.fetch_multiple_urls(headers=cls.headers, urls=urls)
        token_data: dict[str, Any] = res[urls[0]].get('data')
        if not token_data:
            return
        data: dict = dict(
            symbol = token_data['symbol'],
            name = token_data['name'],
            decimals = token_data['decimals'],
            logo = token_data['logo'],
            address = address,
        )
        return data

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
            price_change_24h = pool.get('price_change_percentage', {}).get('h24'),
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
    

class DefinedAPI():
    domain: str | None = os.getenv(key='DEFINED_DOMAIN')
    headers: dict[str, str] = {
        'Authorization': os.getenv(key='DEFINED_KEY'),
        'Content-Type': 'application/json'
    }

    @classmethod
    def search(cls, kw: str) -> list[dict[str, Any]]:
        url: str = f'{cls.domain}'
        headers: dict[str, str] = cls.headers
        payload: dict[str, Any] = {
            "query": """{
            filterTokens(
                filters: {
                liquidity: { gt: %s }
                # network: [1]
                }
                limit: 100
                offset: 0
                phrase: "%s"
            ) {
                results {
                change24
                txnCount24
                volume24
                isScam
                holders
                liquidity
                marketCap
                priceUSD
                pair {
                    token0
                    token1
                }
                exchanges {
                    name
                }
                token {
                    address
                    decimals
                    name
                    networkId
                    symbol
                    info {
                    imageThumbUrl
                    }
                }
                }
            }
            }
            """ % (10000 if len(kw) < 40 else 0, kw)
        }
        response: requests.Response = requests.request(method="POST", url=url, headers=headers, data=json.dumps(obj=payload))
        if response.status_code != 200:
            return []
        res: list[dict[str, Any]] | None = response.json().get('data', {}).get('filterTokens', {}).get('results', [])
        data: list[dict[str, Any]] = []
        for d in res:
            token: dict = d.get('token', {})
            coin_data: dict = dict(
                logo = token.get('info', {}).get('imageThumbUrl'),
                address = token.get('address'),
                name = token.get('name'),
                symbol = token.get('symbol'),
                decimals = token.get('decimals'),
                price_usd = d.get('priceUSD'),
                price_change = d.get('change24'),
                price_change_24h = d.get('change24'),
                holders = d.get('holders'),
                market_cap = d.get('marketCap'),
                volume = d.get('volume24'),
                liquidity = d.get('liquidity'),
                is_scam = d.get('isScam'),
            )
            chain: str | None = constants.CHAIN_DICT_FROM_ID.get(str(token.get('networkId')))
            if not chain:
                coin_data['chain'] = dict(name=None, id = token.get('networkId'), logo = None)
                coin_data['is_supported'] = False
                continue
            else:
                coin_data['chain'] = dict(name=chain, id = str(object=constants.CHAIN_DICT[chain]['id']), logo = f"{os.getenv(key='S3_DOMAIN')}/chains/logo/{chain}.png")
                coin_data['is_supported'] = True
            data.append(coin_data)
        return data