# PokerMachine, la strategia: il valore atteso di ogni tenuta, calcolato esatto.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 24/09/2026: nasce con la versione 5, tappa 1 del piano (issue 4). Serve al
# consiglio durante il gioco e al simulatore che tara la tabella.

"""Il motore della tenuta migliore.

Per una mano servita e la scarpa da cui si pesca, calcola il valore atteso
di ciascuna delle 32 tenute possibili, in multipli della puntata, e la
probabilita' di ogni punteggio finale.

Il calcolo e' esatto, non a campione. La scarpa e' il conteggio di ciascuno
dei 52 tipi di carta, e per una tenuta di j carte si passano in rassegna
tutti i multinsiemi di 5 meno j tipi che si possono pescare, ciascuno con il
suo peso: il prodotto dei coefficienti binomiali sulle copie rimaste. Che
cosa contenga ogni mano finale si legge da un elenco preparato una volta
sola su tutti i 3.819.816 multinsiemi di cinque tipi, con le condizioni di
regole.bandiere.

L'elenco non registra il punteggio ma la combinazione di condizioni
soddisfatte, e le combinazioni che si presentano davvero sono poche decine.
Il calcolo di una mano da' la probabilita' di ciascuna combinazione per ogni
tenuta, e solo alla fine la tabella in vigore dice quale punteggio paghi
ogni combinazione: la stessa pescata serve alla tabella normale, a quella
della Killer Hand, alle regole a sorpresa e al simulatore che prova tabelle
nuove.

Il modulo non stampa. La preparazione impiega un paio di secondi e un
centinaio di megabyte, il calcolo di una mano circa due decimi di secondo:
il gioco li fa in un thread mentre chi gioca legge le carte.
"""

import threading
from collections import namedtuple
from math import comb

import numpy as np

import regole

CARTE = regole.CARTE_PER_MANO
NUM_TENUTE = 1 << CARTE
NUM_PUNTEGGI = len(regole.NOMI_PUNTEGGI)
TUTTE_TENUTE = NUM_TENUTE - 1
# Le condizioni si calcolano a blocchi, per non tenere in memoria venti
# vettori da quasi quattro milioni di voci tutti insieme.
BLOCCO = 400_000
# Quante tabelle il motore ricorda: il gioco ne usa poche, un simulatore puo' provarne migliaia.
TABELLE_RICORDATE = 32
# I coefficienti binomiali che servono all'indice dei multinsiemi.
_BINOMIALI = np.array([[comb(n, k) for k in range(CARTE + 1)] for n in range(regole.NUM_TIPI + CARTE)], dtype=np.int64)

Tenuta = namedtuple("Tenuta", ["maschera", "valore", "distribuzione"])


def multinsiemi(k):
    """Tutti i multinsiemi di k tipi, una riga ordinata per ciascuno."""
    righe = np.arange(regole.NUM_TIPI, dtype=np.uint8)[:, None]
    for _ in range(k - 1):
        ultimo = righe[:, -1].astype(np.int64)
        quante = regole.NUM_TIPI - ultimo
        ripetute = np.repeat(righe, quante, axis=0)
        # Ogni riga si allunga con tutti i tipi dal suo ultimo in su.
        partenze = np.repeat(np.cumsum(quante) - quante, quante)
        nuovi = np.repeat(ultimo, quante) + np.arange(quante.sum()) - partenze
        righe = np.concatenate([ripetute, nuovi.astype(np.uint8)[:, None]], axis=1)
    return righe


def ripetizioni(righe):
    """Per ogni posizione, quante volte il suo tipo compare prima nella riga."""
    volte = np.zeros_like(righe)
    for i in range(1, righe.shape[1]):
        volte[:, i] = np.where(righe[:, i] == righe[:, i - 1], volte[:, i - 1] + 1, 0)
    return volte


def indice(righe):
    """La posizione di ogni multinsieme ordinato nell'elenco di quelli della sua lunghezza.

    E' il sistema combinatorio dei numeri: con a_i il tipo in posizione i,
    la posizione e' la somma dei binomiali di a_i + i su i + 1. Per questo
    i primi k - 1 tipi di un multinsieme di k danno, da soli, la posizione
    del multinsieme che ne resta togliendo l'ultimo.
    """
    posizioni = np.zeros(righe.shape[0], dtype=np.int64)
    for i in range(righe.shape[1]):
        posizioni += _BINOMIALI[righe[:, i].astype(np.int64) + i, i + 1]
    return posizioni


def in_ordine(k):
    """Tutti i multinsiemi di k tipi, ciascuno nella riga che l'indice gli assegna."""
    righe = multinsiemi(k)
    return righe[np.argsort(indice(righe))]


def conteggi_scarpa(carte):
    """Quante carte di ciascun tipo ci sono in una lista di Carta."""
    return np.bincount([regole.tipo_carta(c) for c in carte], minlength=regole.NUM_TIPI)


def carte_tenute(maschera):
    """Le posizioni, da zero, delle carte che una tenuta conserva."""
    return [i for i in range(CARTE) if maschera >> i & 1]


def soddisfatti(codice):
    """I nomi dei punteggi che una combinazione di condizioni soddisfa."""
    return [nome for bit, nome in enumerate(regole.NOMI_PUNTEGGI) if int(codice) >> bit & 1]


class Motore:
    """L'elenco preparato una volta sola e il calcolo delle tenute.

    La preparazione parte alla prima richiesta, oppure prima con prepara,
    che il gioco chiama in un thread all'avvio. Il calcolo si puo' chiedere
    da piu' thread.
    """

    def __init__(self):
        self._lucchetto = threading.Lock()
        self._pronto = False
        self._per_tabella = {}

    def prepara(self):
        with self._lucchetto:
            if self._pronto:
                return
            tutte = in_ordine(CARTE)
            codici = np.zeros(len(tutte), dtype=np.uint32)
            for inizio in range(0, len(tutte), BLOCCO):
                condizioni = regole.bandiere(tutte[inizio : inizio + BLOCCO])
                for bit, nome in enumerate(regole.NOMI_PUNTEGGI):
                    codici[inizio : inizio + BLOCCO] |= condizioni[nome].astype(np.uint32) << bit
            self.combinazioni, inverso = np.unique(codici, return_inverse=True)
            if len(self.combinazioni) > np.iinfo(np.uint8).max:
                raise ValueError("troppe combinazioni di condizioni per un byte")
            self._combinazione = inverso.astype(np.uint8)
            # Il peso di una pescata di k tipi si costruisce da quello della
            # pescata senza l'ultimo tipo, il padre, per il fattore dell'ultimo:
            # la chiave dell'ultimo dice il tipo e quante sue copie lo
            # precedono.
            self._pescate = {}
            self._ultima = {}
            self._padre = {}
            for k in range(1, CARTE + 1):
                righe = tutte if k == CARTE else in_ordine(k)
                self._pescate[k] = righe
                self._ultima[k] = righe[:, -1].astype(np.uint16) * CARTE + ripetizioni(righe)[:, -1]
                if k > 1:
                    self._padre[k] = indice(righe[:, :-1]).astype(np.int32)
            # Chi tiene una carta sola ne pesca quattro: per ogni carta tenuta,
            # la combinazione di ogni mano finale, preparata qui una volta sola.
            quattro = self._pescate[CARTE - 1]
            self._una_tenuta = np.empty((regole.NUM_TIPI, len(quattro)), dtype=np.uint8)
            for tipo in range(regole.NUM_TIPI):
                righe = np.concatenate([np.full((len(quattro), 1), tipo, dtype=np.uint8), quattro], axis=1)
                righe.sort(axis=1)
                self._una_tenuta[tipo] = self._combinazione[indice(righe)]
            del self._pescate[CARTE], self._pescate[CARTE - 1]
            self._pronto = True

    def punteggio_per_combinazione(self, tabella=None):
        """Per ogni combinazione di condizioni, la posizione del punteggio che paga con quella tabella."""
        self.prepara()
        tabella = regole.TABELLA_VINCITE if tabella is None else tabella
        chiave = tuple(tabella[nome] for nome in regole.NOMI_PUNTEGGI)
        with self._lucchetto:
            scelti = self._per_tabella.get(chiave)
            if scelti is None:
                scelti = np.array([regole.POSIZIONE[regole.migliore_punteggio(soddisfatti(c), tabella)] for c in self.combinazioni])
                if len(self._per_tabella) >= TABELLE_RICORDATE:
                    self._per_tabella.clear()
                self._per_tabella[chiave] = scelti
        return scelti

    def _pesi(self, copie):
        """I pesi di tutte le pescate da una scarpa, per ogni numero di carte pescate.

        Il fattore di una carta pescata che e' la r-esima copia del suo tipo
        e' (n - r) / (r + 1): il prodotto dei fattori di una pescata e' il
        prodotto dei binomiali, cioe' in quanti modi la si ottiene.
        """
        volte = np.arange(CARTE)
        fattori = np.clip((copie[:, None] - volte) / (volte + 1), 0, None).ravel()
        pesi = {1: fattori[self._ultima[1]]}
        for k in range(2, CARTE + 1):
            pesi[k] = pesi[k - 1][self._padre[k]] * fattori[self._ultima[k]]
        return pesi

    def distribuzioni(self, mano, conteggi, rimescolo=None):
        """Per ognuna delle 32 tenute, la probabilita' di ogni combinazione di condizioni finale.

        mano sono i cinque tipi nell'ordine in cui il gioco li mostra, e la
        tenuta i conserva la carta j se il bit j di i e' acceso. conteggi
        sono le copie di ciascun tipo nella scarpa da cui si pesca, senza
        le carte della mano. Restituisce una matrice di 32 righe, una per
        tenuta, e una colonna per ciascuna voce di combinazioni.

        rimescolo serve quando la scarpa ha meno di cinque carte: il mazzo di
        GBUtils rimescola dentro gli scarti solo se deve pescare piu' carte
        di quante ne restano. Le tenute che ne pescano al massimo quante ce
        ne sono si calcolano sulla scarpa, le altre sui conteggi di rimescolo,
        cioe' scarpa piu' scarti. Senza rimescolo, una scarpa sotto le cinque
        carte solleva ValueError, come i conteggi negativi.
        """
        self.prepara()
        copie = np.asarray(conteggi, dtype=float)
        if (copie < 0).any():
            raise ValueError("una scarpa non ha copie negative")
        restanti = copie.sum()
        if restanti < CARTE and rimescolo is None:
            raise ValueError("la scarpa ha meno di cinque carte")
        colonne = len(self.combinazioni)
        pesi = self._pesi(copie)
        if restanti < CARTE:
            dopo = np.asarray(rimescolo, dtype=float)
            if (dopo < 0).any() or dopo.sum() < CARTE:
                raise ValueError("la scarpa del rimescolamento ha meno di cinque carte")
            pesi_dopo = self._pesi(dopo)
            pesi = {k: (pesi[k] if k <= restanti else pesi_dopo[k]) for k in pesi}
        totali = {k: pesi[k].sum() for k in pesi}
        risultato = np.zeros((NUM_TENUTE, colonne))
        for maschera in range(NUM_TENUTE):
            tenuti = sorted(mano[i] for i in carte_tenute(maschera))
            k = CARTE - len(tenuti)
            if k == 0:
                risultato[maschera, self._combinazione[indice(np.array([tenuti]))[0]]] = 1.0
                continue
            if k == CARTE:
                finali = self._combinazione
            elif k == CARTE - 1:
                finali = self._una_tenuta[tenuti[0]]
            else:
                pescate = self._pescate[k]
                righe = np.concatenate([np.broadcast_to(np.array(tenuti, dtype=np.uint8), (len(pescate), len(tenuti))), pescate], axis=1)
                righe.sort(axis=1)
                finali = self._combinazione[indice(righe)]
            risultato[maschera] = np.bincount(finali, weights=pesi[k], minlength=colonne) / totali[k]
        return risultato

    def valuta(self, mano, conteggi, tabella=None, rimescolo=None):
        """Le 32 tenute di una mano, nell'ordine delle maschere.

        mano e conteggi sono quelli di distribuzioni; tabella e' quella dei
        multipli in vigore, da nome a multiplo, e senza vale quella del
        gioco. Ogni Tenuta ha la maschera, il valore atteso in multipli
        della puntata e la probabilita' di ogni punteggio, nell'ordine di
        NOMI_PUNTEGGI.
        """
        tabella = regole.TABELLA_VINCITE if tabella is None else tabella
        probabilita = self.distribuzioni(mano, conteggi, rimescolo)
        punteggi = self.punteggio_per_combinazione(tabella)
        multipli = np.array([tabella[nome] for nome in regole.NOMI_PUNTEGGI], dtype=float)
        # Da combinazioni a punteggi: si sommano le colonne che pagano lo stesso.
        per_punteggio = np.zeros((len(self.combinazioni), NUM_PUNTEGGI))
        per_punteggio[np.arange(len(punteggi)), punteggi] = 1.0
        distribuzioni = probabilita @ per_punteggio
        valori = distribuzioni @ multipli
        return [Tenuta(m, float(valori[m]), distribuzioni[m]) for m in range(NUM_TENUTE)]


MOTORE = Motore()


def valuta_tenute(mano, conteggi, tabella=None, rimescolo=None):
    """Le 32 tenute di una mano, calcolate dal motore condiviso. Vedi Motore.valuta."""
    return MOTORE.valuta(mano, conteggi, tabella, rimescolo)


def migliore(tenute):
    """La tenuta con il valore atteso piu' alto; a parita', quella con la maschera piu' bassa."""
    return max(tenute, key=lambda t: (t.valore, -t.maschera))


def e_ottima(tenute, maschera, tolleranza=1e-9):
    """Vero se quella tenuta vale quanto la migliore, a meno degli arrotondamenti."""
    return tenute[maschera].valore >= migliore(tenute).valore - tolleranza
