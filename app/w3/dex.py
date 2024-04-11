from utils.fetch import MultiFetch
import os
import json


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
        return json.loads(res[urls[0]]).get('data') if res and len(res) else dict()
    

class GeckoAPI():
    domain = os.getenv('GECKO_DOMAIN')
    headers = {
        'Accept': 'application/json;version=20230302',
    }

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
            logo = base.get('image_url'),
            name = base.get('name'),
            symbol = base.get('symbol'),
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