from typing import Any


ZERO_ADDRESS: str = '0x0000000000000000000000000000000000000000'
SOL_ADDRESS: str = 'So11111111111111111111111111111111111111112'

MESSAGE_TYPE_DICT: dict[int, str] = {
    0: 'news',
    1: "twitter",
    2: "announcement",
    3: "trade",
    4: "pool"
}

DEFAULT_IDS: list[dict[str, int]] = [
    {
        'type': 1,
        'id': 1
    },
    {
        'type': 1,
        'id': 141
    },
    {
        'type': 1,
        'id': 1563
    },
    {
        'type': 1,
        'id': 325
    },
    {
        'type': 1,
        'id': 2792
    },
    {
        'type': 1,
        'id': 3978
    },
    {
        'type': 1,
        'id': 180450
    },
    {
        'type': 1,
        'id': 182461
    }
]

DEFAULT_PLATFORM: str = 'SOL'

DEFAULT_CHAIN: str = 'solana'

PLATFORM_LIST: list[str] = [
    'EVM',
    "SOL",
]

CHAIN_DICT: dict[str, dict[str, str]] = {
    "solana": {
        'platform': 'SOL',
        'id': '1399811149',
        'cqt': 'solana-mainnet',
        'ankr': '',
        'gecko': 'solana',
        'dex_tools': 'solana',
        'ave': 'solana',
        'rpc': 'https://solana-rpc.publicnode.com',
        'tx_url': 'https://solscan.io/tx/',
    },
    "ethereum": {
        'platform': 'EVM',
        'id': '1',
        'cqt': 'eth-mainnet',
        'ankr': 'eth',
        'gecko': 'eth',
        'dex_tools': 'ether',
        'ave': 'eth',
        'rpc': 'https://ethereum-rpc.publicnode.com',
        'tx_url': 'https://etherscan.io/tx/',
    },
    "bsc": {
        'platform': 'EVM',
        'id': '56',
        'cqt': 'bsc-mainnet',
        'ankr': 'bsc',
        'gecko': 'bsc',
        'dex_tools': 'bsc',
        'ave': 'bsc',
        'rpc': 'https://bsc-rpc.publicnode.com',
        'tx_url': 'https://bscscan.com/tx/',
    },
    "optimism": {
        'platform': 'EVM',
        'id': '10',
        'cqt': 'optimism-mainnet',
        'ankr': 'optimism',
        'gecko': 'optimism',
        'dex_tools': 'optimism',
        'ave': 'optimism',
        'rpc': 'https://optimism-rpc.publicnode.com',
        'tx_url': 'https://optimistic.etherscan.io/tx/',
    },
    "arbitrum": {
        'platform': 'EVM',
        'id': '42161',
        'cqt': 'arbitrum-mainnet',
        'ankr': 'arbitrum',
        'gecko': 'arbitrum',
        'dex_tools': 'arbitrum',
        'ave': 'arbitrum',
        'rpc': 'https://arbitrum-one-rpc.publicnode.com',
        'tx_url': 'https://arbiscan.io/tx/',
    },
    "base": {
        'platform': 'EVM',
        'id': '8453',
        'cqt': 'base-mainnet',
        'ankr': 'base',
        'gecko': 'base',
        'dex_tools': 'base',
        'ave': 'base',
        'rpc': 'https://base-rpc.publicnode.com',
        'tx_url': 'https://basescan.org/tx/',
    },
    "fantom": {
        'platform': 'EVM',
        'id': '250',
        'cqt': 'fantom-mainnet',
        'ankr': 'fantom',
        'gecko': 'ftm',
        'dex_tools': 'fantom',
        'ave': 'ftm',
        'rpc': 'https://fantom-rpc.publicnode.com',
        'tx_url': 'https://ftmscan.com/tx/',
    },
    "zksync": {
        'platform': 'EVM',
        'id': '324',
        'cqt': 'zksync-mainnet',
        'ankr': '',
        'gecko': 'zksync',
        'dex_tools': 'zksync',
        'ave': 'zksync',
        'rpc': 'https://1rpc.io/zksync2-era',
        'tx_url': 'https://explorer.zksync.io/tx/',
    },
    "linea": {
        'platform': 'EVM',
        'id': '59144',
        'cqt': 'linea-mainnet',
        'ankr': 'linea',
        'gecko': 'linea',
        'dex_tools': 'linea',
        'ave': 'linea',
        'rpc': 'https://1rpc.io/linea',
        'tx_url': 'https://lineascan.build/tx/',
    },
    "blast": {
        'platform': 'EVM',
        'id': '81457',
        'cqt': 'blast-mainnet',
        'ankr': '',
        'gecko': 'blast',
        'dex_tools': 'blast',
        'ave': 'blast',
        'rpc': 'https://rpc.ankr.com/blast',
        'tx_url': 'https://blastexplorer.io/tx/',
    },
    "merlin": {
        'platform': 'EVM',
        'id': '4200',
        'cqt': '',
        'ankr': '',
        'gecko': 'merlin-chain',
        'dex_tools': '',
        'ave': 'merlin',
        'rpc': 'https://rpc.merlinchain.io',
        'tx_url': 'https://scan.merlinchain.io/tx/',
    },
    "bevm": {
        'platform': 'EVM',
        'id': '11501',
        'cqt': '',
        'ankr': '',
        'gecko': 'bevm',
        'dex_tools': '',
        'ave': 'bevm',
        'rpc': 'https://rpc-mainnet-1.bevm.io',
        'tx_url': 'https://scan-mainnet.bevm.io/tx/',
    },
    "scroll": {
        'platform': 'EVM',
        'id': '534352',
        'cqt': 'scroll-mainnet',
        'ankr': 'scroll',
        'gecko': 'scroll',
        'dex_tools': 'scroll',
        'ave': 'scroll',
        'rpc': 'https://rpc.ankr.com/scroll',
        'tx_url': 'https://scrollscan.com/tx/',
    },
}

CQT_CHAIN_DICT: dict[str, str] = {CHAIN_DICT[c]['cqt']:c for c in CHAIN_DICT if CHAIN_DICT[c]['cqt']}
ANKR_CHAIN_DICT: dict[str, str] = {CHAIN_DICT[c]['ankr']:c for c in CHAIN_DICT if CHAIN_DICT[c]['ankr']}
GECKO_CHAIN_DICT: dict[str, str] = {CHAIN_DICT[c]['gecko']:c for c in CHAIN_DICT if CHAIN_DICT[c]['gecko']}
AVE_CHAIN_DICT: dict[str, str] = {CHAIN_DICT[c]['ave']:c for c in CHAIN_DICT if CHAIN_DICT[c]['ave']}

ERC20_ABI: list[dict[str, Any]] = [
    {"inputs": [],"name": "name","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"},
    {"inputs": [],"name": "symbol","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"},
    {'constant': True, 'inputs': [], 'name': 'totalSupply', 'outputs': [{'name': '', 'type': 'uint256'}], 'payable': False, 'type': 'function'},
    {'constant': True, 'inputs': [{'name': '_owner', 'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'name': 'balance', 'type': 'uint256'}], 'payable': False, 'type': 'function'},
    {'constant': True, 'inputs': [{'name': '_owner', 'type': 'address'}, {'name': '_spender', 'type': 'address'}], 'name': 'allowance', 'outputs': [{'name': 'remaining', 'type': 'uint256'}], 'payable': False, 'type': 'function'},
    {'constant': False, 'inputs': [{'name': '_to', 'type': 'address'}, {'name': '_value', 'type': 'uint256'}], 'name': 'transfer', 'outputs': [{'name': 'success', 'type': 'bool'}], 'payable': False, 'type': 'function'},
    {'constant': False, 'inputs': [{'name': '_spender', 'type': 'address'}, {'name': '_value', 'type': 'uint256'}], 'name': 'approve', 'outputs': [{'name': 'success', 'type': 'bool'}], 'payable': False, 'type': 'function'},
    {'constant': False, 'inputs': [{'name': '_from', 'type': 'address'}, {'name': '_to', 'type': 'address'}, {'name': '_value', 'type': 'uint256'}], 'name': 'transferFrom', 'outputs': [{'name': 'success', 'type': 'bool'}], 'payable': False, 'type': 'function'},
    {'anonymous': False, 'inputs': [{'indexed': True, 'name': 'from', 'type': 'address'}, {'indexed': True, 'name': 'to', 'type': 'address'}, {'indexed': False, 'name': 'value', 'type': 'uint256'}], 'name': 'Transfer', 'type': 'event'},
    {'anonymous': False, 'inputs': [{'indexed': True, 'name': 'owner', 'type': 'address'}, {'indexed': True, 'name': 'spender', 'type': 'address'}, {'indexed': False, 'name': 'value', 'type': 'uint256'}], 'name': 'Approval', 'type': 'event'}
]

CROSS_PROVIDERS: list[str] = ['okx', 'jumper']