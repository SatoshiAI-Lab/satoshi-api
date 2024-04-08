
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
    },
    "Ethereum": {
        'platform': 'EVM',
        'cqt': 'eth-mainnet',
        'gecko': 'eth',
        'dex_tools': 'ether',
    },
    "BSC": {
        'platform': 'EVM',
        'cqt': 'bsc-mainnet',
        'gecko': 'bsc',
        'dex_tools': 'bsc',
    },
    "Optimism": {
        'platform': 'EVM',
        'cqt': 'optimism-mainnet',
        'gecko': 'optimism',
        'dex_tools': 'optimism',
    },
    "Arbitrum": {
        'platform': 'EVM',
        'cqt': 'arbitrum-mainnet',
        'gecko': 'arbitrum',
        'dex_tools': 'arbitrum',
    },
    "Base": {
        'platform': 'EVM',
        'cqt': 'base-mainnet',
        'gecko': 'base',
        'dex_tools': 'base',
    }
}

CQT_CHAIN_DICT = {CHAIN_DICT[c]['cqt']:c for c in CHAIN_DICT}