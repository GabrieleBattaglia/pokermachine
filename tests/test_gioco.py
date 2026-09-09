# PokerMachine, prova sul programma principale: una sessione intera senza console e senza suoni.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

import json

import pytest

import dati
import pokermachine
import regole


class Copione:
    """Gli ingressi scriptati al posto di dgt, e la lista degli eventi suonati."""

    def __init__(self, risposte):
        self.risposte = list(risposte)
        self.prompt = []
        self.suonati = []

    def dgt(self, prompt="", **_):
        self.prompt.append(prompt)
        if not self.risposte:
            raise AssertionError(f"il copione e' finito al prompt {prompt!r}")
        return self.risposte.pop(0)

    def play_event(self, nome, sync=True):
        self.suonati.append(nome)
        return True


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Il programma con disco, tastiera e casse sostituiti."""
    monkeypatch.setattr(dati, "cartella_programma", lambda: str(tmp_path))
    monkeypatch.setattr(pokermachine, "key", lambda *a, **k: "\r")
    monkeypatch.setattr(pokermachine, "gestisci_aggiornamento", lambda *a, **k: False)

    def prepara(risposte):
        copione = Copione(risposte)
        monkeypatch.setattr(pokermachine, "dgt", copione.dgt)
        monkeypatch.setattr(pokermachine, "play_event", copione.play_event)
        return copione

    return prepara


def test_due_mani_e_uscita(banco, tmp_path, capsys):
    copione = banco(
        [
            "abc",  # non e' una puntata
            "5000",  # piu' delle fiches
            "r",  # le statistiche
            "0",  # sale al minimo
            "",  # cambia tutte le carte
            "m",  # il minimo: non si puo' andare in game over
            "13",  # tiene la prima e la terza
            "",  # esce
        ]
    )
    assert pokermachine.main() == 0
    uscita = capsys.readouterr().out
    assert "Primo avvio" in uscita
    assert "Non ho capito" in uscita
    assert "Hai solo 200 fiches" in uscita
    assert "La puntata minima è 6" in uscita
    assert "Tieni tutte" not in uscita
    assert "Mano finale:" in uscita
    assert "Hai iniziato la sessione con 200 fiches." in uscita
    assert copione.prompt[0].startswith("F 200 S 1 R 0 M 1>")
    assert copione.prompt[-1].startswith("F ")
    assert any(p.endswith(" tieni? ") for p in copione.prompt)
    assert all(len(p) <= 30 for p in copione.prompt)
    for evento in ("avvio", "mescola", "errore", "statistiche", "puntata_minima", "puntata", "distribuzione", "scarto", "chiusura"):
        assert evento in copione.suonati
    assert any(nome in regole.NOMI_PUNTEGGI for nome in copione.suonati)
    with open(dati.percorso(cartella=str(tmp_path)), encoding="utf-8") as f:
        salvato = json.load(f)
    assert salvato["mani_giocate"] == 2
    assert salvato["launches"] == 1
    assert salvato["fiches_guadagnate"] - salvato["fiches_perdute"] == salvato["fiches_attuali"] - regole.FICHES_INIZIALI
    assert sum(v["conteggio"] for v in salvato["punteggi"].values()) == 2
    assert not any("*" * 3 in riga or "=" * 3 in riga or "-" * 3 in riga for riga in uscita.splitlines())


class CopioneTuttoDentro(Copione):
    """Punta sempre tutto e cambia sempre tutte le carte, finche' le fiches non finiscono."""

    LIMITE_MANI = 500

    def dgt(self, prompt="", **_):
        self.prompt.append(prompt)
        if prompt.endswith("tieni? "):
            return ""
        if sum(1 for p in self.prompt if p.startswith("F ")) > self.LIMITE_MANI:
            raise AssertionError("cinquecento mani senza mai perdere tutto: il game over non arriva")
        return "+"


def test_il_game_over_conta_un_fallimento_solo_e_riparte_da_duecento(banco, tmp_path, capsys, monkeypatch):
    copione = CopioneTuttoDentro([])
    monkeypatch.setattr(pokermachine, "dgt", copione.dgt)
    monkeypatch.setattr(pokermachine, "play_event", copione.play_event)
    assert pokermachine.main() == 0
    uscita = capsys.readouterr().out
    assert "Fiches esaurite, game over." in uscita
    assert "Chiudi con 0 fiches: -200, cioè -100,0 per cento." in uscita
    assert "game_over" in copione.suonati
    mani = sum(1 for p in copione.prompt if p.endswith("tieni? "))
    with open(dati.percorso(cartella=str(tmp_path)), encoding="utf-8") as f:
        salvato = json.load(f)
    assert salvato["fallimenti"] == 1
    assert salvato["fiches_attuali"] == regole.FICHES_INIZIALI
    assert salvato["mani_giocate"] == mani
    assert salvato["mani_dall_ultimo_fallimento"] == 0
    assert salvato["record_mani_senza_fallimenti"] == mani
    # Il lancio successivo non conta un secondo fallimento.
    riletto, avvisi = dati.carica_dati(str(tmp_path))
    assert riletto["fallimenti"] == 1
    assert not any("esaurite" in a for a in avvisi)


def test_tenere_tutte_le_carte(banco):
    copione = banco(["m", "12345", ""])
    pokermachine.main()
    assert "tieni_tutte" in copione.suonati
    assert "scarto" not in copione.suonati


def test_numeri_di_carte_fuori_dal_mazzo_vengono_rifiutati(banco, capsys):
    copione = banco(["m", "16", "9", "2", ""])
    pokermachine.main()
    uscita = capsys.readouterr().out
    assert uscita.count("Scrivi i numeri delle carte") == 2
    assert copione.suonati.count("errore") == 2
