# PokerMachine, utilita': fa sentire uno per uno i suoni del gioco.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 09/09/2026: nasce con la revisione 1, per collaudare i preset nuovi.

"""Ascolto guidato dei suoni di PokerMachine.

Per ogni evento scrive il nome, il preset e la sua descrizione, aspetta un
tasto e suona. Spazio ripete il suono, invio passa al successivo, escape
chiude. I suoni si sentono nell'ordine in cui capitano in una partita.
"""

import sys

from GBUtils import Acusticator, key

from suoni import EVENTI, play_event

ORDINE = (
    "avvio",
    "mescola",
    "statistiche",
    "manuale",
    "puntata",
    "puntata_minima",
    "errore",
    "distribuzione",
    "tieni_tutte",
    "scarto",
    "rimescolo",
    "Carta alta",
    "Coppia non pagata",
    "Coppia pagata",
    "Doppia coppia",
    "Tris",
    "Scala",
    "Colore",
    "Full",
    "Poker",
    "Super Poker",
    "Scala a colore",
    "Scala Reale",
    "killer_hand",
    "kh_bonus",
    "kh_penalita",
    "record_vincita",
    "record_perdita",
    "record_mani",
    "traguardo_mani",
    "soglia_fiches",
    "game_over",
    "chiusura",
)


def main():
    print(f"{len(ORDINE)} suoni. Invio suona e passa oltre, spazio ripete, escape chiude.")
    for numero, evento in enumerate(ORDINE, 1):
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
