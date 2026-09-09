# PokerMachine, utilita': prepara l'archivio per la distribuzione.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 04/09/2026: primo chiamante, il mestiere sta in crea_archivio_release di GBUtils V104.
# 09/09/2026: il salvataggio e' diventato JSON, con il vecchio pickle accanto.

"""Comprime il risultato di PyInstaller in un solo archivio.

Tutto il mestiere sta in GBUtils, cosi' la regola sulle esclusioni e' una
sola per tutti i progetti. Qui resta soltanto il nome di PokerMachine.

PokerMachine si compila in un file unico, quindi dentro dist c'e'
soltanto l'eseguibile e tutto il resto viaggia dentro di lui.

Si lascia fuori il salvataggio, che nasce giocando accanto all'eseguibile
e conterrebbe il gruzzolo di chi ha compilato, insieme al pickle della
versione 3 se ci fosse. Le copie di riserva restano fuori d'ufficio.
"""

import sys

from GBUtils import crea_archivio_release

FUORI = ["pokermachine_data.json", "pokermachine_data.pkl", "pokermachine_data.pkl.migrato"]


def main():
    try:
        crea_archivio_release("pokermachine", cartella_dist="dist", escludi=FUORI)
    except (FileNotFoundError, OSError) as e:
        print(f"Archivio non creato: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
