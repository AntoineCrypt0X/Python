import pandas as pd
import os
from datetime import datetime
import time
import Librairy_Kucoin as kc
import Librairy_Gate as gt

class TokenQuantify:

    def __init__(self, symbol: str, time_sleep):

        self.symbol = symbol
        self.pairKucoin = symbol + "-USDT"
        self.pairGate = symbol + "_USDT"
        self.time_sleep = time_sleep
        self.current_date = str(datetime.now().strftime("%Y-%m-%d_%H_%M_%S"))
        self.file_name = f"quant_{symbol}-USDT_{self.current_date}.xlsx"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(script_dir, self.file_name)
        self.data = None
        self.row_index = 1
        self.create_file()
        self.isActive = False

    def create_file(self):
        # Create a new file with predefined columns
        self.data = pd.DataFrame(columns=["date", "ratio_bidKC__askGT", "GT_Dollar_Close_Gap", "GT_Profit_token/dollar","ratio_bidGT__askKC", "KC_Dollar_Close_Gap", "KC_Profit_token/dollar"])
        print(f"File '{self.file_path}' created. Writing will start at row {self.row_index}")
        self.save_file()
            
    def save_file(self):
        self.data.to_excel(self.file_path, index=False, header=True)

    def change_value(self, values):
        try:
            if len(values) != 6:
                raise ValueError("The input list must contain exactly 6 values.")

            columns = ["ratio_bidKC__askGT", "GT_Dollar_Close_Gap", "GT_Profit_token/dollar","ratio_bidGT__askKC", "KC_Dollar_Close_Gap", "KC_Profit_token/dollar"]

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
    

    def Calculate_spreads(self, size=200, range=10):

        if self.isActive:
            print("Function has already been triggered.")
            return
        
        self.isActive = True
        nb_range = int(size / range)

        while True:
            try:
                ratio_bidKC__askGT, ratio_bidGT__askKC = self.getSpreadRatios()
                GT_Dollar_Close_Gap = 0
                KC_Dollar_Close_Gap = 0
                GT_Profit = "0/0"
                KC_Profit = "0/0"

                if ratio_bidGT__askKC > 0.005:
                    #book_gate = gt.getOrderBook(self.pairGate, True)
                    #book_kucoin = kc.getOrderBook(self.pairKucoin, True)

                    new_ask_kucoin, sommeCoinsKucoin = kc.priceImpactBuy(self.pairKucoin, size, False)
                    new_bid_Gate, sommeCoinsGate = gt.priceImpactSell(self.pairGate, size, False)
                    i=0
                    while float(new_ask_kucoin)>float(new_bid_Gate*0.998) and i < nb_range: #*0.998 take into account the fees
                        size -= range
                        new_ask_kucoin, sommeCoinsKucoin = kc.priceImpactBuy(self.pairKucoin, size, False)
                        new_bid_Gate, sommeCoinsGate = gt.priceImpactSell(self.pairGate, size, False)
                        i += 1
                        time.sleep(0.05)
                    
                    if i < nb_range:
                        KC_Dollar_Close_Gap = size
                        profit_token = float(sommeCoinsKucoin)-float(sommeCoinsGate)
                        profit_dollar = profit_token*((float(new_ask_kucoin) + float(new_bid_Gate))/2)
                        KC_Profit = str(round(profit_token,6)) + "/" + str(round(profit_dollar,2))
                    

                if ratio_bidKC__askGT > 0.005:
                    new_ask_Gate, sommeCoinsGate = gt.priceImpactBuy(self.pairGate, size, False)
                    new_bid_kucoin, sommeCoinsKucoin = kc.priceImpactSell(self.pairKucoin, size, False)
                    i=0
                    while float(new_ask_Gate)>float(new_bid_kucoin*0.998) and i < nb_range:
                        size -= range
                        new_ask_Gate, sommeCoinsGate = gt.priceImpactBuy(self.pairGate, size, False)
                        new_bid_kucoin, sommeCoinsKucoin = kc.priceImpactSell(self.pairKucoin, size, False)
                        i += 1
                        time.sleep(0.05)
                    if i < nb_range:
                        GT_Dollar_Close_Gap = size
                        profit_token = float(sommeCoinsGate)-float(sommeCoinsKucoin)
                        profit_dollar = profit_token*((float(new_ask_Gate) + float(new_bid_kucoin))/2)
                        GT_Profit = str(round(profit_token,6)) + "/" + str(round(profit_dollar,2))

                values = [ratio_bidKC__askGT, GT_Dollar_Close_Gap, GT_Profit, ratio_bidGT__askKC, KC_Dollar_Close_Gap, KC_Profit]
                self.row_index += 1
                self.change_value(values)

            except Exception as e:
                print(f"Error : {e}")
            
            time.sleep(self.time_sleep)