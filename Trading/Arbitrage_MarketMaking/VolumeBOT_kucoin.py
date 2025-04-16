import Librairy_Kucoin as lb
import time
import random

#OBJECTIVE: create volume on a trading pair

def volume(token1, token2, time_sleep, size, roundBalance, roundPrice):

    orderId_buy = ""
    orderId_sell = ""
    pair = token1 + "-" + token2

    balanceToken1= lb.balanceToken(token1,True,True)
    balanceToken2= lb.balanceToken(token2,True,True)

    if float(balanceToken2) == 0: 
        raise ValueError("Balance null")
    
    while True:
        try:
            
            if orderId_sell:
                lb.cancel_order_limit(orderId_sell)
            if orderId_buy:
                lb.cancel_order_limit(orderId_buy)
    
            time.sleep(1)

            # order sell limit
            bid, ask = lb.get_bid_ask(pair)
            Mid = round((float(ask) + float(bid)) / 2, roundPrice)
            factor = random.uniform(0.9, 1.1)  # random factor
            size * factor
            quantity = round(size * factor, roundBalance)

            balance1 = lb.balanceToken(token1,True,False)
            balance2 = lb.balanceToken(token2,True,False)
            value_balance2_token1 = round(balance2/Mid,roundBalance)

            if value_balance2_token1 > quantity and balance1 > quantity:
                print(f"order at Mid price {Mid} for quantity {quantity}") 
                orderId_buy = lb.orderLimit(pair, "buy", Mid, quantity)

                time.sleep(1)

                orderId_sell = lb.orderLimit(pair, "sell", Mid, quantity)

            else:
                print(f"insufficient balance {token2} : {balance2}")

        except Exception as e:
            response = None
            print('error', e)
            return e

        rd=random.randrange(-5,5)
        time.sleep(time_sleep + rd)



if __name__ == "__main__":
    volume("CRO","USDT", 30, 10, 0, 5)