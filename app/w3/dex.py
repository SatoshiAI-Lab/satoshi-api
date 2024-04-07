from app.utils.fetch import MultiFetch
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
            f'{cls.domain}/token/{chain}/{address}',
            f'{cls.domain}/token/{chain}/{address}/info',
            f'{cls.domain}/token/{chain}/{address}/pools?sort=creationBlock&order=asc&from=0&to=9999999999'
        ]
        res = MultiFetch.fetch_multiple_urls(cls.headers, urls)

        pools_data = json.loads(res[urls[2]]).get('data', {}).get('results', [])

        pools_price_urls = []
        pools_liquidity_urls = []
        for p in pools_data:
            pools_price_urls.append(f"{cls.domain}/pool/{chain}/{p['address']}/price")
            pools_liquidity_urls.append(f"{cls.domain}/pool/{chain}/{p['address']}/liquidity")

        pool_res = MultiFetch.fetch_multiple_urls(cls.headers, pools_price_urls + pools_liquidity_urls)
        return pool_res