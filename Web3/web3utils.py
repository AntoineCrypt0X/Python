import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Load env vars
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_URL = os.getenv("RPC_URL")
CHAIN_ID = int(os.getenv("CHAIN_ID", "137"))  # default: Polygon Mainnet

# Contract addresses from .env
MY_CONTRACT_ADDRESS = Web3.to_checksum_address(os.getenv("MY_CONTRACT_ADDRESS"))

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)


def load_abi(name):
    """
    Load contract ABI from config/abi folder
    """
    with open(f"config/abi/{name}.json") as f:
        return json.load(f)


def get_contract(name, address):
    """
    Return a contract object (by name and address)
    """
    abi = load_abi(name)
    return w3.eth.contract(address=address, abi=abi)


# Contracts
my_contract = get_contract("my_contract_abi", MY_CONTRACT_ADDRESS)

