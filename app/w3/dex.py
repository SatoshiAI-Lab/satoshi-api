from app.utils.fetch import MultiFetch
import os


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
            f'{cls.domain}/pool/{chain}/{address}/price',
            f'{cls.domain}/pool/{chain}/{address}/liquidity',
        ]
        res = MultiFetch.fetch_multiple_urls(cls.headers, urls)
        return res