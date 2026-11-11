import os
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import Adjustment, DataFeed
from scanner import TICKERS

FUSEAU = "America/New_York"
DOSSIER_CACHE = Path("data_alpaca")
DEBUT = datetime(2021, 1, 1)

load_dotenv()
client = StockHistoricalDataClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"))

def telecharger_alpaca(ticker, debut, fin):
    """ Télécharge les barres de 5 minutes d'un titre, séance normale seulement. """
    requete = StockBarsRequest(
        symbol_or_symbols=ticker,
        timeframe=TimeFrame(5, TimeFrameUnit.Minute),
        start=debut,
        end=fin,
        feed=DataFeed.SIP,
        adjustment=Adjustment.ALL)
    df = client.get_stock_bars(requete).df
    if df.empty:
        return df

    df = df.loc[ticker]
    df.index = df.index.tz_convert(FUSEAU)
    df = df.between_time("09:30", "15:55")
    return df[["open", "high", "low", "close", "volume"]]


def charger_intraday(ticker, debut=DEBUT):
    """ Retourne les barres de 5 minutes d'un titre, depuis le cache si possible."""
    DOSSIER_CACHE.mkdir(exist_ok=True)
    fichier = DOSSIER_CACHE / f"{ticker}_5min.csv"

    if fichier.exists():
        df = pd.read_csv(fichier, index_col=0)
        df.index = pd.to_datetime(df.index, utc=True).tz_convert(FUSEAU)
        return df

    print(f"   Telechargement de {ticker} depuis le {debut.date()}...")
    fin = datetime.now() - timedelta(days=1)
    df = telecharger_alpaca(ticker, debut, fin)
    df.to_csv(fichier)
    return df


def main():
    for ticker in TICKERS:
        df = charger_intraday(ticker)
        nb_jours = len(set(df.index.date))
        print(f"{ticker:5} : {len(df):>7} barres, {nb_jours} jours, "   f"du {df.index.min().date()} au {df.index.max().date()}")




if __name__ == "__main__":
    main()


