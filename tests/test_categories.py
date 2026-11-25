from categories import classer

def test_baisse_analyste():
    assert classer("Keybanc Downgrades Apple to Underweight, Announces $250 Price Target") == "baisse_analyste"
    assert classer("Citigroup Maintains Buy on Advanced Micro Devices, Lowers Price Target to $200") == "baisse_analyste"
    assert classer("Snap shares were trading lower after Morgan Stanley downgraded the stock") == "baisse_analyste"


def test_hausse_analyste():
    assert classer("Wedbush Upgrades Netflix to Outperform") == "hausse_analyste"
    assert classer("UBS Maintains Buy on NVIDIA, Raises Price Target to $540") == "hausse_analyste"


def test_resultats():
    assert classer("Shopify Q1 Adj. EPS $0.25 Misses $0.26 Estimate, Sales $2.36B Beat $2.33B Estimate") == "resultats"
    assert classer("Snap Sees Q3 2024 Revenue $1.335B-$1.375B Vs $1.25B Estimate") == "resultats"


def test_neutre_analyste():
    assert classer("Mizuho Reiterates Outperform on SoFi Techs, Maintains $14 Price Target") == "neutre_analyste"


def test_annonce_de_date_nest_pas_un_resultat():
    assert classer("Tesla To Report Its Q1 2023 Financial Results On Wednesday, April 19, 2023") == "autre"


def test_alerte_options_ne_declenche_jamais_de_trade():
    # categories.py ne contient pas de règle spéciale pour les alertes d'options
    # (voir les notes d'implémentation du README). Ce qui compte pour la stratégie,
    # c'est qu'une alerte ne soit jamais classée comme une baisse d'analyste.
    titre = "Apple Option Alert: Sep 16 $160 Calls Sweep near the Ask vs 72082 OI; Earnings 10/27 (est)"
    assert classer(titre) != "baisse_analyste"


def test_titre_vide():
    assert classer(None) == "autre"