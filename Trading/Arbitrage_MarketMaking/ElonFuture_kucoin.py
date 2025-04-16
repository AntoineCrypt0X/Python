import time
import tweepy
import datetime
import json, requests, time, base64, hmac, hashlib
from kucoin.client import Client
from uuid import uuid1

#Objective: Monitor Elon Musk's latest tweet every second. If the words "Bitcoin" or "Doge" appear in the tweet text or bio, take a long position in futures X100.

#Twitter API
api_key=""
api_key_secret=""
access_token=""
access_token_secret=""
bearer=""
autherticator= tweepy.OAuthHandler(api_key, api_key_secret)
autherticator.set_access_token(access_token, access_token_secret)
api = tweepy.API(autherticator)

#Kucoin API
api_key = ""
api_secret = ''
api_passphrase = ""
client = Client(api_key, api_secret, api_passphrase)

#Create a unique ID
def return_unique_id():
    id = ''.join([each for each in str(uuid1()).split('-')])
    return id
return_unique_id()

#Market order Future
def createMarketFuture(side, size, symbol, leverage, updown=None, typestop=None, pricestop=None):

    print(f"\n{datetime.datetime.now()}\n")
    url = 'https://api-futures.kucoin.com/api/v1/orders'

    clientoid=return_unique_id()
    print("clientoid: " + clientoid)
    now = int(time.time() * 1000)
    data = {
        "clientOid": clientoid,
        "side": side,
        "size": size,
        "symbol": symbol,
        "type": "market",
        "leverage": leverage,
    }
    if updown:
        data["stop"]=updown
    if typestop:
        data["stopPriceType"]=typestop
    if pricestop:
        data["stopPrice"]=pricestop

    data_json = json.dumps(data)
    str_to_sign = str(now) + 'POST' + '/api/v1/orders' + data_json
    signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())
    passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest())

    headers = {
        "KC-API-SIGN": signature,
        "KC-API-TIMESTAMP": str(now),
        "KC-API-KEY": api_key,
        "KC-API-PASSPHRASE": passphrase,
        "KC-API-KEY-VERSION": "2",
        "Content-Type": "application/json"
        # specifying content type or using json=data in request
    }
    response = requests.request('post', url, headers=headers, data=data_json)
    print(response.status_code)
    print(response)
    print(response.json())

    return clientoid

#Get a bio description
def description(username):

    user = api.get_user(screen_name=username)
    userinfo = dict(user._json)
    bio = userinfo["description"]
    #print("Bio : " + bio)
    return bio


def ElonMuskFutureTweet(username, words1, words2=None):

    print(f"\n{datetime.datetime.now()}\n")

    id_tweet_list=[]
    compteurTweetwords=0

    while True:

        try:
            boolwords1 = False
            boolwords2 = False
            user = api.get_user(screen_name=username)
            userinfo = dict(user._json)
            bio = userinfo["description"]
            lasttweet = api.user_timeline(user_id=user.id, count=1, exclude_replies=False, include_rts=True)

            for tweet in lasttweet:

                texte=tweet.text
                idtweet=tweet.id
                
                #words1
                for mot in words1:
                    if mot in bio.upper():
                        boolwords1=True
                    if idtweet not in id_tweet_list:
                        if mot in texte.upper():
                            boolwords1 = True
                            id_tweet_list.append(idtweet)
                            print("texte: " + texte)

                if boolwords1==True:
                    #createFuture
                    createMarketFuture("buy","1","XBTUSDTM","100")
                    print(" BTC future created!!!")
                    compteurTweetwords=compteurTweetwords+1

                #words2
                if words2:
                    for mot in words2:
                        if mot in bio.upper():
                            boolwords2 = True
                        if idtweet not in id_tweet_list:
                            if mot in texte.upper():
                                boolwords2 = True
                                id_tweet_list.append(idtweet)
                                print("texte: " + texte)

                    if boolwords2 == True:
                        # createFuture
                        createMarketFuture("buy", "8", "DOGEUSDTM", "20")
                        print(" DOGE future created!!!")
                        compteurTweetwords = compteurTweetwords + 1

        except Exception as e2:
            print('error', e2)

        print("Tweet with key words: " + str(compteurTweetwords))
        time.sleep(1.1)

ElonMuskFutureTweet('elonmusk', ["BTC", "CRYPTO", "BITCOIN"], ["DOGE", "DOGECOIN"])


