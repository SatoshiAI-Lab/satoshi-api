from django.core.cache import cache

import json
import os
import requests
from eth_account import Account

from covalent import CovalentClient
from concurrent import futures
from utils.constants import *

from utils.fetch import MultiFetch


class WalletHandler():
    def __init__(self) -> None:
        self.domain = os.getenv('WEB3_API')
        self.vybenetwork_domain = os.getenv('VYBENETWORK_DOMAIN')

    def create_wallet(self, platform):
        if platform == DEFAULT_PLATFORM:
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
    
    def multi_get_balances(self, chain, address_list):
        with futures.ThreadPoolExecutor() as executor:
            future_to_address = {executor.submit(self.get_balances, chain, address): address for address in address_list}
            results = dict()
            for future in futures.as_completed(future_to_address):
                address = future_to_address[future]
                try:
                    data = future.result()
                    results[address] = data
                except Exception as e:
                    print(f"Error fetching balances for address '{address}': {str(e)}")
        return results
    
    def get_balances(self, chain, address):
        cache_key = f"satoshi:balances:{address}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        json_data = None
        if chain == 'Solana':
            json_data = self.get_balances_from_helius(address)
        if not json_data:
            json_data = self.get_balances_from_cqt(chain, address)
        if not json_data:
            json_data = dict(address=address, value=0, tokens=[], chain=None)
        
        cache.set(cache_key, json_data, timeout=10)
        return json_data
    
    def get_balances_from_helius(self, address):
        url = os.getenv('HELIUS_DOMAIN')
        payload = json.dumps({
        "jsonrpc": "2.0",
        "id": "my-id",
        "method": "searchAssets",
        "params": {
            "ownerAddress": address,
            "displayOptions": {
            "showNativeBalance": True
            },
            "tokenType": "fungible"
        }
        })
        headers = {
        'Content-Type': 'application/json',
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        try:
            items = json.loads(response.text)['result']['items']
        except:
            return
        tokens = []
        value = 0
        chain = dict(
            id = 1399811149,
            name = 'Solana',
            logo = f"{os.getenv('S3_DOMAIN')}/chains/logo/Solana.png",
        )
        for item in items:
            meta = item['content']['metadata']
            token_info = item['token_info']
            price_info = token_info.get('price_info', {})
            tokens.append(dict(
                symbol = meta['symbol'],
                name = meta['name'],
                decimals = token_info['decimals'],
                amount = token_info['balance'],
                address = item['id'],
                priceUsd = price_info.get('price_per_token', 0),
                valueUsd = price_info.get('total_price', 0),
                logoUrl = None,
                chain_id = chain['id'],
                chain_name = chain['name'],
                chain_logo = chain['logo'],
            ))
            value += price_info.get('total_price', 0)
        json_data = dict(address=address, value=value, tokens=tokens, chain=chain)
        return json_data
    
    def get_balances_from_cqt(self, chain, address):
        network_name = CHAIN_DICT.get(chain, dict()).get('cqt')
        if not network_name:
            return
        
        c = CovalentClient(os.getenv('CQT_KEY'))
        b = c.balance_service.get_token_balances_for_wallet_address(network_name, address)
        if b.error:
            return
        else:
            chain_id = b.data.chain_id
            chain_name = b.data.chain_name
            items = b.data.items
            # items = self.update_token_info(b.data.items)
            tokens = []
            value = 0
            chain = dict(
                id = chain_id,
                name = CQT_CHAIN_DICT[chain_name],
                logo = f"{os.getenv('S3_DOMAIN')}/chains/logo/{CQT_CHAIN_DICT[chain_name]}.png",
            )
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
                    chain_id = chain['id'],
                    chain_name = chain['name'],
                    chain_logo = chain['logo'],
                ))
                value += item.quote
            json_data = dict(address=address, value=value, tokens=tokens, chain=chain)
        return json_data
    
    def update_token_info(self, items):
        addresses = []
        for item in items:
            if item.contract_name and item.contract_ticker_symbol:
                continue
            addresses.append(item.contract_address)
        
        headers = {
        'accept': 'application/json',
        'x-api-key': os.getenv('SHYFT_KEY')
        }
        token_dict = MultiFetch.fetch_multiple_urls(headers, [f"{os.getenv('SHYFT_DOMAIN')}/token/get_info?network=mainnet-beta&token_address={a}" for a in addresses])
        for item in items:
            res = token_dict.get(f"{os.getenv('SHYFT_DOMAIN')}/token/get_info?network=mainnet-beta&token_address={item.contract_address}")
            if not res:
                continue
            data = json.loads(res).get('result', {})
            item.contract_name = data.get('name')
            item.contract_ticker_symbol = data.get('symbol')
        return items
    
    def token_transaction(self, chain, private_key, input_token, output_token, amount, slippageBps):
        hash_tx = None
        if chain == 'Solana':
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
        return hash_tx
    
    def check_hash(self, chain, data_list):
        data = []
        if chain == 'Solana':
            url = f"{self.domain}/transaction/is_success"

            payload = json.dumps(data_list)
            headers = {
            'Content-Type': 'application/json',
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            if response.status_code != 200:
                return data
            data = json.loads(response.text).get('data', [])
        return data
    
    def get_address_from_hash(self, chain, hash_tx):
        data = None
        if chain == 'Solana':
            url = f"{self.domain}/token/address?create_trx_hash={hash_tx}"

            payload = {}
            headers = {
            'Content-Type': 'application/json',
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            if response.status_code != 200:
                return data
            data = json.loads(response.text).get('data', {}).get('token_address')
        return data
    
    def create_token(self, chain, private_key, name, symbol, desc, decimals):
        hash_tx = None
        if chain == 'Solana':
            url = f"{self.domain}/token/create"

            payload = json.dumps(dict(
                secretKey = private_key,
                tokenName = name,
                tokenSymbol = symbol,
                tokenDescription = desc,
                tokenDecimals = decimals,
            ))
            headers = {
            'Content-Type': 'application/json',
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            if response.status_code != 200:
                return hash_tx
            data = json.loads(response.text).get('data', dict())
            hash_tx = data.get('create_trx_hash')
        return hash_tx
    
    def mint_token(self, chain, private_key, create_hash, mint_amount):
        hash_tx = None
        if chain == 'Solana':
            url = f"{self.domain}/token/mint"

            payload = json.dumps(dict(
                secretKey = private_key,
                createTrxHash = create_hash,
                tokenMintAmount = mint_amount,
            ))
            headers = {
            'Content-Type': 'application/json',
            }
            response = requests.request("POST", url, headers=headers, data=payload)
            if response.status_code != 200:
                return hash_tx
            data = json.loads(response.text).get('data', dict())
            hash_tx = data.get('mint_trx_hash')
        return hash_tx
        