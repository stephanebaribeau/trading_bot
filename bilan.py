import argparse
import os
from datetime import date, datetime
from zoneinfo import ZoneInfo
import pandas as pd
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import OrderSide, OrderStatus, QueryOrderStatus

NEW_YORK = ZoneInfo("America/New_York")
DEBUT_TEST = date(2026, 11, 25)  #premier jour du t est
ESPERANCE_BACKTEST = 0.126

def jour_ny(moment):
    """ La date à New York d'un moment donné. """
    return moment.astimezone(NEW_YORK).date()

def construire_trades(ordres):
    """ Associe chaque achat exécuté à sa sortie : le stop, ou la vente de fin de journée. """
    ventes = {}
    for o in ordres:
        if o.side == OrderSide.SELL and o.status == OrderStatus.FILLED:
            ventes[(o.symbol, jour_ny(o.filled_at))] = o

    trades = []
    for o in ordres:
        if o.side != OrderSide.BUY or o.status != OrderStatus.FILLED or not o.legs:
            continue
        stop = o.legs[0]
        jour = jour_ny(o.filled_at)
        entree = float(o.filled_avg_price)
        niveau_stop = float(stop.stop_price)

        if stop.status == OrderStatus.FILLED:
            sortie, raison = float(stop.filled_avg_price), "stop"
        elif (o.symbol, jour) in ventes:
            sortie, raison = float(ventes[(o.symbol, jour)].filled_avg_price), "fermeture"
        else:
            continue

        # Glissement à l'entrée : écart entre le prix visé et le prix obtenu
        if o.stop_price is not None:
            glissement = (entree / float(o.stop_price) - 1) * 100
        else:
            glissement = None

        trades.append({
            "jour": jour,
            "ticker": o.symbol,
            "actions": float(o.filled_qty),
            "entree": entree,
            "stop": niveau_stop,
            "sortie": sortie,
            "raison": raison,
            "resultat_R": (sortie - entree) / (entree - niveau_stop),
            "profit": (sortie - entree) * float(o.filled_qty),
            "glissement_entree_pct": glissement,
        })

    return pd.DataFrame(trades)


def main():
    parser = argparse.ArgumentParser(description="Bilan du test en direct")
    parser.add_argument("--depuis", type=date.fromisoformat, default=DEBUT_TEST, help="date de début, au format AAA-MM-JJ")
    args = parser.parse_args()

    load_dotenv()
    client = TradingClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"), paper=True)
    debut = datetime(args.depuis.year, args.depuis.month, args.depuis.day, tzinfo=NEW_YORK)
    ordres = client.get_orders(GetOrdersRequest(status=QueryOrderStatus.CLOSED, after=debut, nested=True, limit=500))
    trades = construire_trades(ordres)

    print(f"=== Bilan depuis le {args.depuis} ===")
    if trades.empty:
        print("Aucun trade terminé pour l'instant.")
        return

    print(trades.round(3).to_string(index=False))
    print(f"\nNombre de trades : {len(trades)}")
    print(f"Taux de réussite   : {(trades['resultat_R'] > 0).mean() * 100:.1f} %")
    print(f"Espérance          : {trades['resultat_R'].mean():+.3f} R par trade "  f"(backtest : {ESPERANCE_BACKTEST:+.3f} R)")
    print(f"Profit total       : {trades['profit'].sum():+,.2f} $")
    glissement = trades["glissement_entree_pct"].dropna()
    if len(glissement) > 0:
        print(f"Glissement moyen à l'entrée : {glissement.mean():+.3f} % "  f"(backtest : +0,050 %)")
    if len(trades) < 80:
        print(f"\n⚠ Seulement {len(trades)} trades : il en faut au moins 80 pour conclure.")


if __name__ == "__main__":
    main()
