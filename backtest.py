import yfinance as yf
import pandas as pd

from scanner import TICKERS, preparer, passe_les_filtres

STOP_PCT = 2.0      # on coupe la perte à 2%
OBJECTIF_PCT = 4.0  # on prend les projet à +4%
GLISSEMENT_PCT = 0.05

def simuler_trade(ligne):
    entree = ligne["open"] * (1 + GLISSEMENT_PCT / 100)
    stop = entree * (1 - STOP_PCT / 100)
    objectif = entree * (1 + OBJECTIF_PCT / 100)

    if ligne["low"] <= stop:
        sortie, raison = stop, "stop"
    elif ligne["high"] >= objectif:
        sortie, raison = objectif, "objectif"
    else:
        sortie, raison = ligne["close"], "fermeture"

    sortie = sortie * (1 - GLISSEMENT_PCT / 100)
    rendement = (sortie / entree - 1) * 100
    return rendement, raison

brut = yf.download(TICKERS, period="2y", interval="1d", group_by="ticker", progress=False)

trades = []
for ticker in TICKERS:
    df = preparer(brut[ticker])
    for date, ligne in df.iterrows():
        if passe_les_filtres(ligne):
            rendement, raison = simuler_trade(ligne)
            trades.append({"date": date.date(), "ticker": ticker, "gap_pct": round(ligne["gap_pct"], 2), "rendement_pct": round(rendement, 2), "raison": raison})

trades = pd.DataFrame(trades).sort_values("date")
print(trades.tail(15).to_string(index=False))

gagnants = trades[trades["rendement_pct"] > 0]
perdants = trades[trades["rendement_pct"] <= 0]

print(f"\nNombre de trades : {len(trades)}")
print(f"Taux de réussite : {len(gagnants) / len(trades) * 100:.1f} %")
print(f"Gain moyen : {gagnants['rendement_pct'].mean():+.2f} %")
print(f"Perte moyenne : {perdants['rendement_pct'].mean():+.2f} %")
print(f"Rendement moyen : {trades['rendement_pct'].mean():+.3f} % par trades")
print("\nSorties :")
print(trades["raison"].value_counts().to_string())

