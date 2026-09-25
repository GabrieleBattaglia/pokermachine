# PokerMachine, prove sulle regole: punteggi, vincite, Killer Hand, soglie.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 24/09/2026: versione 5, le categorie dei dieci mazzi e la regola del
# punteggio migliore, con un valutatore di riferimento scritto a parte.

import random
from collections import Counter

import numpy as np
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


def tabella_con(**cambi):
    """La tabella del gioco con qualche multiplo cambiato, per provare la regola del migliore."""
    nomi = {
        "tris_gemello": "Tris gemello",
        "full": "Full",
        "colore": "Colore",
        "doppia": "Doppia coppia",
        "gemella_pagata": "Coppia gemella pagata",
    }
    tabella = dict(regole.TABELLA_VINCITE)
    for chiave, multiplo in cambi.items():
        tabella[nomi[chiave]] = multiplo
    return tabella


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


def test_le_gemelle():
    assert regole.valuta_mano(mano((7, "C"), (7, "C"), (7, "C"), (7, "C"), (7, "C"))) == "Cinque gemelle"
    assert regole.valuta_mano(mano((7, "C"), (7, "C"), (7, "C"), (7, "C"), (2, "Q"))) == "Poker gemello"
    assert regole.valuta_mano(mano((9, "F"), (9, "F"), (9, "F"), (2, "Q"), (5, "P"))) == "Tris gemello"
    assert regole.valuta_mano(mano((11, "P"), (11, "P"), (2, "Q"), (5, "F"), (8, "C"))) == "Coppia gemella pagata"
    assert regole.valuta_mano(mano((1, "Q"), (1, "Q"), (2, "Q"), (5, "F"), (8, "C"))) == "Coppia gemella pagata"
    assert regole.valuta_mano(mano((5, "C"), (5, "C"), (2, "Q"), (9, "F"), (13, "P"))) == "Coppia gemella"


def test_poker_per_valore():
    assert regole.valuta_mano(mano((1, "C"), (1, "Q"), (1, "F"), (1, "P"), (9, "C"))) == "Poker d'assi"
    assert regole.valuta_mano(mano((2, "C"), (2, "Q"), (2, "F"), (2, "P"), (9, "C"))) == "Poker dal 2 al 4"
    assert regole.valuta_mano(mano((4, "C"), (4, "Q"), (4, "F"), (4, "P"), (9, "C"))) == "Poker dal 2 al 4"
    assert regole.valuta_mano(mano((5, "C"), (5, "Q"), (5, "F"), (5, "P"), (9, "C"))) == "Poker"
    assert regole.valuta_mano(mano((13, "C"), (13, "Q"), (13, "F"), (13, "P"), (9, "C"))) == "Poker"


def test_full_a_colore():
    assert regole.valuta_mano(mano((7, "C"), (7, "C"), (7, "C"), (2, "C"), (2, "C"))) == "Full a colore"


def test_la_mano_paga_il_punteggio_migliore_che_contiene():
    full_gemello = mano((9, "C"), (9, "C"), (9, "C"), (2, "Q"), (2, "F"))
    assert regole.valuta_mano(full_gemello, tabella_con(tris_gemello=10, full=9)) == "Tris gemello"
    assert regole.valuta_mano(full_gemello, tabella_con(tris_gemello=8, full=9)) == "Full"
    colore_gemello = mano((6, "F"), (6, "F"), (6, "F"), (2, "F"), (12, "F"))
    assert regole.valuta_mano(colore_gemello, tabella_con(tris_gemello=10, colore=6)) == "Tris gemello"
    assert regole.valuta_mano(colore_gemello, tabella_con(tris_gemello=5, colore=6)) == "Colore"
    doppia_gemella = mano((11, "C"), (11, "C"), (5, "Q"), (5, "F"), (8, "P"))
    assert regole.valuta_mano(doppia_gemella, tabella_con(doppia=2, gemella_pagata=2)) == "Doppia coppia"
    assert regole.valuta_mano(doppia_gemella, tabella_con(doppia=2, gemella_pagata=3)) == "Coppia gemella pagata"


def test_con_le_coppie_mute_una_doppia_coppia_resta_pagata():
    tabella = dict(regole.TABELLA_VINCITE, **{"Coppia pagata": 0, "Coppia gemella pagata": 0, "Coppia gemella": 0})
    doppia_gemella = mano((11, "C"), (11, "C"), (5, "Q"), (5, "F"), (8, "P"))
    assert regole.valuta_mano(doppia_gemella, tabella) == "Doppia coppia"
    assert regole.calcola_vincita("Coppia pagata", 10, tabella) == 0


def test_mano_non_valida():
    assert regole.valuta_mano([]) == regole.MANO_NON_VALIDA
    assert regole.valuta_mano(mano((2, "C"), (5, "Q"), (9, "F"), (11, "P"))) == regole.MANO_NON_VALIDA


def test_tipo_della_carta():
    assert regole.tipo_carta(carta(2, "C")) == 0
    assert regole.tipo_carta(carta(1, "P")) == 51
    assert regole.tipo_carta(carta(11, "Q")) == regole.RANGO_JACK * 4 + 1


def _riferimento(tipi):
    """Le condizioni di una mano, scritte da capo in Python semplice, per il confronto."""
    ranghi = [t // 4 for t in tipi]
    per_rango = Counter(ranghi)
    per_tipo = Counter(tipi)
    colore = len({t % 4 for t in tipi}) == 1
    distinti = sorted(per_rango)
    scala = len(distinti) == 5 and (distinti[4] - distinti[0] == 4 or distinti == [0, 1, 2, 3, 12])
    reale = scala and distinti[0] == 8
    alti = [r for r, q in per_rango.items() if q >= 4]
    full = sorted(per_rango.values()) == [2, 3]
    return {
        "Cinque gemelle": max(per_tipo.values()) == 5,
        "Scala Reale": reale and colore,
        "Full a colore": full and colore,
        "Scala a colore": scala and colore and not reale,
        "Poker gemello": max(per_tipo.values()) >= 4,
        "Super Poker": max(per_rango.values()) == 5,
        "Poker d'assi": 12 in alti,
        "Poker dal 2 al 4": any(r <= 2 for r in alti),
        "Poker": any(3 <= r <= 11 for r in alti),
        "Tris gemello": max(per_tipo.values()) >= 3,
        "Full": full,
        "Colore": colore,
        "Scala": scala,
        "Tris": max(per_rango.values()) >= 3,
        "Doppia coppia": sum(1 for q in per_rango.values() if q >= 2) >= 2,
        "Coppia gemella pagata": any(q >= 2 and t // 4 >= 9 for t, q in per_tipo.items()),
        "Coppia pagata": any(q >= 2 and r >= 9 for r, q in per_rango.items()),
        "Coppia gemella": max(per_tipo.values()) >= 2,
        "Coppia non pagata": max(per_rango.values()) >= 2,
        "Carta alta": True,
    }


def test_le_condizioni_coincidono_con_il_riferimento():
    generatore = random.Random(24)
    scarpa = list(range(regole.NUM_TIPI)) * regole.NUM_MAZZI
    # Mani casuali, piu' quelle costruite apposta per le combinazioni rare.
    mani = [sorted(generatore.sample(scarpa, 5)) for _ in range(20000)]
    for _ in range(3000):
        t = generatore.randrange(regole.NUM_TIPI)
        altri = generatore.sample(scarpa, 5 - (quante := generatore.randint(2, 5)))
        mani.append(sorted([t] * quante + altri))
    condizioni = regole.bandiere(np.array(mani))
    for i, m in enumerate(mani):
        atteso = _riferimento(m)
        for nome in regole.NOMI_PUNTEGGI:
            assert bool(condizioni[nome][i]) == atteso[nome], (m, nome)


def test_vincite_e_puntata_minima():
    assert regole.calcola_vincita("Tris", 10) == 10 * regole.TABELLA_VINCITE["Tris"]
    assert regole.calcola_vincita("Carta alta", 10) == 0
    assert regole.calcola_vincita(regole.MANO_NON_VALIDA, 10) == 0
    assert regole.puntata_minima(428) == 12
    assert regole.puntata_minima(10) == 1
    assert regole.puntata_minima(1) == 1


def test_killer_hand_e_minimo_della_gara():
    assert regole.e_killer_hand(25)
    assert regole.e_killer_hand(100)
    assert not regole.e_killer_hand(26)
    assert not regole.e_killer_hand(0)
    minimi = [regole.minimo_killer_hand(n) for n in range(1, 10)]
    assert minimi == sorted(minimi)
    assert minimi[0] == int(regole.KILLER_HAND_BASE * regole.KILLER_HAND_FATTORE)


def test_tabelle_delle_sorprese_e_della_decisione():
    mute = regole.tabella_sorpresa(regole.SORPRESE_PER_CHIAVE["coppie_mute"])
    assert all(mute[nome] == 0 for nome in regole.COPPIE)
    assert mute["Tris"] == regole.TABELLA_VINCITE["Tris"]
    tutto = regole.tabella_sorpresa(regole.SORPRESE_PER_CHIAVE["tutto_o_niente"])
    assert all(multiplo != 1 for multiplo in tutto.values())
    semplice = regole.SORPRESE_PER_CHIAVE["nessuna"]
    decisione = regole.tabella_decisione(semplice)
    assert decisione["Tris"] == 1 + regole.KILLER_HAND_MOLTIPLICATORE * (regole.TABELLA_VINCITE["Tris"] - 1)
    assert decisione["Carta alta"] == 0
    assert regole.tabella_decisione(semplice, scudo=True)["Carta alta"] == 1
    assert regole.tabella_decisione() == regole.TABELLA_VINCITE


def test_soglie_di_fiches():
    assert regole.soglia_raggiunta(999) == 0
    assert regole.soglia_raggiunta(1000) == 1000
    assert regole.soglia_raggiunta(99999) == 10000
    assert regole.soglia_raggiunta(5000000) == 1000000


def test_i_punteggi_sono_ordinati_dal_piu_alto_e_i_pagati_restituiscono_almeno_la_puntata():
    multipli = [m for _, m in regole.PUNTEGGI]
    assert multipli == sorted(multipli, reverse=True)
    assert all(regole.TABELLA_VINCITE[nome] >= 1 for nome in regole.PUNTEGGI_PAGATI)
    assert "Coppia non pagata" not in regole.PUNTEGGI_PAGATI
    assert "Carta alta" not in regole.PUNTEGGI_PAGATI
