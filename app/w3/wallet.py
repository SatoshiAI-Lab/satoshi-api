from django.core.cache import cache

import json
import os
import requests
from eth_account import Account
from web3 import Web3
import re
from base58 import b58decode

from covalent import CovalentClient
from concurrent import futures
from utils import constants

from utils.fetch import MultiFetch

import logging

logger = logging.getLogger(__name__)


class WalletHandler():
    def __init__(self) -> None:
        self.evm_domain = os.getenv('WEB3_EVM_API')
        self.sol_domain = os.getenv('WEB3_SOL_API')
        self.vybenetwork_domain = os.getenv('VYBENETWORK_DOMAIN')

    def identify_platform(self, address):
        if re.match(r'^0x[a-fA-F0-9]{40}$', address):
            return 'EVM'
        try:
            decoded = b58decode(address)
            if len(decoded) in [32, 64]:
                return 'SOL'
        except ValueError:
            pass
        return ''

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
    
    def multi_get_balances(self, address_list, chain_list):           
        with futures.ThreadPoolExecutor() as executor:
            future_to_chain_address = {executor.submit(self.get_balances, chain, address): (chain, address) for address in address_list for chain in chain_list if self.identify_platform(address) == constants.CHAIN_DICT[chain]['platform']}
            results = {}
            for future in futures.as_completed(future_to_chain_address):
                chain, address = future_to_chain_address[future]
                try:
                    data = future.result()
                    if chain not in results:
                        results[chain] = {}
                    results[chain][address] = data
                except Exception as e:
                    logging.error(f"Error fetching balances for chain '{chain}' and address '{address}': {str(e)}")
        return results
    
    def get_balances(self, chain, address):   
        json_data = None
        if chain == 'Merlin':
            json_data = self.get_balances_from_merlin(chain, address)
        if not json_data:
            json_data = self.get_balances_from_cqt(chain, address)
        if not json_data:
            chain = dict(
                id = str(constants.CHAIN_DICT[chain]['id']),
                name = chain,
                logo = f"{os.getenv('S3_DOMAIN')}/chains/logo/{chain}.png",
            )
            json_data = dict(address=address, value=0, tokens=[], chain=chain)
        return json_data
    
    def get_balances_from_merlin(self, chain, address):
        json_data = {}
        url = os.getenv('MERLIN_DOMAIN')
        payload = {}
        headers = {
        'Content-Type': 'application/json',
        }
        try:
            response = requests.request("GET", f"{url}/address.getAddressTokenBalance?input=%7B%22json%22%3A%7B%22address%22%3A%22{address}%22%2C%22tokenType%22%3A%22erc20%22%7D%7D", headers=headers, data=payload, timeout=15)
            items = json.loads(response.text).get('result', {}).get('data', {}).get('json', [])
        except Exception as e:
            logger.error(f'Request timeout: {e}')
            return
        if response.status_code != 200:
            return json_data
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
                logoUrl = None,
            ))
        json_data = dict(address=address, value=value, tokens=tokens, chain=chain)
        return json_data
    
    def get_balances_from_helius(self, chain, address):
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
        try:
            response = requests.request("POST", url, headers=headers, data=payload, timeout=15)
            items = json.loads(response.text)['result']['items']
        except Exception as e:
            logger.error(f'Helius error: {e}')
            return
        tokens = []
        value = 0
        chain = dict(
            id = str(constants.CHAIN_DICT[chain]['id']),
            name = chain,
            logo = f"{os.getenv('S3_DOMAIN')}/chains/logo/{chain}.png",
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
            ))
            value += price_info.get('total_price', 0)
        json_data = dict(address=address, value=value, tokens=tokens, chain=chain)
        return json_data
    
    def get_balances_from_cqt(self, chain, address):
        network_name = constants.CHAIN_DICT.get(chain, dict()).get('cqt')
        if not network_name:
            return
        
        c = CovalentClient(os.getenv('CQT_KEY'))
        b = c.balance_service.get_token_balances_for_wallet_address(network_name, address)
        if b.error:
            logger.error(str(b.error))
            return
        else:
            chain_id = b.data.chain_id
            chain_name = b.data.chain_name
            items = b.data.items
            items = self.update_token_info(chain, b.data.items)
            tokens = []
            value = 0
            chain = dict(
                id = str(chain_id),
                name = constants.CQT_CHAIN_DICT[chain_name],
                logo = f"{os.getenv('S3_DOMAIN')}/chains/logo/{constants.CQT_CHAIN_DICT[chain_name]}.png",
            )
            for item in items:
                tokens.append(dict(
                    symbol = item.contract_ticker_symbol,
                    name = item.contract_name,
                    decimals = item.contract_decimals,
                    amount = item.balance,
                    address = item.contract_address.replace('0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee', '0x0000000000000000000000000000000000000000').replace('11111111111111111111111111111111', '0x0000000000000000000000000000000000000000'),
                    priceUsd = item.quote_rate,
                    valueUsd = item.quote,
                    logoUrl = item.logo_url,
                ))
                value += item.quote or 0
            json_data = dict(address=address, value=value, tokens=tokens, chain=chain)
        return json_data
    
    def update_token_info(self, chain, items):
        if chain == 'Solana':
            addresses = []
            # for item in items:
            #     if item.contract_name and item.contract_ticker_symbol:
            #         continue
            #     addresses.append(item.contract_address)

                # item.contract_name = contract.functions.name().call()
                # item.contract_ticker_symbol = contract.functions.symbol().call()     

            # headers = {
            # 'accept': 'application/json',
            # 'x-api-key': os.getenv('SHYFT_KEY')
            # }
            # token_dict = MultiFetch.fetch_multiple_urls(headers, [f"{os.getenv('SHYFT_DOMAIN')}/token/get_info?network=mainnet-beta&token_address={a}" for a in addresses])
            # for item in items:
            #     res = token_dict.get(f"{os.getenv('SHYFT_DOMAIN')}/token/get_info?network=mainnet-beta&token_address={item.contract_address}")
            #     if not res:
            #         continue
            #     data = json.loads(res).get('result', {})
            #     item.contract_name = data.get('name')
            #     item.contract_ticker_symbol = data.get('symbol')
        else:
            w3 = Web3(Web3.HTTPProvider(constants.CHAIN_DICT[chain]['rpc']))
            for item in items:
                try:
                    if item.contract_name and item.contract_ticker_symbol:
                        continue
                    if item.address == '0x0000000000000000000000000000000000000000':
                        continue
                    contract = w3.eth.contract(address=Web3.to_checksum_address(item.contract_address), abi=constants.ERC20_ABI)
                    item.contract_name = contract.functions.name().call()
                    item.contract_ticker_symbol = contract.functions.symbol().call()    
                except:
                    continue    
        return items
    
    def token_transaction(self, chain, private_key, input_token, output_token, amount, slippageBps):
        hash_tx = None
        if chain == 'Solana':
            url = f"{self.sol_domain}/swap"

            payload = json.dumps(dict(
                secretKey = private_key,
                inputMint = input_token.replace('0x0000000000000000000000000000000000000000', 'So11111111111111111111111111111111111111112'),
                outputMint = output_token.replace('0x0000000000000000000000000000000000000000', 'So11111111111111111111111111111111111111112'),
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
            zero_address = '0x0000000000000000000000000000000000000000'
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
        if chain == 'Solana':
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
    
    def get_address_from_hash(self, chain, hash_tx):
        data = None
        if chain == 'Solana':
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
        if chain == 'Solana':
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
        if chain == 'Solana':
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
        