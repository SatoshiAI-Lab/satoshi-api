from typing import Any
import os


PLATFORM_LIST: list[str] = [
    "EVM",
    "SOL",
]

CHAIN_DICT: dict[str, dict[str, str]] = {
    "ethereum": {
        "platform": "EVM",
        "id": "1",
        "cqt": "eth-mainnet",
        "ankr": "eth",
        "gecko": "eth",
        "dex_tools": "ether",
        "ave": "eth",
        "rpc": "https://ethereum-rpc.publicnode.com",
        "tx_url": "https://etherscan.io/tx/",
        "token": {
            "symbol": "ETH",
            "name": "Ether",
            "decimals": 18,
            "address": "0x0000000000000000000000000000000000000000",
            "logo": f"{os.getenv(key='S3_DOMAIN')}/tokens/logo/ethereum/0x0000000000000000000000000000000000000000.png",
        },
    },
    "bsc": {
        "platform": "EVM",
        "id": "56",
        "cqt": "bsc-mainnet",
        "ankr": "bsc",
        "gecko": "bsc",
        "dex_tools": "bsc",
        "ave": "bsc",
        "rpc": "https://bsc-rpc.publicnode.com",
        "tx_url": "https://bscscan.com/tx/",
        "token": {
            "symbol": "BNB",
            "name": "Binance Coin",
            "decimals": 18,
            "address": "0x0000000000000000000000000000000000000000",
            "logo": f"{os.getenv(key='S3_DOMAIN')}/tokens/logo/bsc/0x0000000000000000000000000000000000000000.png",
        },
    },
    "solana": {
        "platform": "SOL",
        "id": "1399811149",
        "cqt": "solana-mainnet",
        "ankr": "",
        "gecko": "solana",
        "dex_tools": "solana",
        "ave": "solana",
        "rpc": "https://solana-rpc.publicnode.com",
        "tx_url": "https://solscan.io/tx/",
        "token": {
            "symbol": "SOL",
            "name": "Solana",
            "decimals": 9,
            "address": "0x0000000000000000000000000000000000000000",
            "logo": f"{os.getenv(key='S3_DOMAIN')}/tokens/logo/solana/0x0000000000000000000000000000000000000000.png",
        },
    },
    "optimism": {
        "platform": "EVM",
        "id": "10",
        "cqt": "optimism-mainnet",
        "ankr": "optimism",
        "gecko": "optimism",
        "dex_tools": "optimism",
        "ave": "optimism",
        "rpc": "https://optimism-rpc.publicnode.com",
        "tx_url": "https://optimistic.etherscan.io/tx/",
        "token": {
            "symbol": "ETH",
            "name": "Ether",
            "decimals": 18,
            "address": "0x0000000000000000000000000000000000000000",
            "logo": f"{os.getenv(key='S3_DOMAIN')}/tokens/logo/optimism/0x0000000000000000000000000000000000000000.png",
        },
    },
    "arbitrum": {
        "platform": "EVM",
        "id": "42161",
        "cqt": "arbitrum-mainnet",
        "ankr": "arbitrum",
        "gecko": "arbitrum",
        "dex_tools": "arbitrum",
        "ave": "arbitrum",
        "rpc": "https://arbitrum-one-rpc.publicnode.com",
        "tx_url": "https://arbiscan.io/tx/",
        "token": {
            "symbol": "ETH",
            "name": "Arbitrum Mainnet Ether",
            "decimals": 18,
            "address": "0x0000000000000000000000000000000000000000",
            "logo": f"{os.getenv(key='S3_DOMAIN')}/tokens/logo/arbitrum/0x0000000000000000000000000000000000000000.png",
        },
    },
    "base": {
        "platform": "EVM",
        "id": "8453",
        "cqt": "base-mainnet",
        "ankr": "base",
        "gecko": "base",
        "dex_tools": "base",
        "ave": "base",
        "rpc": "https://base-rpc.publicnode.com",
        "tx_url": "https://basescan.org/tx/",
        "token": {
            "symbol": "ETH",
            "name": "Ether",
            "decimals": 18,
            "address": "0x0000000000000000000000000000000000000000",
            "logo": f"{os.getenv(key='S3_DOMAIN')}/tokens/logo/base/0x0000000000000000000000000000000000000000.png",
        },
    },
    "fantom": {
        "platform": "EVM",
        "id": "250",
        "cqt": "fantom-mainnet",
        "ankr": "fantom",
        "gecko": "ftm",
        "dex_tools": "fantom",
        "ave": "ftm",
        "rpc": "https://fantom-rpc.publicnode.com",
        "tx_url": "https://ftmscan.com/tx/",
        "token": {
            "symbol": "FTM",
            "name": "Fantom",
            "decimals": 18,
            "address": "0x0000000000000000000000000000000000000000",
            "logo": f"{os.getenv(key='S3_DOMAIN')}/tokens/logo/fantom/0x0000000000000000000000000000000000000000.png",
        },
    },
    "zksync": {
        "platform": "EVM",
        "id": "324",
        "cqt": "zksync-mainnet",
        "ankr": "",
        "gecko": "zksync",
        "dex_tools": "zksync",
        "ave": "zksync",
        "rpc": "https://1rpc.io/zksync2-era",
        "tx_url": "https://explorer.zksync.io/tx/",
        "token": {
            "symbol": "ETH",
            "name": "Ether",
            "decimals": 18,
            "address": "0x0000000000000000000000000000000000000000",
            "logo": f"{os.getenv(key='S3_DOMAIN')}/tokens/logo/zksync/0x0000000000000000000000000000000000000000.png",
        },
    },
    "linea": {
        "platform": "EVM",
        "id": "59144",
        "cqt": "linea-mainnet",
        "ankr": "linea",
        "gecko": "linea",
        "dex_tools": "linea",
        "ave": "linea",
        "rpc": "https://1rpc.io/linea",
        "tx_url": "https://lineascan.build/tx/",
        "token": {
            "symbol": "ETH",
            "name": "ETH",
            "decimals": 18,
            "address": "0x0000000000000000000000000000000000000000",
            "logo": f"{os.getenv(key='S3_DOMAIN')}/tokens/logo/linea/0x0000000000000000000000000000000000000000.png",
        },
    },
    "blast": {
        "platform": "EVM",
        "id": "81457",
        "cqt": "blast-mainnet",
        "ankr": "",
        "gecko": "blast",
        "dex_tools": "blast",
        "ave": "blast",
        "rpc": "https://rpc.ankr.com/blast",
        "tx_url": "https://blastexplorer.io/tx/",
        "token": {
            "symbol": "ETH",
            "name": "Ether",
            "decimals": 18,
            "address": "0x0000000000000000000000000000000000000000",
            "logo": f"{os.getenv(key='S3_DOMAIN')}/tokens/logo/blast/0x0000000000000000000000000000000000000000.png",
        },
    },
    "merlin": {
        "platform": "EVM",
        "id": "4200",
        "cqt": "",
        "ankr": "",
        "gecko": "merlin-chain",
        "dex_tools": "",
        "ave": "merlin",
        "rpc": "https://rpc.merlinchain.io",
        "tx_url": "https://scan.merlinchain.io/tx/",
        "token": {
            "symbol": "BTC",
            "name": "Bitcoin",
            "decimals": 8,
            "address": "0x0000000000000000000000000000000000000000",
            "logo": f"{os.getenv(key='S3_DOMAIN')}/tokens/logo/merlin/0x0000000000000000000000000000000000000000.png",
        },
    },
    "bevm": {
        "platform": "EVM",
        "id": "11501",
        "cqt": "",
        "ankr": "",
        "gecko": "bevm",
        "dex_tools": "",
        "ave": "bevm",
        "rpc": "https://rpc-mainnet-1.bevm.io",
        "tx_url": "https://scan-mainnet.bevm.io/tx/",
                "token": {
            "symbol": "BTC",
            "name": "Bitcoin",
            "decimals": 8,
            "address": "0x0000000000000000000000000000000000000000",
            "logo": f"{os.getenv(key='S3_DOMAIN')}/tokens/logo/bevm/0x0000000000000000000000000000000000000000.png",
        },
    },
    "scroll": {
        "platform": "EVM",
        "id": "534352",
        "cqt": "scroll-mainnet",
        "ankr": "scroll",
        "gecko": "scroll",
        "dex_tools": "scroll",
        "ave": "scroll",
        "rpc": "https://rpc.ankr.com/scroll",
        "tx_url": "https://scrollscan.com/tx/",
        "token": {
            "symbol": "ETH",
            "name": "Ether",
            "decimals": 18,
            "address": "0x0000000000000000000000000000000000000000",
            "logo": f"{os.getenv(key='S3_DOMAIN')}/tokens/logo/scroll/0x0000000000000000000000000000000000000000.png",
        },
    },
}

CHAIN_DICT_FROM_ID: dict[str, str] = {CHAIN_DICT[c]["id"]:c for c in CHAIN_DICT}
CQT_CHAIN_DICT: dict[str, str] = {CHAIN_DICT[c]["cqt"]:c for c in CHAIN_DICT if CHAIN_DICT[c]["cqt"]}
ANKR_CHAIN_DICT: dict[str, str] = {CHAIN_DICT[c]["ankr"]:c for c in CHAIN_DICT if CHAIN_DICT[c]["ankr"]}
GECKO_CHAIN_DICT: dict[str, str] = {CHAIN_DICT[c]["gecko"]:c for c in CHAIN_DICT if CHAIN_DICT[c]["gecko"]}
AVE_CHAIN_DICT: dict[str, str] = {CHAIN_DICT[c]["ave"]:c for c in CHAIN_DICT if CHAIN_DICT[c]["ave"]}

DEFAULT_PLATFORM: str = "EVM"
DEFAULT_CHAIN: str = "bsc"

ZERO_ADDRESS: str = "0x0000000000000000000000000000000000000000"
SOL_ADDRESS: str = "So11111111111111111111111111111111111111112"

MESSAGE_TYPE_DICT: dict[int, str] = {
    0: "news",
    1: "twitter",
    2: "announcement",
    3: "trade",
    4: "pool"
}

DEFAULT_IDS: list[dict[str, int]] = [
    {
        "type": 1,
        "id": 1
    },
    {
        "type": 1,
        "id": 141
    },
    {
        "type": 1,
        "id": 1563
    },
    {
        "type": 1,
        "id": 325
    },
    {
        "type": 1,
        "id": 2792
    },
    {
        "type": 1,
        "id": 3978
    },
    {
        "type": 1,
        "id": 180450
    },
    {
        "type": 1,
        "id": 182461
    }
]

ERC20_ABI: list[dict[str, Any]] = [
    {"inputs": [],"name": "name","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"},
    {"inputs": [],"name": "symbol","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "payable": False, "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "payable": False, "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "remaining", "type": "uint256"}], "payable": False, "type": "function"},
    {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "success", "type": "bool"}], "payable": False, "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "success", "type": "bool"}], "payable": False, "type": "function"},
    {"constant": False, "inputs": [{"name": "_from", "type": "address"}, {"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transferFrom", "outputs": [{"name": "success", "type": "bool"}], "payable": False, "type": "function"},
    {"anonymous": False, "inputs": [{"indexed": True, "name": "from", "type": "address"}, {"indexed": True, "name": "to", "type": "address"}, {"indexed": False, "name": "value", "type": "uint256"}], "name": "Transfer", "type": "event"},
    {"anonymous": False, "inputs": [{"indexed": True, "name": "owner", "type": "address"}, {"indexed": True, "name": "spender", "type": "address"}, {"indexed": False, "name": "value", "type": "uint256"}], "name": "Approval", "type": "event"}
]

CROSS_PROVIDERS: list[str] = ["okx", "jumper"]