import random
from web3 import Web3

#import your API request, ex "https://eth-mainnet.g.alchemy.com/v2/" or infura
web3=Web3(Web3.HTTPProvider('yourAPI'))

def getbalanceETH(wallet_):
    balance_wei = web3.eth.get_balance(wallet_)

    # Convertir la balance de wei à ether
    balance_eth = web3.fromWei(balance_wei, 'ether')

    print(f'Balance : {round(balance_eth,5)} ETH')
    return balance_eth

def getCurrentGasPrice():

    gas = web3.eth.gas_price
    print("gas_", gas_)
    return gas

