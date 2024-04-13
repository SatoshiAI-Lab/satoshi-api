
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
        'cqt': 'solana-mainnet',
        'gecko': 'solana',
        'dex_tools': 'solana',
        'rpc': '',
    },
    "Ethereum": {
        'platform': 'EVM',
        'cqt': 'eth-mainnet',
        'gecko': 'eth',
        'dex_tools': 'ether',
        'rpc': 'https://ethereum-rpc.publicnode.com',
    },
    "BSC": {
        'platform': 'EVM',
        'cqt': 'bsc-mainnet',
        'gecko': 'bsc',
        'dex_tools': 'bsc',
        'rpc': '',
    },
    "Optimism": {
        'platform': 'EVM',
        'cqt': 'optimism-mainnet',
        'gecko': 'optimism',
        'dex_tools': 'optimism',
        'rpc': 'https://optimism-rpc.publicnode.com',
    },
    "Arbitrum": {
        'platform': 'EVM',
        'cqt': 'arbitrum-mainnet',
        'gecko': 'arbitrum',
        'dex_tools': 'arbitrum',
        'rpc': '',
    },
    "Base": {
        'platform': 'EVM',
        'cqt': 'base-mainnet',
        'gecko': 'base',
        'dex_tools': 'base',
        'rpc': '',
    }
}

CQT_CHAIN_DICT = {CHAIN_DICT[c]['cqt']:c for c in CHAIN_DICT}

ERC20_ABI = [
    {'constant': True, 'inputs': [], 'name': 'totalSupply', 'outputs': [{'name': '', 'type': 'uint256'}], 'payable': False, 'type': 'function'},
    {'constant': True, 'inputs': [{'name': '_owner', 'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'name': 'balance', 'type': 'uint256'}], 'payable': False, 'type': 'function'},
    {'constant': True, 'inputs': [{'name': '_owner', 'type': 'address'}, {'name': '_spender', 'type': 'address'}], 'name': 'allowance', 'outputs': [{'name': 'remaining', 'type': 'uint256'}], 'payable': False, 'type': 'function'},
    {'constant': False, 'inputs': [{'name': '_to', 'type': 'address'}, {'name': '_value', 'type': 'uint256'}], 'name': 'transfer', 'outputs': [{'name': 'success', 'type': 'bool'}], 'payable': False, 'type': 'function'},
    {'constant': False, 'inputs': [{'name': '_spender', 'type': 'address'}, {'name': '_value', 'type': 'uint256'}], 'name': 'approve', 'outputs': [{'name': 'success', 'type': 'bool'}], 'payable': False, 'type': 'function'},
    {'constant': False, 'inputs': [{'name': '_from', 'type': 'address'}, {'name': '_to', 'type': 'address'}, {'name': '_value', 'type': 'uint256'}], 'name': 'transferFrom', 'outputs': [{'name': 'success', 'type': 'bool'}], 'payable': False, 'type': 'function'},
    {'anonymous': False, 'inputs': [{'indexed': True, 'name': 'from', 'type': 'address'}, {'indexed': True, 'name': 'to', 'type': 'address'}, {'indexed': False, 'name': 'value', 'type': 'uint256'}], 'name': 'Transfer', 'type': 'event'},
    {'anonymous': False, 'inputs': [{'indexed': True, 'name': 'owner', 'type': 'address'}, {'indexed': True, 'name': 'spender', 'type': 'address'}, {'indexed': False, 'name': 'value', 'type': 'uint256'}], 'name': 'Approval', 'type': 'event'}
]