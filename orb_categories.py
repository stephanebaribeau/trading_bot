import pandas as pd
from scanner import TICKERS
from donnees_alpaca import charger_intraday
from donnees_nouvelles import charger_nouvelles
from orb import simuler_orb
from categories import classer

DATE_COUPURE = pd.Timestamp("2025-01-01").date()
FUSEAU = "America/New_York"
CATEGORIES = ["hausse_analyste", "baisse_analyste", "resultats", "neutre_analyste", "autre"]


def categories_par_jour(nouvelles, liste_jours):
    """ Pour chaque jour de la bourse, l'ensemble des catégories de nouvelles ciblées
    publiées entre 16h la veille de la bourse à 9h30 le jour même. """
    ciblees = nouvelles[nouvelles["nb_symboles"] <= 2].copy()
    ciblees["categorie"] = ciblees["headline"].apply(classer)

    resultat = {}
    for veille, jour in zip(liste_jours[:-1], liste_jours[1:]):
        debut = pd.Timestamp(f"{veille} 16:00", tz=FUSEAU)
        fin = pd.Timestamp(f"{jour} 09:30", tz=FUSEAU)
        dans_fenetre = ciblees[(ciblees["created_at"] >= debut) & (ciblees["created_at"] < fin)]
        resultat[jour] = set(dans_fenetre["categorie"])

    return resultat

def statistiques(trades):
    return {
        "trades": len(trades),
        "reussite_pct": round((trades["resultat_R"] > 0).mean() * 100, 1),
        "esperance_R": round(trades["resultat_R"].mean(), 3),
    }

def main():
    trades = []
    for ticker in TICKERS:
        print(f"Simulation de {ticker}...")
        df = charger_intraday(ticker)
        liste_jours = sorted(set(df.index.date))
        cats = categories_par_jour(charger_nouvelles(ticker), liste_jours)

        for jour, barres in df.groupby(df.index.date):
            if jour not in cats:
                continue
            trade = simuler_orb(barres)
            if trade is not None:
                trades.append({"jour": jour, "ticker": ticker, "categories": cats[jour], **trade})

    trades = pd.DataFrame(trades)
    trades["periode"] = ["entrainement" if j < DATE_COUPURE else "test" for j in trades["jour"]]

    lignes = []
    for periode, groupe in trades.groupby("periode"):
        sans_nouvelle = groupe[groupe["categories"].apply(len) == 0]
        lignes.append({"periode": periode, "categorie": "aucune nouvelle", **statistiques(sans_nouvelle)})

        for cat in CATEGORIES:
            avec_cat = groupe[groupe["categories"].apply(lambda c: cat in c)]
            lignes.append({"periode": periode, "categorie": cat, **statistiques(avec_cat)})

    tableau = pd.DataFrame(lignes)
    resume = tableau.pivot(index="categorie", columns="periode", values=["trades", "esperance_R"])
    print(f"\n=== ORB selon la catégorie des nouvelles avant l'ouverture ===")
    print(resume.to_string())


if __name__=="__main__":
    main()