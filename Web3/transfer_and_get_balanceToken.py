import json
from web3 import Web3
import time

#import your API request, ex "https://eth-mainnet.g.alchemy.com/v2/..." or infura
web3=Web3(Web3.HTTPProvider('yourAPI'))

abi=json.loads('ABIcode')
address_ct='contractAddress'
contract = web3.eth.contract(address = address_ct , abi = abi)


def getBalance(address):

    callBalance = contract.functions.balanceOf(address).call()
    balanceEther = callBalance / 10**18
    return balanceEther


def transfer(from_address, from_privateKey, to_address, amount):

    balance_from=getBalance(from_address)

    if balance_from>=amount:

        #if the gas price is too high, the BOT waits for lower price
        gas = web3.eth.gas_price
        while round(gas/1000000000)>20:
               time.sleep(30)
               gas = web3.eth.gas_price
               print("gas_", str(round(gas/1000000000)))
                    
        #Add 10% to be executed faster
        gas_ = round(gas * 1.1 / 1000000000,4)
        print("gas_",gas_)

        value = web3.toWei(amount 'ether')
        nonce = web3.eth.getTransactionCount(from_address)

        transaction = contract.functions.transfer(to_address, value).buildTransaction({
                 'gas': 300000,
                 'gasPrice': web3.toWei(gas_, 'gwei'),
                 'from': from_address,
                 'nonce': nonce,
        })
        # print(transaction)
        signed_txn = web3.eth.account.signTransaction(transaction, private_key=from_privateKey)
        print(signed_txn)
        tx_json = Web3.toJSON(signed_txn)
        json_obj = json.loads(tx_json)
        hash = json_obj[len(json_obj) - 4]
        print("Transaction hash", hash)
        tx_transaction = web3.eth.sendRawTransaction(signed_txn.rawTransaction)

    else:
        print("insufficient balance")
