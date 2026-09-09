# PokerMachine, prove sul salvataggio: scrittura, lettura, riserva e conversione dal pickle.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

import json
import os
import pickle

import dati
import regole


def test_scrittura_e_lettura(tmp_path):
    cartella = str(tmp_path)
    nuovo = dati.nuovi_dati()
    nuovo["fiches_attuali"] = 777
    nuovo["punteggi"]["Tris"]["conteggio"] = 4
    dati.salva_dati(nuovo, cartella)
    letto, avvisi = dati.carica_dati(cartella)
    assert avvisi == []
    assert letto["fiches_attuali"] == 777
    assert letto["launches"] == 1
    assert letto["punteggi"]["Tris"]["conteggio"] == 4
    assert letto["versione_formato"] == dati.VERSIONE_FORMATO


def test_la_seconda_scrittura_lascia_la_copia_di_riserva(tmp_path):
    cartella = str(tmp_path)
    dati.salva_dati(dati.nuovi_dati(), cartella)
    dati.salva_dati(dati.nuovi_dati(), cartella)
    assert os.path.exists(dati.percorso(cartella=cartella) + ".bak")
    assert not os.path.exists(dati.percorso(cartella=cartella) + ".tmp")


def test_primo_avvio(tmp_path):
    letto, avvisi = dati.carica_dati(str(tmp_path))
    assert letto["fiches_attuali"] == regole.FICHES_INIZIALI
    assert letto["launches"] == 1
    assert any("Primo avvio" in a for a in avvisi)


def test_file_rotto_con_riserva(tmp_path):
    cartella = str(tmp_path)
    buono = dati.nuovi_dati()
    buono["fiches_attuali"] = 555
    dati.salva_dati(buono, cartella)
    dati.salva_dati(buono, cartella)
    with open(dati.percorso(cartella=cartella), "w", encoding="utf-8") as f:
        f.write("{ rotto")
    letto, avvisi = dati.carica_dati(cartella)
    assert letto["fiches_attuali"] == 555
    assert any("riserva" in a for a in avvisi)


def test_file_rotto_senza_riserva_viene_messo_da_parte(tmp_path):
    cartella = str(tmp_path)
    percorso = dati.percorso(cartella=cartella)
    with open(percorso, "w", encoding="utf-8") as f:
        f.write("{ rotto")
    letto, avvisi = dati.carica_dati(cartella)
    assert letto["fiches_attuali"] == regole.FICHES_INIZIALI
    assert os.path.exists(percorso + ".illeggibile")
    assert not os.path.exists(percorso)
    assert any("nuovo" in a for a in avvisi)


def test_conversione_dal_pickle_della_versione_tre(tmp_path):
    cartella = str(tmp_path)
    vecchio = {
        "launches": 96,
        "mani_giocate": 1976,
        "fiches_attuali": 0,
        "fallimenti": 13,
        "mani_dall_ultimo_fallimento": 109,
        "killer_hand_count": 4,
        "record_mani_senza_fallimenti": 399,
        "punteggi": {"Tris": {"conteggio": 192, "ultima_realizzazione": "2026-07-11 11:08:12"}},
    }
    percorso_pkl = dati.percorso(dati.NOME_SALVATAGGIO_VECCHIO, cartella)
    with open(percorso_pkl, "wb") as f:
        pickle.dump(vecchio, f)
    letto, avvisi = dati.carica_dati(cartella)
    # Il game over della versione 3 aveva gia' contato il fallimento: non si conta di nuovo.
    assert letto["fallimenti"] == 13
    assert letto["fiches_attuali"] == regole.FICHES_INIZIALI
    assert letto["mani_dall_ultimo_fallimento"] == 0
    assert letto["killer_hand_count"] == 0
    assert letto["launches"] == 97
    assert letto["record_mani_senza_fallimenti"] == 399
    assert letto["punteggi"]["Tris"]["conteggio"] == 192
    assert letto["punteggi"]["Scala Reale"]["conteggio"] == 0
    assert any("convertito" in a for a in avvisi)
    assert any("esaurite" in a for a in avvisi)
    assert os.path.exists(percorso_pkl + ".migrato")
    assert not os.path.exists(percorso_pkl)
    with open(dati.percorso(cartella=cartella), encoding="utf-8") as f:
        assert json.load(f)["fallimenti"] == 13


def test_il_pickle_illeggibile_non_ferma_il_gioco(tmp_path):
    cartella = str(tmp_path)
    with open(dati.percorso(dati.NOME_SALVATAGGIO_VECCHIO, cartella), "wb") as f:
        f.write(b"\x80\x04tronco")
    letto, avvisi = dati.carica_dati(cartella)
    assert letto["fiches_attuali"] == regole.FICHES_INIZIALI
    assert any("non si legge" in a for a in avvisi)


def test_completa_scarta_i_tipi_sbagliati():
    letto = dati.completa({"fiches_attuali": "tante", "fallimenti": -3, "launches": True, "data_ultima_giocata": "ieri", "punteggi": "no"})
    assert letto["fiches_attuali"] == regole.FICHES_INIZIALI
    assert letto["fallimenti"] == 0
    assert letto["launches"] == 0
    assert letto["data_ultima_giocata"] is None
    assert all(v["conteggio"] == 0 for v in letto["punteggi"].values())
    assert dati.completa(None)["fiches_attuali"] == regole.FICHES_INIZIALI


def test_la_soglia_di_un_salvataggio_vecchio_parte_da_quella_gia_raggiunta():
    assert dati.completa({"fiches_attuali": 25000})["soglia_fiches"] == 10000
    assert dati.completa({"fiches_attuali": 25000, "soglia_fiches": 0})["soglia_fiches"] == 0


def test_il_primato_di_un_salvataggio_vecchio_conta_come_battuto_solo_se_la_serie_lo_tiene():
    assert dati.completa({"mani_dall_ultimo_fallimento": 109, "record_mani_senza_fallimenti": 399})["record_battuto"] is False
    assert dati.completa({"mani_dall_ultimo_fallimento": 400, "record_mani_senza_fallimenti": 400})["record_battuto"] is True
    assert dati.completa({"mani_dall_ultimo_fallimento": 0, "record_mani_senza_fallimenti": 0})["record_battuto"] is False
    assert dati.completa({"record_battuto": True})["record_battuto"] is True
    assert dati.completa({"record_battuto": "si"})["record_battuto"] is False


def test_tempo_trascorso():
    assert dati.formatta_tempo_trascorso(None) == "mai"
    assert dati.formatta_tempo_trascorso("ieri") == "data non valida"
    assert dati.formatta_tempo_trascorso(dati.adesso()) == "pochi istanti fa"
    assert dati.formatta_tempo_trascorso("2099-01-01 00:00:00") == "in una data futura"
    assert dati.formatta_tempo_trascorso("2020-01-01 00:00:00").endswith(" fa")
