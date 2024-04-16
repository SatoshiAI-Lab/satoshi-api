
MESSAGE_TYPE_DICT = {
    0: 'news',
    1: "twitter",
    2: "announcement",
    3: "trade",
    4: "pool"
}

DEFAULT_IDS = [
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

DEFAULT_PLATFORM = 'SOL'

DEFAULT_CHAIN = 'Solana'

PLATFORM_LIST = [
    'EVM',
    "SOL",
]

CHAIN_DICT = {
    "Solana": {
        'platform': 'SOL',
        'id': '',
        'cqt': 'solana-mainnet',
        'gecko': 'solana',
        'dex_tools': 'solana',
        'rpc': 'https://api.mainnet-beta.solana.com',
        'tx_url': 'https://solscan.io/tx/',
    },
    "Ethereum": {
        'platform': 'EVM',
        'id': '1',
        'cqt': 'eth-mainnet',
        'gecko': 'eth',
        'dex_tools': 'ether',
        'rpc': 'https://ethereum-rpc.publicnode.com',
        'tx_url': 'https://etherscan.io/tx/',
    },
    "BSC": {
        'platform': 'EVM',
        'id': '56',
        'cqt': 'bsc-mainnet',
        'gecko': 'bsc',
        'dex_tools': 'bsc',
        'rpc': 'https://bsc-rpc.publicnode.com',
        'tx_url': 'https://bscscan.com/tx/',
    },
    "Optimism": {
        'platform': 'EVM',
        'id': '10',
        'cqt': 'optimism-mainnet',
        'gecko': 'optimism',
        'dex_tools': 'optimism',
        'rpc': 'https://optimism-rpc.publicnode.com',
        'tx_url': 'https://optimistic.etherscan.io/tx/',
    },
    "Arbitrum": {
        'platform': 'EVM',
        'id': '42161',
        'cqt': 'arbitrum-mainnet',
        'gecko': 'arbitrum',
        'dex_tools': 'arbitrum',
        'rpc': 'https://arbitrum-one-rpc.publicnode.com',
        'tx_url': 'https://arbiscan.io/tx/',
    },
    "Base": {
        'platform': 'EVM',
        'id': '8453',
        'cqt': 'base-mainnet',
        'gecko': 'base',
        'dex_tools': 'base',
        'rpc': 'https://base-rpc.publicnode.com',
        'tx_url': 'https://basescan.org/tx/',
    },
    "Fantom": {
        'platform': 'EVM',
        'id': '250',
        'cqt': 'fantom-mainnet',
        'gecko': 'ftm',
        'dex_tools': 'fantom',
        'rpc': 'https://fantom-rpc.publicnode.com',
        'tx_url': 'https://ftmscan.com/tx/',
    },
    "zkSync": {
        'platform': 'ZK',
        'id': '324',
        'cqt': 'zksync-mainnet',
        'gecko': 'zksync',
        'dex_tools': 'zksync',
        'rpc': 'https://1rpc.io/zksync2-era',
        'tx_url': 'https://explorer.zksync.io/tx/',
    },
    "Linea": {
        'platform': 'Linea',
        'id': '59144',
        'cqt': 'linea-mainnet',
        'gecko': 'linea',
        'dex_tools': 'linea',
        'rpc': 'https://1rpc.io/linea',
        'tx_url': 'https://lineascan.build/tx/',
    },
    "Blast": {
        'platform': 'Blast',
        'id': '81457',
        'cqt': 'blast-mainnet',
        'gecko': 'blast',
        'dex_tools': 'blast',
        'rpc': 'https://rpc.ankr.com/blast',
        'tx_url': 'https://blastexplorer.io/tx/',
    },
}

CQT_CHAIN_DICT = {CHAIN_DICT[c]['cqt']:c for c in CHAIN_DICT}

ERC20_ABI = [
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