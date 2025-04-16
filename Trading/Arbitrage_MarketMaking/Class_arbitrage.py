import pandas as pd
import os
from datetime import datetime
import time
import Librairy_Kucoin as kc
import Librairy_Gate as gt

class Arbitrage:

    def __init__(self, symbol: str, time_sleep, roundBalances=2, roundPrice=2):

        self.symbol = symbol
        self.pairKucoin = symbol + "-USDT"
        self.pairGate = symbol + "_USDT"
        self.time_sleep = time_sleep
        self.roundBalances=roundBalances
        self.roundPrice=roundPrice
        self.current_date = str(datetime.now().strftime("%Y-%m-%d_%H_%M_%S"))
        self.file_name = f"arbitrage_{symbol}-USDT_{self.current_date}.xlsx"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(script_dir, self.file_name)
        self.data = None
        self.row_index = 1
        self.create_file()
        self.isActive = False

    def create_file(self):
        # Create a new file with predefined columns
        self.data = pd.DataFrame(columns=["date", "ratio", "size", "profit_token", "profit_dollar", "ask_price_impact", "bid_price_impact"])
        print(f"File '{self.file_path}' created. Writing will start at row {self.row_index}")
        self.save_file()
            
    def save_file(self):
        self.data.to_excel(self.file_path, index=False, header=True)

    def change_value(self, values):
        try:
            if len(values) != 7:
                raise ValueError("The input list must contain exactly 6 values.")

            columns = ["date", "ratio", "size", "profit_token", "profit_dollar", "ask_price_impact", "bid_price_impact"]

            for col, value in zip(columns, values):
                self.data.at[self.row_index, col] = value

            # Update the "last_modified" column with the current timestamp
            self.data.at[self.row_index, "date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.save_file() 

        except Exception as e:
            print(f"Error updating values {values} at row {self.row_index}: {e}")

    def getSpreadRatios(self):
        bid_Gate, ask_Gate = gt.get_bid_ask(self.pairGate)
        bid_kucoin, ask_kucoin= kc.get_bid_ask(self.pairKucoin)

        ratio_bidKC__askGT = round((float(bid_kucoin)-float(ask_Gate))/float(ask_Gate),5)
        ratio_bidGT__askKC = round((float(bid_Gate) - float(ask_kucoin)) / float(ask_kucoin),5)

        print(f"Ask GT: {ask_Gate}, Bid KC: {bid_kucoin}, ratio {round(ratio_bidKC__askGT*100,3)}% ||| Ask KC: {ask_kucoin}, Bid GT: {bid_Gate}, ratio {round(ratio_bidGT__askKC*100,3)}%")
        return ratio_bidKC__askGT, ratio_bidGT__askKC
    
    def getbalances(self):
        return round(gt.balance(self.symbol, True, False),self.roundBalances), round(gt.balance("USDT", True, False),self.roundBalances), round(kc.balance(self.symbol, True, False),self.roundBalances), round(kc.balance("USDT", True, False),self.roundBalances)
    
    #Size in dollar
    def Calculate_spreads(self, size=200, range=20, trigger_threshold=0.005, balancing_threshold=-0.002, fees=0.001, margin_order=0.05): #Margin order: to account for price impact and the balance needed in the order limit.

        if self.isActive:
            print("Function has already been triggered.")
            return
        
        self.isActive = True
        nb_range = int(size / range)
        total_profit = 0
        initial_balance_token_gt, initial_balance_usdt_gt, initial_balance_token_kc, initial_balance_usdt_kc = self.getbalances()

        while True:
            try:
                ratio_bidKC__askGT, ratio_bidGT__askKC = self.getSpreadRatios()
                _size = size
                balance_token_gt, balance_usdt_gt, balance_token_kc, balance_usdt_kc = self.getbalances()
                print(f"Token GT {balance_token_gt}, Usdt GT {balance_usdt_gt}, Token KC {balance_token_kc}, Usdt KC {balance_usdt_kc}")

                if ratio_bidGT__askKC > trigger_threshold:

                    new_ask_kucoin, sommeCoinsKucoin = kc.priceImpactBuy(self.pairKucoin, _size, False)
                    new_bid_Gate, sommeCoinsGate = gt.priceImpactSell(self.pairGate, _size, False)
                    i=0
                    while float(new_ask_kucoin)>float(new_bid_Gate*(1-fees)) and i < nb_range:
                        _size -= range
                        new_ask_kucoin, sommeCoinsKucoin = kc.priceImpactBuy(self.pairKucoin, _size, False)
                        new_bid_Gate, sommeCoinsGate = gt.priceImpactSell(self.pairGate, _size, False)
                        i += 1
                        time.sleep(0.01)
                    
                    if i < nb_range:
                        if balance_usdt_kc > _size * (1 + margin_order) and balance_token_gt > sommeCoinsGate * (1 + margin_order):
                            order_ask = kc.orderLimit(self.pairKucoin, 'buy', new_ask_kucoin, sommeCoinsKucoin)
                            qty_filled_ask = order_ask["dealSize"]
                            filled_price_ask = float(order_ask["dealFunds"])/float(qty_filled_ask)
                            kc.cancel_order_limit(order_ask)

                            order_bid = gt.orderLimit(self.pairGate, 'sell', new_bid_Gate, qty_filled_ask)
                            order_detail = gt.get_order_details(self.pairGate,order_bid,False)
                            qty_filled_bid = order_detail.amount
                            filled_price_bid = order_detail.price
                            gt.cancel_order_limit(order_bid)

                            check_quantity = qty_filled_ask-qty_filled_bid #Check quantity token bought = quantity sold
                            if check_quantity == 0:
                                profit_dollar = (filled_price_bid-filled_price_ask)*qty_filled_ask*(1-(2*fees))
                            else:
                                profit_dollar = -(filled_price_bid-filled_price_ask)*check_quantity*(1+(2*fees))

                            profit_token = profit_dollar/new_bid_Gate
                            total_profit += profit_dollar

                            print(f"Arbitrage || ratio_bidGT__askKC: {ratio_bidGT__askKC}, size:{_size}$, qty filled ask:{qty_filled_ask}, qty filled bid:{qty_filled_bid}, profit dollar {profit_dollar}$, total profit: {total_profit}$")

                            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            values = [date, "Arbitrage || ratio_bidGT__askKC" , _size, profit_token, profit_dollar, new_ask_kucoin, new_bid_Gate]
                            self.row_index += 1
                            self.change_value(values)
                    
                if ratio_bidKC__askGT > trigger_threshold:
                    new_ask_Gate, sommeCoinsGate = gt.priceImpactBuy(self.pairGate, _size, False)
                    new_bid_kucoin, sommeCoinsKucoin = kc.priceImpactSell(self.pairKucoin, _size, False)
                    i=0
                    while float(new_ask_Gate)>float(new_bid_kucoin*(1-fees)) and i < nb_range:
                        _size -= range
                        new_ask_Gate, sommeCoinsGate = gt.priceImpactBuy(self.pairGate, _size, False)
                        new_bid_kucoin, sommeCoinsKucoin = kc.priceImpactSell(self.pairKucoin, _size, False)
                        i += 1
                        time.sleep(0.01)

                    if i < nb_range:
                        if balance_usdt_gt > _size * (1 + margin_order) and balance_token_kc > sommeCoinsKucoin * (1 + margin_order):
                            order_ask = gt.orderLimit(self.pairGate, 'buy', new_ask_Gate, sommeCoinsGate)
                            qty_filled_ask = gt.get_order_quantityLeft(order_ask, False)        
                            gt.cancel_order_limit(order_ask)

                            order_bid = kc.orderLimit(self.pairKucoin, 'sell', new_bid_kucoin, qty_filled_ask)
                            qty_filled_bid = kc.get_order_quantityLeft(order_ask, False)
                            kc.cancel_order_limit(order_bid)

                            check_quantity = qty_filled_ask-qty_filled_bid #Check quantity token bought = quantity sold
                            if check_quantity == 0:
                                profit_dollar = (filled_price_bid-filled_price_ask)*qty_filled_ask*(1-(2*fees))
                            else:
                                profit_dollar = -(filled_price_bid-filled_price_ask)*check_quantity*(1+(2*fees))
                            
                            profit_token = profit_dollar/new_bid_Gate
                            total_profit += profit_dollar

                            print(f"Arbitrage || ratio_bidKC__askGT: {ratio_bidKC__askGT}, size:{_size}$, qty filled ask:{qty_filled_ask}, qty filled bid:{qty_filled_bid}, profit token {profit_token}, total profit: {total_profit}")
                            profit_dollar = profit_token*((float(new_ask_Gate) + float(new_bid_kucoin))/2)

                            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            values = [date, "Arbitrage || ratio_bidKC__askGT" , _size, profit_token, profit_dollar, new_ask_kucoin, new_bid_Gate]
                            self.row_index += 1
                            self.change_value(values)

            except Exception as e:
                print(f"Error : {e}")
            

            #rebalancing:
            time.sleep(2)

            try:
                ratio_bidKC__askGT, ratio_bidGT__askKC = self.getSpreadRatios()
                if ratio_bidKC__askGT > balancing_threshold: 
                    balance_token_gt, balance_usdt_gt, balance_token_kc, balance_usdt_kc = self.getbalances()
                    print(f"Token GT {balance_token_gt}, Usdt GT {balance_usdt_gt}, Token KC {balance_token_kc}, Usdt KC {balance_usdt_kc}")
                    if  (balance_usdt_kc-initial_balance_usdt_kc) > 0 and int((balance_usdt_kc-initial_balance_usdt_kc)/range) > 0:
                        _nb_range = int((balance_usdt_kc-initial_balance_usdt_kc)/range)
                        _size = _nb_range * range

                        new_ask_Gate, sommeCoinsGate = gt.priceImpactBuy(self.pairGate, _size, False)
                        new_bid_kucoin, sommeCoinsKucoin = kc.priceImpactSell(self.pairKucoin, _size, False)
                        i=0
                        while float(new_ask_Gate)>float(new_bid_kucoin*(1-balancing_threshold+2*fees)) and i < _nb_range:
                            _size -= range
                            new_ask_Gate, sommeCoinsGate = gt.priceImpactBuy(self.pairGate, _size, False)
                            new_bid_kucoin, sommeCoinsKucoin = kc.priceImpactSell(self.pairKucoin, _size, False)
                            i += 1
                            time.sleep(0.01)

                        if i < nb_range:
                            if balance_usdt_gt > _size * (1 + margin_order) and balance_token_kc > sommeCoinsKucoin * (1 + margin_order):
                                order_ask = gt.orderLimit(self.pairGate, 'buy', new_ask_Gate, sommeCoinsGate)
                                qty_filled_ask = gt.get_order_quantityLeft(order_ask, False)        
                                gt.cancel_order_limit(order_ask)

                                order_bid = kc.orderLimit(self.pairKucoin, 'sell', new_bid_kucoin, qty_filled_ask)
                                qty_filled_bid = kc.get_order_quantityLeft(order_ask, False)
                                kc.cancel_order_limit(order_bid)

                                check_quantity = qty_filled_ask-qty_filled_bid #Check quantity token bought = quantity sold
                                if check_quantity == 0:
                                    profit_dollar = (filled_price_bid-filled_price_ask)*qty_filled_ask*(1-(2*fees))
                                else:
                                    profit_dollar = -(filled_price_bid-filled_price_ask)*check_quantity*(1+(2*fees))
                            
                                profit_token = profit_dollar/new_bid_Gate
                                total_profit += profit_dollar

                                print(f"Balancing || ratio_bidKC__askGT: {ratio_bidKC__askGT}, size:{_size}$, qty filled ask:{qty_filled_ask}, qty filled bid:{qty_filled_bid}, profit token {profit_token}, total profit: {total_profit}")
                                profit_dollar = profit_token*((float(new_ask_Gate) + float(new_bid_kucoin))/2)

                                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                values = [date, "Balancing || ratio_bidKC__askGT" , _size, profit_token, profit_dollar, new_ask_kucoin, new_bid_Gate]
                                self.row_index += 1
                                self.change_value(values)

                if ratio_bidGT__askKC > balancing_threshold:
                    balance_token_gt, balance_usdt_gt, balance_token_kc, balance_usdt_kc = self.getbalances()
                    print(f"Token GT {balance_token_gt}, Usdt GT {balance_usdt_gt}, Token KC {balance_token_kc}, Usdt KC {balance_usdt_kc}")
                    if  (balance_usdt_gt-initial_balance_usdt_gt) > 0 and int((balance_usdt_gt-initial_balance_usdt_gt)/range) > 0:
                        _nb_range = int((balance_usdt_gt-initial_balance_usdt_gt)/range)
                        _size = _nb_range * range

                        new_ask_kucoin, sommeCoinsKucoin = kc.priceImpactBuy(self.pairKucoin, _size, False)
                        new_bid_Gate, sommeCoinsGate = gt.priceImpactSell(self.pairGate, _size, False)
                        i=0
                        while float(new_ask_kucoin)>float(new_bid_Gate*(1-balancing_threshold+2*fees)) and i < nb_range:
                            _size -= range
                            new_ask_kucoin, sommeCoinsKucoin = kc.priceImpactBuy(self.pairKucoin, _size, False)
                            new_bid_Gate, sommeCoinsGate = gt.priceImpactSell(self.pairGate, _size, False)
                            i += 1
                            time.sleep(0.01)
                    
                        if i < nb_range:
                            if balance_usdt_kc > _size * (1 + margin_order) and balance_token_gt > sommeCoinsGate * (1 + margin_order):
                                order_ask = kc.orderLimit(self.pairKucoin, 'buy', new_ask_kucoin, sommeCoinsKucoin)
                                qty_filled_ask = order_ask["dealSize"]
                                filled_price_ask = float(order_ask["dealFunds"])/float(qty_filled_ask)
                                kc.cancel_order_limit(order_ask)

                                order_bid = gt.orderLimit(self.pairGate, 'sell', new_bid_Gate, qty_filled_ask)
                                order_detail = gt.get_order_details(self.pairGate,order_bid,False)
                                qty_filled_bid = order_detail.amount
                                filled_price_bid = order_detail.price
                                gt.cancel_order_limit(order_bid)

                                check_quantity = qty_filled_ask-qty_filled_bid #Check quantity token bought = quantity sold
                                if check_quantity == 0:
                                    profit_dollar = (filled_price_bid-filled_price_ask)*qty_filled_ask*(1-(2*fees))
                                else:
                                    profit_dollar = -(filled_price_bid-filled_price_ask)*check_quantity*(1+(2*fees))

                                profit_token = profit_dollar/new_bid_Gate
                                total_profit += profit_dollar

                                print(f"Arbitrage || ratio_bidGT__askKC: {ratio_bidGT__askKC}, size:{_size}$, qty filled ask:{qty_filled_ask}, qty filled bid:{qty_filled_bid}, profit dollar {profit_dollar}$, total profit: {total_profit}$")

                                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                values = [date, "Arbitrage || ratio_bidGT__askKC" , _size, profit_token, profit_dollar, new_ask_kucoin, new_bid_Gate]
                                self.row_index += 1
                                self.change_value(values)

            except Exception as e:
                print(f"Error balancing : {e}")

            time.sleep(self.time_sleep)