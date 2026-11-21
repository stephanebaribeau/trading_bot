import re
import pandas as pd
from scanner import TICKERS
from donnees_nouvelles import charger_nouvelles

REGLES = [
    ("hausse_analyste", r"\bupgrade[sd]?\b|raises price target"),
    ("baisse_analyste", r"\bdowngrade[sd]?\b|lowers price target"),
    ("resultats",r"\beps\b|\bbeats?\b|\bmiss(es)?\b|\bsees (q[1-4]|fy|full|annual)|guidance|\bvs\b.*\best\b"),
    ("neutre_analyste", r"\bmaintains\b|\breiterates\b|initiates coverage"),
]

def classer(titre):
    """ Retourne la catégorie d'un titre de nouvelle selon les mots-clés. """
    titre = str(titre).lower()
    for categorie, motif in REGLES:
        if re.search(motif, titre):
            return categorie
    return "autre"


def main():
    toutes = pd.concat([charger_nouvelles(t) for t in TICKERS])
    ciblees = toutes[toutes["nb_symboles"] < 2].copy()
    ciblees["categorie"] = ciblees["headline"].apply(classer)

    print(f"=== Répartition des {len(ciblees)} nouvelles ciblées ===")
    repartition = ciblees["categorie"].value_counts(normalize=True) * 100
    print(repartition.round(1).to_string())

    for categorie in REGLES + [("autre", None)]:
        nom = categorie[0]
        exemples = ciblees[ciblees["categorie"] == nom].sample(5, random_state=1)
        print(f"\n--- {nom} ---")
        for titre in exemples["headline"]:
            print(f"   {titre[:100]}")


if __name__ == "__main__":
    main()