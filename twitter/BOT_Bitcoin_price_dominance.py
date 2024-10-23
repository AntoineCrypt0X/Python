import tweepy
import time
from tradingview_ta import TA_Handler, Interval, Exchange

api_key="your api_key"
api_key_secret="your api_key_secret"
bearer="your bearer"
access_token="your access_token"
access_token_secret="your access_token_secret"

autherticator= tweepy.OAuthHandler(api_key, api_key_secret)
autherticator.set_access_token(access_token, access_token_secret)
api = tweepy.API(autherticator)

#Get current price of a crypto
def current_price(coin, exchange):
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

#Save the fear and greed image
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

#FearandGreed()


#BOT that tweets every 30 minutes the bitcoin Dominance and BTC price
def BitcoinDominance():

    while True:

        try:
            lastPrice=current_price("BTC", "binance")
            message = "#Bitcoin Fear and Greed index\n\n" + "Current #BTC price is " + str(round(float(lastPrice))) + " $"
            message = message + "\n\n#Crypto #FearAndGreed\n\n"
            image = "yourPath/FearGreed.png"
            _media = api.media_upload(image)
            api.update_status(status=message, media_ids=[_media.media_id])

        except Exception as e1:
            print('error', e1)
            # return e1
            print("Already tweeted or error")

        time.sleep(1800)

BitcoinDominance()

