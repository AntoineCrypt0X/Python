from web3 import Web3
from web3utils import load_abi
from config import MY_CONTRACT_ADDRESS
from utils.web3utils import get_web3
from utils.wallet import get_wallet
import json


class ContractInterface:
    """
    Provides an interface to interact with deployed smart contracts.
    Handles loading ABIs, contract instances, and calling read/write functions.
    """

    def __init__(self, contract_address, abi_name):
        self.web3 = get_web3()
        self.account = get_wallet(self.web3)
        self.contract_address = contract_address
        self.abi_name = abi_name

        # Load and bind contract instances
        self.my_contract = self._load_contract(self.contract_address, self.abi_name)

    def _load_contract(self, contract_address: str, abi_name: str):
        abi = load_abi(abi_name)
        return self.web3.eth.contract(address=contract_address, abi = abi)

    def call_read_function(self, contract, function_name: str, *args):
        """
        Calls a read-only function on the contract.
        Returns the result.
        """
        return getattr(contract.functions, function_name)(*args).call()

    def send_transaction(self, contract, function_name: str, *args):
        """
        Sends a transaction to modify contract state.
        Signs with local wallet.
        """
        nonce = self.web3.eth.get_transaction_count(self.account.address)
        gas_price = self.web3.eth.gas_price

        tx = getattr(contract.functions, function_name)(*args).build_transaction({
            'from': self.account.address,
            'nonce': nonce,
            'gasPrice': gas_price,
        })

        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return self.web3.to_hex(tx_hash)


# Example usage
if __name__ == "__main__":
    ci = ContractInterface(MY_CONTRACT_ADDRESS, "my_contract_abi")
    fund_owner = ci.call_read_function(ci.my_contract, "owner")
    print(f"Fund owner: {fund_owner}")