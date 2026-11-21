import pandas as pd
from scanner import TICKERS
from donnees_alpaca import charger_intraday
from donnees_nouvelles import charger_nouvelles
from orb import simuler_orb

DATE_COUPURE = pd.Timestamp("2025-01-01").date()
FUSEAU = "America/New_York"


def compter_nouvelles(nouvelles, jours):
    """ Pour chaque jour de la bourse, nombre de nouvelles ciblées publiées
    entre 16h la veille de la bourse et 9h30 le jour même. """
    ciblees = nouvelles[nouvelles["nb_symboles"] <= 2]["created_at"]
    comptes = {}

    for veille, jour in zip(jours[:-1], jours[1:]):
        debut = pd.Timestamp(f"{veille} 16:00", tz=FUSEAU)
        fin = pd.Timestamp(f"{jour} 09:30", tz=FUSEAU)
        comptes[jour] = ((ciblees >= debut) & (ciblees < fin)).sum()

    return comptes

def groupe(nb):
    if nb == 0:
        return "0"
    if nb <= 2:
        return "1-2"
    return "3+"

def main():
    trades = []
    for ticker in TICKERS:
        print(f"Simulation de {ticker}...")
        df = charger_intraday(ticker)
        jours = sorted(set(df.index.date))
        comptes = compter_nouvelles(charger_nouvelles(ticker), jours)

        for jour, barres in df.groupby(df.index.date):
            if jour not in comptes:
                continue
            trade = simuler_orb(barres)
            if trade is not None:
                trades.append({"jour": jour, "ticker": ticker, "nouvelles": comptes[jour], **trade})

    trades = pd.DataFrame(trades)
    trades["groupe"] = trades["nouvelles"].apply(groupe)
    trades["periode"] = ["entrainement" if j < DATE_COUPURE else "test" for j in trades["jour"]]

    tableau = (trades.groupby(["periode", "groupe"])["resultat_R"].agg(trades="count", reussite_pct=lambda r:(r>0).mean() * 100, esperance_R="mean").round(3))
    print("\n=== ORB selon les nouvelle avant l'ouverture ===")
    print(tableau.to_string())

if __name__ == "__main__":
    main()