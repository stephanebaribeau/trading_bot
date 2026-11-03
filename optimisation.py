import yfinance as yf
import pandas as pd
from scanner import TICKERS, preparer, passe_les_filtres

GLISSEMENT_PCT = 0.05
DATE_COUPURE = pd.Timestamp("2025-01-01")
STOPS_A_TESTER = [2,3,4,5,6]
OBJECTIFS_A_TESTER = [2,4,6,8]

def simuler_trade(ligne, stop_pct, objectifs_pct):
    """ Achat à l'ouverture, sortie au stop, à l'objectif ou à la fermeture. """
    entree = ligne["open"] * (1 + GLISSEMENT_PCT / 100)
    stop = entree * (1 - stop_pct / 100)
    objectif = entree * (1 + objectifs_pct / 100)

    if ligne["low"] <= stop:
        sortie = stop
    elif ligne["high"] >= objectif:
        sortie = objectif
    else:
        sortie = ligne["close"]

    sortie = sortie * (1 - GLISSEMENT_PCT / 100)
    return (sortie / entree - 1) * 100

def trouver_candidats(donnees):
    """ Toutes les journées qui passent les filtres du scanner. """
    candidats = []
    for ticker, df in donnees.items():
        for date, ligne in df.iterrows():
            if passe_les_filtres(ligne):
                candidats.append((date, ticker, ligne))
    return candidats

def backtester(candidats, stop_pct, objectif_pct):
    """ Simule tous les  candidats avec ces paramètres et retourne les statistiques. """
    rendements = pd.Series(
            [simuler_trade(ligne, stop_pct, objectif_pct) for _, _, ligne in candidats]
            )
    return {
            "stop": stop_pct,
            "objectif": objectif_pct,
            "trades": len(rendements),
            "reussite_pct": round((rendements > 0).mean() * 100, 1),
            "rendement_moyen": round(rendements.mean(), 3),
            }

def detail_par_ticker(candidats, stop_pct, objectif_pct):
    """ Rendement moyen par ticker, pour voir quels titres font gagner ou  perdre. """
    lignes = []
    for date, ticker, ligne in candidats:
        lignes.append({
            "ticker": ticker,
            "rendement": simuler_trade(ligne, stop_pct, objectif_pct),
            })

    df = pd.DataFrame(lignes)
    return (df.groupby("ticker")["rendement"].agg(trades="count", rendement_moyen="mean").round(3).sort_values("rendement_moyen", ascending=False))


if __name__ == "__main__":
    brut = yf.download(TICKERS, period="5y", interval="1d", group_by="ticker", progress=False)
    donnees = {t: preparer(brut[t]) for t in TICKERS}

    candidats = trouver_candidats(donnees)
    entrainement = [c for c in candidats if c[0] < DATE_COUPURE]
    test = [c for c in candidats if c[0] >= DATE_COUPURE]

    print(f"Entrainement : {len(entrainement)} trades | test : {len(test)} trades\n")

    # On cherche les  meilleurs paramètres sur l'entrainement seulement
    resultats = []
    for stop in STOPS_A_TESTER:
        for objectif in OBJECTIFS_A_TESTER:
            resultats.append(backtester(entrainement, stop, objectif))

    grille = pd.DataFrame(resultats).sort_values("rendement_moyen", ascending=False)
    print("=== ENTRAINEMENT (2021-2024) ===")
    print(grille.to_string(index=False))

    meilleur = grille.iloc[0]
    res_test = backtester(test, meilleur["stop"], meilleur["objectif"])

    print(f"\n=== TEST (2025-aujourd'hui) avec stop {meilleur['stop']} % ")
    print(f"et objectif {meilleur['objectif']} % ===")
    print(f"Entrainement : {meilleur['rendement_moyen']:+.3f} % par trade")
    print(f"Test         : {res_test['rendement_moyen']:+.3f} % par trade ")
    print(f"({res_test['trades']} trades, {res_test['reussite_pct']} % de réussite)")
    print(f"\n\n=== DETAIL PAR TICKER (entrainement) ===")
    print(detail_par_ticker(entrainement, meilleur["stop"], meilleur["objectif"]))

    detail = detail_par_ticker(entrainement, meilleur["stop"], meilleur["objectif"])
    tickers_choisis = detail[detail["rendement_moyen"] > 0].index.tolist()
    print(f"\nTickers choisis :", tickers_choisis)

    entrainement_filtre = [c for c in entrainement if c[1] in tickers_choisis]
    test_filtre = [c for c in test if c[1] in tickers_choisis]

    res_entr = backtester(entrainement_filtre, meilleur["stop"], meilleur["objectif"])
    res_test = backtester(test_filtre, meilleur["stop"], meilleur["objectif"])

    print(f"Entrainement : {res_entr['rendement_moyen']:+.3f} % ({res_entr['trades']} trades)")
    print(f"Test         : {res_test['rendement_moyen']:+.3f} % ({res_test['trades']} trades)")

