import time
from web3 import Web3
import json
from openpyxl import load_workbook
import csv

#import your API request, ex "https://eth-mainnet.g.alchemy.com/v2/" or infura
web3=Web3(Web3.HTTPProvider('yourAPI'))

abiToken=json.loads('[{"inputs":[{"internalType":"address","name":"_airdropToken","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"previousOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"inputs":[],"name":"renounceOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"return_To_Owner","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address[]","name":"listAdress","type":"address[]"},{"internalType":"uint256","name":"_amount","type":"uint256"}],"name":"Send_Token_from_List","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"_owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"airdropToken","outputs":[{"internalType":"contract IERC20","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]')
address_ct_Token='contractAddress'
contract_Token = web3.eth.contract(address = address_ct_Token , abi = abiToken)

wallet_airdrop='walletAddressOwner'
private_key_airdrop = 'walletprivateKey'

#Automate airdrop of 1 token to a list of address in an Excel file, 100 by 100 with the function Send_Token_from_List. Check the smart contract in the Github-Solidity section
def airdrop():
    chemin = 'yourCSVpath.csv'

    list_address = []
    List_list_address = []
    with open(chemin, 'r', encoding='UTF8') as f:
        csv_reader = csv.reader(f)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Headers are {", ".join(row)}')
                line_count += 1
            else:
                #check if it's an ethereum address
                if web3.isAddress(row[0]):
                    #Create a list of list of 100 addresses
                    if len(list_address) == 100:
                        List_list_address.append(list_address)
                        list_address = []
                    #Write the address in the correct format (Upper and lower case)
                    list_address.append(Web3.toChecksumAddress(row[0]))
        List_list_address.append(list_address)
        print("Number airdrop function call: ", len(List_list_address))

        if List_list_address[0]:
            for i in range(0, len(List_list_address)):
                try:
                    #if the gas price is too high, the BOT waits for lower price
                    gas = web3.eth.gas_price
                    while round(gas/1000000000)>20:
                        time.sleep(30)
                        gas = web3.eth.gas_price
                        print("gas_", str(round(gas/1000000000)))
                    
                     #Add 10% to be executed faster
                    gas_ = round(gas * 1.1 / 1000000000,4)
                    print("gas_",gas_)
                    input_address = List_list_address[i]

                    nonce = web3.eth.getTransactionCount(wallet_airdrop)
                    transaction = contract_Token.functions.Send_Token_from_List(input_address,10000000000000000000).buildTransaction({
                        'gas': 5000000, #set the quantity of gas
                        'gasPrice': web3.toWei(gas_, 'gwei'),
                        'from': wallet_airdrop,
                        'nonce': nonce,
                    })
                    #print(transaction)
                    signed_txn = web3.eth.account.signTransaction(transaction, private_key=private_key_airdrop)
                    #print(signed_txn)
                    tx_json = Web3.toJSON(signed_txn)
                    json_obj = json.loads(tx_json)
                    #print(json_obj)
                    print("hash",json_obj[len(json_obj)-4])
                    tx_transaction = web3.eth.sendRawTransaction(signed_txn.rawTransaction)
                    print(str(i),"airdrop ok")

                except Exception as e1:
                    print('error1', e1)
                    print(str(i),"error")
                else:
                    a = 1

                time.sleep(60)

airdrop()
