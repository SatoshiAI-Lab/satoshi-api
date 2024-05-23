from typing import Any, Coroutine, Literal
from django.core.cache import cache

import json
import os
import copy
from eth_typing import ChecksumAddress
import requests
import re
from base58 import b58decode

from web3 import Web3
from web3.contract.contract import Contract

import aiohttp
from aiohttp import ClientTimeout
import asyncio

from eth_account import Account
from eth_account.signers.local import (
    LocalAccount,
)

from utils import constants

import logging

logger: logging.Logger = logging.getLogger(name=__name__)


def retry(retries: int=3, delay: int=1):
    def wrapper(func: Any):
        async def wrapped_f(*args, **kwargs) -> Any | None:
            nonlocal delay
            for attempt in range(1, retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries:
                        return
                    delay *= 2  # Exponential backoff
                    # await asyncio.sleep(delay)
        return wrapped_f
    return wrapper


class WalletHandler():
    def __init__(self) -> None:
        self.evm_domain: str | None = os.getenv(key='WEB3_EVM_API')
        self.sol_domain: str | None = os.getenv(key='WEB3_SOL_API')
        self.vybenetwork_domain: str | None = os.getenv(key='VYBENETWORK_DOMAIN')

    async def identify_platform(self, address: str) -> Literal['EVM'] | Literal['SOL'] | Literal['']:
        if re.match(pattern=r'^0x[a-fA-F0-9]{40}$', string=address):
            return 'EVM'
        try:
            decoded: bytes = b58decode(address)
            if len(decoded) in [32, 64]:
                return 'SOL'
        except ValueError:
            pass
        return ""

    @classmethod
    def account_type(cls, address: str, chain: str) -> Literal['token'] | Literal['unknown'] | Literal['user']:
        w3 = Web3(provider=Web3.HTTPProvider(constants.CHAIN_DICT[chain]['rpc']))

        def is_erc20_contract(a) -> bool:
            contract: Contract = w3.eth.contract(address=Web3.to_checksum_address(a), abi=constants.ERC20_ABI)
            try:
                contract.functions.totalSupply().call()
                contract.functions.balanceOf(a).call()
                contract.functions.allowance(a, a).call()
                return True
            except:
                return False

        address: ChecksumAddress = Web3.to_checksum_address(address)
        if w3.eth.get_code(account=address):
            if is_erc20_contract(a=address):
                return 'token'
            else:
                return 'unknown'
        else:
            return 'user'
        
    @classmethod
    async def account_type_exclude_token(cls, address: str, chain: str, session: aiohttp.ClientSession) -> Literal['unknown'] | Literal['user']:
        rpc_url: str = constants.CHAIN_DICT[chain]['rpc']

        payload: str = json.dumps(obj={
            "jsonrpc": "2.0",
            "method": "eth_getCode",
            "params": [address, "latest"],
            "id": 1,
        })

        async with session.post(url=rpc_url, data=payload, headers={"Content-Type": "application/json"}) as response:
            if response.status == 200:
                data: dict[str, Any] = await response.json()
                code: Any = data.get('result')
                if code and code != '0x':
                    return 'unknown'
                else:
                    return 'user'
            else:
                return 'unknown'

    async def multi_account_type_exclude_token(self, address: str, chain_list: list[str]) -> dict:
        results: dict[str, Any] = {}
        async with aiohttp.ClientSession() as session:
            tasks: list[Coroutine[Any, Any, Literal['unknown', 'user']]] = [self.account_type_exclude_token(address=address, chain=chain, session=session) for chain in chain_list]
            data: list[Literal['unknown', 'user']] = await asyncio.gather(*tasks)
            for chain, result in zip(chain_list, data):
                results[chain] = result
        return results

    def create_wallet(self, platform: str) -> None | tuple[Any, Any, str]:
        if platform == 'SOL':
            url: str = f"{self.sol_domain}/account/keyPair/new"
            try:
                response: requests.Response = requests.request(method="GET", url=url, timeout=15)
            except Exception as e:
                logger.error(msg=f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return 
            data: dict[str, Any] = response.json().get('data', {})
            secretKey, publicKey = data.get('secretKey'), data.get('publicKey')
            address: str = publicKey
        else:
            account: LocalAccount = Account.create()
            secretKey: str = account.key.hex()
            publicKey: bytes = account._key_obj.public_key
            address: str = publicKey.to_checksum_address()
            publicKey: str = publicKey.to_hex()
        return secretKey, publicKey, address
    
    async def multi_get_balances(self, address_list: list[str], chain_list: list[str]) -> dict:
        tasks: list = []
        results: dict[str, dict[str, Any]] = {}
        async with aiohttp.ClientSession() as session:
            for address in address_list:
                for chain in chain_list:
                    if await self.identify_platform(address=address) == constants.CHAIN_DICT[chain]['platform']:
                        tasks.append(self.get_balances(chain=chain, address=address, session=session))

            completed_tasks: list[Any | BaseException] = await asyncio.gather(*tasks, return_exceptions=True)
            for result in completed_tasks:
                if isinstance(result, Exception):
                    continue
                chain, address, data = result
                if chain not in results:
                    results[chain] = {}
                results[chain][address] = data
        return results
    
    async def get_balances(self, chain: str, address: str, session: aiohttp.ClientSession) -> tuple[str, str, dict]:
        chain_data = dict(
            id = str(object=constants.CHAIN_DICT[chain]['id']),
            name = chain,
            logo = f"{os.getenv(key='S3_DOMAIN')}/chains/logo/{chain}.png",
        )
        json_data: dict[str, Any] = dict(address=address, value=0, tokens=[], chain=chain_data)
        if chain == 'merlin':
            res: dict[str, Any] | None = await self.get_balances_from_merlin(chain=chain, address=address, session=session)
        else:
            res: dict[str, Any] | None = await self.get_balances_from_cqt(chain=chain, address=address, session=session)
        if res:
            json_data = res
        return (chain, address, json_data)
    
    @retry(retries=3)
    async def request_balances_from_cqt(self, chain: str, address: str, session: aiohttp.ClientSession) -> dict | None:
        url: str = f"{os.getenv(key='CQT_DOMAIN')}/{chain}/address/{address}/balances_v2/"
        headers: dict[str, str] = {
            "Authorization": f"Bearer {os.getenv('CQT_KEY')}",
            "X-Requested-With": "com.covalenthq.sdk.python/0.9.8"
        }

        async with session.get(url=url, headers=headers, timeout=5) as response:
            if response.status == 200:
                return await response.json()
            else:
                response.raise_for_status()
            
    async def get_balances_from_cqt(self, chain: str, address: str, session: aiohttp.ClientSession) -> dict | None:
        network_name: str | None = constants.CHAIN_DICT.get(chain, dict()).get('cqt')
        if not network_name:
            return
        res: dict[str, Any] | None = await self.request_balances_from_cqt(network_name, address, session)
        if not res:
            return
        chain_id: str = res['data']['chain_id']
        chain_name: str = res['data']['chain_name']
        items: dict[str, Any] = res['data']['items']
        tokens: list = []
        value: int = 0
        chain_data = dict(
            id = str(object=chain_id),
            name = constants.CQT_CHAIN_DICT[chain_name],
            logo = f"{os.getenv(key='S3_DOMAIN')}/chains/logo/{constants.CQT_CHAIN_DICT[chain_name]}.png",
        )
        for item in items:
            price_usd: float | None = item.get('quote_rate')
            price_usd_24h: float | None = item.get('quote_rate_24h')
            price_change: float | None = round(number=(price_usd-price_usd_24h)/price_usd_24h*100, ndigits=4) if price_usd and price_usd_24h else None
            tokens.append(dict(
                symbol = item['contract_ticker_symbol'],
                name = item['contract_name'],
                decimals = item['contract_decimals'],
                amount = item['balance'],
                address = re.sub(pattern=r"0xe{40}|1{32}|0x0{36}800a", repl=constants.ZERO_ADDRESS, string=item['contract_address']),
                price_usd = price_usd,
                value_usd = item['quote'],
                price_change_24h = price_change,
                logo = item['logo_url'],
            ))
            value += item.get('quote') or 0
        json_data: dict[str, Any] = dict(address=address, value=value, tokens=tokens, chain=chain_data)
        return json_data
    
    @retry(retries=3)
    async def request_balances_from_merlin(self, address: str, session: aiohttp.ClientSession) -> dict | None:
        url: str | None = os.getenv(key='MERLIN_DOMAIN')
        headers: dict[str, str] = {'Content-Type': 'application/json'}

        timeout = ClientTimeout(connect=3, sock_read=6)
        async with session.get(url=f"{url}/address.getAddressTokenBalance?input=%7B%22json%22%3A%7B%22address%22%3A%22{address}%22%2C%22tokenType%22%3A%22erc20%22%7D%7D", headers=headers, timeout=timeout) as response:
            if response.status == 200:
                return await response.json()
            else:
                response.raise_for_status()

    async def get_balances_from_merlin(self, chain: str, address: str, session: aiohttp.ClientSession) -> dict | None:
        res: dict[str, Any] | None = await self.request_balances_from_merlin(address, session)
        if not res:
            return
        
        items: list = res.get('result', {}).get('data', {}).get('json', [])
        tokens: list = []
        value: int | None = None
        chain: dict[str, Any] = dict(
            id = str(object=constants.CHAIN_DICT[chain]['id']),
            name = chain,
            logo = f"{os.getenv(key='S3_DOMAIN')}/chains/logo/{chain}.png",
        )
        for item in items:
            tokens.append(dict(
                symbol = item['symbol'],
                name = item['name'],
                decimals = item['decimals'],
                amount = int(float(x=item.get('balance', 0)))/(10 ** int(x=item['decimals'])),
                address = item['token_address'],
                price_usd = None,
                value_usd = None,
                price_change_24h = None,
                logo = None,
            ))
        json_data: dict[str, Any] = dict(address=address, value=value, tokens=tokens, chain=chain)
        return json_data
    
    def token_transaction(self, chain: str, private_key: str, input_token: str, output_token: str, amount: str, slippageBps: int) -> str | None:
        hash_tx: str | None = None
        if chain == 'solana':
            url: str = f"{self.sol_domain}/swap"

            payload: str = json.dumps(obj=dict(
                secretKey = private_key,
                inputMint = input_token.replace(constants.ZERO_ADDRESS, constants.SOL_ADDRESS),
                outputMint = output_token.replace(constants.ZERO_ADDRESS, constants.SOL_ADDRESS),
                amount = amount,
                slippageBps = slippageBps,
            ))
            headers: dict[str, str] = {
            'Content-Type': 'application/json',
            }
            try:
                response: requests.Response = requests.request(method="POST", url=url, headers=headers, data=payload, timeout=60)
            except Exception as e:
                logger.error(msg=f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return 

            data: dict[str, Any] = response.json()
            hash_tx = data.get('data', {}).get('trx_hash')
        else:
            zero_address: str = constants.ZERO_ADDRESS
            if input_token == zero_address and output_token == zero_address:
                return
            url: str = f"{self.evm_domain}/evm/swap"
            payload: str = json.dumps(obj=dict(
                net = chain.lower(),
                secretKey = private_key,
                tokenInAddress = input_token,
                tokenOutAddress = output_token,
                tokenInAmount = amount,
                slippageBps = slippageBps,
            ))
            headers: dict[str, str] = {
            'Content-Type': 'application/json',
            }
            try:
                response = requests.request(method="POST", url=url, headers=headers, data=payload, timeout=60)
            except Exception as e:
                logger.error(msg=f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return 

            data: dict[str, Any] = response.json()
            hash_tx = data.get('data', {}).get('trx_hash')
        return hash_tx
    
    def check_hash(self, chain: str, data_list: list[dict]) -> list | None:
        data: list = []
        if chain == 'solana':
            url: str = f"{self.sol_domain}/transaction/is_success"

            payload: str = json.dumps(obj=data_list)
            headers: dict[str, str] = {
            'Content-Type': 'application/json',
            }
            try:
                response: requests.Response = requests.request(method="POST", url=url, headers=headers, data=payload, timeout=15)
            except Exception as e:
                logger.error(msg=f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return data
            data: list = response.json().get('data', [])
        else:
            url: str = f"{self.evm_domain}/evm/transaction/is_success"

            payload: str = json.dumps(obj=dict(net=chain.lower(), list=data_list))
            headers: dict[str, str] = {
            'Content-Type': 'application/json',
            }
            try:
                response = requests.request(method="POST", url=url, headers=headers, data=payload, timeout=15)
            except Exception as e:
                logger.error(msg=f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return data
            data: list = response.json().get('data', [])
        return data
    
    def multi_check_hash(self, hash_data: dict) -> dict | None:
        data: list = []

        url: str = f"{self.evm_domain}/evm/transaction/is_success/batch"

        payload: str = json.dumps(obj=hash_data)
        headers: dict[str, str] = {
        'Content-Type': 'application/json',
        }
        try:
            response: requests.Response = requests.request(method="POST", url=url, headers=headers, data=payload, timeout=15)
        except Exception as e:
            logger.error(msg=f'Request timeout: {e}')
            return
        if response.status_code != 200:
            return data
        data: dict[str, Any] | None = response.json().get('data', {})
        return data
    
    def get_address_from_hash(self, chain: str, hash_tx: str) -> None | str:
        data: str | None = None
        if chain == 'solana':
            url: str = f"{self.sol_domain}/token/address?create_trx_hash={hash_tx}"

            payload: dict[str, Any] = {}
            headers: dict[str, str] = {
            'Content-Type': 'application/json',
            }
            try:
                response: requests.Response = requests.request(method="GET", url=url, headers=headers, data=payload, timeout=15)
            except Exception as e:
                logger.error(msg=f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return data
            data: str = response.json().get('data', {}).get('token_address')
        return data
    
    def create_token(self, chain: str, private_key: str, name: str, symbol: str, desc: str, decimals: int, amount: int) -> tuple[str | None, str | None]:
        hash_tx: str | None = None
        address: str | None = None
        if chain == 'solana':
            url: str = f"{self.sol_domain}/token/create"

            payload: str = json.dumps(obj=dict(
                secretKey = private_key,
                tokenName = name,
                tokenSymbol = symbol,
                tokenDescription = desc,
                tokenDecimals = decimals,
            ))
            headers: dict[str, str] = {
            'Content-Type': 'application/json',
            }
            try:
                response: requests.Response = requests.request(method="POST", url=url, headers=headers, data=payload, timeout=60)
            except Exception as e:
                logger.error(msg=f'Request timeout: {e}')
                return hash_tx, address
            if response.status_code != 200:
                return hash_tx, address
            data: dict[str, Any] = response.json().get('data', dict())
            hash_tx = data.get('create_trx_hash')
            address = self.get_address_from_hash(chain=chain, hash_tx=hash_tx)
        else:
            url: str = f"{self.evm_domain}/evm/token/new"

            payload: str = json.dumps(obj=dict(
                net = chain.lower(),
                secretKey = private_key,
                tokenName = name,
                tokenSymbol = symbol,
                tokenDecimals = decimals,
                mintAmount = amount,
            ))
            headers: dict[str, str] = {
            'Content-Type': 'application/json',
            }
            try:
                response: requests.Response = requests.request(method="POST", url=url, headers=headers, data=payload, timeout=60)
            except Exception as e:
                logger.error(msg=f'Request timeout: {e}')
                return hash_tx, address
            if response.status_code != 200:
                return hash_tx, address
            data: dict[str, Any] = response.json().get('data', dict())
            hash_tx = data.get('trx_hash')
            address = data.get('token_address')
        return hash_tx, address
    
    def mint_token(self, chain: str, private_key: str, create_hash: str, mint_amount: int) -> str | None:
        hash_tx: str | None = None
        if chain == 'solana':
            url: str = f"{self.sol_domain}/token/mint"

            payload: str = json.dumps(dict(
                secretKey = private_key,
                createTrxHash = create_hash,
                tokenMintAmount = mint_amount,
            ))
            headers: dict[str, str] = {
            'Content-Type': 'application/json',
            }
            try:
                response: requests.Response = requests.request(method="POST", url=url, headers=headers, data=payload, timeout=60)
            except Exception as e:
                logger.error(msg=f'Request timeout: {e}')
                return
            if response.status_code != 200:
                return hash_tx
            data: dict[str, Any] = response.json().get('data', dict())
            hash_tx = data.get('mint_trx_hash')
        return hash_tx
        
    def token_cross_quote(self, form_data: dict) -> tuple[int, dict]:
        target_url: str = f"{os.getenv(key='WEB3_EVM_API')}/cross_chain/quote"
        response: requests.Response = requests.post(url=target_url, json=form_data)
        if response.status_code != 200:
            try: 
                resp_json: dict = response.json()
            except:
                resp_json = dict(code=response.status_code, message='Web3 server error', data = response.text)
            logger.error(msg=f"{resp_json['code']} {resp_json['message']}")
            return response.status_code, resp_json
        return response.status_code, response.json()
    
    def token_cross(self, form_data: dict) -> tuple[int, dict]:
        provider: str = form_data.get('provider')
        target_url: str = f"{os.getenv(key='WEB3_EVM_API')}/cross_chain/cross/{provider}"
        response: requests.Response = requests.post(url=target_url, json=form_data)
        if response.status_code != 200:
            try: 
                resp_json: dict = response.json()
            except:
                resp_json = dict(code=response.status_code, message='Web3 server error', data = response.text)
            logger.error(msg=f"{resp_json['code']} {resp_json['message']}")
            return response.status_code, resp_json
        return response.status_code, response.json()
    
    def token_cross_status(self, provider: str, chain: str, hash_tx: str) -> tuple[int, dict]:
        target_url: str = f"{os.getenv(key='WEB3_EVM_API')}/cross_chain/state/{provider}"
        response: requests.Response = requests.get(url=target_url, params=dict(from_net=chain, trx_hash=hash_tx))
        if response.status_code != 200:
            try: 
                resp_json: dict = response.json()
            except:
                resp_json = dict(code=response.status_code, message='Web3 server error', data = response.text)
            logger.error(msg=f"{resp_json['code']} {resp_json['message']}")
            return response.status_code, resp_json
        return response.status_code, response.json()