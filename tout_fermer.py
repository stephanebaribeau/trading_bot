import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient

load_dotenv()
client = TradingClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"), paper=True)
client.close_all_positions(cancel_orders=True)
print("Tous les ordres sont annulés et toutes les positions sont vendues.")
