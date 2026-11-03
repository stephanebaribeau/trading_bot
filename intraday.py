import pandas as pd
from scanner import telecharger

TICKER = "NVDA"
FUSEAU = "America/New_York"

brut = telecharger([TICKER], "60d", intervalle="5m")
df = brut[TICKER].copy()
df.columns = [c.lower() for c in df.columns]
df = df.dropna()
df.index = df.index.tz_convert(FUSEAU)

aujourd_hui = pd.Timestamp.now(tz=FUSEAU).date()
df = df[df.index.date < aujourd_hui]

print(df.head(8).round(2))
print(f"\n{len(df)} barres de 5 minutes\n")

jours = []
for jour, barres in df.groupby(df.index.date):
    premieres = barres.between_time("09:30", "09:40")
    apres = barres.between_time("09:45", "15:55")
    if len(premieres) < 3 or apres.empty:
        continue

    haut = premieres["high"].max()
    bas = premieres["low"].min()
    cassures = apres[apres["high"] > haut]
    fermeture = apres["close"].iloc[-1]

    jours.append({
        "jour": jour,
        "haut_15min": round(haut, 2),
        "bas_15min": round(bas, 2),
        "largeur_pct": round((haut / bas - 1) * 100, 2),
        "cassure": cassures.index[0].strftime("%H:%M") if len(cassures) > 0 else "-",
        "fermeture": round(fermeture, 2),
        })

resume = pd.DataFrame(jours)
print(resume.tail(15).to_string(index=False))

avec_cassure = resume[resume["cassure"] != "-"]
au_dessus = (avec_cassure["fermeture"] > avec_cassure["haut_15min"]).mean() * 100

print(f"\nJours analysés                        : {len(resume)}")
print(f"Jours avec cassure du haut              : {len(avec_cassure)}")
print(f"({len(avec_cassure) / len(resume) * 100:.0f} %)")
print(f"Après une cassure, fermeture au-dessus  : {au_dessus:.1f} %")
print(f"Largeur moyenne des 15 premières min.   : {resume['largeur_pct'].mean():.2f} %")

