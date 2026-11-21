import os
from datetime import datetime, timedelta
from os import path
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from alpaca.data.historical.news import NewsClient
from alpaca.data.requests import NewsRequest
from scanner import TICKERS

FUSEAU = "America/New_York"
DOSSIER_CACHE = Path("data_alpaca")
DEBUT = datetime(2021,1,1)
COLONNES = ["created_at", "headline", "summary", "symboles", "nb_symboles"]

load_dotenv()
client = NewsClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"))


def telecharger_nouvelles(ticker, debut, fin):
    """ Télécharge toutes les nouvelles d'un titre entre deux dates. """
    requete = NewsRequest(symbols=ticker, start=debut, end=fin, sort="asc")
    articles = client.get_news(requete).data["news"]

    lignes = [
        {
            "created_at": a.created_at,
            "headline": a.headline,
            "summary": a.summary,
            "symboles": "|".join(a.symbols),
            "nb_symboles": len(a.symbols),
        }
        for a in articles
    ]
    df = pd.DataFrame(lignes, columns=COLONNES)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True).dt.tz_convert(FUSEAU)
    return df


def charger_nouvelles(ticker, debut=DEBUT):
    """ Retourne les nouvelles d'un titre, depuis la cache  si possible. """
    DOSSIER_CACHE.mkdir(exist_ok=True)
    fichier = DOSSIER_CACHE / f"{ticker}_nouvelles.csv"

    if fichier.exists():
        df = pd.read_csv(fichier)
        df["created_at"] = pd.to_datetime(df["created_at"], utc=True).dt.tz_convert(FUSEAU)
        return df

    print(f"   Telechargement des nouvelles de {ticker} depuis le {debut.date()}...")
    fin = datetime.now() - timedelta(days=1)
    df = telecharger_nouvelles(ticker, debut, fin)
    df.to_csv(fichier, index=False)
    return df


def main():
    for ticker in TICKERS:
        df = charger_nouvelles(ticker)
        ciblees = (df["nb_symboles"] <= 2).sum()
        print(f"{ticker:5} : {len(df):>6} nouvelles, dont {ciblees:>5} ciblées "     f"({ciblees / len(df) * 100:.0f} %)")

if __name__ == "__main__":
    main()