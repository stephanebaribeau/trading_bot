import math
from typing import final
import pandas as pd
from scanner import TICKERS, preparer, telecharger
from optimisation import trouver_candidats, simuler_trade, DATE_COUPURE
from fade import simuler_short

STRATEGIE = "long"      # "long" (gap et go) ou "short" (gap fade)
STOP_LONG = 6
OBJECTIF_LONG = 8
STOP_SHORT = 4          # replace par le meilleur stop trouvé dans fade.py

CAPITAL_INITIAL = 10_000
RISQUE_PAR_TRADE_PCT = 1.0      # on risque 1% du capital par trade
POSITION_MAX_PCT = 25.0         # une position ne dépasse jamais 25% du capital
MAX_TRADES_PAR_JOUR = 3
COMMISSION_PAR_ORDRE = 1.0      # en $, à l'achat et à la vente


def rendement_trade(ligne):
    """ Rendement en % d'une trade, selon la stratégie choisi. """
    if STRATEGIE == "long":
        return simuler_trade(ligne, STOP_LONG, OBJECTIF_LONG)
    return simuler_short(ligne, STOP_SHORT)


def taille_position(capital, prix):
    """ Nombre d'actions pour r isquer RISQUE_PAR_TRADE_PCT du capital. """
    stop_pct = STOP_LONG if STRATEGIE == "long" else STOP_SHORT
    risque_dollars = capital * RISQUE_PAR_TRADE_PCT / 100
    perte_par_action = prix * stop_pct / 100
    actions = risque_dollars / perte_par_action
    actions_max = capital * POSITION_MAX_PCT / 100 / prix
    return math.floor(min(actions, actions_max))

def main():
    brut = telecharger(TICKERS, "5y")
    donnees = {t: preparer(brut[t]) for t in TICKERS}

    #test = [c for c in trouver_candidats(donnees) if c[0] >= DATE_COUPURE]
    PERIODE = "test"    # entrainement ou test

    candidats = trouver_candidats(donnees)
    if PERIODE == "test":
        selection = [c for c in candidats if c[0] >= DATE_COUPURE]
    else:
        selection = [c for c in candidats if c[0] < DATE_COUPURE]

    par_jour = {}
    for date, ticker, ligne in selection:
        par_jour.setdefault(date, []).append((ticker, ligne))

    capital = CAPITAL_INITIAL
    historique = []
    trades = []

    for date in sorted(par_jour):
        du_jour = sorted(par_jour[date], key=lambda x: x[1]["gap_pct"], reverse=True)
        du_jour = du_jour[:MAX_TRADES_PAR_JOUR]

        capital_debut = capital
        for ticker, ligne in du_jour:
            actions = taille_position(capital_debut, ligne["open"])
            if actions < 1:
                continue
            valeur = actions * ligne["open"]
            profit_brut = valeur * rendement_trade(ligne) / 100
            commissions = 2 * COMMISSION_PAR_ORDRE
            capital += profit_brut - commissions
            trades.append({"date": date.date(), "ticker": ticker, "actions": actions, "valeur": round(valeur,2), "profit_brut": round(profit_brut, 2), "commissions": commissions})

        historique.append((date, capital))

    trades = pd.DataFrame(trades)
    equite = pd.Series(dict(historique))
    drawdown_max = (equite / equite.cummax() - 1).min() * 100

    print(f"=== {STRATEGIE.upper()} : période de {PERIODE} (2025-aujourd'hui) ===")
    print(f"Capital initial             : {CAPITAL_INITIAL:>10,.2f} $")
    print(f"Capital final               : {capital:>10,.2f} $")
    print(f"Rendement total             : {(capital / CAPITAL_INITIAL - 1) * 100:>+10.2f} %")
    print(f"Nombre de trades            : {len(trades):>10}")
    print(f"Taille moyenne              : {trades['valeur'].mean():>10,.2f} $")
    print(f"Profit avant frais          : {trades['profit_brut'].sum():>+10,.2f} $")
    print(f"Commissions payées          : {trades['commissions'].sum():>10,.2f} $")
    print(f"Pire baisse                 : {drawdown_max:>10.2f} %")

    spy = preparer(telecharger(["SPY"], "5y")["SPY"])
    debut = equite.index.min()
    fin = equite.index.max()
    spy_periode = spy[(spy.index >= debut) & (spy.index <= fin)]
    rendement_spy = (spy_periode["close"].iloc[-1] / spy_periode["open"].iloc[0] - 1) * 100
    print(f"\nSPY (acheter et garder) : {rendement_spy:+.2f} % sur la même période")

if __name__ == "__main__":
    main()

