import pandas as pd
from scanner import TICKERS
from donnees_alpaca import charger_intraday
from donnees_nouvelles import charger_nouvelles
from orb import simuler_orb
from orb_categories import categories_par_jour

def resume(trades, colonne):
    """ Nombre de trades en espérance, regroupés selon une colonne. """
    return (trades.groupby(colonne, observed=True)["resultat_R"].agg(trades="count", esperance_R="mean").round(3))

def main():
    trades = []
    for ticker in TICKERS:
        print(f"Simulation de {ticker}...")
        df = charger_intraday(ticker)
        liste_jours = sorted(set(df.index.date))
        cats = categories_par_jour(charger_nouvelles(ticker), liste_jours)

        fermeture_veille = None
        for jour, barres in df.groupby(df.index.date):
            ouverture = barres["open"].iloc[0]
            if fermeture_veille is not None:
                gap_pct = (ouverture / fermeture_veille - 1) * 100
            else:
                gap_pct = None
            fermeture_veille = barres["close"].iloc[-1]

            if jour not in cats or "baisse_analyste" not in cats[jour]:
                continue
            trade = simuler_orb(barres)
            if trade is not None:
                trades.append({"jour": jour, "ticker": ticker, "gap_pct": gap_pct, "avec_resultats": "resultats" in cats[jour], **trade})

    trades = pd.DataFrame(trades)
    trades["annee"] = pd.to_datetime(trades["jour"]).dt.year
    trades["sens_gap"] = pd.cut(trades["gap_pct"], bins=[-100, -1, 1, 100], 
                                labels=["baissier (< -1 %)", "plat", "haussier (> 1 %)"])

    print(f"\n{len(trades)} trades les jours de baisse d'analyste")
    print("\n=== Par année ===")
    print(resume(trades, "annee").to_string())
    print("\n=== Par ticker ===")
    print(resume(trades, "ticker").sort_values("esperance_R", ascending=False).to_string())
    print("\n=== Avec ou sans résultats trimestriels le même jour ===")
    print(resume(trades, "avec_resultats").to_string())
    print("\n=== Selon le sens du gap ===")
    print(resume(trades, "sens_gap").to_string())

if __name__ == "__main__":
    main()
