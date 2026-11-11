import pandas as pd
from scanner import TICKERS
from donnees_alpaca import charger_intraday
from orb import simuler_orb

DATE_COUPURE = pd.Timestamp("2025-01-01").date()

def resumer(trades, titre):
    """ Affiche les statistiques d'un groupe de dtrade. """
    gagnants = trades[trades["resultat_R"] > 0]
    perdants = trades[trades["resultat_R"] <= 0]
    print(f"\n=== {titre} ===")
    print(f"Nombre de trades        : {len(trades)}")
    print(f"Taux de réussite        : {len(gagnants) / len(trades) * 100:.1f} %") 
    print(f"Gain moyen              : {gagnants['resultat_R'].mean():+.2f} R")
    print(f"Perte moyenne           : {perdants['resultat_R'].mean():+.2f} R")
    print(f"Espérance               : {trades['resultat_R'].mean():+.3f} R par trade")
    print(f"Sortie                  : {trades['raison'].value_counts().to_dict()}")

def main():
    trades = []
    for ticker in TICKERS:
        print(f"Simulation de {ticker}...")
        df = charger_intraday(ticker)
        for jour, barres in df.groupby(df.index.date):
            trade = simuler_orb(barres)
            if trade is not None:
                trades.append({"jour": jour, "ticker": ticker, **trade})

    trades = pd.DataFrame(trades)
    entrainement = trades[trades["jour"] < DATE_COUPURE]
    test = trades[trades["jour"] >= DATE_COUPURE]

    resumer(entrainement, "ENTRAINEMENT (2021-2024)")
    resumer(test, "TEST (2025-aujourd'hui)")

    trades["annee"] = pd.to_datetime(trades["jour"]).dt.year
    print("\n=== Par année ===")
    par_annee = (trades.groupby("annee")["resultat_R"].agg(trades="count", esperance_R="mean").round(3))
    print(par_annee.to_string())


if __name__=="__main__":
    main()