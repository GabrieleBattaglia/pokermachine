# PokerMachine, i suoni: la mappa fra gli eventi del gioco e i preset condivisi.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 09/09/2026: nasce con la revisione 1. Ogni evento ha il suo suono, e ogni
# punteggio il suo jingle, che cresce di lunghezza e di ricchezza con il
# valore della mano: dalle due note gravi della carta alta ai tre secondi
# di fanfara della scala reale. I preset della famiglia pokermachine stanno
# nella collezione condivisa Acu_Collection.json, insieme a quelli di tutti.
# 24/09/2026: versione 5. I suoni delle categorie nuove, delle regole a
# sorpresa, degli scudi, del consiglio, del raddoppio, del montepremi, dei
# trofei e delle sfide. La penalita' della Killer Hand non c'e' piu'.

"""Collega gli eventi di PokerMachine ai suoni della collezione condivisa.

Qui sta soltanto quale suono va con quale evento: la lettura della
collezione, la conversione dei volumi e il mixer sono di Acusticator.
I punteggi sono eventi a loro volta, con il loro stesso nome, cosi' chi
contabilizza la mano puo' restituire il nome del punteggio e chi suona non
deve tradurre niente. Un preset che manca dalla collezione non suona e non
e' un errore.
"""

from GBUtils import Acusticator

EVENTI = {
    "avvio": "pokermachine_avvio",
    "chiusura": "pokermachine_chiusura",
    "mescola": "mazzo_mescolato",
    "rimescolo": "mazzo_mescolato",
    "puntata": "pokermachine_puntata",
    "puntata_minima": "pokermachine_puntata_minima",
    "distribuzione": "pokermachine_distribuzione",
    "scarto": "pokermachine_scarto",
    "tieni_tutte": "doppio_tic_conferma",
    "errore": "errore_secco",
    "manuale": "apertura",
    "statistiche": "apertura",
    "consiglio": "pokermachine_consiglio",
    "tenuta_migliore": "pokermachine_tenuta_migliore",
    "killer_hand": "pokermachine_killer_hand",
    "sorpresa_nessuna": "pokermachine_sorpresa_nessuna",
    "sorpresa_nessun_cambio": "pokermachine_sorpresa_nessun_cambio",
    "sorpresa_coppie_mute": "pokermachine_sorpresa_coppie_mute",
    "sorpresa_tutto_o_niente": "pokermachine_sorpresa_tutto_o_niente",
    "kh_bonus": "pokermachine_kh_bonus",
    "scudo_guadagnato": "pokermachine_scudo_guadagnato",
    "scudo_usato": "pokermachine_scudo_usato",
    "scudi_pieni": "pokermachine_scudi_pieni",
    "montepremi_vinto": "pokermachine_montepremi_vinto",
    "montepremi_soglia": "pokermachine_montepremi_soglia",
    "raddoppio_offerto": "pokermachine_raddoppio_offerto",
    "raddoppio_carta": "pokermachine_raddoppio_carta",
    "raddoppio_vinto": "pokermachine_raddoppio_vinto",
    "raddoppio_perso": "pokermachine_raddoppio_perso",
    "raddoppio_incassato": "pokermachine_raddoppio_incassato",
    "record_vincita": "pokermachine_record_vincita",
    "record_perdita": "pokermachine_record_perdita",
    "record_mani": "pokermachine_record_mani",
    "traguardo_mani": "jingle_livello_superato",
    "soglia_fiches": "pokermachine_soglia_fiches",
    "sfide": "pokermachine_sfide",
    "sfida_vinta": "pokermachine_sfida_vinta",
    "trofeo_mano": "pokermachine_trofeo_mano",
    "trofeo_killer": "pokermachine_trofeo_killer",
    "trofeo_fiches": "pokermachine_trofeo_fiches",
    "trofeo_serie": "pokermachine_trofeo_serie",
    "trofeo_abilita": "pokermachine_trofeo_abilita",
    "game_over": "pokermachine_game_over",
    "Carta alta": "pokermachine_carta_alta",
    "Coppia non pagata": "pokermachine_coppia_non_pagata",
    "Coppia gemella": "pokermachine_coppia_gemella",
    "Coppia pagata": "pokermachine_coppia_pagata",
    "Coppia gemella pagata": "pokermachine_coppia_gemella_pagata",
    "Doppia coppia": "pokermachine_doppia_coppia",
    "Tris": "pokermachine_tris",
    "Scala": "pokermachine_scala",
    "Colore": "pokermachine_colore",
    "Full": "pokermachine_full",
    "Tris gemello": "pokermachine_tris_gemello",
    "Poker": "pokermachine_poker",
    "Poker dal 2 al 4": "pokermachine_poker_dal_2_al_4",
    "Poker d'assi": "pokermachine_poker_d_assi",
    "Super Poker": "pokermachine_super_poker",
    "Poker gemello": "pokermachine_poker_gemello",
    "Scala a colore": "pokermachine_scala_a_colore",
    "Full a colore": "pokermachine_full_a_colore",
    "Scala Reale": "pokermachine_scala_reale",
    "Cinque gemelle": "pokermachine_cinque_gemelle",
}


def play_event(nome_evento, sync=True):
    """Suona il preset legato a un evento. Vero se e' partito.

    I suoni sono sincroni: ognuno finisce prima che il gioco prosegua,
    cosi' non si accavallano fra loro e con la voce dello screen reader.
    Un evento senza suono, come quelli che portano solo una frase, non fa
    niente e non e' un errore.
    """
    preset = EVENTI.get(nome_evento)
    if preset is None:
        return False
    return Acusticator.play(preset, sync=sync)
