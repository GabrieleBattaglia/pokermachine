# PokerMachine, taratura: la conferma del pacchetto che il gioco usa davvero.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 25/09/2026: nasce con la versione 5. Strumento di misura, non fa parte del gioco.

"""Rilancia il simulatore con la tabella e la gara scritte in regole.py.

Dopo ogni ritocco alle regole, questo script dice se i conti tornano ancora:
ritorno, frequenze, valore delle regole a sorpresa e durata delle serie per
tutta la batteria dei modi di puntare, con la strategia ottima e con chi
sbaglia una tenuta su venti. Si lancia con:
    python taratura/conferma.py [serie] [seme]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from esplora import Campione, Gara, esegui

import regole

# Le sfide danno circa due scudi nelle prime 150 mani: e' una stima, fatta
# sulle frequenze delle mani che le sfide chiedono.
SFIDE = ((40, 0.7), (90, 0.6), (150, 0.5))
REGOLE_KH = {"nessuna": "semplice", "nessun_cambio": "nessun cambio", "coppie_mute": "coppie mute", "tutto_o_niente": "tutto o niente"}


def main():
    serie = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    seme = int(sys.argv[2]) if len(sys.argv) > 2 else 9001
    campione = Campione()
    gara = Gara(base=regole.KILLER_HAND_BASE, fattore=regole.KILLER_HAND_FATTORE, sfide=SFIDE, scudi_max=regole.SCUDI_MAX)
    regole_kh = [REGOLE_KH[s.chiave] for s in regole.SORPRESE]
    minimi = ", ".join(str(regole.minimo_killer_hand(n)) for n in range(1, 13))
    print(f"Minimi delle prime dodici Killer Hand: {minimi}.")
    for errore in (0.0, 0.05):
        print(f"Errore {errore}:")
        esegui(
            campione,
            regole.TABELLA_VINCITE,
            gara,
            set(regole.PUNTEGGI_SCUDO),
            regole_kh,
            netta=regole.KILLER_HAND_MOLTIPLICATORE,
            serie=serie,
            seme=seme,
            errore=errore,
        )


if __name__ == "__main__":
    main()
