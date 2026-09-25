# PokerMachine, il consiglio: il motore della strategia al servizio di chi gioca.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 24/09/2026: nasce con la versione 5, tappa 4 del piano (issue 7).

"""Il consiglio sulla tenuta.

Consigliere fa lavorare il motore di strategia in un thread: all'avvio lo
prepara, e a ogni mano servita calcola il valore di tutte le tenute mentre
chi gioca legge le carte. Quando serve il consiglio, o la precisione a fine
mano, il risultato e' quasi sempre gia' pronto. Se il calcolo fallisce il
gioco prosegue senza: il consiglio e la precisione di quella mano mancano.

Le funzioni di testo dicono una tenuta come la si scrive al prompt delle
carte, con i numeri attaccati, seguiti dalle carte in forma breve.
"""

from concurrent.futures import ThreadPoolExecutor

import numpy as np

import regole
import strategia
from numeri import formatta_fiches


class Consigliere:
    def __init__(self):
        self._esecutore = ThreadPoolExecutor(max_workers=1, thread_name_prefix="consiglio")
        self._esecutore.submit(strategia.MOTORE.prepara)
        self._futuro = None

    def calcola(self, mano, mazzo, tabella):
        """Avvia il calcolo delle tenute di una mano.

        mano sono le cinque Carta nell'ordine in cui il gioco le mostra,
        mazzo quello da cui si pescheranno le nuove, tabella quella su cui
        decidere, da partita.tabella_decisione.
        """
        tipi = [regole.tipo_carta(c) for c in mano]
        scarpa, rimescolo = scarpe_per_la_pesca(mazzo)
        self._futuro = self._esecutore.submit(strategia.valuta_tenute, tipi, scarpa, tabella, rimescolo)

    def tenute(self):
        """Le 32 tenute della mano in corso, oppure None se il calcolo non c'e' o e' fallito."""
        if self._futuro is None:
            return None
        try:
            return self._futuro.result()
        except (ValueError, MemoryError, np.exceptions.AxisError, IndexError):
            return None

    def dimentica(self):
        self._futuro = None

    def chiudi(self):
        self._esecutore.shutdown(wait=False, cancel_futures=True)


def scarpe_per_la_pesca(mazzo):
    """I conteggi della scarpa da cui si pescheranno le nuove carte, e quelli dopo un rimescolamento.

    Il mazzo rimescola dentro gli scarti solo quando deve pescare piu' carte
    di quante ne restano: se la scarpa ne ha almeno cinque il secondo valore
    e' None, altrimenti conta scarpa e scarti insieme, e il motore sceglie
    tenuta per tenuta. Le carte che chi gioca scarta in questa mano
    finirebbero a loro volta fra gli scarti prima del rimescolamento, ma
    sono poche su cinquecento e il consiglio non ne tiene conto.
    """
    scarpa = strategia.conteggi_scarpa(mazzo.carte)
    if len(mazzo.carte) >= regole.CARTE_PER_MANO:
        return scarpa, None
    return scarpa, scarpa + strategia.conteggi_scarpa(mazzo.scarti)


def tenuta_breve(maschera, mano):
    """La tenuta come si scrive al prompt, con le carte in forma breve: 13, cioè QC JQ."""
    posizioni = strategia.carte_tenute(maschera)
    if not posizioni:
        return "invio, cioè cambiale tutte"
    numeri = "".join(str(i + 1) for i in posizioni)
    if len(posizioni) == regole.CARTE_PER_MANO:
        return f"{numeri}, cioè tienile tutte"
    return f"{numeri}, cioè {' '.join(mano[i].desc_breve for i in posizioni)}"


def maschera_di(tenute_scelte):
    """La maschera di una scelta di carte, date le posizioni da zero."""
    return sum(1 << i for i in tenute_scelte)


def in_fiches(valore, puntata):
    """Un valore atteso in puntate, detto in fiches: sotto dieci con un decimale e la virgola, sopra come le altre fiches."""
    fiches = valore * puntata
    if fiches >= 10:
        return formatta_fiches(round(fiches))
    return f"{fiches:.1f}".replace(".", ",")
