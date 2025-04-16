from kucoin.client import Client

api_key = "67e15a0a38e2bb0001e95ec1"
api_secret = '647977fd-936c-4450-80e7-7fa54bbc447e'
api_passphrase = 'main1BOT'
client = Client(api_key, api_secret, api_passphrase)


def allBalances():
    allbalances=client.get_accounts()
    return allbalances

def balanceToken(currency, bool_available=False, bool_print=False):
    allbalance=client.get_accounts()
    #print(allbalance)
    for token in range(len(allbalance)):
        if allbalance[token]["currency"]==currency and allbalance[token]["type"]=="trade":
            if bool_available:
                if bool_print:
                    print(f"Balance available {currency} : {allbalance[token]['available']}")
                return float(allbalance[token]["available"])
            else:
                if bool_print:
                    print(f"Balance total {currency} : {allbalance[token]['balance']}")
                return float(allbalance[token]["balance"])

#size = quantity of tokens bought
def orderLimit(ticker, side, price, size):

    if side not in ["buy", "sell"]:
        raise ValueError("side must be 'buy' or 'sell'")
    
    if side=="buy":
        orderKucoin = client.create_limit_order(ticker, Client.SIDE_BUY, price, size=size, hidden=False)
    else:
        orderKucoin = client.create_limit_order(ticker, Client.SIDE_SELL, price, size=size, hidden=False)
    orderId=orderKucoin["orderId"]
    print("orderId Kucoin: " + orderId)
    return orderId

#size = quantity of tokens bought
def orderMarket(ticker, side, size):
    if side not in ["buy", "sell"]:
        raise ValueError("side must be 'buy' or 'sell'")
    
    if side=="buy":
        orderKucoin = client.create_market_order(ticker, Client.SIDE_BUY, size)
    else:
        orderKucoin = client.create_limit_order(ticker, Client.SIDE_SELL, size)
    orderId=orderKucoin["orderId"]
    print("orderId Kucoin: " + orderId)

    return orderId
    
def get_order_details(orderid, bool_print=False):
    if not isinstance(bool_print, bool):  # Vérifie si bool_print est bien un booléen
        raise ValueError("Parameter bool_print must be a boolean (True ou False)")
    
    order = client.get_order(order_id=orderid)
    if bool_print:
        print(order)
    return order

def get_order_quantity_left(orderid, bool_print=False):
    order = client.get_order(order_id=orderid)
    if bool_print:
        print(f"Size left for {orderid}", float(order["size"])-float(order["dealSize"]))
    return float(order["size"])-float(order["dealSize"])

def get_order_quantity_filled(orderid, bool_print=False):
    order = client.get_order(order_id=orderid)
    if bool_print:
        print(f"Size filled ", float(order["dealSize"]))
    return float(order["dealSize"])

def get_order_filled_price(orderid):
    order = client.get_order(order_id=orderid)
    return float(order["dealFunds"])/float(order["dealSize"])

def get_order_dollar_filled(orderid):
    order = client.get_order(order_id=orderid)
    return float(order["dealFunds"])

def get_active_orders(symbol=None):
    try:
        if symbol:
            orders = client.get_active_orders(symbol=symbol,status="active")
        else:
            orders = client.get_orders(status="active")
            
        return orders
    except Exception as e:
        print(f"Error to get active orders : {e}")
        return None
    
def get_active_orders_ID(symbol=None, bool_print=False): #Array of IDs
    Id_list=[]
    try:
        if symbol:
            orders = client.get_active_orders(symbol=symbol,status="active")
        else:
            orders = client.get_orders(status="active")
        
        for e in orders['items']:
            Id_list.append(e['id'])
        if bool_print:
            print(Id_list) 
        return Id_list
    except Exception as e:
        print(f"Error to get active orders Id: {e}")
        return None

def cancel_order_limit(orderId):
    try:
        cancelorder = client.cancel_order(orderId)
        print(f"Order {orderId} cancelled.")
        return cancelorder
    except Exception as e:
        print(f"Error for cancelling order {orderId} : {e}")
        return None
    
def cancel_order_limit_Batch(list_ordersID):
    
    for order in list_ordersID:
        try:
            client.cancel_order(order)
            print(f"Order {order} cancelled.")

        except Exception as e:
            print(f"Error for cancelling order {order} : {e}")

def getOrderBook(ticker, bool_print=False):
    book = client.get_order_book(ticker)
    if bool_print:
            print(book)
    return book

#example: price impact if we sell for 500 USDT
def priceImpactSell(ticker, amount, bool_print=False):
    book = client.get_order_book(ticker)
    bids_book = book["bids"]
    #print(bids_book)
    sommetotaldollar=0
    sommeCoins=0
    index=0
    while sommetotaldollar<amount:
        ligne=bids_book[index]
        price=ligne[0]
        size=ligne[1]
        sommeCoins = sommeCoins + min((amount - sommetotaldollar) / float(price), float(size))
        sommetotaldollar = sommetotaldollar + (float(price) * float(size))

        index=index+1
    if bool_print:
        print(f"Bid impact for selling {amount} USDT: {bids_book[index-1][0]} vs current bid {bids_book[0][0]}, need {str(sommeCoins)} tokens")
    return bids_book[index-1][0], sommeCoins


#example: price impact if we buy for 500 USDT
def priceImpactBuy(ticker, amount, bool_print=False):
    book = client.get_order_book(ticker)
    asks_book = book["asks"]
    #print(asks_book)
    sommetotaldollar=0
    sommeCoins = 0
    index=0
    while sommetotaldollar<amount:
        ligne=asks_book[index]
        price=ligne[0]
        size=ligne[1]
        sommeCoins = sommeCoins + min((amount - sommetotaldollar) / float(price), float(size))
        sommetotaldollar = sommetotaldollar + (float(price) * float(size))

        index=index+1
    if bool_print:
        print(f"Ask impact for selling {amount} USDT: {asks_book[index-1][0]} vs current ask {asks_book[0][0]}, get {str(sommeCoins)} tokens")
    return asks_book[index-1][0], sommeCoins

#example: Calculate the dollar quantity to reach a bid level
def get_amount_to_reach_bid(ticker, bid, bool_print=False):
    book = client.get_order_book(ticker)
    bids_book = book["bids"]
    #print(bids_book)
    sommetotaldollar=0
    current_bid=bids_book[0][0]
    index=0
    while float(current_bid)>bid:
        ligne=bids_book[index]
        price=ligne[0]
        size=ligne[1]
        sommetotaldollar += (float(price)*float(size))
        index=index+1
        current_bid=bids_book[index][0]
        
    if bool_print:
        print(f"Need {round(sommetotaldollar,2)} dollars to reach bid {bid}")
    return sommetotaldollar

#example: Calculate the dollar quantity to reach a ask level
def get_amount_to_reach_ask(ticker, ask, bool_print=False):
    book = client.get_order_book(ticker)
    asks_book = book["asks"]
    #print(asks_book)
    sommetotaldollar=0
    current_ask=asks_book[0][0]
    index=0
    while float(current_ask)<=ask:
        ligne=asks_book[index]
        price=ligne[0]
        size=ligne[1]
        sommetotaldollar += (float(price)*float(size))
        index=index+1
        current_ask=asks_book[index][0]

    if bool_print:
        print(f"Need {round(sommetotaldollar,2)} dollars to reach ask {ask}")
    return sommetotaldollar

def get_bid_ask(ticker):
    book = client.get_order_book(ticker)
    asks_book = book["asks"]
    bids_book = book["bids"]
    ask=asks_book[0][0]
    bid=bids_book[0][0]

    return bid, ask

if __name__ == "__main__":
    #balanceToken("USDT", True, True)
    #orderLimit("CRO-USDT","buy","0.15","5")
    #get_active_orders_ID(bool_print=True)
    print(get_bid_ask("CRO-USDT"))