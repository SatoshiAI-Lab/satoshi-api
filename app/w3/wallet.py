from django.core.cache import cache

import json
import os
import requests
from eth_account import Account

from covalent import CovalentClient


class WalletHandler():
    def __init__(self, platform) -> None:
        self.platform = platform
        self.domain = os.getenv('WEB3_API')
        self.vybenetwork_domain = os.getenv('VYBENETWORK_DOMAIN')

    def create_wallet(self):
        if self.platform == 'SOL':
            url = f"{self.domain}/account/keyPair/new"
            response = requests.request("GET", url)
            if response.status_code != 200:
                return 
            data = json.loads(response.text)['data']
            secretKey, publicKey = data.get('secretKey'), data.get('publicKey')
        else:
            account = Account.create()
            secretKey = account.key.hex()
            publicKey = account._key_obj.public_key.to_hex()
        return secretKey, publicKey
    
    def get_balances(self, address):
        cache_key = f"satoshi:balances:{address}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        c = CovalentClient(os.getenv('CQT_KEY'))
        if self.platform == 'SOL':
            network_name = 'solana-mainnet'
            b = c.balance_service.get_token_balances_for_wallet_address(network_name, address)
            if b.error:
                json_data = dict(address=address, value=0, tokens=[])
            else:
                items = b.data.items
                tokens = []
                value = 0
                for item in items:
                    tokens.append(dict(
                        symbol = item.contract_ticker_symbol,
                        name = item.contract_name,
                        decimals = item.contract_decimals,
                        amount = item.balance,
                        address = item.contract_address,
                        priceUsd = item.quote_rate,
                        valueUsd = item.quote,
                        logoUrl = item.logo_url,
                    ))
                    value += item.quote
                json_data = dict(address=address, value=value, tokens=tokens)      
        else:
            json_data = dict(address=address, value=0, tokens=[])
            
        cache.set(cache_key, json_data, timeout=10)
        return json_data
    
    def token_transaction(self, private_key, input_token, output_token, amount, slippageBps):
        if self.platform == 'SOL':
            url = f"{self.domain}/swap"

            payload = json.dumps(dict(
                secretKey = private_key,
                inputMint = input_token,
                outputMint = output_token,
                amount = amount,
                slippageBps = slippageBps,
            ))
            headers = {
            'Content-Type': 'application/json',
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            if response.status_code != 200:
                return 

            data = json.loads(response.text)
            hash_tx = data.get('data', {}).get('trx_hash')
        else:
            hash_tx = None
        return hash_tx