import yfinance as yf

donnees = yf.download("AAPL", period="3mo", interval="1d", progress=False)

donnees.columns = donnees.columns.get_level_values(0)

donnees.columns = [c.lower() for c in donnees.columns]

donnees["fermeture_veille"] = donnees["close"].shift(1)
donnees["gap_pct"] = (donnees["open"] / donnees["fermeture_veille"] - 1) * 100

print(donnees[["fermeture_veille", "open", "gap_pct"]].tail(10).round(2))

print("\nPlus gros gaps à la hausse : ")
print(donnees.nlargest(5, "gap_pct")[["fermeture_veille", "open", "gap_pct"]].round(2))

