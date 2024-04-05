from django.core.cache import cache

import json
import os
import requests
from eth_account import Account


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
    
    def get_decimals(self, address):
        cache_key = f"satoshi:decimals:{address}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        if self.platform == 'SOL':
            decimals = 6
            if address == 'So11111111111111111111111111111111111111112':
                decimals = 9
            elif address in ['Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB', 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v']:
                decimals = 6
        else:
            decimals = 18
            
        cache.set(cache_key, decimals, timeout=3600)
        
        return decimals
    
    def get_balances(self, address):
        cache_key = f"satoshi:balances:{address}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        if self.platform == 'SOL':
            url = f"{self.vybenetwork_domain}/account/token-balance/{address}"
            headers = {
                'X-API-Key': os.getenv('VYBENETWORK_KEY'),
                'accept': 'application/json',
            }
            response = requests.request("GET", url, headers=headers, json={})
            
            if response.status_code != 200:
                return dict()
            
            data = json.loads(response.text)
            json_data = dict(address=address, value=data.get('valueUsd', 0), tokens=data.get('data', []))
        else:
            json_data = dict(address=address, value=0, tokens=[])
            
        cache.set(cache_key, json_data, timeout=90)
        
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