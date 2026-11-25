import pandas as pd
import pytest

from orb import heures_range, simuler_orb

JOUR = "2026-01-05"
FUSEAU = "America/New_York"


def journee(barres_speciales):
    """Une journée calme de barres de 5 minutes, avec quelques barres modifiées.
    Zone d'ouverture : haut 100,5 $ et bas 99,0 $ (fixé par la barre de 9:30)."""
    index = pd.date_range(f"{JOUR} 09:30", f"{JOUR} 15:55", freq="5min", tz=FUSEAU)
    df = pd.DataFrame({"open": 100.0, "high": 100.5, "low": 99.6,
                       "close": 100.0, "volume": 1000}, index=index)
    barres_speciales = {"09:30": [100.0, 100.5, 99.0, 100.0], **barres_speciales}
    for heure, valeurs in barres_speciales.items():
        df.loc[pd.Timestamp(f"{JOUR} {heure}", tz=FUSEAU), ["open", "high", "low", "close"]] = valeurs
    return df


def test_heures_range():
    assert heures_range(15) == ("09:40", "09:45")
    assert heures_range(5) == ("09:30", "09:35")


def test_pas_de_cassure_pas_de_trade():
    assert simuler_orb(journee({})) is None


def test_journee_incomplete():
    df = journee({}).drop(pd.Timestamp(f"{JOUR} 09:35", tz=FUSEAU))
    assert simuler_orb(df) is None


def test_cassure_puis_fermeture():
    trade = simuler_orb(journee({
        "10:00": [100.4, 101.0, 100.3, 100.9],   # cassure du haut (100,5 $)
        "15:55": [100.9, 101.2, 100.8, 101.0],   # fermeture à 101 $
    }))
    entree = 100.5 * 1.0005                       # au haut, plus le glissement
    sortie = 101.0 * 0.9995                       # à la fermeture, moins le glissement
    assert trade["heure_entree"] == "10:00"
    assert trade["raison"] == "fermeture"
    assert trade["resultat_R"] == pytest.approx((sortie - entree) / (entree - 99.0))


def test_cassure_puis_stop():
    trade = simuler_orb(journee({
        "10:00": [100.4, 101.0, 100.3, 100.9],
        "10:30": [100.0, 100.1, 98.5, 98.8],      # touche le stop (99 $)
    }))
    assert trade["raison"] == "stop"
    assert trade["resultat_R"] == pytest.approx(-1.03, abs=0.01)


def test_stop_saute_par_un_trou_de_prix():
    trade = simuler_orb(journee({
        "10:00": [100.4, 101.0, 100.3, 100.9],
        "10:30": [98.0, 98.2, 97.5, 97.8],        # ouvre déjà sous le stop
    }))
    assert trade["raison"] == "stop"
    assert trade["resultat_R"] < -1.5              # on sort à 98 $, pas à 99 $