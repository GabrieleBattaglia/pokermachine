# PokerMachine, prove sulla contabilita' della mano.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

import partita
import regole
from dati import nuovi_dati


def giocatore(fiches=1000, **campi):
    dati = nuovi_dati()
    dati["fiches_attuali"] = fiches
    dati.update(campi)
    return dati


def nomi(eventi):
    return [e.nome for e in eventi]


def test_vincita_normale_entra_nel_saldo_e_nelle_statistiche():
    dati = giocatore(1000)
    eventi = partita.esito_mano(dati, 100, "Tris")
    assert dati["fiches_attuali"] == 1200
    assert dati["fiches_guadagnate"] == 200
    assert dati["punteggi"]["Tris"]["conteggio"] == 1
    assert dati["mani_giocate"] == 1
    assert nomi(eventi) == ["Tris", "record_vincita", "soglia_fiches"]
    eventi = partita.esito_mano(dati, 100, "Tris")
    assert nomi(eventi) == ["Tris"]


def test_pareggio_restituisce_la_puntata():
    dati = giocatore(500)
    eventi = partita.esito_mano(dati, 100, "Coppia pagata")
    assert dati["fiches_attuali"] == 500
    assert dati["fiches_guadagnate"] == 0
    assert dati["fiches_perdute"] == 0
    assert nomi(eventi) == ["Coppia pagata"]


def test_perdita_normale():
    dati = giocatore(500)
    eventi = partita.esito_mano(dati, 100, "Carta alta")
    assert dati["fiches_attuali"] == 400
    assert dati["fiches_perdute"] == 100
    assert dati["perdita_massima"] == 100
    assert nomi(eventi) == ["Carta alta", "record_perdita"]


def test_bonus_killer_hand_arriva_nel_saldo():
    dati = giocatore(1000)
    eventi = partita.esito_mano(dati, 100, "Poker", killer=True)
    # restituiti 2500, netta 2400, bonus 4800: il saldo li vede tutti
    assert dati["fiches_attuali"] == 900 + 2500 + 4800
    assert dati["fiches_guadagnate"] == 7200
    assert dati["vincita_massima"] == 7200
    assert dati["killer_hand_count"] == 1
    assert nomi(eventi) == ["Poker", "kh_bonus", "record_vincita", "soglia_fiches"]


def test_killer_hand_in_pareggio_non_fa_niente():
    dati = giocatore(800)
    eventi = partita.esito_mano(dati, 100, "Coppia pagata", killer=True)
    assert dati["fiches_attuali"] == 800
    assert nomi(eventi) == ["Coppia pagata"]
    assert dati["killer_hand_count"] == 1


def test_penalita_killer_hand_sulle_fiches_prima_della_puntata():
    dati = giocatore(1000)
    eventi = partita.esito_mano(dati, 500, "Carta alta", killer=True)
    # prima Killer Hand, dieci per cento di 1000, non di 500
    assert dati["fiches_attuali"] == 400
    assert dati["fiches_perdute"] == 600
    assert nomi(eventi) == ["Carta alta", "kh_penalita", "record_perdita"]
    assert "delle 1K fiches" in eventi[1].testo


def test_penalita_killer_hand_non_scende_sotto_zero_e_porta_al_game_over():
    dati = giocatore(1000, killer_hand_count=8, mani_dall_ultimo_fallimento=224, record_mani_senza_fallimenti=300)
    eventi = partita.esito_mano(dati, 900, "Carta alta", killer=True)
    assert dati["fiches_perdute"] == 1000
    assert dati["fallimenti"] == 1
    assert dati["fiches_attuali"] == regole.FICHES_INIZIALI
    assert dati["mani_dall_ultimo_fallimento"] == 0
    assert dati["killer_hand_count"] == 0
    assert dati["soglia_fiches"] == 0
    assert dati["data_ultimo_fallimento"] is not None
    assert nomi(eventi) == ["Carta alta", "kh_penalita", "record_perdita", "game_over"]
    assert "225 mani" in eventi[-1].testo


def test_il_game_over_conta_anche_l_ultima_mano_nel_record():
    dati = giocatore(100, mani_dall_ultimo_fallimento=9, record_mani_senza_fallimenti=9)
    eventi = partita.esito_mano(dati, 100, "Carta alta")
    assert dati["record_mani_senza_fallimenti"] == 10
    assert "record_mani" in nomi(eventi)
    assert "game_over" in nomi(eventi)
    assert dati["record_battuto"] is False


def test_il_primato_si_annuncia_una_volta_sola_quando_si_supera():
    dati = giocatore(1000, mani_dall_ultimo_fallimento=5, record_mani_senza_fallimenti=5)
    assert "record_mani" in nomi(partita.esito_mano(dati, 10, "Carta alta"))
    assert dati["record_mani_senza_fallimenti"] == 6
    assert "record_mani" not in nomi(partita.esito_mano(dati, 10, "Carta alta"))
    assert dati["record_mani_senza_fallimenti"] == 7


def test_il_primo_giocatore_non_sente_un_primato_alla_prima_mano():
    dati = giocatore(200)
    assert "record_mani" not in nomi(partita.esito_mano(dati, 10, "Carta alta"))
    assert dati["record_mani_senza_fallimenti"] == 1


def test_traguardo_ogni_cento_mani():
    dati = giocatore(1000, mani_dall_ultimo_fallimento=99, record_mani_senza_fallimenti=500)
    assert "traguardo_mani" in nomi(partita.esito_mano(dati, 10, "Carta alta"))
    assert "traguardo_mani" not in nomi(partita.esito_mano(dati, 10, "Carta alta"))


def test_le_soglie_si_annunciano_una_volta_per_serie():
    dati = giocatore(990, soglia_fiches=0)
    assert "soglia_fiches" in nomi(partita.esito_mano(dati, 10, "Doppia coppia"))
    assert dati["soglia_fiches"] == 1000
    partita.esito_mano(dati, 500, "Carta alta")
    assert "soglia_fiches" not in nomi(partita.esito_mano(dati, 10, "Doppia coppia"))


def test_killer_hand_in_arrivo():
    assert partita.killer_hand_in_arrivo(giocatore(mani_dall_ultimo_fallimento=24)) == (1, 10)
    assert partita.killer_hand_in_arrivo(giocatore(mani_dall_ultimo_fallimento=99, killer_hand_count=3)) == (4, 40)
    assert partita.killer_hand_in_arrivo(giocatore(mani_dall_ultimo_fallimento=10)) == (0, 0)


def test_bilancio_sessione():
    inizio, fine = partita.bilancio_sessione(400, 428)
    assert inizio == "Hai iniziato la sessione con 400 fiches."
    assert fine == "Chiudi con 428 fiches: +28, cioè +7,0 per cento."
    assert partita.bilancio_sessione(400, 300)[1] == "Chiudi con 300 fiches: -100, cioè -25,0 per cento."
