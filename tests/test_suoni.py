# PokerMachine, prove sui suoni: ogni evento del gioco ha il suo preset e si ascolta nel collaudo.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 24/09/2026: nasce con la versione 5, che aggiunge trenta suoni.

import ascolta_suoni
import regole
import trofei
from suoni import EVENTI


def test_ogni_punteggio_ogni_sorpresa_e_ogni_famiglia_di_trofei_ha_un_suono():
    for nome in regole.NOMI_PUNTEGGI:
        assert nome in EVENTI, nome
    for sorpresa in regole.SORPRESE:
        assert f"sorpresa_{sorpresa.chiave}" in EVENTI, sorpresa.chiave
    for famiglia in trofei.FAMIGLIE:
        assert famiglia in EVENTI, famiglia


def test_l_ascolto_guidato_li_contiene_tutti():
    assert set(ascolta_suoni.ORDINE) == set(EVENTI)
    assert len(ascolta_suoni.ORDINE) == len(set(ascolta_suoni.ORDINE))
    assert set(ascolta_suoni.NUOVI) <= set(ascolta_suoni.ORDINE)
