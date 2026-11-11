import os
from datetime import datetime
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import Adjustment, DataFeed

load_dotenv()
client = StockHistoricalDataClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"))

requete = StockBarsRequest(
    symbol_or_symbols="AMD",
    timeframe=TimeFrame(5, TimeFrameUnit.Minute),
    start=datetime(2023,1,1),
    end=datetime(2023,1,31),
    feed=DataFeed.SIP,
    adjustment=Adjustment.ALL,
    )

barres = client.get_stock_bars(requete).df

print(barres.head(10))
print(f"\n{len(barres)} barres")
print("Fuseau horaire : ", barres.index.get_level_values("timestamp").tz)
