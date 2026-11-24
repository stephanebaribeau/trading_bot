import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import StopOrderRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
from alpaca.data.enums import DataFeed

load_dotenv()
trading = TradingClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"), paper=True)
donnees = StockHistoricalDataClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"))

dernier = donnees.get_stock_latest_trade(StockLatestTradeRequest(symbol_or_symbols="AAPL", feed=DataFeed.IEX))
prix = dernier["AAPL"].price
print(f"Dernier prix d'AAPL : {prix:.2f} $")

ordre = StopOrderRequest(
    symbol="AAPL",
    qty=1,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY,
    stop_price=round(prix * 1.5, 2),
    order_class=OrderClass.OTO,
    stop_loss=StopLossRequest(stop_price=round(prix  * 0.5, 2)),
)

try:
    envoye = trading.submit_order(ordre)
    print(f"✅ Accepté : statut = {envoye.status.value}, class = {envoye.order_class.value}")
    trading.cancel_order_by_id(envoye.id)
    print("Ordre annulé.")
except Exception as erreur:
    print(f"❌ Refusé : {erreur}")
