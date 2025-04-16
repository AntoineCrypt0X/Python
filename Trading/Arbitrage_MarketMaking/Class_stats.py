import pandas as pd
import os
from datetime import datetime
import time
import Librairy_Kucoin as kc
import Librairy_Gate as gt

class TokenStats:
    def __init__(self, symbol: str, time_sleep):

        self.symbol = symbol
        self.pairKucoin = symbol + "-USDT"
        self.pairGate = symbol + "_USDT"
        self.time_sleep = time_sleep
        self.file_name = f"{symbol}-USDT.xlsx"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(script_dir, self.file_name)
        self.data = None
        self.row_index = None  # Row number where future data will be written
        self.load_or_create_file()
        self.isActive = False

    def load_or_create_file(self):
        "Loads the Excel file if it exists; otherwise, creates a new one."
        if os.path.exists(self.file_path):
            self.data = pd.read_excel(self.file_path, header=0)
            self.row_index = self._find_first_empty_row()

            # Add the current date to column A
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.data.at[self.row_index, "date"] = current_date
            self.data.at[self.row_index, "last_modified"] = current_date
            
            print(f"File '{self.file_path}' loaded. First empty row: {self.row_index}")

        else:
            # Create a new file with predefined columns
            self.data = pd.DataFrame(columns=["date", "last_modified", "algo", "KC_+0.5%/+1%", "KC_+1%/+3%", "KC_+3%/+5%", "KC_+5%Plus", "GT_+0.5%/+1%", "GT_+1%/+3%", "GT_+3%/+5%", "GT_+5%Plus"])
            self.row_index = 0  # Start writing from row 2 (row 1 is the header)

            # Add the current date to column A
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.data.at[self.row_index, "date"] = current_date  # Store the creation date in column A

            # Add "last modified" date in column B
            self.data.at[self.row_index, "last_modified"] = current_date

            print(f"File '{self.file_path}' created. Writing will start at row {self.row_index}")
        
        self.data.loc[self.row_index, ["KC_+0.5%/+1%", "KC_+1%/+3%", "KC_+3%/+5%", "KC_+5%Plus","GT_+0.5%/+1%", "GT_+1%/+3%", "GT_+3%/+5%", "GT_+5%Plus"]] = 0
        self.save_file()

    def save_file(self):
        self.data.to_excel(self.file_path, index=False, header=True)

    def _find_first_empty_row(self):
        for i, row in self.data.iterrows():
            if row.isnull().all():  # If the entire row is empty
                return i
        return len(self.data)  # If no empty rows, return the next available row

    def get_value(self, column_name: str):
        try:
            return self.data.at[self.row_index, column_name]
        except Exception as e:
            print(f"Error retrieving {column_name} at row {self.row_index}: {e}")
            return None

    def change_value(self, column_name: str, new_value):
        try:
            # Check if the column exists
            if column_name not in self.data.columns:
                print(f"Column '{column_name}' does not exist.")
                return

            # Update the value in the specific column for the current row
            self.data.at[self.row_index, column_name] = new_value

            # Update the last modified date in column B
            self.data.at[self.row_index, "last_modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.save_file()

        except Exception as e:
            print(f"Error updating {column_name} at row {self.row_index}: {e}")

    def getSpreadRatios(self):
        bid_Gate, ask_Gate = gt.get_bid_ask(self.pairGate)
        bid_kucoin, ask_kucoin= kc.get_bid_ask(self.pairKucoin)

        ratio_bidKC__askGT = round((float(bid_kucoin)-float(ask_Gate))/float(ask_Gate),5)
        ratio_bidGT__askKC = round((float(bid_Gate) - float(ask_kucoin)) / float(ask_kucoin),5)

        print(f"Ask GT: {ask_Gate}, Bid KC: {bid_kucoin}, ratio {round(ratio_bidKC__askGT*100,3)}% ||| Ask KC: {ask_kucoin}, Bid GT: {bid_Gate}, ratio {round(ratio_bidGT__askKC*100,3)}%")
        return ratio_bidKC__askGT, ratio_bidGT__askKC
    
    #Same function, but simulate the price impact of buying/selling an amount of X dollars on the bid and ask ratio
    def getSpreadRatios_price_impact(self, dollar):
        
        bid_Gate = gt.priceImpactSell(self.pairGate, dollar, False)[0]
        ask_Gate = gt.priceImpactBuy(self.pairGate, dollar, False)[0]
        
        bid_kucoin = kc.priceImpactSell(self.pairKucoin, dollar, False)[0]
        ask_kucoin = kc.priceImpactBuy(self.pairKucoin, dollar, False)[0]

        ratio_bidKC__askGT = round((float(bid_kucoin)-float(ask_Gate))/float(ask_Gate),5)
        ratio_bidGT__askKC = round((float(bid_Gate) - float(ask_kucoin)) / float(ask_kucoin),5)

        print(f"Price impact of {dollar} dollars, Ask GT: {ask_Gate}, Bid KC: {bid_kucoin}, ratio {round(ratio_bidKC__askGT*100,3)}% ||| Ask KC: {ask_kucoin}, Bid GT: {bid_Gate}, ratio {round(ratio_bidGT__askKC*100,3)}%")
        return ratio_bidKC__askGT, ratio_bidGT__askKC
    
    def stats_bid_ask(self):

        if self.isActive:
            print("Function has already been triggered.")
            return
        
        self.isActive = True
        self.change_value("algo", "stats_bid_ask")

        ratio_Gate = -1 ## linked to ratio_bidKC__askGT
        ratio_Kucoin = -1 # linked to ratio_bidGT__askKC
        ratio_Gate_Temp = 5 ## linked to ratio_bidKC__askGT
        ratio_Kucoin_Temp = 5 # linked to ratio_bidGT__askKC
        can_record_Gate = False # # linked to ratio_bidKC__askGT
        can_record_Kucoin= False # linked to ratio_bidGT__askKC

        ratio_order =  {
        1 : "+0.5%/+1%",
        2 : "+1%/+3%",
        3 : "+3%/+5%",
        4 : "+5%Plus"
        }

        while True:
            try:
                ratio_bidKC__askGT, ratio_bidGT__askKC = self.getSpreadRatios()

                # A new arbitrage point can be recorded after the spread ratio drops back below 0.5% or after a downgrade of two levels in the ratio_order classification.
                if ratio_bidGT__askKC < 0.005:
                    can_record_Kucoin = True
                    ratio_Kucoin = -1
                if ratio_bidKC__askGT < 0.005:
                    can_record_Gate = True
                    ratio_Gate = -1
                
                if ratio_bidGT__askKC >= 0.005 and ratio_bidGT__askKC < 0.01:
                    ratio_Kucoin = 1
                if ratio_bidGT__askKC >= 0.01 and ratio_bidGT__askKC < 0.03:
                    ratio_Kucoin = 2
                if ratio_bidGT__askKC >= 0.03 and ratio_bidGT__askKC < 0.05:
                    ratio_Kucoin = 3
                if ratio_bidGT__askKC >= 0.05:
                    ratio_Kucoin = 4

                if ratio_bidKC__askGT >= 0.005 and ratio_bidKC__askGT < 0.01:
                    ratio_Gate = 1
                if ratio_bidKC__askGT >= 0.01 and ratio_bidKC__askGT < 0.03:
                    ratio_Gate = 2
                if ratio_bidKC__askGT >= 0.03 and ratio_bidKC__askGT < 0.05:
                    ratio_Gate = 3
                if ratio_bidKC__askGT >= 0.05:
                    ratio_Gate = 4
                
                if ratio_Kucoin > ratio_Kucoin_Temp and can_record_Kucoin and ratio_Kucoin > 0:
                    for i in range(ratio_Kucoin_Temp + 1, ratio_Kucoin + 1):
                        current_value = int(self.get_value("KC_" + ratio_order[i]))
                        self.change_value("KC_" + ratio_order[i], current_value + 1)
                    ratio_Kucoin_Temp = ratio_Kucoin

                if ratio_Gate > ratio_Gate_Temp and can_record_Gate and ratio_Gate > 0:
                    for i in range(ratio_Gate_Temp + 1, ratio_Gate + 1):
                        current_value = int(self.get_value("GT_" + ratio_order[i]))
                        self.change_value("GT_" + ratio_order[i], current_value + 1)
                    ratio_Gate_Temp = ratio_Gate

                # We can record a new arbitrage opportunity again when the ratio_order has dropped by at least two levels, which would correspond to the price impact of an arbitrage. 
                # This is done to avoid counting overly frequent oscillations between two consecutive ratio_order levels.
                # Example: If the ratio_order is 3 (spread between 3% and 5%), there needs to be a return to at least below +1% spread before recording another arbitrage opportunity.
                if ratio_Kucoin_Temp >= ratio_Kucoin + 2:
                    can_record_Kucoin = True
                    ratio_Kucoin_Temp = ratio_Kucoin

                if ratio_Kucoin_Temp == ratio_Kucoin + 1:
                    can_record_Kucoin = False

                if ratio_Gate_Temp >= ratio_Gate + 2:
                    can_record_Gate = True
                    ratio_Gate_Temp = ratio_Gate
                    
                if ratio_Gate_Temp == ratio_Gate + 1:
                    can_record_Gate = False

            except Exception as e:
                print(f"Error : {e}")
            
            time.sleep(self.time_sleep)

    #Same function, but simulate the price impact of buying/selling an amount of X dollars on the bid and ask. Goal: Do not record arbitrage opportunities with no market depth.
    def stats_bid_ask_price_impact(self, dollar):

        if self.isActive:
            print("Function has already been triggered.")
            return
        
        self.isActive = True
        self.change_value("algo", f"stats_bid_ask_price_impact {dollar}")

        ratio_Gate = -1 ## linked to ratio_bidKC__askGT
        ratio_Kucoin = -1 # linked to ratio_bidGT__askKC
        ratio_Gate_Temp = 5 ## linked to ratio_bidKC__askGT
        ratio_Kucoin_Temp = 5 # linked to ratio_bidGT__askKC
        can_record_Gate = False # # linked to ratio_bidKC__askGT
        can_record_Kucoin= False # linked to ratio_bidGT__askKC

        ratio_order =  {
        1 : "+0.5%/+1%",
        2 : "+1%/+3%",
        3 : "+3%/+5%",
        4 : "+5%Plus"
        }

        while True:
            try:
                ratio_bidKC__askGT, ratio_bidGT__askKC = self.getSpreadRatios_price_impact(dollar)

                # A new arbitrage point can be recorded after the spread ratio drops back below 0.5% or after a downgrade of two levels in the ratio_order classification.
                if ratio_bidGT__askKC < 0.005:
                    can_record_Kucoin = True
                    ratio_Kucoin = -1
                if ratio_bidKC__askGT < 0.005:
                    can_record_Gate = True
                    ratio_Gate = -1
                
                if ratio_bidGT__askKC >= 0.005 and ratio_bidGT__askKC < 0.01:
                    ratio_Kucoin = 1
                if ratio_bidGT__askKC >= 0.01 and ratio_bidGT__askKC < 0.03:
                    ratio_Kucoin = 2
                if ratio_bidGT__askKC >= 0.03 and ratio_bidGT__askKC < 0.05:
                    ratio_Kucoin = 3
                if ratio_bidGT__askKC >= 0.05:
                    ratio_Kucoin = 4

                if ratio_bidKC__askGT >= 0.005 and ratio_bidKC__askGT < 0.01:
                    ratio_Gate = 1
                if ratio_bidKC__askGT >= 0.01 and ratio_bidKC__askGT < 0.03:
                    ratio_Gate = 2
                if ratio_bidKC__askGT >= 0.03 and ratio_bidKC__askGT < 0.05:
                    ratio_Gate = 3
                if ratio_bidKC__askGT >= 0.05:
                    ratio_Gate = 4
                
                if ratio_Kucoin > ratio_Kucoin_Temp and can_record_Kucoin and ratio_Kucoin > 0:
                    for i in range(ratio_Kucoin_Temp + 1, ratio_Kucoin + 1):
                        current_value = int(self.get_value("KC_" + ratio_order[i]))
                        self.change_value("KC_" + ratio_order[i], current_value+1)
                    ratio_Kucoin_Temp = ratio_Kucoin

                if ratio_Gate > ratio_Gate_Temp and can_record_Gate and ratio_Gate > 0:
                    for i in range(ratio_Gate_Temp + 1, ratio_Gate + 1):
                        current_value = int(self.get_value("GT_" + ratio_order[i]))
                        self.change_value("GT_" + ratio_order[i], current_value+1)
                    ratio_Gate_Temp = ratio_Gate

                # We can record a new arbitrage opportunity again when the ratio_order has dropped by at least two levels, which would correspond to the price impact of an arbitrage. 
                # This is done to avoid counting overly frequent oscillations between two consecutive ratio_order levels.
                # Example: If the ratio_order is 3 (spread between 3% and 5%), there needs to be a return to at least below +1% spread before recording another arbitrage opportunity.
                if ratio_Kucoin_Temp >= ratio_Kucoin + 2:
                    can_record_Kucoin = True
                    ratio_Kucoin_Temp = ratio_Kucoin

                if ratio_Kucoin_Temp == ratio_Kucoin + 1:
                    can_record_Kucoin = False

                if ratio_Gate_Temp >= ratio_Gate + 2:
                    can_record_Gate = True
                    ratio_Gate_Temp = ratio_Gate
                    
                if ratio_Gate_Temp == ratio_Gate + 1:
                    can_record_Gate = False

            except Exception as e:
                print(f"Error : {e}")
            
            time.sleep(self.time_sleep)