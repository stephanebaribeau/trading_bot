import pandas as pd
from pandas.tseries.offsets import Minute
from scanner import TICKERS, telecharger
from classement import nettoyer

GLISSEMENT_PCT = 0.05


def heures_range(minutes_range):
    """ Heure de la dernière barre de la zone d'ouverture. """
    debut = pd.Timestamp("09:30")
    fin = debut + pd.Timedelta(minutes=minutes_range - 5)
    action = debut + pd.Timedelta(minutes=minutes_range)
    return fin.strftime("%H:%M"), action.strftime("%H:%M")

def simuler_orb(barres, minutes_range=15):
    """ Simule un trade ORB sur une journée. Return un dict, ou None s'il n'y a pas de trade. """
    fin_range, debut_action = heures_range(minutes_range)
    premieres = barres.between_time("09:30", fin_range)
    apres = barres.between_time(debut_action, "15:55")
    if len(premieres) < minutes_range // 5 or apres.empty:
        return None
    haut = premieres["high"].max()
    stop = premieres["low"].min()

    entree = None
    sortie = None

    for heure, barre in apres.iterrows():
        if entree is None:
            if barre["high"] > haut:
                # Si la barre ouvre déjà au-dessus du haut, on entre à l'ouverture
                entree = max(barre["open"], haut) * (1 + GLISSEMENT_PCT / 100)
                heure_entree = heure
                #Pire cas : si cette meme barre touche aussi le stop, on support que le stop a été touché après notre entree
                if barre["low"] <= stop:
                    sortie, raison = stop, "stop"
                    break

        else:
            if barre["low"] <= stop:
                # Si la barre ouvre déjà sous le stop, on sort à l'ouverture
                sortie, raison = min(barre["open"], stop), "stop"
                break

    if entree is None:
        return None
    if sortie is None:
        sortie, raison = apres["close"].iloc[-1], "fermeture"

    sortie = sortie * (1 - GLISSEMENT_PCT /100)
    risque = entree - stop
    return {
        "heure_entree": heure_entree.strftime("%H:%M"),
        "rendement_pct": (sortie / entree - 1) * 100,
        "resultat_R": (sortie - entree) / risque,
        "raison": raison,
        }



def main():
    print(f"Téléchargement de {len(TICKERS)} titres en barres de 5 minutes...")
    brut = telecharger(TICKERS, "60d", intervalle="5m")

    trades = []
    for ticker in TICKERS:
        df = nettoyer(brut[ticker])
        for jour, barres in df.groupby(df.index.date):
            trade = simuler_orb(barres)
            if trade is not None:
                trades.append({"jour": jour, "ticker": ticker, **trade})

    trades = pd.DataFrame(trades)
    print(trades.tail(10).round(2).to_string(index=False))

    gagnants = trades[trades["rendement_pct"] > 0]
    perdants = trades[trades["rendement_pct"] <= 0]

    print(f"\nNombre de trades : {len(trades)}")
    print(f"Taux de réussite        : {len(gagnants) / len(trades) * 100:.1f} %")  
    print(f"Gain moyen              : {gagnants['rendement_pct'].mean():+.2f} %   " f"({gagnants['resultat_R'].mean():+.2f} R)")           
    print(f"Perte moyen             : {perdants['rendement_pct'].mean():+.2f} %   " f"({perdants['resultat_R'].mean():+.2f} R)")
    print(f"Espérance               : {trades['rendement_pct'].mean():+.3f} % par trade     " f"({trades['resultat_R'].mean():+.3f} R)")

    print("\nSorties :")
    print(trades["raison"].value_counts().to_string())

    print("\n=== Par ticker ===")
    par_ticker = trades.groupby("ticker")["resultat_R"].agg(trades="count", esperance_R="mean").round(3).sort_values("esperance_R", ascending=False)
    print(par_ticker.to_string())


if __name__ == "__main__":
    main()