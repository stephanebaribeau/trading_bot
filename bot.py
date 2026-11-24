import argparse
import csv
import math
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (GetCalendarRequest, MarketOrderRequest, StopOrderRequest, StopLossRequest)
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.news import NewsClient
from alpaca.data.requests import NewsRequest, StockBarsRequest, StockLatestTradeRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import DataFeed
from scanner import TICKERS
from categories import classer

NEW_YORK = ZoneInfo("America/New_York")
RISQUE_PAR_TRADE = 0.01 #1% du compte par trade
POSITION_MAX=0.25
JOURNAL = Path("journal_paper.csv")

load_dotenv()
cle_api = os.getenv("ALPACA_API_KEY")
secret_api = os.getenv("ALPACA_SECRET_KEY")
trading = TradingClient(cle_api, secret_api, paper=True)
donnees = StockHistoricalDataClient(cle_api,  secret_api)
client_prix = StockHistoricalDataClient(cle_api, secret_api)
client_nouvelles = NewsClient(cle_api, secret_api)


def maintenant():
    """ L'heure actuelle à New York. """
    return datetime.now(NEW_YORK)

def attendre_jusqua(moment):
    """ Attend jusqu'à l'heure indiquée, en affichant le temps restant. """
    while maintenant() < moment:
        restant = (moment - maintenant()).total_seconds()
        print(f"  En attente jusqu'à {moment:%H:%M} (encore {restant / 60:.0f} min)...")
        time.sleep(min(restant, 300))  # on relance toutes les 5 minutes


def journal(evenement, ticker="", details=""):
    """ Ajoute une ligne au journal CSV et l'affiche à l'écran. """
    moment = f"{maintenant():%Y-%m-%d %H:%M:%S}"
    print(f"[{moment}] {evenement:<16} {ticker:<5} {details}")
    nouveau = not JOURNAL.exists()
    with JOURNAL.open("a", newline="", encoding="utf-8") as f:
        ecrivain = csv.writer(f)
        if nouveau:
            ecrivain.writerow(["moment", "evenement", "ticker", "details"])
        ecrivain.writerow([moment, evenement, ticker, details])


def seance_du_jour():
    """ (veille, ouverture, fermeture) de la séance d'aujourd'hui, ou None si la bourse  est fermée. """
    aujourd_hui = maintenant().date()
    calendrier = trading.get_calendar(GetCalendarRequest(start=aujourd_hui -  timedelta(days=10), end=aujourd_hui))
    if not calendrier or calendrier[-1].date != aujourd_hui:
        return None

    seance = calendrier[-1]
    veille = calendrier[-2].date
    ouverture = seance.open.replace(tzinfo=NEW_YORK)
    fermeture = seance.close.replace(tzinfo=NEW_YORK)
    return veille, ouverture, fermeture


def candidats_nouvelles(veille, ouverture):
    """ Titre avec une baisse d'analyse ciblée entre 16h la veille et 9h30. """
    debut = datetime(veille.year, veille.month, veille.day, 16, 0, tzinfo=NEW_YORK)
    requete = NewsRequest(symbols=",".join(TICKERS), start=debut, end=ouverture)
    articles = client_nouvelles.get_news(requete).data["news"]

    candidats = {}
    for article in articles:
        if not (debut <= article.created_at  < ouverture):
            continue
        if len(article.symbols) > 2 or classer(article.headline) != "baisse_analyste":
            continue
        for symbole in article.symbols:
            if symbole in TICKERS:
                candidats.setdefault(symbole, []).append(article.headline)
    return candidats

def zone_ouverture(ticker, ouverture):
    """ (haut, bas) des 15 premières minutes avec le flux IEX. None si incomplet. """
    fin = ouverture + timedelta(minutes=15)
    requete = StockBarsRequest(symbol_or_symbols=ticker, timeframe=TimeFrame(5, TimeFrameUnit.Minute), start=ouverture, end=fin, feed=DataFeed.IEX)
    barres = client_prix.get_stock_bars(requete).df
    if barres.empty:
        return None
    barres = barres.loc[ticker]
    barres = barres[barres.index < fin]
    if len(barres) < 3:
        return None
    return barres["high"].max(), barres["low"].min()


def nombre_actions(valeur_compte, haut, bas):
    """ Risque 1% du compte, sans dépasser 25% du compte en valeur. """
    risque_par_action = haut - bas
    if risque_par_action <= 0:
        return 0
    selon_risque = valeur_compte * RISQUE_PAR_TRADE / risque_par_action
    selon_plafond = valeur_compte * POSITION_MAX / haut
    return math.floor(min(selon_risque, selon_plafond))

def placer_ordre(ticker, haut, bas, quantite):
    """ Ordre OTO : achat à la cassure du haut, puis stop de protection au bas. """
    stop_loss = StopLossRequest(stop_price=round(basd, 2))
    dernier = client_prix.get_stock_latest_trade(StockLatestTradeRequest(symbol_or_symbols=ticker, feed=DataFeed.IEX))[ticker].price

    if dernier > haut:
        ordre = MarketOrderRequest(symbol=ticker, qty=quantite, side=OrderSide.BUY, time_in_force=TimeInForce.DAY, order_class=OrderClass.OTO, stop_loss=stop_loss)
        entre = f"au marché (prix {dernier:.2f} déjà au-dessus)"
    else:
        ordre = StopOrderRequest(symbol=ticker, qty=quantite,side=OrderSide.BUY,time_in_force=TimeInForce.DAY,stop_price=round(haut + 0.01, 2),order_class=OrderClass.OTO, stop_loss=stop_loss)
        entree = f"stop à {haut + 0.01:.2f}"

    try:
        envoye = trading.submit_order(ordre)
        journal("ordre envoyé", ticker, f"{quantite} actions, entrée {entree}, stop {bas:.2f}, id {envoye.id}")
        return True
    except Exception as erreur:
        journal("ordre refusé", ticker, str(erreur))
        return False


def main():
    parser = argparse.ArgumentParser(description="Bot ORB de paper trading")
    parser.add_argument("--test", metavar="TICKER", help="force un trade de 1 action sur ce titre, sans filtre de nouvelles")
    args = parser.parse_args()

    seance = seance_du_jour()
    if seance is None:
        print("La bourse est fermée aujourd'hui.")
        return
    veille, ouverture, fermeture = seance
    journal("démarrage", details=f"seance {ouverture:%H:%M}-{fermeture:%H:%M}, veille {veille}")

    attendre_jusqua(ouverture +  timedelta(minutes=16))

    if args.test:
        candidats = {args.test: ["mode test : aucun filtre de nouvelles"]}
    else:
        candidats = candidats_nouvelles(veille, ouverture)
    if not candidats:
        journal("aucun candidat", details="pas de baisse d'analyste ciblée avant l'ouverture")
        return

    valeur_compte = float(trading.get_account().equity)
    nb_ordres = 0
    for ticker, titres in candidats.items():
        journal("candidat", ticker, " | ".join(titres))
        zone = zone_ouverture(ticker, ouverture)
        if zone is None:
            journal("zone incomplète", ticker, "moins de 3 barres IEX entre 9:30 et 9:45")
            continue
        haut, bas =  zone
        quantite = 1 if args.test else nombre_actions(valeur_compte, haut, bas)
        if quantite < 1:
            journal("taille nulle", ticker, f"haut {haut:.2f}, bas {bas:.2f}")
            continue
        if placer_ordre(ticker, haut, bas, quantite):
            nb_ordres += 1

    if nb_ordres == 0:
        return

    attendre_jusqua(fermeture - timedelta(minutes=5))
    trading.close_all_positions(cancel_ordres=True)
    journal("fermeture", details="ordres annulés, positions vendues")


if __name__ == "__main__":
    main()
    
    

