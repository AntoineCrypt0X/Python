import tweepy
import time
import datetime

api_key="your api_key"
api_key_secret="your api_key_secret"
bearer="your bearer"
access_token="your access_token"
access_token_secret="your access_token_secret"

autherticator= tweepy.OAuthHandler(api_key, api_key_secret)
autherticator.set_access_token(access_token, access_token_secret)
api = tweepy.API(autherticator)


# Retweet a tweet that contains a hashtag
#The Twitter API is subject to rate limits per minute and per hour. Check the latest updates to adjust the waiting times between each request.
def botRetweetHashtag(listHashtag):

    #parametres d'attente
    delaybetweenAction=1800
    api = tweepy.API(autherticator)
    lengthList=len(listHashtag)
    index=0

    while True:
        print(f"\n{datetime.datetime.utcnow()}\n")

        try:
            hashtag=listHashtag[index]
            search_query = "#" + hashtag + " -filter:retweets -filter:replies"
            # -filter:retweets
            tweets = tweepy.Cursor(api.search_tweets, q=search_query, lang="en").items(1)
        
            for tweet in tweets:
                print(tweet.text)
                api.retweet(tweet.id) 
                print('Comment\n')
                api.create_friendship(user_id=tweet.user.id)
                print('Account follow-up')

        except Exception as e1:
            print('error', e1)

        else:
            a = 1

        index = index + 1
        q, index = divmod(index, lengthList) #index reset to 0 if index>lengthList
        time.sleep(delaybetweenAction)

botRetweetHashtag(["Bitcoin","BTC","ETH","Crypto","Web3","NFT"])
