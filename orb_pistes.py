import pandas as pd
from scanner import TICKERS
from donnees_alpaca import charger_intraday
from orb import simuler_orb, heures_range

DATE_COUPURE = pd.Timestamp("2025-01-01").date()
VOLUME_RELATIF_MIN = 2.0 # au moins 2 fois le volume habituel à l'ouverture


def simuler_ticker(ticker, minutes_range):
    """ Simule chaque jour d'un titlre et calcule le volume relatif de la zone d'ouverture. """
    df = charger_intraday(ticker)
    fin_range, _ = heures_range(minutes_range)

    lignes = []
    for jour, barres in df.groupby(df.index.date):
        ligne = {
            "jour": jour,
            "ticker": ticker,
            "volume_range": barres.between_time("09:30", fin_range)["volume"].sum(),
            }
        trade = simuler_orb(barres, minutes_range)
        if trade is not None:
            ligne.update(trade)
        lignes.append(ligne)

    tableau = pd.DataFrame(lignes)
    # VOlume moyen de la zone sur les 20 jours précédents.
    volume_moyen = tableau["volume_range"].shift(1).rolling(20).mean()
    tableau["volume_relatif"] = tableau["volume_range"] / volume_moyen

    # On garde seulement les jours avec un trade et un volume relatif connu
    return tableau.dropna(subset=["resultat_R", "volume_relatif"])

def statistiques(trades):
    return {
        "trades": len(trades),
        "reussite_pct": round((trades["resultat_R"] > 0).mean() * 100, 1),
        "esperance_R": round(trades["resultat_R"].mean(), 3),
        }


def filtrer(trades, filtre_volume):
    if filtre_volume:
        return trades[trades["volume_relatif"] >= VOLUME_RELATIF_MIN]
    return trades

def main():
    donnees = {}
    for minutes in [5, 15]:
        print(f"Simulation avec une zone de {minutes} minutes...")
        donnees[minutes] = pd.concat([simuler_ticker(t, minutes) for t in TICKERS])

    resultats = []
    for minutes in [5, 15]:
        for filtre_volume in [False, True]:
            trades = filtrer(donnees[minutes], filtre_volume)
            entrainement = trades[trades["jour"] < DATE_COUPURE]
            resultats.append({"zone_min": minutes, "filtre_volume": filtre_volume, **statistiques(entrainement)})

    grille = pd.DataFrame(resultats).sort_values("esperance_R", ascending=False)
    print("\n=== ENTRAINEMENT (2021-2024) ===")
    print(grille.to_string(index=False))

    meilleur = grille.iloc[0]
    trades = filtrer(donnees[int(meilleur["zone_min"])], bool(meilleur["filtre_volume"]))
    test = trades[trades["jour"] >= DATE_COUPURE]
    stats_test = statistiques(test)

    print(f"\n=== TEST (2025-aujourd'hui) : zone de {meilleur['zone_min']} min, "   f"filtre volume = {meilleur['filtre_volume']} ===")
    print(f"Entrainement : {meilleur['esperance_R']:+.3f} R par trade")
    print(f"Test         : {stats_test['esperance_R']:+.3f} R par trade "   f"({stats_test['trades']} trades, {stats_test['reussite_pct']} % de réussite)")       


if __name__ == '__main__':
    main()