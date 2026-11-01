import yfinance as yf

donnees = yf.download("AAPL", period="3mo", interval="1d", progress=False)

print(donnees.head())
print("...")
print(donnees.tail())

print(f"\nNombre de jours : {len(donnees)}")

