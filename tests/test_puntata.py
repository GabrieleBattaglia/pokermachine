# PokerMachine, prove sul prompt della puntata: scorciatoie, prefissi, errori e correzioni.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

import pytest

import pokermachine
from dati import nuovi_dati


@pytest.fixture
def chiedi(monkeypatch):
    """chiedi_puntata con le risposte scriptate; restituisce anche i suoni e le righe stampate."""

    def prepara(fiches, risposte, capsys):
        dati = nuovi_dati()
        dati["fiches_attuali"] = fiches
        coda = list(risposte)
        suonati = []
        monkeypatch.setattr(pokermachine, "dgt", lambda prompt="", **_: coda.pop(0))
        monkeypatch.setattr(pokermachine, "play_event", lambda nome, sync=True: suonati.append(nome))
        puntata = pokermachine.chiedi_puntata(dati, 1)
        return puntata, suonati, capsys.readouterr().out

    return prepara


@pytest.mark.parametrize(
    ("risposta", "attesa"),
    [
        ("-", 100),
        (",", 250),
        (".", 500),
        (";", 750),
        ("+", 1000),
        ("m", 30),
        ("M", 30),
        ("500", 500),
        ("1k", 1000),
        ("1K", 1000),
        ("0.5k", 500),
        ("0,25k", 250),
        ("1000", 1000),
    ],
)
def test_scorciatoie_e_prefissi_con_mille_fiches(chiedi, capsys, risposta, attesa):
    puntata, suonati, _ = chiedi(1000, [risposta], capsys)
    assert puntata == attesa
    assert "errore" not in suonati


def test_i_prefissi_valgono_sulle_puntate_alte(chiedi, capsys):
    puntata, _, _ = chiedi(5_000_000, ["1.5m"], capsys)
    assert puntata == 1_500_000
    puntata, _, _ = chiedi(5_000_000, ["200K"], capsys)
    assert puntata == 200_000
    # Sotto il tre per cento, che qui vale 150K, si sale al minimo.
    puntata, suonati, _ = chiedi(5_000_000, ["2.5k"], capsys)
    assert puntata == 150_000
    assert suonati == ["puntata_minima"]


def test_i_simboli_non_previsti_vengono_rifiutati(chiedi, capsys):
    puntata, suonati, uscita = chiedi(1000, [":", "!", "*", "abc", "-5", "1kk", "k", "1.2.3", "100"], capsys)
    assert puntata == 100
    assert suonati.count("errore") == 8
    assert uscita.count("Non ho capito") == 8


def test_sopra_le_fiches_si_rifiuta_e_sotto_il_minimo_si_corregge(chiedi, capsys):
    puntata, suonati, uscita = chiedi(1000, ["2k", "1001", "5"], capsys)
    assert puntata == 30
    assert suonati == ["errore", "errore", "puntata_minima"]
    assert uscita.count("Hai solo 1K fiches.") == 2
    assert "La puntata minima è 30, il 3 per cento: correggo." in uscita


def test_lo_zero_e_i_decimali_salgono_al_minimo(chiedi, capsys):
    assert chiedi(1000, ["0"], capsys)[0] == 30
    assert chiedi(1000, ["0.7"], capsys)[0] == 30
    assert chiedi(1000, ["0,02k"], capsys)[0] == 30


def test_invio_esce_e_r_mostra_le_statistiche(chiedi, capsys):
    puntata, suonati, uscita = chiedi(1000, ["r", ""], capsys)
    assert puntata is None
    assert suonati == ["statistiche"]
    assert "Statistiche." in uscita
