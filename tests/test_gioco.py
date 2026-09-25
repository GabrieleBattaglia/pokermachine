# PokerMachine, prova sul programma principale: una sessione intera senza console e senza suoni.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 24/09/2026: versione 5. Il copione incassa sempre al raddoppio, il consiglio
# e' finto tranne che nella prova che lo chiede, e si provano scudi e sfide.

import json
import random

import pytest
from GBUtils import Mazzo

import dati
import pokermachine
import regole
from consiglio import Consigliere


class Copione:
    """Gli ingressi scriptati al posto di dgt, e la lista degli eventi suonati."""

    def __init__(self, risposte):
        self.risposte = list(risposte)
        self.prompt = []
        self.suonati = []

    def dgt(self, prompt="", default=None, **_):
        self.prompt.append(prompt)
        risposta = self._risposta(prompt)
        # Come dgt vera: invio a vuoto restituisce il predefinito, se c'e'.
        return default if risposta == "" and default is not None else risposta

    def _risposta(self, prompt):
        if prompt.startswith("Posta ") and not (self.risposte and self.risposte[0].startswith("raddoppio:")):
            # Dopo una vincita il copione incassa, salvo quando la sua prossima
            # risposta e' scritta apposta per il raddoppio.
            return ""
        if self.risposte and self.risposte[0].startswith("raddoppio:"):
            return self.risposte.pop(0).removeprefix("raddoppio:")
        if not self.risposte:
            raise AssertionError(f"il copione e' finito al prompt {prompt!r}")
        return self.risposte.pop(0)

    def play_event(self, nome, sync=True):
        self.suonati.append(nome)
        return True


class ConsigliereFinto:
    """Il consigliere senza motore: nessun calcolo, quindi niente consiglio e niente precisione."""

    def calcola(self, *_):
        pass

    def tenute(self):
        return None

    def dimentica(self):
        pass

    def chiudi(self):
        pass


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Il programma con disco, tastiera e casse sostituiti."""
    monkeypatch.setattr(dati, "cartella_programma", lambda: str(tmp_path))
    monkeypatch.setattr(pokermachine, "key", lambda *a, **k: "\r")
    monkeypatch.setattr(pokermachine, "gestisci_aggiornamento", lambda *a, **k: False)
    monkeypatch.setattr(pokermachine, "Consigliere", ConsigliereFinto)

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
    assert copione.prompt[0].startswith("F200 S1 R0 M1>")
    assert copione.prompt[-1].startswith("F")
    assert any(" tieni " in p for p in copione.prompt)
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

    def _risposta(self, prompt):
        if " tieni " in prompt or prompt.startswith("Posta "):
            return ""
        if sum(1 for p in self.prompt if p.startswith("F") and p.endswith("> ")) > self.LIMITE_MANI:
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
    mani = sum(1 for p in copione.prompt if " tieni " in p)
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


SEMI = {"C": ("Cuori", 1), "Q": ("Quadri", 2), "F": ("Fiori", 3), "P": ("Picche", 4)}


def carta(breve):
    """Una carta dalla forma breve con il valore in numero: 7C, 12Q, 1P."""
    valore, seme = int(breve[:-1]), breve[-1]
    nome_seme, id_seme = SEMI[seme]
    lettera = {1: "A", 10: "0", 11: "J", 12: "Q", 13: "K"}.get(valore, str(valore))
    return Mazzo.Carta(
        id=0, nome=f"{valore} di {nome_seme}", valore=valore, seme_nome=nome_seme, seme_id=id_seme, desc_breve=lettera + seme
    )


class MazzoFinto:
    """Un mazzo che serve prima le carte scritte in ordine, poi il resto dei dieci mazzi mescolato sempre uguale.

    Il resto conta: il consiglio guarda la scarpa vera, e una scarpa fatta
    di carte tutte uguali gli farebbe consigliare altro.
    """

    ordine = ()

    def __init__(self, *_, **__):
        resto = [f"{valore}{seme}" for valore in range(1, 14) for seme in SEMI] * regole.NUM_MAZZI
        for breve in self.ordine:
            resto.remove(breve)
        random.Random(0).shuffle(resto)
        self.carte = [carta(b) for b in reversed([*self.ordine, *resto])]
        self.scarti = []
        self.ultimo_rimescolo = False

    def mescola_mazzo(self):
        pass

    def pesca(self, quante):
        return [self.carte.pop() for _ in range(min(quante, len(self.carte)))]

    def scarta_carte(self, carte):
        self.scarti.extend(carte)


def test_il_raddoppio_sul_colore(banco, tmp_path, monkeypatch, capsys):
    MazzoFinto.ordine = ["7C", "7Q", "7F", "2P", "9C", "5C"]
    monkeypatch.setattr(pokermachine, "Mazzo", MazzoFinto)
    copione = banco(["m", "12345", "raddoppio:r", "raddoppio:", ""])
    pokermachine.main()
    uscita = capsys.readouterr().out
    posta = 6 * regole.TABELLA_VINCITE["Tris"]
    assert "Raddoppio: r rosso" in uscita
    assert "Esce 5 di Cuori." in uscita
    assert f"Incassi {posta * 2} fiches." in uscita
    for evento in ("raddoppio_offerto", "raddoppio_carta", "raddoppio_vinto", "raddoppio_incassato"):
        assert evento in copione.suonati
    with open(dati.percorso(cartella=str(tmp_path)), encoding="utf-8") as f:
        salvato = json.load(f)
    assert salvato["fiches_attuali"] == 200 - 6 + posta * 2
    assert salvato["raddoppi"]["vinti"] == 1


def test_la_killer_hand_annuncia_minimo_sorpresa_e_scudi(banco, tmp_path, capsys):
    iniziali = dati.nuovi_dati()
    iniziali.update(fiches_attuali=100, mani_dall_ultimo_fallimento=24, sorpresa_kh="nessun_cambio", scudi=2)
    iniziali["serie"]["sfide"] = [{"chiave": "full", "fatta": False}]
    dati.salva_dati(iniziali, str(tmp_path))
    copione = banco(["1", ""])
    pokermachine.main()
    uscita = capsys.readouterr().out
    minimo = regole.minimo_killer_hand(1)
    assert regole.puntata_minima(100) < minimo
    assert "Killer Hand numero 1, mano 25 della serie." in uscita
    assert f"La puntata minima è {minimo} fiches." in uscita
    assert "Sorpresa: Nessun cambio." in uscita
    assert "Hai 2 scudi" in uscita
    assert f"La puntata minima di questa Killer Hand è {minimo} fiches: correggo." in uscita
    assert "Nessun cambio: la mano servita è quella finale." in uscita
    assert not any(" tieni " in p for p in copione.prompt)
    assert copione.prompt[0].endswith(" D2> ")
    assert "sorpresa_nessun_cambio" in copione.suonati
    assert "Sfide della serie" not in uscita


def test_le_sfide_si_annunciano_all_inizio_della_serie(banco, capsys):
    copione = banco([""])
    pokermachine.main()
    uscita = capsys.readouterr().out
    assert "Sfide della serie, ciascuna vale uno scudo:" in uscita
    assert "sfide" in copione.suonati


def test_il_consiglio_con_il_motore_vero(banco, monkeypatch, capsys):
    MazzoFinto.ordine = ["12C", "12Q", "2F", "5P", "9C"]
    monkeypatch.setattr(pokermachine, "Mazzo", MazzoFinto)
    monkeypatch.setattr(pokermachine, "Consigliere", Consigliere)
    copione = banco(["m", "c", "3", ""])
    pokermachine.main()
    uscita = capsys.readouterr().out
    # Ordinate per valore sono 2F 5P 9C QC QQ: la coppia di regine e' la quarta e la quinta.
    assert "Servita: Coppia pagata, di regine." in uscita
    assert any(p.endswith(" tieni 45? ") for p in copione.prompt)
    assert "Consiglio: 45, cioè QC QQ." in uscita
    assert "La tenuta migliore era 45, cioè QC QQ" in uscita
    assert "consiglio" in copione.suonati
    assert "tenuta_migliore" in copione.suonati


def test_al_raddoppio_una_risposta_lunga_non_e_una_scommessa(banco, monkeypatch, capsys):
    MazzoFinto.ordine = ["7C", "7Q", "7F", "2P", "9C", "5C"]
    monkeypatch.setattr(pokermachine, "Mazzo", MazzoFinto)
    banco(["m", "12345", "raddoppio:no", "raddoppio:", ""])
    pokermachine.main()
    uscita = capsys.readouterr().out
    assert "Scrivi r o n per il colore" in uscita
    assert "Esce " not in uscita


def test_le_percentuali_hanno_l_articolo_giusto():
    assert pokermachine._per_cento(1, 4) == "il 25,0"
    assert pokermachine._per_cento(1, 12) == "l'8,3"
    assert pokermachine._per_cento(1, 100) == "l'1,0"
    assert pokermachine._per_cento(7, 60) == "l'11,7"
    assert pokermachine._per_cento(4, 5) == "l'80,0"
    assert pokermachine._per_cento(0, 5) == "lo 0,0"
    assert pokermachine._per_cento(1, 0) == "lo 0,0"


def test_invio_accetta_la_tenuta_proposta(banco, tmp_path, monkeypatch, capsys):
    MazzoFinto.ordine = ["12C", "12Q", "2F", "5P", "9C"]
    monkeypatch.setattr(pokermachine, "Mazzo", MazzoFinto)
    monkeypatch.setattr(pokermachine, "Consigliere", Consigliere)
    banco(["m", "", ""])
    pokermachine.main()
    uscita = capsys.readouterr().out
    assert "Cambi 3 carte." in uscita
    assert "La tenuta migliore era" not in uscita
    assert "nuova." in uscita
    with open(dati.percorso(cartella=str(tmp_path)), encoding="utf-8") as f:
        salvato = json.load(f)
    assert salvato["precisione"] == {"tenute": 1, "ottime": 1, "di_fila": 1, "valore_perso": 0.0}


def test_zero_cambia_tutte_le_carte(banco, capsys):
    copione = banco(["m", "0", ""])
    pokermachine.main()
    assert "Cambi 5 carte." in capsys.readouterr().out
    assert "scarto" in copione.suonati


def test_la_servita_si_descrive_con_i_valori_dei_gruppi():
    assert pokermachine.descrivi([carta(b) for b in ("11C", "11Q", "2F", "5P", "9C")]) == "Coppia pagata, di jack"
    assert pokermachine.descrivi([carta(b) for b in ("5C", "5Q", "13F", "13P", "9C")]) == "Doppia coppia, di re e di cinque"
    assert pokermachine.descrivi([carta(b) for b in ("7C", "7Q", "7F", "1P", "1C")]) == "Full, di sette e di assi"
    assert pokermachine.descrivi([carta(b) for b in ("2C", "5C", "9C", "11C", "13C")]) == "Colore"
    assert pokermachine.descrivi([carta(b) for b in ("2C", "5Q", "9C", "11F", "13C")]) == "Carta alta"


def test_il_prompt_della_puntata_sta_in_trenta_caratteri_anche_con_numeri_grandi():
    stato = dati.nuovi_dati()
    stato.update(fiches_attuali=999_990_000, mani_dall_ultimo_fallimento=9998, record_mani_senza_fallimenti=9999, scudi=3)
    assert len(pokermachine.prompt_puntata(stato, 999)) <= 30
