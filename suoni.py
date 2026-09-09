# PokerMachine, i suoni: la mappa fra gli eventi del gioco e i preset condivisi.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 09/09/2026: nasce con la revisione 1. Ogni evento ha il suo suono, e ogni
# punteggio il suo jingle, che cresce di lunghezza e di ricchezza con il
# valore della mano: dalle due note gravi della carta alta ai tre secondi
# di fanfara della scala reale. I preset della famiglia pokermachine stanno
# nella collezione condivisa Acu_Collection.json, insieme a quelli di tutti.

"""Collega gli eventi di PokerMachine ai suoni della collezione condivisa.

Qui sta soltanto quale suono va con quale evento: la lettura della
collezione, la conversione dei volumi e il mixer sono di Acusticator.
I dodici punteggi sono eventi a loro volta, con il loro stesso nome, cosi'
chi contabilizza la mano puo' restituire il nome del punteggio e chi suona
non deve tradurre niente.
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
    "killer_hand": "pokermachine_killer_hand",
    "kh_bonus": "pokermachine_kh_bonus",
    "kh_penalita": "pokermachine_kh_penalita",
    "record_vincita": "pokermachine_record_vincita",
    "record_perdita": "pokermachine_record_perdita",
    "record_mani": "pokermachine_record_mani",
    "traguardo_mani": "jingle_livello_superato",
    "soglia_fiches": "pokermachine_soglia_fiches",
    "game_over": "pokermachine_game_over",
    "Carta alta": "pokermachine_carta_alta",
    "Coppia non pagata": "pokermachine_coppia_non_pagata",
    "Coppia pagata": "pokermachine_coppia_pagata",
    "Doppia coppia": "pokermachine_doppia_coppia",
    "Tris": "pokermachine_tris",
    "Scala": "pokermachine_scala",
    "Colore": "pokermachine_colore",
    "Full": "pokermachine_full",
    "Poker": "pokermachine_poker",
    "Super Poker": "pokermachine_super_poker",
    "Scala a colore": "pokermachine_scala_a_colore",
    "Scala Reale": "pokermachine_scala_reale",
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
