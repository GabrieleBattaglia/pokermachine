# PokerMachine, prove sul motore della tenuta migliore.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 24/09/2026: nasce con la versione 5. Il motore si confronta con l'enumerazione
# diretta delle pescate su scarpe piccole, dove si possono contare una per una.

from itertools import combinations

import numpy as np
import pytest

import regole
import strategia


def _esatte(mano, scarpa, maschera, tabella):
    """Il valore di una tenuta contando una per una le pescate di carte fisiche distinte."""
    tenuti = [mano[i] for i in strategia.carte_tenute(maschera)]
    k = regole.CARTE_PER_MANO - len(tenuti)
    totale = valore = 0
    for pescate in combinations(scarpa, k):
        riga = np.array([sorted(tenuti + list(pescate))])
        condizioni = regole.bandiere(riga)
        nome = regole.migliore_punteggio([n for n in regole.NOMI_PUNTEGGI if condizioni[n][0]], tabella)
        valore += tabella[nome]
        totale += 1
    return valore / totale


def test_il_motore_coincide_con_le_pescate_contate_una_per_una():
    generatore = np.random.default_rng(7)
    for _ in range(3):
        scarpa = [int(t) for t in generatore.choice(regole.NUM_TIPI, 14)]
        mano = [int(t) for t in generatore.choice(regole.NUM_TIPI, 5)]
        tenute = strategia.valuta_tenute(mano, np.bincount(scarpa, minlength=regole.NUM_TIPI))
        for maschera in (0, 1, 0b00110, 0b01011, 0b01111, 0b11111):
            assert tenute[maschera].valore == pytest.approx(_esatte(mano, scarpa, maschera, regole.TABELLA_VINCITE), abs=1e-12)


def test_le_distribuzioni_sommano_a_uno_e_la_migliore_e_ottima():
    copie = np.full(regole.NUM_TIPI, regole.NUM_MAZZI)
    mano = [51, 50, 49, 48, 3]
    for t in mano:
        copie[t] -= 1
    tenute = strategia.valuta_tenute(mano, copie)
    assert all(t.distribuzione.sum() == pytest.approx(1) for t in tenute)
    assert strategia.migliore(tenute).maschera == 0b01111
    assert strategia.e_ottima(tenute, 0b01111)
    assert not strategia.e_ottima(tenute, 0)


def test_la_scarpa_corta_si_pesca_da_se_e_si_rimescola_solo_se_non_basta():
    # Restano tre assi di picche: chi tiene i due assi ne pesca tre e fa le
    # cinque gemelle di sicuro; chi ne pesca di piu' passa dal rimescolamento.
    mano = [51, 51, 41, 25, 13]
    scarpa = np.zeros(regole.NUM_TIPI, dtype=int)
    scarpa[51] = 3
    rimescolo = np.full(regole.NUM_TIPI, regole.NUM_MAZZI) - np.bincount(mano, minlength=regole.NUM_TIPI)
    tenute = strategia.valuta_tenute(mano, scarpa, rimescolo=rimescolo)
    assert tenute[0b00011].valore == pytest.approx(regole.TABELLA_VINCITE["Cinque gemelle"])
    assert tenute[0].valore < 5
    with pytest.raises(ValueError):
        strategia.valuta_tenute(mano, scarpa)
    scarpa[0] = -1
    with pytest.raises(ValueError):
        strategia.valuta_tenute(mano, scarpa, rimescolo=rimescolo)
