import os
from symtable import Symbol
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import LimitOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus

load_dotenv()
client = TradingClient(os.getenv("ALPACA_API_KEY"), os.getenv("ALPACA_SECRET_KEY"), paper=True)

#1. L'état du compte
compte = client.get_account()
print("=== Compte Paper ===")
print(f"Statut          : {compte.status}")
print(f"Valeur totale   : {float(compte.equity):>12,.2f} $")
print(f"Liquidités      : {float(compte.cash):>12,.2f} $")
print(f"Pouvoir d'achat : {float(compte.buying_power):>12,.2f} $")

# 2. L'holorge du marché
horloge = client.get_clock()
print("\n=== Marché ===")
print(f"Ouvert maintenant    : {horloge.is_open}")
print(f"Prochaine ouverture  : {horloge.next_open}")
print(f"Prochaine fermeture  : {horloge.next_close}")

# 3. Les positions ouvertes
positions = client.get_all_positions()
print(f"\n=== Positions ouvertes : {len(positions)} ===")
for p in positions:
    print(f"{p.symbol} : {p.qty} actions, profit {float(p.unrealized_pl):+.2f} $")

# 4. Un ordre de test SANS RISQUE : acheter 1 action d'AAPL à 1$
ordre = LimitOrderRequest(
    symbol="AAPL",
    qty=1,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY,
    limit_price=1.00,
)

envoye = client.submit_order(ordre)
print(f"\nOrdre envoyé : {envoye.symbol}, statut={envoye.status}, id={envoye.id}")

# 5. On l'annule tout de suite
client.cancel_order_by_id(envoye.id)
print("Ordre annulé.")

# 6. l'historique des derniers ordres
print("\n===  5 derniers ordres ===")
derniers = client.get_orders(GetOrdersRequest(status=QueryOrderStatus.ALL, limit=5))
for o in derniers:
    print(f"{o.submitted_at:%Y-%m-%d %H:%M}  {o.side.value:4}  {o.qty}  {o.symbol:5} "   f"limite {o.limit_price}  ->  {o.status.value}")