from tradingview_ta import TA_Handler, Interval, Exchange
from openpyxl import load_workbook
import pandas as pd

def current_priceUSDT(coin, exchange):

    try:
        tokenBTC = TA_Handler(
            symbol=coin+"USDT",
            screener="crypto",
            exchange=exchange,
            interval=Interval.INTERVAL_1_MINUTE
        )
        LastPriceBTC = tokenBTC.get_indicators()['open']
        #print(LastPriceBTC)
        return LastPriceBTC

    except Exception as e1:
        print('error', e1)

    return 0

#current_price("BTC","binance")

def GET_info_daily(coin, exchange):

    try:
        tokenBTC = TA_Handler(
            symbol=coin+"USDT",
            screener="crypto",
            exchange=exchange,
            interval=Interval.INTERVAL_1_DAY
        )
        info = tokenBTC.get_indicators()
        df_daily=pd.DataFrame([info])
        print(df_daily)
        return df_daily

    except Exception as e1:
        print('error', e1)

    return ""

def FearandGreed():
    try:
        rss_url = 'https://alternative.me/crypto/fear-and-greed-index.png'
        res = requests.get(rss_url, stream=True)
        if res.status_code == 200:
            with open("FearGreed.png", 'wb') as f:
                shutil.copyfileobj(res.raw, f)
            print('Image sucessfully Downloaded')
        else:
            print('Image Couldn\'t be retrieved')

    except Exception as e1:
        print('error', e1)
