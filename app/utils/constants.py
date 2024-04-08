
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

CHAIN_DICT = {
    "SOL": {
        'cqt': 'solana-mainnet',
        'gecko': 'solana',
        'dex_tools': 'solana',
    },
    "ETH": {
        'cqt': 'eth-mainnet',
        'gecko': 'eth',
        'dex_tools': 'ether',
    },
    "BSC": {
        'cqt': 'bsc-mainnet',
        'gecko': 'bsc',
        'dex_tools': 'bsc',
    },
    "OP": {
        'cqt': 'optimism-mainnet',
        'gecko': 'optimism',
        'dex_tools': 'optimism',
    },
    "ARB": {
        'cqt': 'arbitrum-mainnet',
        'gecko': 'arbitrum',
        'dex_tools': 'arbitrum',
    },
    "BASE": {
        'cqt': 'base-mainnet',
        'gecko': 'base',
        'dex_tools': 'base',
    }
}
