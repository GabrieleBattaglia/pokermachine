# PokerMachine, prove sulle regole: punteggi, vincite, Killer Hand, soglie.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

from GBUtils import Mazzo

import regole

SEMI = {"C": ("Cuori", 1), "Q": ("Quadri", 2), "F": ("Fiori", 3), "P": ("Picche", 4)}


def carta(valore, seme):
    """Una Carta come quelle di Mazzo: valore da 1 a 13, seme come lettera."""
    nome_seme, id_seme = SEMI[seme]
    return Mazzo.Carta(
        id=0, nome=f"{valore} di {nome_seme}", valore=valore, seme_nome=nome_seme, seme_id=id_seme, desc_breve=f"{valore}{seme}"
    )


def mano(*coppie):
    return [carta(v, s) for v, s in coppie]


def test_scala_reale():
    assert regole.valuta_mano(mano((10, "C"), (11, "C"), (12, "C"), (13, "C"), (1, "C"))) == "Scala Reale"


def test_scala_a_colore_anche_bassa_con_l_asso():
    assert regole.valuta_mano(mano((5, "P"), (6, "P"), (7, "P"), (8, "P"), (9, "P"))) == "Scala a colore"
    assert regole.valuta_mano(mano((1, "P"), (2, "P"), (3, "P"), (4, "P"), (5, "P"))) == "Scala a colore"


def test_super_poker_con_dieci_mazzi():
    assert regole.valuta_mano(mano((7, "C"), (7, "C"), (7, "Q"), (7, "F"), (7, "P"))) == "Super Poker"


def test_poker_full_colore_scala():
    assert regole.valuta_mano(mano((7, "C"), (7, "Q"), (7, "F"), (7, "P"), (2, "C"))) == "Poker"
    assert regole.valuta_mano(mano((7, "C"), (7, "Q"), (7, "F"), (2, "P"), (2, "C"))) == "Full"
    assert regole.valuta_mano(mano((2, "F"), (5, "F"), (9, "F"), (11, "F"), (13, "F"))) == "Colore"
    assert regole.valuta_mano(mano((10, "C"), (11, "Q"), (12, "F"), (13, "P"), (1, "C"))) == "Scala"
    assert regole.valuta_mano(mano((1, "C"), (2, "Q"), (3, "F"), (4, "P"), (5, "C"))) == "Scala"


def test_tris_doppia_coppia_e_coppie():
    assert regole.valuta_mano(mano((9, "C"), (9, "Q"), (9, "F"), (2, "P"), (5, "C"))) == "Tris"
    assert regole.valuta_mano(mano((9, "C"), (9, "Q"), (4, "F"), (4, "P"), (5, "C"))) == "Doppia coppia"
    assert regole.valuta_mano(mano((11, "C"), (11, "Q"), (4, "F"), (7, "P"), (5, "C"))) == "Coppia pagata"
    assert regole.valuta_mano(mano((1, "C"), (1, "Q"), (4, "F"), (7, "P"), (5, "C"))) == "Coppia pagata"
    assert regole.valuta_mano(mano((10, "C"), (10, "Q"), (4, "F"), (7, "P"), (5, "C"))) == "Coppia non pagata"


def test_carta_alta_e_una_coppia_non_finge_la_scala():
    assert regole.valuta_mano(mano((2, "C"), (5, "Q"), (9, "F"), (11, "P"), (13, "C"))) == "Carta alta"
    assert regole.valuta_mano(mano((2, "C"), (2, "Q"), (3, "F"), (4, "P"), (5, "C"))) == "Coppia non pagata"
    assert regole.valuta_mano(mano((12, "C"), (13, "Q"), (1, "F"), (2, "P"), (3, "C"))) == "Carta alta"


def test_mano_non_valida():
    assert regole.valuta_mano([]) == regole.MANO_NON_VALIDA
    assert regole.valuta_mano(mano((2, "C"), (5, "Q"), (9, "F"), (11, "P"))) == regole.MANO_NON_VALIDA


def test_vincite_e_puntata_minima():
    assert regole.calcola_vincita("Tris", 10) == 30
    assert regole.calcola_vincita("Coppia pagata", 10) == 10
    assert regole.calcola_vincita("Carta alta", 10) == 0
    assert regole.calcola_vincita(regole.MANO_NON_VALIDA, 10) == 0
    assert regole.puntata_minima(428) == 12
    assert regole.puntata_minima(10) == 1
    assert regole.puntata_minima(1) == 1


def test_killer_hand_e_penalita():
    assert regole.e_killer_hand(25)
    assert regole.e_killer_hand(100)
    assert not regole.e_killer_hand(26)
    assert not regole.e_killer_hand(0)
    assert regole.penalita_percentuale(1) == 10
    assert regole.penalita_percentuale(9) == 90
    assert regole.penalita_percentuale(12) == 90


def test_soglie_di_fiches():
    assert regole.soglia_raggiunta(999) == 0
    assert regole.soglia_raggiunta(1000) == 1000
    assert regole.soglia_raggiunta(99999) == 10000
    assert regole.soglia_raggiunta(5000000) == 1000000


def test_i_punteggi_sono_ordinati_dal_piu_alto_e_i_pagati_sono_dieci():
    multipli = [m for _, m in regole.PUNTEGGI]
    assert multipli == sorted(multipli, reverse=True)
    assert len(regole.PUNTEGGI_PAGATI) == 10
    assert "Coppia non pagata" not in regole.PUNTEGGI_PAGATI
