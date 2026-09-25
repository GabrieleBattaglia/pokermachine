# PokerMachine, utilita': fa sentire uno per uno i suoni del gioco.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 09/09/2026: nasce con la revisione 1, per collaudare i preset nuovi.
# 24/09/2026: versione 5, con i suoni delle categorie nuove, delle sorprese,
# degli scudi, del consiglio, del raddoppio, del montepremi, delle sfide e dei
# trofei. Con un argomento, per esempio "nuovi", suona solo quelli della 5.

"""Ascolto guidato dei suoni di PokerMachine.

Per ogni evento scrive il nome, il preset e la sua descrizione, aspetta un
tasto e suona. Spazio ripete il suono, invio passa al successivo, escape
chiude. I suoni si sentono nell'ordine in cui capitano in una partita.
Lanciato con l'argomento nuovi, fa sentire solo i suoni nati con la
versione 5; con rifatti, solo quelli rifatti dopo il collaudo.
"""

import sys

from GBUtils import Acusticator, key

import trofei
from suoni import EVENTI, play_event

ORDINE = (
    "avvio",
    "mescola",
    "statistiche",
    "trofei",
    "manuale",
    "sfide",
    "puntata",
    "puntata_minima",
    "errore",
    "distribuzione",
    "consiglio",
    "tieni_tutte",
    "scarto",
    "rimescolo",
    "tenuta_migliore",
    "Carta alta",
    "Coppia non pagata",
    "coppia_muta",
    "Coppia gemella",
    "Coppia pagata",
    "Coppia gemella pagata",
    "Doppia coppia",
    "Tris",
    "Scala",
    "Colore",
    "Full",
    "Tris gemello",
    "Poker",
    "Poker dal 2 al 4",
    "Poker d'assi",
    "Super Poker",
    "Poker gemello",
    "Scala a colore",
    "Full a colore",
    "Scala Reale",
    "Cinque gemelle",
    "killer_hand",
    "sorpresa_nessuna",
    "sorpresa_nessun_cambio",
    "sorpresa_coppie_mute",
    "sorpresa_tutto_o_niente",
    "kh_bonus",
    "scudo_guadagnato",
    "scudo_usato",
    "scudi_pieni",
    "raddoppio_offerto",
    "raddoppio_carta",
    "raddoppio_vinto",
    "raddoppio_perso",
    "raddoppio_incassato",
    "montepremi_soglia",
    "montepremi_vinto",
    "sfida_vinta",
    *trofei.SUONI,
    "record_vincita",
    "record_perdita",
    "record_mani",
    "traguardo_mani",
    "soglia_fiches",
    "game_over",
    "chiusura",
)
NUOVI = (
    "trofei",
    "manuale",
    "rimescolo",
    "coppia_muta",
    "sfide",
    "consiglio",
    "tenuta_migliore",
    "Coppia gemella",
    "Coppia gemella pagata",
    "Tris gemello",
    "Poker dal 2 al 4",
    "Poker d'assi",
    "Poker gemello",
    "Full a colore",
    "Cinque gemelle",
    "sorpresa_nessuna",
    "sorpresa_nessun_cambio",
    "sorpresa_coppie_mute",
    "sorpresa_tutto_o_niente",
    "scudo_guadagnato",
    "scudo_usato",
    "scudi_pieni",
    "raddoppio_offerto",
    "raddoppio_carta",
    "raddoppio_vinto",
    "raddoppio_perso",
    "raddoppio_incassato",
    "montepremi_soglia",
    "montepremi_vinto",
    "sfida_vinta",
    *trofei.SUONI,
)


# Quelli rifatti dopo il collaudo del 25 settembre 2026, perche' nessun suono
# si ripeta fra due eventi.
RIFATTI = ("trofei", "manuale", "rimescolo", "coppia_muta", *trofei.SUONI)


def main():
    argomenti = sys.argv[1:]
    if "rifatti" in argomenti:
        elenco = [e for e in ORDINE if e in RIFATTI]
    elif "nuovi" in argomenti:
        elenco = [e for e in ORDINE if e in NUOVI]
    else:
        elenco = list(ORDINE)
    print(f"{len(elenco)} suoni. Invio suona e passa oltre, spazio ripete, escape chiude.")
    for numero, evento in enumerate(elenco, 1):
        preset = EVENTI[evento]
        print(f"{numero}. Evento {evento}, preset {preset}.")
        print(Acusticator.descrizione(preset) or "Senza descrizione.")
        tasto = key("\rPremi invio per sentirlo.\r")
        print()
        if tasto == "\x1b":
            return 0
        while True:
            play_event(evento)
            tasto = key("\rSpazio ripete, invio prosegue.\r")
            print()
            if tasto == "\x1b":
                return 0
            if tasto != " ":
                break
    print("Fine dei suoni.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
