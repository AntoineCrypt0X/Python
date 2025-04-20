from eth_account import Account
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware
import logging

from config import PRIVATE_KEY, PUBLIC_ADDRESS, RPC_URL, GAS_PRICE_GWEI

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    raise ConnectionError("Web3 RPC is not connected")

# Load account from private key
account = Account.from_key(PRIVATE_KEY)
assert account.address.lower() == PUBLIC_ADDRESS.lower(), "Address mismatch"

# Attach middleware for signing
w3.middleware_onion.add(construct_sign_and_send_raw_middleware(account))
w3.eth.default_account = account.address

logger.info(f"Wallet loaded: {account.address}")


def build_tx(contract_function, value=0):
    """ Prepares a transaction dictionary to be sent.
    """
    tx = contract_function.build_transaction({
        'from': account.address,
        'value': value,
        'gas': 300000,  # Can be overridden
        'gasPrice': w3.to_wei(GAS_PRICE_GWEI, 'gwei'),
        'nonce': w3.eth.get_transaction_count(account.address),
        'chainId': w3.eth.chain_id
    })
    return tx


def send_tx(tx):
    """Signs and sends a raw transaction.
    """
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    logger.info(f"Transaction sent: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    logger.info(f"Tx mined in block {receipt.blockNumber}, status: {receipt.status}")
    return receipt
