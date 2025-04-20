from dotenv import load_dotenv
import os
from web3 import Web3

# Load environment variables
load_dotenv()

# Web3 instance setup
RPC_URL = os.getenv("RPC_URL")
w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    raise ConnectionError("Unable to connect to Web3 RPC")

# Chainlink feeds (can be extended in .env)
CHAINLINK_FEEDS = {
    "ETH/USD": os.getenv("CHAINLINK_ETH_USD"),
    "BTC/USD": os.getenv("CHAINLINK_BTC_USD"),
}

# ABI for Chainlink AggregatorV3Interface
CHAINLINK_ABI = [
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {"internalType": "uint80", "name": "roundId", "type": "uint80"},
            {"internalType": "int256", "name": "answer", "type": "int256"},
            {"internalType": "uint256", "name": "startedAt", "type": "uint256"},
            {"internalType": "uint256", "name": "updatedAt", "type": "uint256"},
            {"internalType": "uint80", "name": "answeredInRound", "type": "uint80"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
]

def get_latest_price(symbol: str) -> float:
    """
    Fetch the latest USD price for a given asset using Chainlink feeds.
    """
    feed_address = CHAINLINK_FEEDS.get(symbol)
    if not feed_address:
        raise ValueError(f"No Chainlink feed found for symbol: {symbol}")

    aggregator = w3.eth.contract(address=feed_address, abi=CHAINLINK_ABI)
    _, answer, _, _, _ = aggregator.functions.latestRoundData().call()

    return float(answer) / 1e8  # Chainlink answers use 8 decimals

if __name__ == "__main__":
    print("ETH/USD:", get_latest_price("ETH/USD"))
