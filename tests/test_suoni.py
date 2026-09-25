# PokerMachine, prove sui suoni: ogni evento del gioco ha il suo preset e si ascolta nel collaudo.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 24/09/2026: nasce con la versione 5, che aggiunge i suoni nuovi.
# 25/09/2026: dal collaudo, mai lo stesso suono per due eventi diversi, ne' per
# nome del preset ne' per contenuto.

import json

from GBUtils import Acusticator

import ascolta_suoni
import regole
import trofei
from suoni import EVENTI


def test_ogni_punteggio_ogni_sorpresa_e_ogni_trofeo_ha_un_suono():
    for nome in regole.NOMI_PUNTEGGI:
        assert nome in EVENTI, nome
    for sorpresa in regole.SORPRESE:
        assert f"sorpresa_{sorpresa.chiave}" in EVENTI, sorpresa.chiave
    for suono in trofei.SUONI:
        assert suono in EVENTI, suono


def test_nessun_suono_si_ripete_fra_due_eventi():
    preset = list(EVENTI.values())
    assert len(set(preset)) == len(preset)
    impronte = {}
    for evento, nome in EVENTI.items():
        score, kind, adsr = Acusticator.preset(nome)
        assert score, f"il preset {nome} dell'evento {evento} manca dalla collezione"
        impronta = json.dumps([score, kind, adsr])
        assert impronta not in impronte, f"{evento} suona come {impronte.get(impronta)}"
        impronte[impronta] = evento


def test_l_ascolto_guidato_li_contiene_tutti():
    assert set(ascolta_suoni.ORDINE) == set(EVENTI)
    assert len(ascolta_suoni.ORDINE) == len(set(ascolta_suoni.ORDINE))
    assert set(ascolta_suoni.NUOVI) <= set(ascolta_suoni.ORDINE)
