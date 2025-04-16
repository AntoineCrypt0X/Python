from kucoin.client import Client
import time
import datetime
import time
import telebot
from tradingview_ta import TA_Handler, Interval, Exchange
import telebot

api_key = ""
api_secret = ''
api_passphrase = ""
client = Client(api_key, api_secret, api_passphrase)

#OBJECTIVE: Retrieve the Forex EUR/USD price and place orders at -3% and +3% to capture the wicks of the candlesticks.

def Open_TradingView(coin):

    try:
        token = TA_Handler(
            symbol="USDT"+coin,
            screener="crypto",
            exchange="kucoin",
            interval=Interval.INTERVAL_1_HOUR
        )
        open = token.get_indicators()["open"]
        return open

    except Exception as e2:
        print('error', e2)
    return 0

def current_price(pair):

    try:
        token = TA_Handler(
            symbol=pair,
            screener="forex",
            exchange=Exchange.FOREX,
            interval=Interval.INTERVAL_1_MINUTE
        )
        #print(token.get_indicators())
        LastPrice = token.get_indicators()['open']
        #print(LastPrice)
        return LastPrice

    except Exception as e2:
        print('error', e2)
    else:
        b = 1
    return 0

def orderKucoinLimit(ticker, side, price, size):

    if side=="buy":
        orderKucoin = client.create_limit_order(ticker, Client.SIDE_BUY, price, size=size, hidden=True)
    else:
        orderKucoin = client.create_limit_order(ticker, Client.SIDE_SELL, price, size=size, hidden=True)
    orderId=orderKucoin["orderId"]
    print("orderId Kucoin: " + orderId)
    return orderId

def balanceKucoin(currency):
    allbalance=client.get_accounts()
    for e in range(len(allbalance)):
        if allbalance[e]["currency"]==currency and allbalance[e]["type"]=="trade":
            return float(allbalance[e]["available"])

def getorderKucoin(orderid):
    order=client.get_order(order_id=orderid)
    return order

def cancelKucoinlimit(orderId):
    cancelorder = client.cancel_order(orderId)


def Meche():
    coin="EUR"
    order_bid=""
    order_ask=""

    #Telegram alert message
    API_KEY = ""
    chatID = 0
    bot = telebot.TeleBot(API_KEY, parse_mode=None)

    coeff=1.03
    #coeff re-buy/re-sell
    re_coeff=1.01
    max_amount=1000

    while True:
        print(f"\n{datetime.datetime.utcnow()}\n")
        try:
            if order_bid != "":
                try:
                    cancelKucoinlimit(str(order_bid))
                    order_bid = ""
                except Exception as e:
                    print('error order_bid', e)
                    order_bid = ""

            if order_ask != "":
                try:
                    cancelKucoinlimit(order_ask)
                    order_ask = ""
                except Exception as e:
                    print('error order_ask', e)
                    order_ask = ""

            time.sleep(0.1)
            balanceGBP = balanceKucoin(coin)
            balanceUSDT = min(balanceKucoin("USDT"), max_amount)
            print(balanceGBP, balanceUSDT)

            spot = current_price("USD" + coin)
            print("spot", spot)

            if balanceUSDT > 1:
                order_ask = orderKucoinLimit("USDT-" + coin, "sell", str(round(spot * coeff, 4)),str(round(float(balanceUSDT) * 0.998, 2)))
                time.sleep(1)

            if balanceGBP > 1:
                price_exe = round(spot / coeff, 4)
                size = min(max_amount, balanceGBP / price_exe)
                order_bid = orderKucoinLimit("USDT-" + coin, "buy", str(price_exe), str(round(size * 0.998, 2)))

            time.sleep(900)

            sell_filled = 0
            buy_filled = 0
            order_sell = {}
            order_buy = {}

            if order_ask != "":
                order_sell = getorderKucoin(order_ask)
                sell_filled = float(order_sell["dealSize"])

            if order_bid != "":
                order_buy = getorderKucoin(order_bid)
                buy_filled = float(order_buy["dealSize"])
            print("filled sell-buy", sell_filled, buy_filled)

            if sell_filled > 1:
                message = "EUR USDT: Order Sell, amount: " + str(sell_filled) + ", at price: " + str((float(order_sell["dealFunds"]) / sell_filled)) + " vs Spot price: " + str(spot)
                bot.send_message(chat_id=chatID, text=message)
                rebuy = orderKucoinLimit("USDT-" + coin, "buy", str(round(float(spot) * re_coeff, 4)), str(round(sell_filled, 2)))
            if buy_filled > 1:
                message = "EUR USDT: Order Buy, amount: " + str(buy_filled) + ", at price: " + str((float(order_buy["dealFunds"]) / buy_filled)) + " vs Spot price: " + str(spot)
                bot.send_message(chat_id=chatID, text=message)
                resell = orderKucoinLimit("USDT-" + coin, "sell", str(round(float(spot) * (1 - (re_coeff - 1)), 4)), str(round(buy_filled, 2)))

        except Exception as e:
            print('error', e)

        print("\n")

Meche()