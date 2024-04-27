from django.core.cache import cache

import json
import os
import requests
from eth_account import Account
from web3 import Web3
import re
from base58 import b58decode

import aiohttp
import asyncio

from concurrent import futures
from utils import constants

import logging

logger = logging.getLogger(__name__)


class WalletHandler():
    def __init__(self) -> None:
        self.evm_domain = os.getenv('WEB3_EVM_API')
        self.sol_domain = os.getenv('WEB3_SOL_API')
        self.vybenetwork_domain = os.getenv('VYBENETWORK_DOMAIN')

    async def identify_platform(self, address):
        if re.match(r'^0x[a-fA-F0-9]{40}$', address):
            return 'EVM'
        try:
            decoded = b58decode(address)
            if len(decoded) in [32, 64]:
                return 'SOL'
        except ValueError:
            pass
        return ""

    @classmethod
    def account_type(cls, address, chain):
        w3 = Web3(Web3.HTTPProvider(constants.CHAIN_DICT[chain]['rpc']))

        def is_erc20_contract(a):
            contract = w3.eth.contract(address=Web3.to_checksum_address(a), abi=constants.ERC20_ABI)
            try:
                contract.functions.totalSupply().call()
                contract.functions.balanceOf(a).call()
                contract.functions.allowance(a, a).call()
                return True
            except:
                return False

        address = Web3.to_checksum_address(address)
        if w3.eth.get_code(address):
            if is_erc20_contract(address):
                return 'token'
            else:
                return 'unknown'
        else:
            return 'user'
        
    @classmethod
    def account_type_exclude_token(cls, address, chain):
        w3 = Web3(Web3.HTTPProvider(constants.CHAIN_DICT[chain]['rpc']))

        address = Web3.to_checksum_address(address)
        if w3.eth.get_code(address):
            return 'unknown'
        else:
            return 'user'
        
    def multi_account_type_exclude_token(self, address, chain_list):
        with futures.ThreadPoolExecutor() as executor:
            future_to_chain = {executor.submit(self.account_type_exclude_token, address, chain): chain for chain in chain_list}
            results = {}
            for future in futures.as_completed(future_to_chain):
                chain = future_to_chain[future]
                try:
                    data = future.result()
                    if chain not in results:
                        results[chain] = {}
                    results[chain] = data
                except Exception as e:
                    logging.error(f"Error query account type for chain '{chain}': {str(e)}")
        return results

    def create_wallet(self, platform):
        if platform == 'SOL':
            url = f"{self.sol_domain}/account/keyPair/new"
            try:
                response = requests.request("GET", url, timeout=15)
            except Exception as e:
                logger.error(f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return 
            data = json.loads(response.text)['data']
            secretKey, publicKey = data.get('secretKey'), data.get('publicKey')
            address = publicKey
        else:
            account = Account.create()
            secretKey = account.key.hex()
            publicKey = account._key_obj.public_key
            address = publicKey.to_checksum_address()
            publicKey = publicKey.to_hex()
        return secretKey, publicKey, address
    
    async def multi_get_balances(self, address_list, chain_list):
        tasks = []
        async with aiohttp.ClientSession() as session:
            for address in address_list:
                for chain in chain_list:
                    if await self.identify_platform(address) == constants.CHAIN_DICT[chain]['platform']:
                        tasks.append(self.get_balances(chain, address))

            results = {}
            for future in asyncio.as_completed(tasks):
                chain, address, data = await future
                if chain not in results:
                    results[chain] = {}
                results[chain][address] = data

        return results

    async def get_balances(self, chain, address):   
        chain_data = dict(
            id = str(constants.CHAIN_DICT[chain]['id']),
            name = chain,
            logo = f"{os.getenv('S3_DOMAIN')}/chains/logo/{chain}.png",
        )
        json_data = dict(address=address, value=0, tokens=[], chain=chain_data)
        if chain == 'merlin':
            res = await self.get_balances_from_merlin(chain, address)
        else:
            res = await self.get_balances_from_cqt(chain, address)
        if res:
            json_data = res
        return (chain, address, json_data)
    
    async def get_token_balances_from_cqt(self, chain, address):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{os.getenv('CQT_DOMAIN')}/{chain}/address/{address}/balances_v2/",
                    headers={
                        "Authorization": f"Bearer {os.getenv('CQT_KEY')}",
                        "X-Requested-With": "com.covalenthq.sdk.python/0.9.8"
                    }
                ) as response:
                    if response.status != 200:
                        return
                    return await response.json()
            except Exception as e:
                logging.error(f"Error fetching balances for chain '{chain}': {str(e)}")
                return
            
    async def get_balances_from_cqt(self, chain, address):
        network_name = constants.CHAIN_DICT.get(chain, dict()).get('cqt')
        if not network_name:
            return
        res = await self.get_token_balances_from_cqt(network_name, address)
        if not res:
            return
        chain_id = res['data']['chain_id']
        chain_name = res['data']['chain_name']
        items = res['data']['items']
        # items = self.update_token_info(chain, b.data.items)
        tokens = []
        value = 0
        chain_data = dict(
            id = str(chain_id),
            name = constants.CQT_CHAIN_DICT[chain_name],
            logo = f"{os.getenv('S3_DOMAIN')}/chains/logo/{constants.CQT_CHAIN_DICT[chain_name]}.png",
        )
        for item in items:
            address = re.sub(r'0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee|11111111111111111111111111111111', constants.ZERO_ADDRESS, item['contract_address'])
            price_usd = item.get('quote_rate')
            price_usd_24h = item.get('quote_rate_24h')
            tokens.append(dict(
                symbol = item['contract_ticker_symbol'],
                name = item['contract_name'],
                decimals = item['contract_decimals'],
                amount = item['balance'],
                address = address,
                priceUsd = price_usd,
                valueUsd = item['quote'],
                price_usd = price_usd,
                value_usd = item['quote'],
                price_change_24h = round((price_usd-price_usd_24h)/price_usd_24h*100, 4) if price_usd and price_usd_24h else None,
                logoUrl = item['logo_url'],
            ))
            value += item.get('quote') or 0
        json_data = dict(address=address, value=value, tokens=tokens, chain=chain_data)
        return json_data

    async def get_balances_from_merlin(self, chain, address):
        url = os.getenv('MERLIN_DOMAIN')
        json_data = {}
        headers = {'Content-Type': 'application/json'}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/address.getAddressTokenBalance?input=%7B%22json%22%3A%7B%22address%22%3A%22{address}%22%2C%22tokenType%22%3A%22erc20%22%7D%7D", headers=headers, timeout=15) as response:
                    if response.status != 200:
                        return json_data
                    data = await response.json()
                    items = data.get('result', {}).get('data', {}).get('json', [])
                    tokens = []
                    value = None
                    chain = dict(
                        id = str(constants.CHAIN_DICT[chain]['id']),
                        name = chain,
                        logo = f"{os.getenv('S3_DOMAIN')}/chains/logo/{chain}.png",
                    )
                    for item in items:
                        tokens.append(dict(
                            symbol = item['symbol'],
                            name = item['name'],
                            decimals = item['decimals'],
                            amount = int(float(item.get('balance', 0)))/(10 ** int(item['decimals'])),
                            address = item['token_address'],
                            priceUsd = None,
                            valueUsd = None,
                            price_usd = None,
                            value_usd = None,
                            price_change_24h = None,
                            logoUrl = None,
                        ))
                    json_data = dict(address=address, value=value, tokens=tokens, chain=chain)
        except Exception as e:
            logger.error(f'Request timeout: {e}')
            return
        return json_data
    
    def update_token_info(self, chain, items):
        if chain != 'solana':
            w3 = Web3(Web3.HTTPProvider(constants.CHAIN_DICT[chain]['rpc']))
            for item in items:
                try:
                    if item.contract_name and item.contract_ticker_symbol:
                        continue
                    if item.address == constants.ZERO_ADDRESS:
                        continue
                    contract = w3.eth.contract(address=Web3.to_checksum_address(item.contract_address), abi=constants.ERC20_ABI)
                    item.contract_name = contract.functions.name().call()
                    item.contract_ticker_symbol = contract.functions.symbol().call()    
                except:
                    continue    
        return items
    
    def token_transaction(self, chain, private_key, input_token, output_token, amount, slippageBps):
        hash_tx = None
        if chain == 'solana':
            url = f"{self.sol_domain}/swap"

            payload = json.dumps(dict(
                secretKey = private_key,
                inputMint = input_token.replace(constants.ZERO_ADDRESS, constants.SOL_ADDRESS),
                outputMint = output_token.replace(constants.ZERO_ADDRESS, constants.SOL_ADDRESS),
                amount = amount,
                slippageBps = slippageBps,
            ))
            headers = {
            'Content-Type': 'application/json',
            }
            try:
                response = requests.request("POST", url, headers=headers, data=payload, timeout=60)
            except Exception as e:
                logger.error(f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return 

            data = json.loads(response.text)
            hash_tx = data.get('data', {}).get('trx_hash')
        else:
            zero_address = constants.ZERO_ADDRESS
            if input_token == zero_address and output_token == zero_address:
                return
            url = f"{self.evm_domain}/evm/swap"
            payload = json.dumps(dict(
                net = chain.lower(),
                secretKey = private_key,
                tokenInAddress = input_token,
                tokenOutAddress = output_token,
                tokenInAmount = amount,
                slippageBps = slippageBps,
            ))
            headers = {
            'Content-Type': 'application/json',
            }
            try:
                response = requests.request("POST", url, headers=headers, data=payload, timeout=60)
            except Exception as e:
                logger.error(f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return 

            data = json.loads(response.text)
            hash_tx = data.get('data', {}).get('trx_hash')
        return hash_tx
    
    def check_hash(self, chain, data_list):
        data = []
        if chain == 'solana':
            url = f"{self.sol_domain}/transaction/is_success"

            payload = json.dumps(data_list)
            headers = {
            'Content-Type': 'application/json',
            }
            try:
                response = requests.request("POST", url, headers=headers, data=payload, timeout=15)
            except Exception as e:
                logger.error(f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return data
            data = json.loads(response.text).get('data', [])
        else:
            url = f"{self.evm_domain}/evm/transaction/is_success"

            payload = json.dumps(dict(net=chain.lower(), list=data_list))
            headers = {
            'Content-Type': 'application/json',
            }
            try:
                response = requests.request("POST", url, headers=headers, data=payload, timeout=15)
            except Exception as e:
                logger.error(f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return data
            data = json.loads(response.text).get('data', [])
        return data
    
    def multi_check_hash(self, hash_data):
        data = []

        url = f"{self.evm_domain}/evm/transaction/is_success/batch"

        payload = json.dumps(hash_data)
        headers = {
        'Content-Type': 'application/json',
        }
        try:
            response = requests.request("POST", url, headers=headers, data=payload, timeout=15)
        except Exception as e:
            logger.error(f'Request timeout: {e}')
            return
        if response.status_code != 200:
            return data
        data = json.loads(response.text).get('data', {})
        return data
    
    def get_address_from_hash(self, chain, hash_tx):
        data = None
        if chain == 'solana':
            url = f"{self.sol_domain}/token/address?create_trx_hash={hash_tx}"

            payload = {}
            headers = {
            'Content-Type': 'application/json',
            }
            try:
                response = requests.request("GET", url, headers=headers, data=payload, timeout=15)
            except Exception as e:
                logger.error(f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return data
            data = json.loads(response.text).get('data', {}).get('token_address')
        return data
    
    def create_token(self, chain, private_key, name, symbol, desc, decimals, amount):
        hash_tx = None
        address = None
        if chain == 'solana':
            url = f"{self.sol_domain}/token/create"

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
            try:
                response = requests.request("POST", url, headers=headers, data=payload, timeout=60)
            except Exception as e:
                logger.error(f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return hash_tx, address
            data = json.loads(response.text).get('data', dict())
            hash_tx = data.get('create_trx_hash')
            address = self.get_address_from_hash(chain, hash_tx)
        else:
            url = f"{self.evm_domain}/evm/token/new"

            payload = json.dumps(dict(
                net = chain.lower(),
                secretKey = private_key,
                tokenName = name,
                tokenSymbol = symbol,
                tokenDecimals = decimals,
                mintAmount = amount,
            ))
            headers = {
            'Content-Type': 'application/json',
            }
            try:
                response = requests.request("POST", url, headers=headers, data=payload, timeout=60)
            except Exception as e:
                logger.error(f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return hash_tx, address
            data = json.loads(response.text).get('data', dict())
            hash_tx = data.get('trx_hash')
            address = data.get('token_address')
        return hash_tx, address
    
    def mint_token(self, chain, private_key, create_hash, mint_amount):
        hash_tx = None
        if chain == 'solana':
            url = f"{self.sol_domain}/token/mint"

            payload = json.dumps(dict(
                secretKey = private_key,
                createTrxHash = create_hash,
                tokenMintAmount = mint_amount,
            ))
            headers = {
            'Content-Type': 'application/json',
            }
            try:
                response = requests.request("POST", url, headers=headers, data=payload, timeout=60)
            except Exception as e:
                logger.error(f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return hash_tx
            data = json.loads(response.text).get('data', dict())
            hash_tx = data.get('mint_trx_hash')
        return hash_tx
        