import yfinance as yf
import pandas as pd
import warnings

TICKERS = ["AAPL", "NVDA", "AMD", "TSLA", "META", "PLTR", "COIN", "MU", "SOFI", "MARA", "RIVN", "SNAP", "UBER", "SHOP", "NFLX"]

GAP_MIN = 3.0  # au moins +3%
GAP_MAX = 15.0 # au plus +15%
PRIX_MIN = 5.0  # pas de penny stock
VOLUME_MIN = 1_000_000

warnings.filterwarnings("ignore", message=".*inplace keywords.*")

def preparer(df):
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    df = df.dropna()
    df["fermeture_veille"] = df["close"].shift(1)
    df["gap_pct"] = (df["open"] / df["fermeture_veille"] - 1) * 100

    df["volume_moyen"] = df["volume"].shift(1).rolling(20).mean()
    return df

def passe_les_filtres(ligne):
    """Retourne True si cette journée est un bon candidat."""
    return(
            GAP_MIN <= ligne["gap_pct"] <= GAP_MAX
            and ligne["open"] >= PRIX_MIN
            and ligne["volume_moyen"] >= VOLUME_MIN
            )

if __name__ == "__main__":
    brut = yf.download(TICKERS, period="6mo", interval="1d", group_by="ticker", progress=False)

    candidats = []
    for ticker in TICKERS:
        df = preparer(brut[ticker])
        for date, ligne in df.iterrows():
            if passe_les_filtres(ligne):
                candidats.append({
                    "date": date.date(),
                    "ticker": ticker,
                    "gap_pct": round(ligne["gap_pct"], 2),
                    "ouverture": round(ligne["open"], 2),
                    })

    resultat = pd.DataFrame(candidats).sort_values("date")
    print(resultat.tail(20).to_string(index=False))
    print(f"\n{len(resultat)} gaps trouvés en 6 mois sur {len(TICKERS)} titres")

