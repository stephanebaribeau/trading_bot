from bot import nombre_actions


def test_taille_limitee_par_le_risque():
    # Risque de 1 000 $ (1 % de 100 000 $) et 10 $ de risque par action : 100 actions
    assert nombre_actions(100_000, haut=100, bas=90) == 100


def test_taille_limitee_par_le_plafond_de_25_pourcent():
    # Le risque permettrait 200 actions, mais 25 % du compte n'en achète que 71
    assert nombre_actions(100_000, haut=350, bas=345) == 71


def test_zone_sans_largeur():
    assert nombre_actions(100_000, haut=100, bas=100) == 0