import Librairy_Kucoin as lb
import time
import random
from kucoin.client import Client
import requests
import base64, hmac, hashlib, json
import uuid

api_key = ""
api_secret = ''
api_passphrase = ''
client = Client(api_key, api_secret, api_passphrase)

#Objective: Check the debt ratio on the isolated margin account every X seconds. If the ratio falls below a threshold, borrow to reposition at a higher debt level threshold.

def Margin_Isolated_Account(symbol):

    url = 'https://api.kucoin.com/api/v3/isolated/accounts'

    now = int(time.time() * 1000)
    str_to_sign = str(now) + 'GET' + '/api/v3/isolated/accounts'
    signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
    passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
    headers = {
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": str(now),
        "KC-API-KEY": api_key,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": "2"
    }
    response = requests.request('get', url, headers=headers)
    final = response.json()
    assets = final["data"]["assets"]
    for pair in assets:
        if pair['symbol']==symbol:
            return pair
    return None

def Post_Borrow_Order(symbol, size):

    url = 'https://api.kucoin.com/api/v3/margin/borrow'

    data = {"isIsolated": True,
            "symbol": symbol,
            "currency": "USDT",
            "size": size,
            "timeInForce": "IOC",
            "isHf": False
            }

    data_json = json.dumps(data)
    now = int(time.time() * 1000)
    str_to_sign = str(now) + 'POST' + '/api/v3/margin/borrow' + data_json

    signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
    passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
    headers = {
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": str(now),
        "KC-API-KEY": api_key,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json"  # specifying content type or using json=data in request
    }
    response = requests.request('post', url, headers=headers, data=data_json)
    print(response.status_code)
    print(response.json())


def extract_data(_json):
    debt = _json['debtRatio']
    liability = _json['quoteAsset']['liability']
    return debt, liability

def place_order(symbol,size):

    url = 'https://api.kucoin.com/api/v1/margin/order'

    data = {
        "clientOid": str(uuid.uuid4()),
        "side": "buy",
        "symbol": symbol,
        "type": "market",
        "size": size,
        "marginModel": "isolated",
        "autoBorrow": False,
    }

    data_json = json.dumps(data)
    now = int(time.time() * 1000)
    str_to_sign = str(now) + 'POST' + '/api/v1/margin/order' + data_json

    signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
    passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())
    headers = {
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": str(now),
        "KC-API-KEY": api_key,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json"  # specifying content type or using json=data in request
    }
    response = requests.request('post', url, headers=headers, data=data_json)
    print(response.status_code)
    print(response.json())

def BOT_margin_isolated(symbol, min_ratio=0.65, target_ratio=0.7, interval=60, roundSize=4):

    while True:
        try:
            info=Margin_Isolated_Account(symbol)
            debt, liability = extract_data(info)
            debt=float(debt)
            liability=round(float(liability),2)

            if debt < min_ratio:
                    total_asset = liability / debt
                    amount_to_borrow = ((target_ratio*total_asset)-liability)/(1-target_ratio)
                    amount_to_borrow=round(amount_to_borrow)

                    print(f"Ratio Liability {debt}. Total asset {round(total_asset,2)}, liability {liability}. Borrow {amount_to_borrow} USDT")
                    Post_Borrow_Order(symbol,amount_to_borrow)
                    time.sleep(3)
                    quantity_token=round(amount_to_borrow/lb.get_mid_Price(symbol,4),roundSize)
                    place_order(symbol,quantity_token)

        except Exception as e:
            print(f"Error : {e}")

        time.sleep(interval)

if __name__ == "__main__":
    BOT_margin_isolated('CRO-USDT', 0.55, 0.7, 4)


