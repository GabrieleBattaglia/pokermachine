# PokerMachine, taratura: le probabilita' di ogni tenuta su un campione di mani servite.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 24/09/2026: nasce con la versione 5, per tarare tabella e Killer Hand con la
# strategia ottima (issue 5 e 6). Strumento di misura, non fa parte del gioco.

"""Il campione su cui si tara PokerMachine.

Pesca un certo numero di mani da una scarpa nuova di dieci mazzi e, per
ciascuna, fa calcolare al motore la probabilita' di ogni combinazione di
condizioni finale per tutte le 32 tenute. Con questi numeri qualunque
tabella si valuta con la strategia ottima in una frazione di secondo,
senza rifare i conti: lo fa taratura.py.

Si lancia con:
    python taratura/dati_tenute.py [mani] [processi] [cartella]
e un calcolo fermato a meta' si riprende da dove era arrivato con:
    python taratura/dati_tenute.py riprendi [mani] [processi] [cartella]
Predefiniti: 100000 mani, 24 processi, E:\\git\\tmp\\pokermachine_taratura.
Scrive nella cartella tenute.npy, con le probabilita' in float32, mani.npy
con le cinque carte di ogni mano e combinazioni.npy con i codici delle
combinazioni di condizioni, un bit per punteggio, e nomi.json con l'ordine dei
punteggi a cui i bit si riferiscono.
"""

import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import regole
import strategia

CARTELLA = r"E:\git\tmp\pokermachine_taratura"
BLOCCO = 250
SEME = 20260924


def pesca_mani(quante, seme):
    """Le mani servite, cinque tipi ciascuna, da scarpe nuove di dieci mazzi."""
    generatore = np.random.default_rng(seme)
    scarpa = np.repeat(np.arange(regole.NUM_TIPI, dtype=np.uint8), regole.NUM_MAZZI)
    chiavi = generatore.random((quante, len(scarpa)))
    scelte = np.argpartition(chiavi, regole.CARTE_PER_MANO, axis=1)[:, : regole.CARTE_PER_MANO]
    return scarpa[scelte]


def _prepara():
    strategia.MOTORE.prepara()


def _calcola(lavoro):
    inizio, mani = lavoro
    risultato = np.empty((len(mani), strategia.NUM_TENUTE, len(strategia.MOTORE.combinazioni)), dtype=np.float32)
    for i, mano in enumerate(mani):
        conteggi = regole.NUM_MAZZI - np.bincount(mano, minlength=regole.NUM_TIPI)
        risultato[i] = strategia.MOTORE.distribuzioni([int(t) for t in mano], conteggi)
    return inizio, risultato


def complete(tenute):
    """Per ogni mano, vero se tutte le sue 32 tenute sono state scritte per intero.

    Una tenuta scritta ha le probabilita' che sommano a uno; una mano mai
    calcolata ha tutti zeri, e una interrotta a meta' della copia ha qualche
    tenuta incompleta. Serve a riprendere un calcolo fermato.
    """
    return np.abs(tenute.sum(axis=2, dtype=np.float64) - 1).max(axis=1) < 1e-3


def main():
    """Con riprendi come primo argomento continua un calcolo fermato, con gli stessi parametri."""
    argomenti = sys.argv[1:]
    riprendi = bool(argomenti) and argomenti[0] == "riprendi"
    if riprendi:
        argomenti = argomenti[1:]
    quante = int(argomenti[0]) if len(argomenti) > 0 else 100_000
    processi = int(argomenti[1]) if len(argomenti) > 1 else 24
    cartella = argomenti[2] if len(argomenti) > 2 else CARTELLA
    os.makedirs(cartella, exist_ok=True)
    strategia.MOTORE.prepara()
    colonne = len(strategia.MOTORE.combinazioni)
    percorso = os.path.join(cartella, "tenute.npy")
    if riprendi:
        mani = np.load(os.path.join(cartella, "mani.npy"))
        tenute = np.lib.format.open_memmap(percorso, mode="r+")
        if tenute.shape != (len(mani), strategia.NUM_TENUTE, colonne):
            raise ValueError("il calcolo da riprendere ha una forma diversa")
        quante = len(mani)
        fatte_prima = complete(tenute)
    else:
        mani = pesca_mani(quante, SEME)
        np.save(os.path.join(cartella, "mani.npy"), mani)
        np.save(os.path.join(cartella, "combinazioni.npy"), strategia.MOTORE.combinazioni)
        with open(os.path.join(cartella, "nomi.json"), "w", encoding="utf-8") as f:
            json.dump(list(regole.NOMI_PUNTEGGI), f, ensure_ascii=False)
        tenute = np.lib.format.open_memmap(percorso, mode="w+", dtype=np.float32, shape=(quante, strategia.NUM_TENUTE, colonne))
        fatte_prima = np.zeros(quante, dtype=bool)
    lavori = [(i, mani[i : i + BLOCCO]) for i in range(0, quante, BLOCCO) if not fatte_prima[i : i + BLOCCO].all()]
    da_fare = sum(len(m) for _, m in lavori)
    print(f"Da calcolare: {da_fare} mani su {quante}.", flush=True)
    partenza = time.perf_counter()
    fatte = 0
    with Pool(processi, initializer=_prepara) as pool:
        for inizio, risultato in pool.imap_unordered(_calcola, lavori):
            tenute[inizio : inizio + len(risultato)] = risultato
            fatte += len(risultato)
            if fatte % (BLOCCO * 40) == 0 or fatte == da_fare:
                tenute.flush()
                trascorsi = time.perf_counter() - partenza
                print(f"{fatte} mani su {da_fare}, {trascorsi:.0f} secondi.", flush=True)
    tenute.flush()
    print(f"Fatto: {da_fare} mani, {colonne} combinazioni, in {time.perf_counter() - partenza:.0f} secondi.")


if __name__ == "__main__":
    main()
