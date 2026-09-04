# PokerMachine, utilita': prepara l'archivio per la distribuzione.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5, modalita' auto).
# 04/09/2026: primo chiamante, il mestiere sta in crea_archivio_release di GBUtils V104.

"""Comprime il risultato di PyInstaller in un solo archivio.

Tutto il mestiere sta in GBUtils, cosi' la regola sulle esclusioni e' una
sola per tutti i progetti. Qui resta soltanto il nome di PokerMachine.

PokerMachine si compila in un file unico, quindi dentro dist c'e'
soltanto l'eseguibile e tutto il resto viaggia dentro di lui.

Si lascia fuori il salvataggio, che nasce giocando accanto all'eseguibile
e conterrebbe il gruzzolo di chi ha compilato. L'estensione pkl non e' fra
quelle saltate d'ufficio, percio' va nominata qui.
"""

import sys

from GBUtils import crea_archivio_release

FUORI = ["pokermachine_data.pkl"]


def main():
    try:
        crea_archivio_release("pokermachine", cartella_dist="dist", escludi=FUORI)
    except (FileNotFoundError, OSError) as e:
        print(f"Archivio non creato: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
