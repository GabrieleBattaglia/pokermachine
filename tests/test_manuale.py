# PokerMachine, prove sulla guida: dice quello che il gioco fa davvero.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 25/09/2026: nasce con la versione 5, perche' la tabella tarata non resti
# diversa da quella scritta nella guida.

import os

import regole
import sfide
import trofei
from version import VERSION

GUIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "manuale.txt")


def _guida():
    with open(GUIDA, encoding="utf-8") as f:
        return f.read()


def test_la_guida_ha_la_versione_del_programma():
    assert f"Versione {VERSION}." in _guida()


def test_la_guida_ha_ogni_punteggio_con_il_suo_multiplo():
    righe = _guida().splitlines()
    for nome, multiplo in regole.PUNTEGGI:
        if multiplo == 0:
            assert any(nome in r and "persa" in r for r in righe), nome
        else:
            assert any(r.startswith(f"{nome}: {multiplo}") for r in righe), nome


def test_la_guida_ha_i_minimi_della_gara_e_gli_scudi():
    testo = _guida()
    for numero in (1, 2, 3, 9, 10):
        assert str(regole.minimo_killer_hand(numero)) in testo
    for nome in regole.PUNTEGGI_SCUDO:
        assert nome in testo
    assert "al massimo tre" in testo
    assert regole.SCUDI_MAX == 3


def test_la_guida_nomina_ogni_sorpresa_e_conta_trofei_e_sfide():
    testo = _guida()
    for sorpresa in regole.SORPRESE:
        assert sorpresa.nome in testo, sorpresa.nome
    assert sfide.QUANTE == 3
    assert "tre sfide" in testo
    assert len(trofei.TROFEI) == 22
