import pandas as pd
from scanner import TICKERS, telecharger

FUSEAU = "America/New_York"

def nettoyer(df):
    """ Met les colonnes en minuscules, retire les trous et la journée en cours. """
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    df = df.dropna()
    df.index = df.index.tz_convert(FUSEAU)
    aujourd_hui = pd.Timestamp.now(tz=FUSEAU).date()
    return df[df.index.date < aujourd_hui]

def analyser_jours(df):
    """ Une ligne par jour : zone de 15 minutes, cassures, amplitude, volume. """
    jours = []
    for jour, barres in df.groupby(df.index.date):
        premieres = barres.between_time("09:30", "09:40")
        apres = barres.between_time("09:45", "15:55")
        if len(premieres) < 3 or apres.empty:
            continue

        haut = premieres["high"].max()
        bas = premieres["low"].min()
        cassures = apres[apres["high"] > haut]

        jours.append({
            "haut_15min": haut,
            "largeur_pct": (haut / bas - 1) * 100,
            "cassure": len(cassures) > 0,
            "fermeture": apres["close"].iloc[-1],
            "amplitude_pct": (barres["high"].max() / barres["low"].min() - 1) * 100,
            "volume_dollars": (barres["close"] * barres["volume"]).sum(),
            })

    return pd.DataFrame(jours)

def statistiques(resume):
    """ Résume toutes les journées d'un titre en une seule ligne. """
    avec_cassure = resume[resume["cassure"]]
    if len(avec_cassure) > 0:
        au_dessus = (avec_cassure["fermeture"] > avec_cassure["haut_15min"]).mean() * 100
    else:
        au_dessus = None
    return {
            "jours": len(resume),
            "volume_M$": round(resume["volume_dollars"].mean() / 1_000_000),
            "amplitude_pct": round(resume["amplitude_pct"].mean(), 2),
            "largeur_15min_pct": round(resume["largeur_pct"].mean(), 2),
            "cassure": len(avec_cassure),
            "ferme_au_dessus_pct": round(au_dessus, 1) if au_dessus is not None else None,
            }

def main():
    print(f"Téléchargement de {len(TICKERS)} titres en barres de 5 minutes...")
    brut = telecharger(TICKERS, "60d", intervalle="5m")

    lignes = []
    for ticker in TICKERS:
        df = nettoyer(brut[ticker])
        if df.empty:
            print(f"   Aucune donnée pour {ticker}, on le saute.")
            continue
        resume = analyser_jours(df)
        if resume.empty:
            continue
        lignes.append({"ticker": ticker, **statistiques(resume)})

    tableau = pd.DataFrame(lignes)

    print("\n=== Classé par liquidité (le plus facile à trader au haut) ===")
    print(tableau.sort_values("volume_M$", ascending=False).to_string(index=False))

    print("\n=== Classé par amplitude (le plus de mouvement en haut) ===")
    print(tableau.sort_values("amplitude_pct", ascending=False).to_string(index=False))


if __name__ == "__main__":
    main()
