from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from alpaca.trading.enums import OrderSide, OrderStatus

from bilan import construire_trades

MATIN = datetime(2026, 11, 25, 15, 0, tzinfo=timezone.utc)    # 10 h à New York
FIN = datetime(2026, 11, 25, 20, 55, tzinfo=timezone.utc)     # 15 h 55 à New York


def ordre(**champs):
    """Un faux ordre Alpaca, avec seulement les champs utilisés par le bilan."""
    defauts = dict(symbol="AAPL", side=OrderSide.BUY, status=OrderStatus.FILLED,
                   legs=None, filled_at=MATIN, filled_avg_price=None,
                   filled_qty="10", stop_price=None)
    return SimpleNamespace(**{**defauts, **champs})


def test_trade_ferme_a_la_fin_de_journee():
    stop = ordre(side=OrderSide.SELL, status=OrderStatus.CANCELED, stop_price="99.00")
    achat = ordre(legs=[stop], filled_avg_price="101.10", stop_price="101.01")
    vente = ordre(side=OrderSide.SELL, filled_at=FIN, filled_avg_price="103.00")

    trades = construire_trades([achat, vente])
    assert len(trades) == 1
    t = trades.iloc[0]
    assert t["raison"] == "fermeture"
    assert t["resultat_R"] == pytest.approx((103.00 - 101.10) / (101.10 - 99.00))
    assert t["glissement_entree_pct"] == pytest.approx((101.10 / 101.01 - 1) * 100)


def test_trade_sorti_par_le_stop():
    stop = ordre(side=OrderSide.SELL, stop_price="50.00", filled_avg_price="49.95")
    achat = ordre(symbol="AMD", legs=[stop], filled_avg_price="52.00")

    t = construire_trades([achat]).iloc[0]
    assert t["raison"] == "stop"
    assert t["resultat_R"] < -1


def test_achat_jamais_execute():
    stop = ordre(side=OrderSide.SELL, status=OrderStatus.CANCELED, stop_price="99.00")
    achat = ordre(status=OrderStatus.CANCELED, legs=[stop])
    assert construire_trades([achat]).empty