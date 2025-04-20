import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# === RPC CONFIG ===
RPC_URL = os.getenv("RPC_URL")  # Your mainnet/testnet RPC endpoint
CHAIN_ID = int(os.getenv("CHAIN_ID", "1"))  # Default to Ethereum Mainnet

# === PRIVATE KEYS / ACCOUNTS ===
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
PUBLIC_ADDRESS = os.getenv("PUBLIC_ADDRESS")

# === CHAINLINK FEEDS ===
CHAINLINK_FEEDS = {
    "ETH": os.getenv("CHAINLINK_ETH_USD"),
    "BTC": os.getenv("CHAINLINK_BTC_USD"),
}

# === GENERAL CONFIG ===
GAS_LIMIT = int(os.getenv("GAS_LIMIT", 300000))
GAS_PRICE_GWEI = int(os.getenv("GAS_PRICE_GWEI", 5))
