import tweepy
import time
import datetime
import openai

openai.api_key="YourOpenAIapi"
openai.organization = "YourOpenAIorganization"
openai.Model.list()

api_key="your api_key"
api_key_secret="your api_key_secret"
bearer="your bearer"
access_token="your access_token"
access_token_secret="your access_token_secret"

autherticator= tweepy.OAuthHandler(api_key, api_key_secret)
autherticator.set_access_token(access_token, access_token_secret)
api = tweepy.API(autherticator)

def firstreply(ListAccount):
    print(f"\n{datetime.datetime.now()}\n")

    delaybetweenAction = 1800

    treated_tweet_id=[]
    list_words_to_avoid = ["kill", "war", "ukrainian"]

    while True:

        for account in ListAccount:

            try:
                user = api.get_user(screen_name=account)
                lasttweet = api.user_timeline(user_id=user.id, count=1, exclude_replies=True, include_rts=False)

                for tweet in lasttweet:
                    if not tweet.id in treated_tweet_id:
                            textTweet=tweet.text
                            response = openai.Completion.create(
                                model="text-davinci-003",
                                #example
                                prompt="Is the subject of this tweet related to the crypto or blockchain sector?. If yes, reply 'Yes' and answer to this tweet with a positive manner. if not or if it is related to one of this list of topics " + str(list_words_to_avoid) + ", just say 'no':\n\n"+textTweet,
                                temperature=0.6,
                                max_tokens=100,
                                top_p=1.0,
                                frequency_penalty=0.0,
                                presence_penalty=0.0
                            )
                            reponse =response["choices"][0]["text"]
                            print("\n\n"+account)
                            print("tweeet Text :" + treated_tweet_id)
                            print('reponse: ' + reponse)

                            isno=False
                            Non=["no", "No"]
                            for e in Non:
                                if e in reponse[:5]:
                                    print('no answer')
                                    isno=True
                            
                            #if the tweet can be commented
                            if isno==False:
                                rep=reponse[6:]
                                api.update_status(status=rep, in_reply_to_status_id=tweet.id, auto_populate_reply_metadata=True)

                    treated_tweet_id.append(tweet.id)
                    time.sleep(delaybetweenAction)

            except Exception as e:
                print('error', e)
                # return e
                print("Already replied or error")

        print(str(treated_tweet_id))
        time.sleep(delaybetweenAction)

firstreply(["BitcoinMagazine","Ashcryptoreal","BTC_Archive"])


