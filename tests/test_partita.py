# PokerMachine, prove sulla contabilita' della mano.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 24/09/2026: versione 5. La Killer Hand come gara, gli scudi, le sorprese, il
# montepremi, il raddoppio, la precisione, i trofei e le sfide. I multipli si
# leggono dalla tabella del gioco, cosi' le prove sopravvivono a una taratura.

import random

from GBUtils import Mazzo

import partita
import regole
import sfide
import trofei
from dati import adesso, nuovi_dati

T = regole.TABELLA_VINCITE


def giocatore(fiches=1000, trofei_presi=True, **campi):
    """Un giocatore con quelle fiches; con trofei_presi li ha gia' tutti, e le prove non li sentono."""
    dati = nuovi_dati()
    dati["fiches_attuali"] = fiches
    dati["soglia_fiches"] = regole.soglia_raggiunta(fiches)
    dati["serie"]["fiches_minime"] = fiches
    dati["serie"]["fiches_massime"] = fiches
    if trofei_presi:
        dati["trofei"] = {chiave: adesso() for chiave in trofei.CHIAVI}
    dati.update(campi)
    return dati


def killer(numero=1, chiave="nessuna"):
    return partita.KillerHand(numero, regole.minimo_killer_hand(numero), regole.SORPRESE_PER_CHIAVE[chiave])


def carta(valore, seme):
    return Mazzo.Carta(id=0, nome=f"{valore} di {seme}", valore=valore, seme_nome=seme, seme_id=trofei.SEMI.index(seme) + 1, desc_breve="")


def nomi(eventi):
    return [e.nome for e in eventi]


def test_vincita_normale_entra_nel_saldo_e_nelle_statistiche():
    dati = giocatore(500)
    eventi = partita.esito_mano(dati, 10, "Tris")
    netta = 10 * (T["Tris"] - 1)
    assert dati["fiches_attuali"] == 500 + netta
    assert dati["fiches_guadagnate"] == netta
    assert dati["punteggi"]["Tris"]["conteggio"] == 1
    assert dati["mani_giocate"] == 1
    assert nomi(eventi) == ["Tris", "record_vincita"]
    assert nomi(partita.esito_mano(dati, 10, "Tris")) == ["Tris"]


def test_pareggio_restituisce_la_puntata():
    dati = giocatore(500)
    pari = next(nome for nome, multiplo in regole.PUNTEGGI if multiplo == 1)
    eventi = partita.esito_mano(dati, 100, pari)
    assert dati["fiches_attuali"] == 500
    assert dati["fiches_guadagnate"] == 0
    assert dati["fiches_perdute"] == 0
    assert nomi(eventi) == [pari]


def test_perdita_normale():
    dati = giocatore(500)
    eventi = partita.esito_mano(dati, 100, "Carta alta")
    assert dati["fiches_attuali"] == 400
    assert dati["fiches_perdute"] == 100
    assert dati["perdita_massima"] == 100
    assert nomi(eventi) == ["Carta alta", "record_perdita"]


def test_bonus_killer_hand_arriva_nel_saldo():
    dati = giocatore(1000, sorpresa_kh="nessuna")
    eventi = partita.esito_mano(dati, 100, "Tris", killer=killer())
    netta = 100 * (T["Tris"] - 1)
    bonus = netta * (regole.KILLER_HAND_MOLTIPLICATORE - 1)
    assert dati["fiches_attuali"] == 1000 + netta + bonus
    assert dati["fiches_guadagnate"] == netta + bonus
    assert dati["killer_hand_count"] == 1
    assert dati["sorpresa_kh"] is None
    assert nomi(eventi)[:2] == ["Tris", "kh_bonus"]
    assert partita.incasso(100, "Tris", killer()) == 100 + netta + bonus


def test_killer_hand_persa_toglie_solo_la_puntata():
    dati = giocatore(1000)
    eventi = partita.esito_mano(dati, 300, "Carta alta", killer=killer(3))
    assert dati["fiches_attuali"] == 700
    assert dati["fiches_perdute"] == 300
    assert nomi(eventi) == ["Carta alta", "record_perdita"]


def test_lo_scudo_restituisce_la_puntata_della_killer_hand():
    dati = giocatore(1000, scudi=2)
    eventi = partita.esito_mano(dati, 300, "Carta alta", killer=killer(2))
    assert dati["fiches_attuali"] == 1000
    assert dati["fiches_perdute"] == 0
    assert dati["scudi"] == 1
    assert nomi(eventi) == ["Carta alta", "scudo_usato"]
    assert "Te ne resta uno" in eventi[1].testo


def test_lo_scudo_non_serve_nelle_mani_normali():
    dati = giocatore(1000, scudi=1)
    partita.esito_mano(dati, 300, "Carta alta")
    assert dati["fiches_attuali"] == 700
    assert dati["scudi"] == 1


def test_le_mani_rarissime_regalano_uno_scudo_fino_al_massimo():
    rara = regole.PUNTEGGI_SCUDO[-1]
    dati = giocatore(1000, scudi=regole.SCUDI_MAX - 1)
    assert "scudo_guadagnato" in nomi(partita.esito_mano(dati, 10, rara))
    assert dati["scudi"] == regole.SCUDI_MAX
    assert "scudi_pieni" in nomi(partita.esito_mano(dati, 10, rara))
    assert dati["scudi"] == regole.SCUDI_MAX


def test_coppie_mute_e_tutto_o_niente():
    dati = giocatore(1000)
    partita.esito_mano(dati, 100, "Coppia pagata", killer=killer(1, "coppie_mute"))
    assert dati["fiches_attuali"] == 900
    dati = giocatore(1000)
    pari = next(nome for nome, multiplo in regole.PUNTEGGI if multiplo == 1)
    partita.esito_mano(dati, 100, pari, killer=killer(1, "tutto_o_niente"))
    assert dati["fiches_attuali"] == 900
    dati = giocatore(1000)
    partita.esito_mano(dati, 100, "Tris", killer=killer(1, "tutto_o_niente"))
    assert dati["fiches_attuali"] == 1000 + 100 * (T["Tris"] - 1) * 5


def test_il_montepremi_accumula_la_percentuale_e_paga_con_le_mani_rarissime():
    dati = giocatore(100_000, montepremi_centesimi=250)
    partita.esito_mano(dati, 1000, "Carta alta")
    assert dati["montepremi_centesimi"] == 250 + 1000 * regole.MONTEPREMI_PERCENTUALE
    assert partita.montepremi(dati) == (250 + 1000 * regole.MONTEPREMI_PERCENTUALE) // 100
    premio = partita.montepremi(dati) + 10 * regole.MONTEPREMI_PERCENTUALE // 100
    fiches = dati["fiches_attuali"]
    rara = regole.PUNTEGGI_MONTEPREMI[-1]
    eventi = partita.esito_mano(dati, 10, rara)
    assert "montepremi_vinto" in nomi(eventi)
    assert dati["fiches_attuali"] == fiches - 10 + 10 * T[rara] + premio
    assert dati["montepremi_vinti"] == 1
    assert dati["montepremi_centesimi"] < 100


def test_la_sorpresa_resta_finche_la_killer_hand_non_si_gioca():
    dati = giocatore(mani_dall_ultimo_fallimento=24)
    prima = partita.killer_hand_in_arrivo(dati, random.Random(1))
    assert prima.numero == 1
    assert prima.minimo == regole.minimo_killer_hand(1)
    for seme in range(20):
        assert partita.killer_hand_in_arrivo(dati, random.Random(seme)) == prima
    dati = giocatore(mani_dall_ultimo_fallimento=99, killer_hand_count=3)
    assert partita.killer_hand_in_arrivo(dati).numero == 4
    assert partita.killer_hand_in_arrivo(giocatore(mani_dall_ultimo_fallimento=10)) is None


def test_la_puntata_minima_della_killer_hand():
    numero = 3
    minimo = regole.minimo_killer_hand(numero)
    assert minimo == int(regole.KILLER_HAND_BASE * regole.KILLER_HAND_FATTORE**numero)
    assert regole.puntata_minima_killer_hand(minimo * 100, numero) == regole.puntata_minima(minimo * 100)
    assert regole.puntata_minima_killer_hand(minimo * 2, numero) == minimo
    assert regole.puntata_minima_killer_hand(minimo - 1, numero) == minimo - 1


def test_il_game_over_chiude_la_serie():
    dati = giocatore(1000, killer_hand_count=8, mani_dall_ultimo_fallimento=224, record_mani_senza_fallimenti=300, scudi=0)
    dati["serie"]["sfide"] = sfide.estrai(random.Random(2))
    eventi = partita.esito_mano(dati, 1000, "Carta alta", killer=killer(9))
    assert dati["fallimenti"] == 1
    assert dati["fiches_attuali"] == regole.FICHES_INIZIALI
    assert dati["mani_dall_ultimo_fallimento"] == 0
    assert dati["killer_hand_count"] == 0
    assert dati["sorpresa_kh"] is None
    assert dati["soglia_fiches"] == 0
    assert dati["serie"]["sfide"] == []
    assert dati["data_ultimo_fallimento"] is not None
    assert nomi(eventi)[-1] == "game_over"
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
    assert "soglia_fiches" in nomi(partita.esito_mano(dati, 10, "Tris"))
    assert dati["soglia_fiches"] == 1000
    partita.esito_mano(dati, 500, "Carta alta")
    assert "soglia_fiches" not in nomi(partita.esito_mano(dati, 10, "Tris"))


def test_raddoppio_sul_colore_e_sul_seme():
    dati = giocatore(1000)
    vinta, posta, eventi = partita.raddoppio(dati, 100, "rosso", carta(5, "Quadri"), 50)
    assert vinta
    assert posta == 200
    assert dati["fiches_attuali"] == 1100
    assert dati["raddoppi"] == {"tentati": 1, "vinti": 1, "di_fila": 1, "fiches_vinte": 100, "fiches_perse": 0}
    vinta, posta, _ = partita.raddoppio(dati, 200, "Picche", carta(9, "Picche"), 50)
    assert vinta
    assert posta == 800
    assert dati["fiches_attuali"] == 1700
    vinta, posta, eventi = partita.raddoppio(dati, 800, "nero", carta(1, "Cuori"), 50)
    assert not vinta
    assert posta == 0
    assert dati["fiches_attuali"] == 900
    assert dati["raddoppi"]["di_fila"] == 0
    assert dati["raddoppi"]["fiches_perse"] == 800
    assert nomi(eventi) == ["raddoppio_perso"]


def test_raddoppio_perso_con_tutto_in_gioco_e_game_over():
    dati = giocatore(300)
    _, _, eventi = partita.raddoppio(dati, 300, "Fiori", carta(2, "Cuori"), 100)
    assert nomi(eventi)[-1] == "game_over"
    assert dati["fallimenti"] == 1


def test_raddoppio_conta_il_record_sulla_mano_intera():
    dati = giocatore(1000)
    partita.raddoppio(dati, 300, "rosso", carta(5, "Cuori"), 100)
    assert dati["vincita_massima"] == 600 - 100


def test_precisione_delle_tenute():
    dati = giocatore()
    partita.registra_tenuta(dati, True, 0.0)
    partita.registra_tenuta(dati, True, 0.0)
    partita.registra_tenuta(dati, False, 3.5)
    assert dati["precisione"] == {"tenute": 3, "ottime": 2, "di_fila": 0, "valore_perso": 3.5}


def test_trofei_della_mano_e_della_puntata():
    dati = giocatore(500, trofei_presi=False)
    colore = [carta(v, "Cuori") for v in (2, 5, 9, 11, 13)]
    eventi = partita.esito_mano(dati, 500, "Colore", carte=colore)
    assert "colore_cuori" in dati["trofei"]
    assert "tutto_vinto" in dati["trofei"]
    assert "trofeo_colore_cuori" in nomi(eventi)
    assert "trofeo_tutto_vinto" in nomi(eventi)
    assert "colore_cuori" not in [t.chiave for t in trofei.da_conquistare(dati)]
    assert not any(n.startswith("trofeo_colore") for n in nomi(partita.esito_mano(dati, 10, "Colore", carte=colore)))


def test_trofeo_della_killer_hand_solo_se_si_sopravvive():
    dati = giocatore(10_000, trofei_presi=False, killer_hand_count=4)
    partita.esito_mano(dati, 5000, "Carta alta", killer=killer(5))
    assert "killer_5" in dati["trofei"]
    dati = giocatore(100, trofei_presi=False, killer_hand_count=4)
    partita.esito_mano(dati, 100, "Carta alta", killer=killer(5))
    assert "killer_5" not in dati["trofei"]


def test_le_sfide_si_estraggono_e_regalano_uno_scudo():
    dati = giocatore(1000)
    righe = partita.inizia_serie(dati, random.Random(5))
    assert len(dati["serie"]["sfide"]) == sfide.QUANTE
    assert len({v["chiave"] for v in dati["serie"]["sfide"]}) == sfide.QUANTE
    assert len(righe) == sfide.QUANTE + 1
    dati["serie"]["sfide"] = [{"chiave": "full", "fatta": False}, {"chiave": "scala", "fatta": False}]
    full = [carta(7, "Cuori"), carta(7, "Quadri"), carta(7, "Fiori"), carta(2, "Picche"), carta(2, "Cuori")]
    eventi = partita.esito_mano(dati, 10, "Full", carte=full)
    assert nomi(eventi)[-2:] == ["sfida_vinta", "scudo_guadagnato"]
    assert dati["scudi"] == 1
    assert dati["serie"]["sfide"][0]["fatta"] is True
    assert "sfida_vinta" not in nomi(partita.esito_mano(dati, 10, "Full", carte=full))


def test_bilancio_sessione():
    inizio, fine = partita.bilancio_sessione(400, 428)
    assert inizio == "Hai iniziato la sessione con 400 fiches."
    assert fine == "Chiudi con 428 fiches: +28, cioè +7,0 per cento."
    assert partita.bilancio_sessione(400, 300)[1] == "Chiudi con 300 fiches: -100, cioè -25,0 per cento."


def test_la_decisione_conta_scudo_e_montepremi():
    dati = giocatore(1000, scudi=1, montepremi_centesimi=50_000)
    normale = partita.tabella_decisione(dati, None, 100)
    rara = regole.PUNTEGGI_MONTEPREMI[0]
    assert normale[rara] == T[rara] + 500 / 100
    assert normale["Carta alta"] == 0
    nella_killer = partita.tabella_decisione(dati, killer(), 100)
    assert nella_killer["Carta alta"] == 1
    assert nella_killer["Tris"] == 1 + regole.KILLER_HAND_MOLTIPLICATORE * (T["Tris"] - 1)


def test_le_coppie_mute_non_contano_fra_le_mani_pagate():
    dati = giocatore(1000)
    partita.esito_mano(dati, 100, "Coppia pagata", killer=killer(1, "coppie_mute"))
    assert dati["mani_pagate"] == 0
    partita.esito_mano(dati, 100, "Coppia pagata")
    assert dati["mani_pagate"] == 1


def test_un_full_con_il_tris_gemello_supera_la_sfida_del_full():
    dati = giocatore(1000)
    dati["serie"]["sfide"] = [{"chiave": "full", "fatta": False}]
    gemello = [carta(7, "Cuori"), carta(7, "Cuori"), carta(7, "Cuori"), carta(2, "Picche"), carta(2, "Fiori")]
    punteggio = regole.valuta_mano(gemello)
    partita.esito_mano(dati, 10, punteggio, carte=gemello)
    assert dati["serie"]["sfide"][0]["fatta"] is True


def test_le_tenute_ottime_di_fila_della_sfida_ripartono_con_la_serie():
    dati = giocatore(100)
    dati["precisione"]["di_fila"] = 50
    dati["serie"]["sfide"] = [{"chiave": "dieci_ottime", "fatta": False}]
    partita.registra_tenuta(dati, True, 0.0)
    assert dati["serie"]["sfide"][0]["fatta"] is False
    for _ in range(9):
        partita.registra_tenuta(dati, True, 0.0)
    assert dati["serie"]["sfide"][0]["fatta"] is True
    partita.esito_mano(dati, 100, "Carta alta")
    assert dati["serie"]["ottime_di_fila"] == 0


def test_con_la_serie_avviata_non_si_estraggono_sfide_gia_vinte_o_perse():
    dati = giocatore(5000, killer_hand_count=7)
    for seme in range(200):
        chiavi = {v["chiave"] for v in sfide.estrai(random.Random(seme), dati)}
        assert "doppio" not in chiavi
        assert "killer_6" not in chiavi


def test_il_raddoppio_segna_soglie_e_minimo_della_serie():
    dati = giocatore(800)
    _, _, eventi = partita.raddoppio(dati, 300, "rosso", carta(5, "Cuori"), 100)
    assert "soglia_fiches" in nomi(eventi)
    assert dati["soglia_fiches"] == 1000
    dati = giocatore(80)
    partita.raddoppio(dati, 40, "nero", carta(5, "Cuori"), 20)
    assert dati["serie"]["fiches_minime"] == 40


def test_la_coppia_resa_muta_suona_come_una_perdita():
    dati = giocatore(1000)
    eventi = partita.esito_mano(dati, 100, "Coppia pagata", killer=killer(1, "coppie_mute"))
    assert nomi(eventi)[0] == partita.MUTA
    assert dati["punteggi"]["Coppia pagata"]["conteggio"] == 1


def test_il_game_over_alla_prima_mano_dice_una_mano():
    eventi = partita.esito_mano(giocatore(200), 200, "Carta alta")
    assert "Serie chiusa a 1 mano," in eventi[-1].testo


def test_il_montepremi_annuncia_le_soglie_una_volta_e_riparte_dopo_la_vincita():
    dati = giocatore(10_000_000, montepremi_centesimi=99_950)
    eventi = partita.esito_mano(dati, 100, "Carta alta")
    assert "montepremi_soglia" in nomi(eventi)
    assert dati["montepremi_soglia"] == 1000
    assert "montepremi_soglia" not in nomi(partita.esito_mano(dati, 100, "Carta alta"))
    partita.esito_mano(dati, 10, "Poker d'assi")
    assert dati["montepremi_soglia"] == 0
    assert dati["montepremi_vinti"] == 1


def test_il_bilancio_delle_killer_hand_e_il_ritorno_personale():
    dati = giocatore(1000, scudi=1)
    partita.esito_mano(dati, 100, "Tris", killer=killer())
    partita.esito_mano(dati, 100, "Coppia pagata", killer=killer(2))
    partita.esito_mano(dati, 100, "Carta alta", killer=killer(3))
    partita.esito_mano(dati, 100, "Carta alta", killer=killer(4))
    conti = dati["killer"]
    assert (conti["giocate"], conti["vinte"], conti["pareggiate"], conti["salvate"], conti["perse"]) == (4, 1, 1, 1, 1)
    assert conti["bonus"] == 100 * (T["Tris"] - 1) * (regole.KILLER_HAND_MOLTIPLICATORE - 1)
    assert dati["fiches_puntate"] == 400
    assert dati["fiches_restituite"] == dati["fiches_attuali"] - 1000 + 400


def test_le_ultime_serie_si_ricordano_al_game_over():
    dati = giocatore(100, mani_dall_ultimo_fallimento=41)
    partita.esito_mano(dati, 10, "Tris")
    partita.esito_mano(dati, dati["fiches_attuali"], "Carta alta")
    assert dati["ultime_serie"][-1]["mani"] == 43
    assert dati["ultime_serie"][-1]["fiches_massime"] == 100 + 10 * (T["Tris"] - 1)
    for _ in range(12):
        partita.esito_mano(dati, dati["fiches_attuali"], "Carta alta")
    assert len(dati["ultime_serie"]) == 10
