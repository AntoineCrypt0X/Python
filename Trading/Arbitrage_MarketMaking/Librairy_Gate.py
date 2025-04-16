from kucoin.client import Client
import time, hashlib, hmac, requests, json
from gate_api import ApiClient, Configuration, Order, SpotApi

keyG = ""
secretG = ''


def gen_sign(method, url, query_string=None, payload_string=None):
    key = keyG
    secret = secretG

    t = time.time()
    m = hashlib.sha512()
    m.update((payload_string or "").encode('utf-8'))
    hashed_payload = m.hexdigest()
    s = '%s\n%s\n%s\n%s\n%s' % (method, url, query_string or "", hashed_payload, t)
    sign = hmac.new(secret.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
    return {'KEY': key, 'Timestamp': str(t), 'SIGN': sign}

def balance(currency, bool_available=False, bool_print=False):
    config = Configuration(key=keyG,secret=secretG, host="https://api.gateio.ws/api/v4")
    spot_api = SpotApi(ApiClient(config))
    balance = spot_api.list_spot_accounts()
    for e in range(len(balance)):
        if balance[e].currency == currency:
            if bool_print:
                print("balance Gate " + currency + " " + balance[e].available)
            return float(balance[e].available)

def orderLimit(currencypair, side, price, size):
    config = Configuration(key=keyG,secret=secretG, host="https://api.gateio.ws/api/v4")
    spot_api = SpotApi(ApiClient(config))

    order=Order(currency_pair=currencypair, side=side, price=price, amount=size)
    create=spot_api.create_order(order)
    print("orderId Gate: " + create.id)
    return create.id

def orderMarket(pair, side, amount):

    host = "https://api.gateio.ws"
    prefix = "/api/v4"
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    url = '/spot/orders'
    query_param = ''
    body = {
        "text": "t-abc123",
        "currency_pair": pair,
        "type": "market", 
        "side": side,
        "amount": amount,
        "time_in_force": "ioc",
    }
    body=json.dumps(body)
    sign_headers = gen_sign('POST', prefix + url, query_param, body)
    headers.update(sign_headers)
    r = requests.request('POST', host + prefix + url, headers=headers, data=body)
    print(r.json()['id'])
    return r.json()['id']

def cancel_order_limit(orderId, pair):
    try:
        config = Configuration(key=keyG,secret=secretG, host="https://api.gateio.ws/api/v4")
        spot_api = SpotApi(ApiClient(config))
        cancel = spot_api.cancel_order(order_id=orderId, currency_pair=pair)
        print(f"Order {orderId} cancelled.")
        return cancel
    except Exception as e:
        print(f"Error for cancelling order {orderId} : {e}")
        return None
    
def cancel_order_limit_Batch(list_ordersID, pair):
    for order in list_ordersID:
        try:
            config = Configuration(key=keyG,secret=secretG, host="https://api.gateio.ws/api/v4")
            spot_api = SpotApi(ApiClient(config))
            spot_api.cancel_order(order_id=order, currency_pair=pair)
            print(f"Order {order} cancelled.")

        except Exception as e:
            print(f"Error for cancelling order {order} : {e}")
    
def get_active_orders(pair):
    config = Configuration(key=keyG,secret=secretG, host="https://api.gateio.ws/api/v4")
    spot_api = SpotApi(ApiClient(config))
    list=spot_api.list_orders(currency_pair=pair, status="open")
    return list

def get_active_orders_ID(pair, bool_print=False): #Array of IDs
    Id_list=[]
    try:
        config = Configuration(key=keyG,secret=secretG, host="https://api.gateio.ws/api/v4")
        spot_api = SpotApi(ApiClient(config))
        list=spot_api.list_orders(currency_pair=pair, status="open")
        for e in list:
            Id_list.append(e.id)
        if bool_print:
            print(Id_list) 
        return Id_list
    except Exception as e:
        print(f"Error to get active orders Id: {e}")
        return None

def get_order_details(currency, orderId, bool_print=False):
    config = Configuration(key=keyG,secret=secretG, host="https://api.gateio.ws/api/v4")
    spot_api = SpotApi(ApiClient(config))
    order = spot_api.get_order_with_http_info(currency_pair=currency, order_id=orderId)
    if bool_print:
        print(order)
    return order[0]

def get_order_quantity_left(currency, orderId, bool_print=False):
    config = Configuration(key=keyG,secret=secretG, host="https://api.gateio.ws/api/v4")
    spot_api = SpotApi(ApiClient(config))
    order = spot_api.get_order_with_http_info(currency_pair=currency, order_id=orderId)
    if bool_print:
        print(f"Size left for {orderId}, {order[0].left}")
    return order[0].left

def get_order_quantity_filled(currency, orderId, bool_print=False):
    config = Configuration(key=keyG,secret=secretG, host="https://api.gateio.ws/api/v4")
    spot_api = SpotApi(ApiClient(config))
    order = spot_api.get_order_with_http_info(currency_pair=currency, order_id=orderId)
    if bool_print:
        print(f"Size left for {orderId}, {order[0].amount}")
    return order[0].amount

def get_order_filled_price(currency, orderId):
    config = Configuration(key=keyG,secret=secretG, host="https://api.gateio.ws/api/v4")
    spot_api = SpotApi(ApiClient(config))
    order = spot_api.get_order_with_http_info(currency_pair=currency, order_id=orderId)
    return order[0].price

def get_order_dollar_filled(currency, orderId):
    config = Configuration(key=keyG,secret=secretG, host="https://api.gateio.ws/api/v4")
    spot_api = SpotApi(ApiClient(config))
    order = spot_api.get_order_with_http_info(currency_pair=currency, order_id=orderId)
    return order[0].filled_total

def getOrderBook(ticker, bool_print=False):

    host = "https://data.gateapi.io"
    prefix = ""
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    url = '/api2/1/orderBook/' + ticker

    query_param = ''
    # for `gen_sign` implementation, refer to section `Authentication` above
    sign_headers = gen_sign('GET', prefix + url, query_param)
    headers.update(sign_headers)
    r = requests.request('GET', host + prefix + url + "?" + query_param, headers=headers)
    if bool_print:
       print(r.json())
    return r.json()

#example: price impact if we sell for 500 USDT
def priceImpactSell(ticker, amount, bool_print=False):
    book = getOrderBook(ticker)
    bids_book=book["bids"]
    sommeCoins=0
    sommetotaldollar=0
    index=0
    while sommetotaldollar<amount:
        ligne=bids_book[index]
        price=ligne[0]
        size=ligne[1]
        sommeCoins = sommeCoins + min((amount - sommetotaldollar) / float(price), float(size))
        sommetotaldollar=sommetotaldollar+(float(price)*float(size))
        index=index+1
    if bool_print:
        print(f"Bid impact for selling {amount} USDT: {bids_book[index-1][0]} vs current bid {bids_book[0][0]}, need {str(sommeCoins)} tokens")
    return bids_book[index-1][0], sommeCoins

#example: price impact if we buy for 500 USDT
def priceImpactBuy(ticker, amount, bool_print=False):

    book = getOrderBook(ticker)
    asks_book = book["asks"]
    # Reverse the array
    asks_book = asks_book[len(asks_book) - 1::-1]

    sommeCoins=0
    sommetotaldollar=0
    index=0
    while sommetotaldollar<amount:
        ligne=asks_book[index]
        price=ligne[0]
        size=ligne[1]
        sommeCoins = sommeCoins + min((amount - sommetotaldollar) / float(price), float(size))
        sommetotaldollar=sommetotaldollar+(float(price)*float(size))
        index=index+1
    if bool_print:
        print(f"Ask impact for selling {amount} USDT: {asks_book[index-1][0]} vs current ask {asks_book[0][0]}, get {str(sommeCoins)} tokens")
    return asks_book[index-1][0], sommeCoins

#example: Calculate the dollar quantity to reach a bid level
def get_amount_to_reach_bid(ticker, bid, bool_print=False):

    book = getOrderBook(ticker)
    bids_book=book["bids"]
    sommetotaldollar = 0
    index = 0
    bids_actuel=bids_book[0][0]
    while float(bids_actuel)>bid:
        ligne=bids_book[index]
        price=ligne[0]
        size=ligne[1]
        sommetotaldollar=sommetotaldollar+(float(price)*float(size))
        index=index+1
        bids_actuel=bids_book[index][0]

    if bool_print:
        print(f"Need {round(sommetotaldollar,2)} dollars to reach bid {bid}")
    return sommetotaldollar

#example: Calculate the dollar quantity to reach a ask level
def get_amount_to_reach_ask(ticker, ask, bool_print=False):
    book = getOrderBook(ticker)
    asks_book = book["asks"]
    #reverse the array
    asks_book=asks_book[len(asks_book)-1::-1]

    sommetotaldollar = 0
    index = 0
    asks_actuel=asks_book[0][0]
    while float(asks_actuel)<ask:
        ligne=asks_book[index]
        price=ligne[0]
        size=ligne[1]
        sommetotaldollar=sommetotaldollar+(float(price)*float(size))
        index=index+1
        asks_actuel=asks_book[index][0]

    if bool_print:
        print(f"Need {round(sommetotaldollar,2)} dollars to reach ask {ask}")
    return sommetotaldollar

def get_bid_ask(pair):

    host = "https://api.gateio.ws"
    prefix = "/api/v4"
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    url = '/spot/tickers'
    query_param = 'currency_pair=' + pair
    sign_headers = gen_sign('GET', prefix + url, query_param)
    headers.update(sign_headers)
    r = requests.request('GET', host + prefix + url + "?" + query_param, headers=headers)
    ask_Gate = r.json()[0]["lowest_ask"]
    bid_Gate = r.json()[0]["highest_bid"]
    return bid_Gate, ask_Gate


if __name__ == "__main__":
    #balance("USDT", True, True)
    #orderLimit("CRO_USDT", "buy", 0.06, 50)
    print(get_bid_ask("POL_USDT"))
