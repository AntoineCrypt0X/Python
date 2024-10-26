import requests
import datetime

def MarketCap(crypto):
    # gets data from coingecko
    response = requests.get(
        'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false')
    response = response.json()

    MCap = 0

    # iterates through response
    for x in response:
        if x['id'] == crypto:  
            MCap = x['market_cap']
            print(MCap)
            return float(MCap)
    return 0


def MarketCapList(cryptos):
    # gets data from coingecko
    response = requests.get(
        'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false')
    response = response.json()

    ListMCap=[]
    for token in cryptos:
        # iterates through response
        for x in response:
            if x['id'] == token:
                ListMCap.append(x['market_cap'])

    print(ListMCap)
    return ListMCap


def dominance(crypto):

    # gets data from coingecko
    response = requests.get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false')
    response = response.json()

    MCap = 0
    altCap = 0

    # iterates through response
    for x in response:
        if x['id'] == crypto:
            MCap = x['market_cap']
            altCap = altCap + x['market_cap']
        else:  # adds any altcoin market cap to altCap
            altCap = altCap + x['market_cap']

    dominance="{:.2f}".format((MCap / altCap) * 100)
    print(dominance)
    return dominance

def totalMcap():
    # gets data from coingecko
    response = requests.get(
        'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false')
    response = response.json()

    altCap = 0

    # iterates through response
    for x in response:
        altCap += x['market_cap']
    print(f"{altCap:,}")
    return altCap


def GetTopRank(number):
    # gets data from coingecko
    response = requests.get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false')
    response = response.json()

    listTop=[]

    removeStable=["usdt","usdc","busd","dai", "tusd","usdd","gusd","usdp","steth","hbtc","reth"]

    for x in response:
        if float(x['market_cap_rank'])>number:
            break
        else:
            if x['symbol'] not in removeStable:
                listTop.append(x['symbol'].upper())
    print(listTop)
    return listTop


def getPrice(token):
    lastPrice=""
    try:
        token1M = TA_Handler(
            symbol=token+"USDT",
            screener="crypto",
            exchange="binance",
            interval=Interval.INTERVAL_1_MINUTE
        )

        lastPrice = token1M.get_indicators()['open']

    except Exception as e1:
        try:
            if str(e1)=="Exchange or symbol not found.":
                token1M = TA_Handler(
                    symbol=token + "USDT",
                    screener="crypto",
                    exchange="kucoin",
                    interval=Interval.INTERVAL_1_MINUTE
                )

                lastPrice = token1M.get_indicators()['open']

        except Exception as e2:
            try:
                if str(e1) == "Exchange or symbol not found.":
                    token1M = TA_Handler(
                        symbol=token + "USDT",
                        screener="crypto",
                        exchange="gateio",
                        interval=Interval.INTERVAL_1_MINUTE
                    )

                    lastPrice = token1M.get_indicators()['open']

            except Exception as e3:
                #print('error binance and kucoin and gate', e3)
                return 0

    print(lastPrice)
    return lastPrice


def getOpen(timescale, token):

    openPrice=""

    if timescale=="DAY":
        intervalle = Interval.INTERVAL_1_DAY
    elif timescale=="WEEK":
        intervalle = Interval.INTERVAL_1_WEEK
    elif timescale=="4H":
        intervalle = Interval.INTERVAL_4_HOURS
    else:
        intervalle = Interval.INTERVAL_1_DAY

    try:
        tokenData = TA_Handler(
            symbol=token+"USDT",
            screener="crypto",
            exchange="kucoin",
            interval=intervalle
        )
        openPrice = tokenData.get_indicators()['open']

    except Exception as e1:
        try:
            if str(e1) == "Exchange or symbol not found.":
                tokenData = TA_Handler(
                    symbol=token + "USDT",
                    screener="crypto",
                    exchange="kucoin",
                    interval=intervalle
                )
                openPrice = tokenData.get_indicators()['open']

        except Exception as e2:
            try:
                if str(e1) == "Exchange or symbol not found.":
                    tokenData = TA_Handler(
                        symbol=token + "USDT",
                        screener="crypto",
                        exchange="gateio",
                        interval=intervalle
                    )
                    openPrice = tokenData.get_indicators()['open']

            except Exception as e3:
                #print('error binance and kucoin and gate', e3)
                return None

    print(openPrice)
    return openPrice

#getOpen("DAY", 'OKB')

def getPerfarray(tabToken, timescale):
    perf={}
    for token in tabToken:
        price=getPrice(token)
        open=getOpen(timescale,token)
        if open!=None:
            perf[token]=round((float(price) - float(open)) / float(open)*100,2)
    print(perf)
    return perf

#getPerfarray(['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'DOGE', 'MATIC', 'OKB', 'SOL', 'DOT', 'SHIB'],"DAY")

def getTopPerf(rank, timescale, number):
    topRank=GetTopRank(rank)
    tabPerf=getPerfarray(topRank,timescale)

    tabTopToken=[]
    tabTopPerf={}

    while len(tabTopToken)<number:
        Top_perf = -99999
        Token_top=""
        for token in topRank:
            perf=float(tabPerf[token])
            if perf>Top_perf and token not in tabTopToken:
                Top_perf=perf
                Token_top=token

        tabTopToken.append(Token_top)
        tabTopPerf[Token_top]=Top_perf

    print(tabTopPerf)
    return tabTopPerf
#getTopPerf(50,"DAY",5)

def getFlopPerf(rank, timescale, number):
    topRank=GetTopRank(rank)
    tabPerf=getPerfarray(topRank,timescale)

    tabFlopToken=[]
    tabFlopPerf={}

    while len(tabFlopToken)<number:
        Top_perf = 99999
        Token_top=""
        for token in topRank:
            perf=float(tabPerf[token])
            if perf<Top_perf and token not in tabFlopToken:
                Top_perf=perf
                Token_top=token

        tabFlopToken.append(Token_top)
        tabFlopPerf[Token_top]=Top_perf

    print(tabFlopPerf)
    return tabFlopPerf
#getFlopPerf(50,"DAY",3)

