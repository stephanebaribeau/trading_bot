import yfinance as yf
import pandas as pd
from scanner import TICKERS, preparer
from optimisation import trouver_candidats, GLISSEMENT_PCT, DATE_COUPURE
import warnings

STOPS_A_TESTER = [2,3,4,5,6]
warnings.filterwarnings("ignore", message=".*inplace keyword.*")

def mouvement_journee(ligne):
    """ De combien le titre a bougé entre l'ouverture et la fermeture (en %). """
    return (ligne["close"] / ligne["open"] - 1) * 100

def simuler_short(ligne, stop_pct):
    """ Vente à découvert à l'ouverture : on parie que le gap se referme. Objectif: La fermeture de la veille. Stop : X % au-dessus de l'entrée. """
    entree = ligne["open"] * (1 - GLISSEMENT_PCT / 100)
    stop = entree * (1 + stop_pct / 100)
    objectif = ligne["fermeture_veille"]

    if ligne["high"] >= stop:
        sortie = stop
    elif ligne["low"] <= objectif:
        sortie = objectif
    else:
        sortie = ligne["close"]

    sortie = sortie * (1 + GLISSEMENT_PCT / 100)
    return (entree - sortie) / entree * 100

if __name__ == "__main__":
    brut = yf.download(TICKERS, period="5y", interval="1d", group_by="ticker", progress=False)
    donnees = {t: preparer(brut[t]) for t in TICKERS}
    candidats = trouver_candidats(donnees)
    entrainement = [c for c in candidats if c[0] < DATE_COUPURE]
    test = [c for c in candidats if c[0] >= DATE_COUPURE]

    mouvements = pd.Series([mouvement_journee(ligne) for _, _, ligne in entrainement])
    refermes = sum(ligne["low"] <= ligne["fermeture_veille"] for _, _, ligne in entrainement)

    print("=== DIAGNOSTIC (entrainement) ===")
    print(f"Mouvement moyen ouverture -> fermeture : {mouvements.mean():+.3f} %")
    print(f"Jours ou le titre a fini sous l'ouverture : {(mouvements < 0).mean() * 100:.1f} %")
    print(f"Gaps complètement refermés dans la journée : {refermes / len(entrainement) * 100:.1f} %")

    resultats = []
    for stop in STOPS_A_TESTER:
        r = pd.Series([simuler_short(ligne, stop) for _, _, ligne in entrainement])
        resultats.append({
            "stop": stop,
            "reussite_pct": round((r > 0).mean() * 100, 1),
            "rendement_moyen": round(r.mean(), 3),
            })

    grille = pd.DataFrame(resultats).sort_values("rendement_moyen", ascending=False)
    print("\n=== SHORT : ENTRAINEMENT (2021-2024) ===")
    print(grille.to_string(index=False))

    meilleur = grille.iloc[0]
    r_test = pd.Series([simuler_short(ligne, meilleur["stop"]) for _, _, ligne in test])
    print(f"\n=== SHORT : TEST (2025-aujourd'hui) avec stop {meilleur['stop']} % ===")
    print(f"Entrainement : {meilleur['rendement_moyen']:+.3f} % par trade")
    print(f"Test         : {r_test.mean():+.3f} % par trade ")
    print(f"({len(r_test)} trades, {(r_test > 0).mean() * 100:.1f} % de reussite)")

