import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import asyncio
import aiohttp
import json
import ccxt.async_support as ccxt_async
import ccxt 
import ta
import plotly.express as px
import plotly.graph_objects as go
import time
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint
from sklearn.cluster import KMeans

def get_format_from_price(value):
    """
    Retourne un format '%.Nf' adapté à l'ordre de grandeur de la valeur.
    """
    if value >= 100:
        return "%.2f"
    elif value >= 1:
        return "%.4f"
    elif value >= 0.01:
        return "%.6f"
    else:
        return "%.8f"

# Récupère les données de CoinGecko de manière asynchrone
async def fetch_crypto_data(num_cryptos):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "price_change_percentage": "1h,24h,7d,14d,30d,200d,1y",
                "per_page": num_cryptos,
                "page": 1,
            },
        ) as response:
            data = await response.json()
            df = pd.DataFrame(data)
            # Conversion des symboles en majuscules
            df["symbol"] = df["symbol"].str.upper()
            # Filtrage des stablecoins USD
            df = df[~df["symbol"].str.startswith("USD")]
            return df

# Récupère les données OHLCV pour une seule paire
async def fetch_single_ohlcv(exchange, symbol, timeframe, limit, base):

    interval_in_ms = {
        "5m": 5 * 60 * 1000,
        "15m": 15 * 60 * 1000,
        "30m": 30 * 60 * 1000,
        "1h": 60 * 60 * 1000,
        "2h": 2 * 60 * 60 * 1000,
        "4h": 4 * 60 * 60 * 1000,
        "1d": 24 * 60 * 60 * 1000,
        "1w": 7 * 24 * 60 * 60 * 1000,
    }[timeframe]

    try:
        now = exchange.milliseconds()
        since = now - limit * interval_in_ms

        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
        df = pd.DataFrame(
            ohlcv,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        df["symbol"] = base
        
        # Calcul des bandes de Bollinger
        df["bb_middle"] = ta.volatility.bollinger_mavg(df["close"], window=20)
        df["bb_upper"] = ta.volatility.bollinger_hband(df["close"], window=20)
        df["bb_lower"] = ta.volatility.bollinger_lband(df["close"], window=20)

        # Calcul de l'EMA 50 et de l'écart en pourcentage
        df["ema_50"] = ta.trend.ema_indicator(df["close"], window=50)
        df["ema_50_gap"] = ((df["close"] - df["ema_50"]) / df["ema_50"]) * 100
        
        # Calcul de l'EMA 200 et de l'écart en pourcentage
        df["ema_200"] = ta.trend.ema_indicator(df["close"], window=200)
        df["ema_200_gap"] = ((df["close"] - df["ema_200"]) / df["ema_200"]) * 100
        
        # Vérification si le prix est dans les bandes
        df["in_bollinger_bands"] = (df["close"] <= df["bb_upper"]) & (df["close"] >= df["bb_lower"])
        return df
    except Exception as e:
        print(f"Erreur lors de la recuperation des donnees pour {symbol}: {e}")
        return None

# Récupère les bougies OHLCV pour chaque paire spot en USDT de manière concurrente
async def fetch_ohlcv_for_cryptos(crypto_list, timeframe="1d", limit=200):
    """
        Récupère les bougies OHLCV pour chaque paire spot en USDT de manière concurrente.

        Parameters:
            crypto_list (list): Liste de chaînes de caractères représentant les cryptomonnaies recherchées (ex. ['BTC', 'ETH']).
            timeframe (str): La période de temps des bougies (ex. '1h', '1d', etc.).
            limit (int): Le nombre maximum de bougies à récupérer.

        Returns:
            DataFrame: Un DataFrame contenant les dernières données OHLCV pour chaque paire.
    """
    exchange = ccxt_async.binance(  # Utilisation de ccxt_async ici
        {
            "enableRateLimit": True,
        }
    )

    try:
        await exchange.load_markets()
        tasks = []

        # Création des tâches pour chaque paire valide
        for symbol, market in exchange.markets.items():
            if (
                market.get("spot", False)
                and market.get("quote") == "USDT"
                and market.get("base") in crypto_list
            ):
                print(f"Preparation de la recuperation pour {symbol}...")
                tasks.append(
                    fetch_single_ohlcv(
                        exchange, symbol, timeframe, limit, market.get("base")
                    )
                )

        # Exécution concurrente de toutes les tâches
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Traitement des résultats
        valid_results = []
        for df in results:
            if df is not None and not isinstance(df, Exception) and df.shape[0] !=0 :
                df["rsi_14"] = ta.momentum.rsi(df["close"], window=14)
                df["return"] = df["close"].pct_change()
                last_row = df.iloc[-1]
                mean_return = df["return"].mean()
                std_return = df["return"].std()
                sharpe_ratio = (365**0.5) * (mean_return / std_return)
                valid_results.append(
                    last_row.to_dict()
                    | {
                        "sharpe_ratio": sharpe_ratio,
                        "mean_return": mean_return * 100,
                        "std_return": std_return * 100,
                        "in_bollinger_bands": last_row["in_bollinger_bands"],
                        "ema_50_gap": last_row["ema_50_gap"],
                        "ema_200_gap": last_row["ema_200_gap"]
                    }
                )

        return pd.DataFrame(valid_results)

    finally:
        await exchange.close()


async def fetch_ohlcv_histo(crypto1, crypto2, timeframe="1d", limit=500):
    """
        Récupère les bougies OHLCV pour les deux cryptos en parametre.

        Parameters:
            crypto1.
            crypto2.
            timeframe (str): La période de temps des bougies (ex. '1h', '1d', etc.).
            limit (int): Le nombre maximum de bougies à récupérer.

        Returns:
            DataFrame: Un DataFrame contenant les l'historique des prix des deux cryptos
    """
    exchange = ccxt_async.binance(  # Utilisation de ccxt_async ici
        {
            "enableRateLimit": True,
        }
    )

    try:
        await exchange.load_markets()
        tasks = []

        # Création des tâches pour chaque paire valide
        for symbol, market in exchange.markets.items():
            if (
                market.get("spot", False)
                and market.get("quote") == "USDT"
                and market.get("base") in [crypto1, crypto2]
            ):
                print(f"Preparation de la recuperation pour {symbol}...")
                tasks.append(
                    fetch_single_ohlcv(
                        exchange, symbol, timeframe, limit, market.get("base")
                    )
                )

        # Exécution concurrente de toutes les tâches
        results = await asyncio.gather(*tasks, return_exceptions=True)

        dfs = []
        for r, market in zip(results, [crypto1, crypto2]):
            if isinstance(r, pd.DataFrame):
                df = pd.DataFrame(r, columns=["timestamp", "open", "high", "low", "close", "volume"])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                df[f"pct_change_{market}"] = df["close"].pct_change()*100
                df[f"evolve_3_periods_{market}"] = ((df["close"].shift(-3) - df["close"])/df["close"])*100
                df[f"evolve_10_periods_{market}"] = ((df["close"].shift(-10) - df["close"])/df["close"])*100
                df = df.set_index("timestamp")
                df = df[["close", f"pct_change_{market}",f"evolve_3_periods_{market}",f"evolve_10_periods_{market}"]].rename(columns={"close": market})
                dfs.append(df)
        #print(dfs)
        if len(dfs) != 2:
            raise ValueError("Impossible de récupérer les deux cryptos.")

        df_merged = pd.merge(dfs[0], dfs[1], left_index=True, right_index=True)

        return df_merged
    
    finally:
        await exchange.close()

async def fetch_ohlcv_close_from_list(symbols, timeframe="1d", limit=500):
    """
    Récupère uniquement les prix de clôture (close) pour une liste de cryptos.

    Parameters:
        symbols (list): Liste des symboles à récupérer (ex. ['BTC', 'ETH']).
        timeframe (str): La période de temps des bougies (ex. '1h', '1d', etc.).
        limit (int): Le nombre maximum de bougies à récupérer.

    Returns:
        DataFrame: Un DataFrame contenant les colonnes 'close' pour chaque symbole.
    """
    exchange = ccxt_async.binance({
        "enableRateLimit": True,
    })

    try:
        await exchange.load_markets()
        tasks = []

        # Création des tâches pour chaque crypto
        for symbol, market in exchange.markets.items():
            if (
                market.get("spot", False)
                and market.get("quote") == "USDT"
                and market.get("base") in symbols
            ):
                print(f"Préparation de la récupération pour {symbol}...")
                tasks.append(
                    fetch_single_ohlcv(
                        exchange, symbol, timeframe, limit, market.get("base")
                    )
                )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        dfs = []
        for r, symbol in zip(results, symbols):
            if isinstance(r, pd.DataFrame) and not r.empty:
                df = pd.DataFrame(r, columns=["timestamp", "open", "high", "low", "close", "volume"])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                df = df.set_index("timestamp")
                df = df[["close"]].rename(columns={"close": symbol})  # Renomme "close" en symbole
                dfs.append(df)
        
        # Fusion de tous les DataFrames sur l'index (timestamp)
        df_merged = dfs[0]
        for df in dfs[1:]:
            # Vérifie que les timestamps sont du même type (et non vides)
            if df.shape[0]==0:
                continue
            # Fusionne
            df_merged = df_merged.merge(df, left_index=True, right_index=True, how="outer")

        return df_merged

    finally:
        await exchange.close()

# Fonction principale pour obtenir les données de crypto
@st.cache_data(ttl=60)
def get_crypto_data(num_cryptos):
    return asyncio.run(fetch_crypto_data(num_cryptos))

# Fonction principale pour récupérer les données OHLCV pour une liste de cryptos
@st.cache_data(ttl=3600)
def fetch_ohlcv_for_cryptos_sync(crypto_list, timeframe="1d", limit=200):
    return asyncio.run(fetch_ohlcv_for_cryptos(crypto_list, timeframe, limit))

@st.cache_data(ttl=3600)
def fetch_ohlcv_histo_sync(crypto1, crypto2, timeframe="1d", limit=500):
    return asyncio.run(fetch_ohlcv_histo(crypto1, crypto2, timeframe, limit))

@st.cache_data(ttl=3600)
def fetch_ohlcv_histo_list_sync(list_crypto, timeframe="1d", limit=500):
    return asyncio.run(fetch_ohlcv_close_from_list(list_crypto, timeframe, limit))

def aggregate_crypto_data(df_coingecko, df_binance):
    """
    Agrège les données de CoinGecko et binance en un seul DataFrame.

    Parameters:
        df_coingecko (DataFrame): Données de CoinGecko
        df_binance (DataFrame): Données de binance

    Returns:
        DataFrame: DataFrame agrégé contenant les données des deux sources
    """
    # Sélection des colonnes pertinentes de CoinGecko
    df_coingecko_clean = df_coingecko[
        [
            "symbol",
            "name",
            "image",
            "market_cap_rank",
            "current_price",
            "market_cap",
            "total_volume",
            "ath",
            "ath_change_percentage",
            "price_change_percentage_24h_in_currency",
            "price_change_percentage_7d_in_currency",
            "price_change_percentage_14d_in_currency",
            "price_change_percentage_30d_in_currency",
            "price_change_percentage_200d_in_currency",
            "price_change_percentage_1y_in_currency",
        ]
    ].copy()

    # Conversion de la market cap en millions
    df_coingecko_clean["market_cap"] = df_coingecko_clean["market_cap"] / 1_000_000

    # Renommage des colonnes de binance pour éviter les conflits
    df_binance_clean = df_binance[["symbol", "close", "rsi_14", "sharpe_ratio", "mean_return", "std_return", "in_bollinger_bands", "ema_50_gap", "ema_200_gap"]].copy()

    # Conversion du booléen en texte pour les bandes de Bollinger
    df_binance_clean["in_bollinger_bands"] = df_binance_clean["in_bollinger_bands"].map({True: "Oui", False: "Non"})

    # Fusion des DataFrames sur la colonne symbol
    df_merged = pd.merge(df_coingecko_clean, df_binance_clean, on="symbol", how="right")
    df_merged = df_merged.sort_values(by="market_cap", ascending=False)

    return df_merged

def rolling_beta(x, y, _crypto1, window):
    betas = []
    for i in range(len(x)):
        if i < window:
            betas.append(None)
        else:
            x_window = x.iloc[i - window:i]
            y_window = y.iloc[i - window:i]
            x_const = sm.add_constant(x_window)
            model = sm.OLS(y_window, x_const).fit()
            betas.append(model.params[_crypto1])  # La pente uniquement
    return pd.Series(betas, index=x.index)

def rolling_spread_log(x, y, window):
    """
    Calcule le spread logarithmique glissant entre deux séries de prix.

    Paramètres :
    - x : pd.Series — prix du premier actif (ex: close_1)
    - y : pd.Series — prix du deuxième actif (ex: close_2)
    - window : int — taille de la fenêtre glissante

    Retour :
    - spread_log : pd.Series — spread log glissant (log-rendement relatif)
    """
    rol_x = x.shift(periods=window)
    rol_y = y.shift(periods=window)

    spread_log = np.log10(x / rol_x) - np.log10(y / rol_y)
    return spread_log

@st.cache_data(ttl=15)
def create_cluster(df, symbols, nb_cluster):

    full_df = pd.DataFrame()

    for symbol in symbols:
        full_df[symbol] = df[symbol]
        cumret = np.log(full_df).diff().cumsum()+1 # calculate cumulative returns

        threshold = len(cumret) * 0.2 #supprimer les colonnes avec plus de 20% de NaN
        cumret = cumret.loc[:, cumret.isna().sum() <= threshold]
        cumret = cumret.dropna(axis=0)

        pre_select_obj = {}
        for col in list(cumret.columns.values):
            if not cumret[col].isna().all():
                pre_select_obj[col] = {
                    "return": cumret[col].iloc[-1] - cumret[col].iloc[0],
                    "std": cumret[col].std()
                }

    #pre_select_obj
    df_pre_select = pd.DataFrame.from_dict(pre_select_obj, orient='index')

    # Application du KMeans
    kmeans = KMeans(n_clusters=nb_cluster, n_init="auto").fit(df_pre_select)
    centroids = kmeans.cluster_centers_

    # Ajout des labels dans le DataFrame
    df_clustered = df_pre_select.copy()
    #df_clustered.drop(columns=["symbol"], inplace=True)
    df_clustered["cluster"] = kmeans.labels_
    df_clustered["symbol"] = df_clustered.index

    return df_pre_select, df_clustered, centroids
        


def main():
    st.set_page_config(page_title="Crypto Dashboard", layout="wide")

    # Logo dans la barre latérale
    st.sidebar.image("https://static.vecteezy.com/system/resources/previews/021/016/948/original/trading-icon-trading-graphic-symbol-trade-logo-design-trade-mark-logo-vector.jpg",width=100)

    # Barre latérale pour la navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Sélectionnez une page:", ["Correlation/Cointegration", "Metrics", "Clustering"])

    if page == "Metrics":
        
        html = """
    <div class="tradingview-widget-container" >
    <div class="tradingview-widget-container__widget"></div>
    <div class="tradingview-widget-copyright"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
    {
    "symbols": [
        {
        "proName": "BITSTAMP:BTCUSD",
        "title": "Bitcoin"
        },
        {
        "proName": "BITSTAMP:ETHUSD",
        "title": "Ethereum"
        },
        {
        "description": "BNB",
        "proName": "BINANCE:BNBUSDT"
        }
    ],
    "showSymbolLogo": true,
    "isTransparent": false,
    "displayMode": "adaptive",
    "colorTheme": "dark",
    "locale": "en"
    }
    </script>
    </div>
    """

        # Intégration avec Streamlit Components pour afficher le HTML/Javascript
        components.html(html, height=100)

        # Création de 4 colonnes pour les sélecteurs
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        # Sélection du nombre de cryptos
        with col1:
            num_cryptos = st.selectbox(
                "Nombre de cryptomonnaies",
                options=[("Top 10", 10), ("Top 50", 50), ("Top 100", 100), ("Top 200", 200)],
                format_func=lambda x: x[0],
                index=1
            )

        _timeframe = "1d"
        _periods = 200
        # Chargement initial des données
        with st.spinner(f"Chargement des {num_cryptos[0]} cryptomonnaies..."):
            df_coingecko_initial = get_crypto_data(num_cryptos[1])
            df_binance_initial = fetch_ohlcv_for_cryptos_sync(df_coingecko_initial["symbol"].tolist(), timeframe=_timeframe, limit=_periods)
            df_merged_initial = aggregate_crypto_data(df_coingecko_initial, df_binance_initial)
        
        # Sélection multiple pour exclure des cryptos
        with col2:
            cryptos_to_exclude = st.multiselect(
                "Exclure des cryptomonnaies (optionnel)",
                options=df_coingecko_initial['symbol'].tolist(),
                help="Sélectionnez les cryptomonnaies à exclure du tableau et des graphiques"
            )

        with col3:
            _timeframe = st.selectbox(
                "Timeframe",
                options=["5m", "15m", "30m","1h", "2h", "4h", "1d", "1w"],
                index=3
            )

        with col4:
            _periods = st.selectbox(
                "Nombre historique periodes",
                options=[7,15,30,50,100,200,500,1000],
                index=5
            )
        
        with st.spinner(f"Chargement nombre periodes {_periods} "):
            df_coingecko_initial = get_crypto_data(num_cryptos[1])
            df_binance_initial = fetch_ohlcv_for_cryptos_sync(df_coingecko_initial["symbol"].tolist(), timeframe=_timeframe, limit=_periods)
            df_merged_initial = aggregate_crypto_data(df_coingecko_initial, df_binance_initial)

        # Contenu principal
        st.title("Tableau de bord Crypto (ohlcv: Binance data)")

        # Filtrage des données sans recharger
        df_merged = df_merged_initial[~df_merged_initial['symbol'].isin(cryptos_to_exclude)].copy()

        # Configuration des colonnes pour les données fusionnées
        merged_config = {
            "image": st.column_config.ImageColumn("", help="Logo de la cryptomonnaie", pinned=True),
            "market_cap_rank": st.column_config.NumberColumn(
                "Rang", 
                help="Classement par capitalisation boursière",
                step=1
            ),
            "symbol": st.column_config.TextColumn("Symbole"),
            "name": "Nom",
            "market_cap": st.column_config.NumberColumn(
                "Market Cap", 
                help="Capitalisation boursière en millions USD",
                format="$ %d M",
                step=1
            ),
            "current_price": st.column_config.NumberColumn(
                "Prix", 
                format="$ %.2f",
                step=0.01
            ),
            "ath": st.column_config.NumberColumn(
                "ATH", 
                format="$ %.2f",
                step=0.01
            ),
            "ath_change_percentage": st.column_config.NumberColumn(
                "Distance à l'ATH", format="%.2f%%"
            ),
            "rsi_14": st.column_config.NumberColumn("RSI 14", format="%.2f"),
            "in_bollinger_bands": st.column_config.TextColumn(
                "Dans les BB",
                help="Indique si le prix est à l'intérieur des bandes de Bollinger (20,2)"
            ),
            "ema_50_gap": st.column_config.NumberColumn(
                "Écart EMA 50", 
                format="%.2f%%",
                help="Écart en pourcentage entre le prix actuel et l'EMA 50"
            ),
            "ema_200_gap": st.column_config.NumberColumn(
                "Écart EMA 200", 
                format="%.2f%%",
                help="Écart en pourcentage entre le prix actuel et l'EMA 200"
            ),
            "sharpe_ratio": st.column_config.NumberColumn("Sharpe Ratio", format="%.2f"),
            "mean_return": st.column_config.NumberColumn(
                "Moyenne rendements", format="%.2f%%"
            ),
            "std_return": st.column_config.NumberColumn(
                "Écart-type rendements", format="%.2f%%"
            ),
            "price_change_percentage_24h_in_currency": st.column_config.NumberColumn(
                "Variation 24h", format="%.2f%%"
            ),
            "price_change_percentage_7d_in_currency": st.column_config.NumberColumn(
                "Variation 7j", format="%.2f%%"
            ),
            "price_change_percentage_14d_in_currency": st.column_config.NumberColumn(
                "Variation 14j", format="%.2f%%"
            ),
            "price_change_percentage_30d_in_currency": st.column_config.NumberColumn(
                "Variation 30j", format="%.2f%%"
            ),
            "price_change_percentage_200d_in_currency": st.column_config.NumberColumn(
                "Variation 200j", format="%.2f%%"
            ),
            "price_change_percentage_1y_in_currency": st.column_config.NumberColumn(
                "Variation 1an", format="%.2f%%"
            )
        }

    
        # Dictionnaire de correspondance pour les noms des colonnes
        column_names = {
            "market_cap_rank": "Rang",
            "current_price": "Prix",
            "market_cap": "Market Cap",
            "ath": "ATH",
            "ath_change_percentage": "Distance à l'ATH",
            "rsi_14": "RSI 14",
            "ema_50_gap": "Écart EMA 50",
            "ema_200_gap": "Écart EMA 200",
            "sharpe_ratio": "Sharpe Ratio",
            "mean_return": "Moyenne rendements",
            "std_return": "Écart-type rendements",
            "price_change_percentage_24h_in_currency": "Variation 24h",
            "price_change_percentage_7d_in_currency": "Variation 7j",
            "price_change_percentage_14d_in_currency": "Variation 14j",
            "price_change_percentage_30d_in_currency": "Variation 30j",
            "price_change_percentage_200d_in_currency": "Variation 200j",
            "price_change_percentage_1y_in_currency": "Variation 1an"
        }

        # Application du style conditionnel pour plusieurs colonnes
        def color_bollinger(val):
            if val == "Oui":
                return 'background-color: #90EE90'
            elif val == "Non":
                return 'background-color: #FFB6C1'
            return ''

        def color_rsi(val):
            try:
                val = float(val)
                if val > 70:
                    return 'background-color: #90EE90'
                elif val < 30:
                    return 'background-color: #FFB6C1'
            except:
                pass
            return ''

        def color_percentage(val):
            try:
                val = float(val)
                if val > 0:
                    return 'background-color: #90EE90'
                elif val < 0:
                    return 'background-color: #FFB6C1'
            except:
                pass
            return ''

        # Application du style
        df_styled = df_merged.style\
            .map(color_bollinger, subset=['in_bollinger_bands'])\
            .map(color_rsi, subset=['rsi_14'])\
            .map(color_percentage, subset=[col for col in df_merged.columns if 'price_change_percentage' in col])\
            .map(color_percentage, subset=['ema_200_gap'])\
            .map(color_percentage, subset=['ema_50_gap'])

        st.dataframe(
            df_styled,
            column_config=merged_config,
            column_order=list(merged_config.keys()),
            hide_index=True,
            use_container_width=True,
        )

        # Colonnes numériques disponibles pour les graphiques
        numeric_columns = df_merged.select_dtypes(include=["float64", "int64"]).columns.tolist()

        # Section pour le Scatter Plot
        st.subheader("Graphique de Dispersion")
        col1, col2 = st.columns(2)

        with col1:
            x_column = st.selectbox(
                "Choisir la variable X",
                options=numeric_columns,
                format_func=lambda x: column_names.get(x, x),
                index=(
                    numeric_columns.index("mean_return")
                    if "mean_return" in numeric_columns
                    else 0
                ),
            )

        with col2:
            y_column = st.selectbox(
                "Choisir la variable Y",
                options=numeric_columns,
                format_func=lambda x: column_names.get(x, x),
                index=(
                    numeric_columns.index("std_return")
                    if "std_return" in numeric_columns
                    else 0
                ),
            )

        # Création du scatter plot avec les noms d'affichage
        fig_scatter = px.scatter(
            df_merged,
            x=x_column,
            y=y_column,
            text="symbol",
            title=f"Relation entre {column_names.get(x_column, x_column)} et {column_names.get(y_column, y_column)}",
            template="plotly_dark",
            color="symbol",
            color_discrete_sequence=px.colors.qualitative.Set3,
            hover_data=["name", x_column, y_column]
        )

        # Ajustement du texte au-dessus des points
        fig_scatter.update_traces(
            textposition="top center",
            marker=dict(size=12, line=dict(width=1, color='white'))
        )
        
        # Personnalisation du layout
        fig_scatter.update_layout(
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        # Affichage du scatter plot
        st.plotly_chart(fig_scatter, use_container_width=True)

        # Section pour le Bar Plot
        st.subheader("Graphique en Barres")

        y_column_bar = st.selectbox(
            "Choisir la variable à afficher",
            options=numeric_columns,
            format_func=lambda x: column_names.get(x, x),
            index=numeric_columns.index("rsi_14") if "rsi_14" in numeric_columns else 0,
        )

        # Création du bar plot avec le nom d'affichage
        fig_bar = px.bar(
            df_merged,
            x="symbol",
            y=y_column_bar,
            title=f"{column_names.get(y_column_bar, y_column_bar)} par Crypto",
            template="plotly_dark",
            text_auto=".2s",
            color=y_column_bar,
            color_continuous_scale="Viridis",
            hover_data=["name", y_column_bar]
        )

        # Personnalisation du bar plot
        fig_bar.update_traces(
            textposition="outside",
            textfont=dict(color="white"),
        )
        
        # Personnalisation du layout
        fig_bar.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            coloraxis_colorbar_title="Valeur"
        )
        
        # Affichage du bar plot
        st.plotly_chart(fig_bar, use_container_width=True)

    if page == "Correlation/Cointegration":
        st.subheader("Correlation / Cointegration")

        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        _timeframe = "4h"
        _periods = 500
        _crypto1="BTC"
        _crypto2="ETH"
        format1 = "%.2f"
        format2 = "%.2f"

        with st.spinner(f"Chargement data"):
            df_coingecko_initial = get_crypto_data(150)
            df_binance_initial = fetch_ohlcv_for_cryptos_sync(df_coingecko_initial["symbol"].tolist(), timeframe=_timeframe, limit=_periods)
            df_merged_initial = aggregate_crypto_data(df_coingecko_initial, df_binance_initial)
            df_histo = fetch_ohlcv_histo_sync(_crypto1, _crypto2, _timeframe, _periods)
            price1 = df_histo[_crypto1].dropna().iloc[-1]
            price2 = df_histo[_crypto2].dropna().iloc[-1]
            format1 = get_format_from_price(price1)
            format2 = get_format_from_price(price2)

        with col1:
            _crypto1 = st.selectbox(
                "Crypto 1",
                options=df_merged_initial['symbol'].tolist(),
                index = 0
            )
        
        with col2:
            _crypto2 = st.selectbox(
                "Crypto 2",
                options=df_merged_initial['symbol'].tolist(),
                index = 1
            )

        with col3:
            _timeframe = st.selectbox(
                "Timeframe",
                options=["5m", "15m", "30m","1h", "2h", "4h", "1d", "1w"],
                index=5
            )

        with col4:
            _periods = st.selectbox(
                "Nombre historique periodes",
                options=[7,15,30,50,100,200,500,1000,2000],
                index=6
            )

        with st.spinner(f"Chargement data"):
            df_coingecko_initial = get_crypto_data(150)
            df_binance_initial = fetch_ohlcv_for_cryptos_sync(df_coingecko_initial["symbol"].tolist(), timeframe=_timeframe, limit=_periods)
            df_merged_initial = aggregate_crypto_data(df_coingecko_initial, df_binance_initial)
            df_histo = fetch_ohlcv_histo_sync(_crypto1, _crypto2, _timeframe, _periods)
            price1 = df_histo[_crypto1].dropna().iloc[-1]
            price2 = df_histo[_crypto2].dropna().iloc[-1]
            format1 = get_format_from_price(price1)
            format2 = get_format_from_price(price2)

        merged_config = {
            _crypto1: st.column_config.NumberColumn(
                _crypto1, 
                format=format1,
                help="Historique de la crypto 1"
            ),
            f"pct_change_{_crypto1}": st.column_config.NumberColumn(
                f"pct_change_{_crypto1}", 
                format="%.2f%%",
                help="Percentage return crypto 1"
            ),
            f"evolve_3_periods_{_crypto1}": st.column_config.NumberColumn(
                f"evolve_3_periods_{_crypto1}", 
                format="%.2f%%",
                help="Evolution dans 3 periodes"
            ),
            f"evolve_10_periods_{_crypto1}": st.column_config.NumberColumn(
                f"evolve_10_periods_{_crypto1}", 
                format="%.2f%%",
                help="Evolution dans 10 periodes"
            ),
            _crypto2: st.column_config.NumberColumn(
                _crypto2, 
                format=format2,
                help="Historique de la crypto 2"
            ),
            f"pct_change_{_crypto2}": st.column_config.NumberColumn(
                f"pct_change_{_crypto2}", 
                format="%.2f%%",
                help="Percentage return crypto 1"
            ),
            f"evolve_3_periods_{_crypto2}": st.column_config.NumberColumn(
                f"evolve_3_periods_{_crypto2}", 
                format="%.2f%%",
                help="Evolution dans 3 periodes"
            ),
            f"evolve_10_periods_{_crypto2}": st.column_config.NumberColumn(
                f"evolve_10_periods_{_crypto2}", 
                format="%.2f%%",
                help="Evolution dans 10 periodes"
            ),
        }

        st.dataframe(
            df_histo,
            column_config=merged_config,
            column_order=list(merged_config.keys()),
            hide_index=False,
            use_container_width=True,
        )

        fig_line = px.line(
            df_histo,  # DataFrame contenant les données
            x=df_histo.index,  # Colonne pour l'axe x
            y=df_histo[_crypto1],  # Première courbe, associée à l'axe Y principal
            labels={_crypto1: f'{_crypto1}', _crypto2: f'{_crypto2}'}
        )

        fig_line.update_traces(
            name=_crypto1,  # Nom pour la légende de la première courbe
            line=dict(color='orange'), 
            showlegend=True 
        )

        # Ajouter la deuxième courbe avec un axe Y secondaire
        fig_line.add_scatter(
            x=df_histo.index,  # Utiliser le même axe X
            y=df_histo[_crypto2],  # Deuxième courbe
            mode='lines',  # Mode de ligne
            name=_crypto2,  # Nom de la courbe
            yaxis="y2"  # Spécifie que cette courbe doit utiliser l'axe Y secondaire
        )

        # Mise à jour du layout pour configurer les axes
        fig_line.update_layout(
            title="Price chart",
            xaxis_title="Date",  # Par exemple si c'est une série temporelle
            yaxis_title=f'{_crypto1}',  # Titre de l'axe Y principal
            yaxis2=dict(
                title=f'{_crypto2}',  # Titre de l'axe Y secondaire
                overlaying="y",  # Superpose le deuxième axe Y avec le premier
                side="right"  # Place le deuxième axe à droite
            )
        )

        # Affichage du graphique avec Streamlit
        st.plotly_chart(fig_line, use_container_width=True)

        st.subheader("1. Etudes sur les prix")
        correlation = df_histo[_crypto1].corr(df_histo[_crypto2])
        score, p_value, _ = coint(df_histo[_crypto1], df_histo[_crypto2])

        _crypto1_with_const = sm.add_constant(df_histo[_crypto1])
        if isinstance(_crypto1_with_const, pd.Series):
            _crypto1_with_const = _crypto1_with_const.to_frame()
        # Modèle de régression linéaire Y = beta * X + epsilon
        model = sm.OLS(df_histo[_crypto2].iloc[:], _crypto1_with_const.iloc[:]).fit()
        beta = model.params[_crypto1]
        alpha = model.params['const']
        _crypto2_pred = model.predict(_crypto1_with_const)

        score_beta, p_value_beta, _ = coint(df_histo[_crypto1]*beta, df_histo[_crypto2])

        # Affichage des résultats dans Streamlit
        st.write(f"**Corrélation entre {_crypto1} et {_crypto2}** : {correlation:.4f}")
        st.write(f"**Régression linéaire** entre {_crypto1} et {_crypto2}: Pente (β) : {beta:.4f}, Intercept (α) : {alpha:.4f}")
        #st.write(f"**Test de cointégration (p-value)** entre {_crypto1} et {_crypto2} : {p_value:.4f}")
        st.write(f"**Test de Cointégration (p-value)** entre {beta:.4f}*{_crypto1} et {_crypto2} : {p_value_beta:.4f}")

        fig_scatter = px.scatter(
            df_histo,
            x=_crypto1,  # Axe x : crypto1
            y=_crypto2,  # Axe y : crypto2
            title=f"Scatter plot des prix entre {_crypto1} et {_crypto2}",
            labels={_crypto1: f"{_crypto1}", _crypto2: f"{_crypto2}"},
            template="plotly_dark",  # Utilisation du thème noir (si tu veux)
        )

        # Ajouter la droite de régression
        fig_scatter.add_scatter(
            x=df_histo[_crypto1], 
            y=_crypto2_pred, 
            mode='lines',  # Tracer la droite
            name=f"Droite de régression: {beta:.4f}x + {alpha:.4f}", 
            line=dict(color='red', width=2)
        )

        # Affichage du graphique avec Streamlit
        st.plotly_chart(fig_scatter, use_container_width=True)

        ####
        # ZSCORE
        ####
        st.subheader("1.1. Zscore avec moyenne, std et beta glissants")
        #Zscore avec moyenne, std et beta glissants
        col1_zscore= st.columns(1)[0]
        with col1_zscore:
            _wd = st.selectbox(
                "Window zscore",
                options=[7,10,24,30,50,100,200],
                index=2
            )
        beta_series = rolling_beta(df_histo[_crypto1], df_histo[_crypto2], _crypto1, window=_wd)
        #beta_series
        spread = df_histo[_crypto2] - beta_series * df_histo[_crypto1]
        spread_mean_wd = pd.Series(spread).rolling(window=_wd).mean()
        spread_std_wd = pd.Series(spread).rolling(window=_wd).std()
        zscore_wd = (spread - spread_mean_wd) / spread_std_wd
        #zscore_wd
        # Créer un DataFrame pour tracer avec Plotly Express
        df_plot_wd = pd.DataFrame({
            "Index": zscore_wd.index,
            "Z-score": zscore_wd
        })

        # Tracer avec Plotly Express
        fig = px.line(df_plot_wd, x="Index", y="Z-score", title=f"Z-score du spread (Moyenne, volatilite et Beta glissants {_wd} periodes)")

        # Ajouter les lignes horizontales pour les seuils ±2
        fig.add_hline(y=2, line_dash="dash", line_color="red", annotation_text="z = 2", annotation_position="top left")
        fig.add_hline(y=-2, line_dash="dash", line_color="green", annotation_text="z = -2", annotation_position="bottom left")

        # Affichage dans Streamlit
        st.plotly_chart(fig, use_container_width=True)

        # Histogramme avec Plotly Express
        fig_hist = px.histogram(df_plot_wd, x="Z-score", nbins=50, title="Distribution du Z-score", color_discrete_sequence=["skyblue"])
        fig_hist.update_traces(marker_line_color="black", marker_line_width=1.2)
        # Affichage dans Streamlit
        st.plotly_chart(fig_hist, use_container_width=True)

        #Z-SCORE avec moyeen et std globales (sur tout l'historique)
        st.subheader("1.2. Zscore avec moyenne, std et beta globaux")
        spread = df_histo[_crypto2] - beta * df_histo[_crypto1]
        spread_mean = spread.mean()
        spread_std = spread.std()
        # Z-score global
        zscore = (spread - spread_mean) / spread_std

        # Créer un DataFrame pour tracer avec Plotly Express
        df_plot = pd.DataFrame({
            "Index": zscore.index,
            "Z-score": zscore
        })

        # Tracer avec Plotly Express
        fig = px.line(df_plot, x="Index", y="Z-score", title=f"Z-score du spread (Moyenne, volatilite et Beta globaux {_periods} periodes)")

        # Ajouter les lignes horizontales pour les seuils ±2
        fig.add_hline(y=2, line_dash="dash", line_color="red", annotation_text="z = 2", annotation_position="top left")
        fig.add_hline(y=-2, line_dash="dash", line_color="green", annotation_text="z = -2", annotation_position="bottom left")

        # Affichage dans Streamlit
        st.plotly_chart(fig, use_container_width=True)

        # Histogramme avec Plotly Express
        fig_hist = px.histogram(df_plot, x="Z-score", nbins=50, title="Distribution du Z-score", color_discrete_sequence=["skyblue"])
        fig_hist.update_traces(marker_line_color="black", marker_line_width=1.2)
        # Affichage dans Streamlit
        st.plotly_chart(fig_hist, use_container_width=True)

        ###
        #LOG PRIX
        ###


        st.subheader("2. Etudes sur les log prix")
        # Prendre les log-prix
        log_crypto1 = np.log(df_histo[_crypto1])
        log_crypto2 = np.log(df_histo[_crypto2])

        # Corrélation sur les log-prix
        correlation = log_crypto1.corr(log_crypto2)

        # Test de cointégration sur les log-prix
        score, p_value, _ = coint(log_crypto1, log_crypto2)

        # Régression linéaire log(Y) = alpha + beta * log(X)
        log_crypto1_with_const = sm.add_constant(log_crypto1)
        if isinstance(log_crypto1_with_const, pd.Series):
            log_crypto1_with_const = log_crypto1_with_const.to_frame()

        model = sm.OLS(log_crypto2, log_crypto1_with_const).fit()
        beta = model.params[_crypto1]
        alpha = model.params['const']
        log_crypto2_pred = model.predict(log_crypto1_with_const)

        # Affichage des résultats dans Streamlit
        st.write(f"**Corrélation (log-prix)** entre {_crypto1} et {_crypto2} : {correlation:.4f}")
        st.write(f"**Régression linéaire (log)** entre {_crypto1} et {_crypto2} : Pente (β) : {beta:.4f}, Intercept (α) : {alpha:.4f}")
        st.write(f"**Test de cointégration (log-prix)** : p-value = {p_value:.4f}")

        # Créer un DataFrame pour les log-prix et la prédiction
        df_plot_log = pd.DataFrame({
            "log_crypto1": log_crypto1,
            "log_crypto2": log_crypto2,
            "log_crypto2_pred": log_crypto2_pred
        })

        # Tracer avec Plotly Express
        fig_scatter = px.scatter(
            df_plot_log,
            x="log_crypto1",  # Axe x : log de crypto1
            y="log_crypto2",  # Axe y : log de crypto2
            title=f"Scatter plot des log-prix entre {_crypto1} et {_crypto2}",
            labels={"log_crypto1": f"log({ _crypto1})", "log_crypto2": f"log({ _crypto2})"},
            template="plotly_dark",  # Utilisation du thème noir
        )

        # Ajouter la droite de régression
        fig_scatter.add_scatter(
            x=df_plot_log["log_crypto1"], 
            y=df_plot_log["log_crypto2_pred"], 
            mode='lines',  # Tracer la droite
            name=f"Droite de régression: {beta:.4f}x + {alpha:.4f}", 
            line=dict(color='red', width=2)
        )

        # Affichage du graphique avec Streamlit
        st.plotly_chart(fig_scatter, use_container_width=True)

        ####
        # ZSCORE
        ####

        st.subheader("2.1. Zscore log des prix, avec moyenne, std et beta glissants")
        #Zscore avec moyenne, std et beta glissants
        col1_zscore_log= st.columns(1)[0]
        with col1_zscore_log:
            _wd_log = st.selectbox(
                "Window zscore",
                options=[7,10,24,30,50,100,200],
                index=2,
                key="zscore_log_window"
            )

        beta_series = rolling_beta(log_crypto1, log_crypto2, _crypto1, window=_wd_log)
        #beta_series
        # Calcul du spread et du Z-score
        spread = log_crypto2 - beta_series * log_crypto1
        spread_mean_wd = pd.Series(spread).rolling(window=_wd_log).mean()
        spread_std_wd = pd.Series(spread).rolling(window=_wd_log).std()
        zscore_wd = (spread - spread_mean_wd) / spread_std_wd
        #zscore_wd
        # Créer un DataFrame pour tracer avec Plotly Express
        df_plot_wd = pd.DataFrame({
            "Index": zscore_wd.index,
            "Z-score": zscore_wd
        })

        # Tracer avec Plotly Express
        fig = px.line(df_plot_wd, x="Index", y="Z-score", title=f"Z-score du spread (Moyenne, volatilité et Beta glissants {_wd_log} périodes)")

        # Ajouter les lignes horizontales pour les seuils ±2
        fig.add_hline(y=2, line_dash="dash", line_color="red", annotation_text="z = 2", annotation_position="top left")
        fig.add_hline(y=-2, line_dash="dash", line_color="green", annotation_text="z = -2", annotation_position="bottom left")

        # Affichage dans Streamlit
        st.plotly_chart(fig, use_container_width=True)

        # Histogramme avec Plotly Express
        fig_hist = px.histogram(df_plot_wd, x="Z-score", nbins=50, title="Distribution du Z-score", color_discrete_sequence=["skyblue"])
        fig_hist.update_traces(marker_line_color="black", marker_line_width=1.2)
        # Affichage dans Streamlit
        st.plotly_chart(fig_hist, use_container_width=True, key="zscore_log_histo_glissant")

        #Z-SCORE avec moyeen et std globales (sur tout l'historique)
        st.subheader("2.2. Zscore log des prix, avec moyenne, std et beta globaux")
        spread = log_crypto2 - beta * log_crypto1
        spread_mean = spread.mean()
        spread_std = spread.std()
        # Z-score global
        zscore = (spread - spread_mean) / spread_std

        # Créer un DataFrame pour tracer avec Plotly Express
        df_plot_wd = pd.DataFrame({
            "Index": zscore_wd.index,
            "Z-score": zscore
        })

        # Tracer avec Plotly Express
        fig = px.line(df_plot_wd, x="Index", y="Z-score", title=f"Z-score du spread (Moyenne, volatilite et Beta globaux {_periods} periodes)")

        # Ajouter les lignes horizontales pour les seuils ±2
        fig.add_hline(y=2, line_dash="dash", line_color="red", annotation_text="z = 2", annotation_position="top left")
        fig.add_hline(y=-2, line_dash="dash", line_color="green", annotation_text="z = -2", annotation_position="bottom left")

        # Affichage dans Streamlit
        st.plotly_chart(fig, use_container_width=True, key="zscore_log_globaux")

        # Histogramme avec Plotly Express
        fig_hist = px.histogram(df_plot_wd, x="Z-score", nbins=50, title="Distribution du Z-score", color_discrete_sequence=["skyblue"])
        fig_hist.update_traces(marker_line_color="black", marker_line_width=1.2)
        st.plotly_chart(fig_hist, use_container_width=True, key="zscore_log_histo_globaux")


        st.subheader("3. Etude spread log-rendement")
        col_wd= st.columns(1)[0]
        with col_wd:
            _wd = st.selectbox(
                "Window log",
                options=[1,2,3,5,10,15,20,30,50,100,200],
                index=4,
                key="wd_log_rdt"
            )
        st.latex(rf"""\text{{Spread}}_t = \log\left( \frac{{\text{{ETH}}_{{t+{_wd}}}}}{{\text{{ETH}}_t}} \right) - \log\left( \frac{{\text{{BTC}}_{{t+{_wd}}}}}{{\text{{BTC}}_t}} \right)""")
        spread_log = rolling_spread_log(df_histo[_crypto1], df_histo[_crypto2], window=_wd)
        spread_std = spread_log.std()

        # Créer un DataFrame pour tracer avec Plotly Express
        df_plot_wd = pd.DataFrame({
            "Index": spread_log.index,
            "Spread": spread_log
        })

        # Tracer avec Plotly Express
        fig = px.line(df_plot_wd, x="Index", y="Spread", title=f"Spread log rendements sur {_wd} periodes)")

        # Ajouter les lignes horizontales pour les seuils ±2
        fig.add_hline(y=2*spread_std, line_dash="dash", line_color="red", annotation_text="z = 2", annotation_position="top left")
        fig.add_hline(y=-2*spread_std, line_dash="dash", line_color="green", annotation_text="z = -2", annotation_position="bottom left")

        # Affichage dans Streamlit
        st.plotly_chart(fig, use_container_width=True, key="spread_log_rdt")

        # Histogramme avec Plotly Express
        fig_hist = px.histogram(df_plot_wd, x="Spread", nbins=50, title="Distribution du spread", color_discrete_sequence=["skyblue"])
        fig_hist.update_traces(marker_line_color="black", marker_line_width=1.2)
        st.plotly_chart(fig_hist, use_container_width=True, key="spread_histo_log_rdt")

    if page == "Clustering":

        # Création de 4 colonnes pour les sélecteurs
        col1, col2, col3, col4, col5 = st.columns([1, 1.5, 0.7, 1, 1])

        # Sélection du nombre de cryptos
        with col1:
            num_cryptos = st.selectbox(
                "Nombre de cryptomonnaies",
                options=[("Top 10", 10), ("Top 30", 30), ("Top 50", 50), ("Top 100", 100), ("Top 200", 200)],
                format_func=lambda x: x[0],
                index=1
            )

        _timeframe = "1h"
        _periods = 200
        cluster = 5
        # Chargement initial des données
        with st.spinner(f"Chargement data"):
            df_coingecko_initial = get_crypto_data(num_cryptos[1])
            df_binance_initial = fetch_ohlcv_for_cryptos_sync(df_coingecko_initial["symbol"].tolist(), timeframe=_timeframe, limit=_periods)
            df_merged_initial = aggregate_crypto_data(df_coingecko_initial, df_binance_initial)
            symbols = [sym for sym in df_merged_initial["symbol"].tolist()]
            df_histo = fetch_ohlcv_histo_list_sync(symbols, timeframe=_timeframe, limit=_periods)
            df_pre_select, df_clustered, centroids = create_cluster(df_histo, symbols, cluster)

        # Sélection multiple pour exclure des cryptos
        with col2:
            cryptos_to_exclude = st.multiselect(
                "Exclure des cryptomonnaies (optionnel)",
                options=df_merged_initial['symbol'].tolist(),
                help="Sélectionnez les cryptomonnaies à exclure du tableau et des graphiques"
            )
        
        with st.spinner(f"Chargement data"):
            df_coingecko_initial = get_crypto_data(num_cryptos[1])
            df_binance_initial = fetch_ohlcv_for_cryptos_sync(df_coingecko_initial["symbol"].tolist(), timeframe=_timeframe, limit=_periods)
            df_merged_initial = aggregate_crypto_data(df_coingecko_initial, df_binance_initial)
            symbols = [sym for sym in df_merged_initial["symbol"].tolist() if sym not in cryptos_to_exclude]
            df_histo = fetch_ohlcv_histo_list_sync(symbols, timeframe=_timeframe, limit=_periods)
            df_pre_select, df_clustered, centroids = create_cluster(df_histo,symbols, cluster)

        with col3:
            _timeframe = st.selectbox(
                "Timeframe",
                options=["5m", "15m", "30m","1h", "2h", "4h", "1d", "1w"],
                index=3
            )
        
        with st.spinner(f"Chargement data"):
            df_coingecko_initial = get_crypto_data(num_cryptos[1])
            df_binance_initial = fetch_ohlcv_for_cryptos_sync(df_coingecko_initial["symbol"].tolist(), timeframe=_timeframe, limit=_periods)
            df_merged_initial = aggregate_crypto_data(df_coingecko_initial, df_binance_initial)
            symbols = [sym for sym in df_merged_initial["symbol"].tolist() if sym not in cryptos_to_exclude]
            df_histo = fetch_ohlcv_histo_list_sync(symbols, timeframe=_timeframe, limit=_periods)
            df_pre_select, df_clustered, centroids = create_cluster(df_histo,symbols, cluster)

        with col4:
            _periods = st.selectbox(
                "Nombre historique periodes",
                options=[7,15,30,50,100,200,500,1000],
                index=5
            )
        
        with st.spinner(f"Chargement data"):
            df_coingecko_initial = get_crypto_data(num_cryptos[1])
            df_binance_initial = fetch_ohlcv_for_cryptos_sync(df_coingecko_initial["symbol"].tolist(), timeframe=_timeframe, limit=_periods)
            df_merged_initial = aggregate_crypto_data(df_coingecko_initial, df_binance_initial)
            symbols = [sym for sym in df_merged_initial["symbol"].tolist() if sym not in cryptos_to_exclude]
            df_histo = fetch_ohlcv_histo_list_sync(symbols, timeframe=_timeframe, limit=_periods)
            df_pre_select, df_clustered, centroids = create_cluster(df_histo,symbols, cluster)

        # Choix du nombre de clusters
        with col5:
            cluster = st.selectbox(
                "Nombre de clusters",
                options=list(range(2, 11)),
                index=3,
                key="cluster"
            )

        with st.spinner(f"Chargement data"):
            df_coingecko_initial = get_crypto_data(num_cryptos[1])
            df_binance_initial = fetch_ohlcv_for_cryptos_sync(df_coingecko_initial["symbol"].tolist(), timeframe=_timeframe, limit=_periods)
            df_merged_initial = aggregate_crypto_data(df_coingecko_initial, df_binance_initial)
            symbols = [sym for sym in df_merged_initial["symbol"].tolist() if sym not in cryptos_to_exclude]
            df_histo = fetch_ohlcv_histo_list_sync(symbols, timeframe=_timeframe, limit=_periods)
            df_pre_select, df_clustered, centroids = create_cluster(df_histo,symbols, cluster)

        df_clustered

        # Plot du clustering avec Plotly Express
        fig_cluster = px.scatter(
            df_clustered,
            x="return",
            y="std",
            color="cluster",
            text="symbol",
            title="KMeans Clustering : Rendement vs Volatilité",
            labels={"return": "Rendement cumulé", "std": "Volatilité (std)"},
        )

        # Ajout des centroides
        for i, (x, y) in enumerate(centroids):
            fig_cluster.add_scatter(
                x=[x],
                y=[y],
                mode="markers+text",
                marker=dict(color="red", size=10, symbol="x"),
                text=[f"Center {i}"],
                textposition="top center",
                showlegend=False,
            )

        # Affichage final
        st.plotly_chart(fig_cluster, use_container_width=True)
        
if __name__ == "__main__":
    main()