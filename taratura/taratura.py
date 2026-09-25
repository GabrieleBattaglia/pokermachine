# PokerMachine, taratura: tabella e Killer Hand provate con la strategia ottima.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 24/09/2026: nasce con la versione 5 (issue 5 e 6). Strumento di misura, non
# fa parte del gioco: le funzioni si importano da altri script di prova.

"""Gli attrezzi per tarare PokerMachine.

Campione legge cio' che dati_tenute.py ha calcolato e valuta qualunque
tabella con la strategia ottima: per ogni mano del campione sceglie la
tenuta dal valore atteso piu' alto con i multipli in vigore, e somma le
probabilita' delle combinazioni finali. Le decisioni si possono prendere con
multipli diversi da quelli pagati: nella Killer Hand conta la vincita netta
moltiplicata, e con uno scudo in tasca la mano persa restituisce la puntata.

simula_serie gioca migliaia di serie insieme, dalla partenza al fallimento,
con la Killer Hand come gara: alla Killer Hand numero N la puntata minima e'
base per fattore alla N, e chi ha meno fiches punta tutto. Ogni modo di
puntare e' una funzione che riceve lo stato di tutte le serie e restituisce
le puntate desiderate; il simulatore le porta dentro i limiti.
"""

import json
import os
import sys
from dataclasses import dataclass, field

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import regole
import strategia

CARTELLA = r"E:\git\tmp\pokermachine_taratura"
TUTTE = strategia.TUTTE_TENUTE
COPPIE = regole.COPPIE
# Solo un freno contro l'overflow: la gara raddoppia il minimo per sempre, e
# raggiunge anche chi ha un milione di miliardi di fiches. Fino al 25/09/2026
# la soglia era 1e15, e contava arrivate al tetto serie che non lo erano.
FUGA = 1e250


class Campione:
    """Le probabilita' delle tenute su un campione di mani, e cosa ne esce con una tabella."""

    def __init__(self, cartella=CARTELLA, mani=None):
        tenute = np.load(os.path.join(cartella, "tenute.npy"), mmap_mode="r")
        self.tenute = np.array(tenute[:mani] if mani else tenute)
        self.combinazioni = np.load(os.path.join(cartella, "combinazioni.npy"))
        # I bit dei codici seguono l'ordine dei punteggi del momento in cui il
        # campione e' stato calcolato, che dati_tenute.py salva in nomi.json.
        with open(os.path.join(cartella, "nomi.json"), encoding="utf-8") as f:
            nomi = json.load(f)
        if sorted(nomi) != sorted(regole.NOMI_PUNTEGGI):
            raise ValueError("il campione e' stato calcolato con altri punteggi: va rifatto")
        self.soddisfatti = [[nome for bit, nome in enumerate(nomi) if int(c) >> bit & 1] for c in self.combinazioni]
        self.mani = len(self.tenute)
        # La distribuzione esatta delle mani servite: cinque carte pescate da
        # una scarpa nuova, cioe' la tenuta vuota con tutte le copie. Serve da
        # variabile di controllo: la media del campione si corregge con la
        # differenza fra le servite del campione e quelle esatte, e l'errore
        # dovuto alle mani servite fortunate, come un poker gia' fatto, sparisce.
        strategia.MOTORE.prepara()
        tutte = np.full(regole.NUM_TIPI, regole.NUM_MAZZI)
        dal_motore = strategia.MOTORE.distribuzioni([0] * regole.CARTE_PER_MANO, tutte)[0]
        # Il motore numera le combinazioni con l'ordine dei punteggi di adesso,
        # il campione con quello di quando e' stato calcolato: si abbinano per
        # insieme di nomi, che non dipende dall'ordine.
        colonna = {frozenset(s): i for i, s in enumerate(self.soddisfatti)}
        self.esatte = np.zeros(len(self.combinazioni))
        for codice, p in zip(strategia.MOTORE.combinazioni, dal_motore, strict=True):
            self.esatte[colonna[frozenset(strategia.soddisfatti(codice))]] += p
        self.servite_campione = self.tenute[:, TUTTE].astype(np.float64).mean(axis=0)

    def punteggi(self, tabella):
        """Per ogni combinazione, la posizione del punteggio pagato."""
        return np.array([regole.POSIZIONE[regole.migliore_punteggio(s, tabella)] for s in self.soddisfatti])

    def multipli(self, tabella):
        """Per ogni combinazione, il multiplo pagato."""
        return np.array([tabella[regole.migliore_punteggio(s, tabella)] for s in self.soddisfatti], dtype=float)

    def ottimo(self, valori):
        """Probabilita' delle combinazioni finali giocando sempre la tenuta dal valore piu' alto.

        valori e' il guadagno di ogni combinazione su cui si decide. Restituisce
        anche il valore medio della tenuta migliore.
        """
        attesi = self.tenute @ valori.astype(np.float32)
        scelte = attesi.argmax(axis=1)
        finali = self.tenute[np.arange(self.mani), scelte].astype(np.float64).mean(axis=0)
        stima = np.clip(finali - self.servite_campione + self.esatte, 0, None)
        stima /= stima.sum()
        return stima, float(stima @ valori)

    def imperfetto(self, valori, errore):
        """Come ottimo, ma una volta su 1/errore si gioca la seconda tenuta migliore invece della prima.

        E' un modello grezzo di chi gioca bene ma non sempre al meglio: serve a
        vedere quanto il ritorno e la gara dipendono dalla precisione.
        """
        attesi = self.tenute @ valori.astype(np.float32)
        ordine = np.argsort(attesi, axis=1)
        righe = np.arange(self.mani)
        prima = self.tenute[righe, ordine[:, -1]].astype(np.float64).mean(axis=0)
        seconda = self.tenute[righe, ordine[:, -2]].astype(np.float64).mean(axis=0)
        finali = (1 - errore) * prima + errore * seconda
        stima = np.clip(finali - self.servite_campione + self.esatte, 0, None)
        stima /= stima.sum()
        return stima, float(stima @ valori)

    def servite(self):
        """Probabilita' esatte delle combinazioni delle mani servite, senza cambiare niente."""
        return self.esatte

    def frequenze(self, probabilita, tabella):
        """Da probabilita' delle combinazioni a probabilita' dei punteggi."""
        per_punteggio = np.zeros(len(regole.NOMI_PUNTEGGI))
        np.add.at(per_punteggio, self.punteggi(tabella), probabilita)
        return per_punteggio


def killer(multipli, netta):
    """Il guadagno in una Killer Hand: la vincita netta moltiplicata, pareggio e perdita invariati."""
    return np.where(multipli > 1, 1 + netta * (multipli - 1), multipli)


@dataclass
class Esito:
    """Una distribuzione da cui estrarre: probabilita', ritorno per fiche puntata, scudo guadagnato."""

    probabilita: np.ndarray
    ritorni: np.ndarray
    scudo: np.ndarray
    cumulate: np.ndarray = field(init=False)

    def __post_init__(self):
        p = np.clip(self.probabilita, 0, None)
        self.cumulate = np.cumsum(p / p.sum())

    def estrai(self, generatore, quante):
        i = np.searchsorted(self.cumulate, generatore.random(quante) * self.cumulate[-1])
        i = np.minimum(i, len(self.ritorni) - 1)
        return self.ritorni[i], self.scudo[i]

    def valore(self):
        return float(self.probabilita @ self.ritorni)

    def perdita(self):
        return float(self.probabilita[self.ritorni == 0].sum())


@dataclass
class Regola:
    """Una regola a sorpresa della Killer Hand: cosa cambia nella tabella e nella vincita."""

    nome: str
    muta: tuple = ()
    netta: float = 3
    pareggio_perde: bool = False
    nessun_cambio: bool = False


REGOLE_SORPRESA = {
    "semplice": Regola("semplice"),
    "nessun cambio": Regola("nessun cambio", nessun_cambio=True),
    "coppie mute": Regola("coppie mute", muta=COPPIE),
    "tutto o niente": Regola("tutto o niente", netta=5, pareggio_perde=True),
}


def esiti(campione, tabella, scudo_da, regole_kh, netta_base=3, errore=0.0):
    """Le distribuzioni per il simulatore: la mano normale e, per ogni regola, la Killer Hand senza e con scudo.

    scudo_da e' l'insieme dei punteggi che regalano uno scudo. errore e' la
    frequenza con cui si gioca la seconda tenuta migliore invece della prima.
    Restituisce (normale, {nome regola: (senza scudo, con scudo)}, rapporto)
    dove il rapporto dice ritorno e frequenze della mano normale.
    """

    def gioca(valori):
        return campione.imperfetto(valori, errore) if errore else campione.ottimo(valori)

    base = campione.multipli(tabella)
    punteggi = campione.punteggi(tabella)
    da_scudo = np.array([regole.NOMI_PUNTEGGI[p] in scudo_da for p in punteggi])
    probabilita, _ = gioca(base)
    normale = Esito(probabilita, base, da_scudo)
    per_regola = {}
    for nome in regole_kh:
        regola = REGOLE_SORPRESA[nome]
        in_vigore = dict(tabella)
        for voce in regola.muta:
            in_vigore[voce] = 0
        if regola.pareggio_perde:
            in_vigore = {k: (0 if v == 1 else v) for k, v in in_vigore.items()}
        pagati = campione.multipli(in_vigore)
        netta = regola.netta * netta_base / 3
        guadagno = killer(pagati, netta)
        coppia = []
        for con_scudo in (False, True):
            decisione = np.where(guadagno == 0, 1.0, guadagno) if con_scudo else guadagno
            if regola.nessun_cambio:
                p = campione.servite()
            else:
                p, _ = gioca(decisione)
            coppia.append(Esito(p, guadagno, da_scudo))
        per_regola[nome] = tuple(coppia)
    rapporto = {
        "ritorno": float(probabilita @ base),
        "frequenze": campione.frequenze(probabilita, tabella),
        "scudo_ogni": 1 / max(float(probabilita[da_scudo].sum()), 1e-12),
    }
    return normale, per_regola, rapporto


@dataclass
class Gara:
    """I parametri della Killer Hand come gara."""

    base: float = 20
    fattore: float = 2.5
    ogni: int = regole.KILLER_HAND_FREQUENZA
    scudi_max: int = 3
    # Le sfide: a quali mani della serie si completano, con quale probabilita' ciascuna.
    sfide: tuple = ()


def minimo_killer(gara, numero):
    return np.floor(gara.base * gara.fattore**numero)


def simula_serie(normale, per_regola, gara, politiche, serie=2000, tetto=3000, seme=1, fiches=regole.FICHES_INIZIALI):
    """Gioca le serie di tutte le politiche insieme. Restituisce, per politica, le durate e gli scudi usati.

    politiche e' un dizionario da nome a funzione(stato) che restituisce le
    puntate desiderate; stato ha fiches, mano (numero nella serie), killer
    (vero se la mano e' una Killer Hand), minimo_kh (il minimo della
    prossima Killer Hand, o di questa), mancano (mani alla prossima Killer
    Hand) e scudi.
    """
    nomi = list(politiche)
    righe = serie * len(nomi)
    generatore = np.random.default_rng(seme)
    f = np.full(righe, float(fiches))
    vive = np.ones(righe, dtype=bool)
    durata = np.full(righe, tetto)
    scudi = np.zeros(righe)
    usati = np.zeros(righe)
    quale = np.repeat(np.arange(len(nomi)), serie)
    regole_kh = list(per_regola)
    for mano in range(1, tetto + 1):
        attive = np.flatnonzero(vive)
        if len(attive) == 0:
            break
        e_kh = mano % gara.ogni == 0
        numero = (mano + gara.ogni - 1) // gara.ogni
        stato = {
            "fiches": f[attive],
            "mano": mano,
            "killer": e_kh,
            "minimo_kh": float(minimo_killer(gara, numero)),
            "mancano": (-mano) % gara.ogni,
            "scudi": scudi[attive],
        }
        desiderate = np.zeros(len(attive))
        for p, nome in enumerate(nomi):
            dentro = quale[attive] == p
            if dentro.any():
                sotto = {k: (v[dentro] if isinstance(v, np.ndarray) else v) for k, v in stato.items()}
                desiderate[dentro] = politiche[nome](sotto)
        fa = f[attive]
        minima = np.maximum(np.floor(fa * regole.PERCENTUALE_MINIMA_PUNTATA / 100), 1)
        if e_kh:
            minima = np.maximum(minima, stato["minimo_kh"])
        puntata = np.minimum(np.maximum(np.floor(desiderate), minima), fa)
        if e_kh:
            ritorno = np.empty(len(attive))
            scudo = np.empty(len(attive), dtype=bool)
            regola = generatore.integers(len(regole_kh), size=len(attive))
            protetti = scudi[attive] > 0
            for r, nome in enumerate(regole_kh):
                for con in (False, True):
                    sel = (regola == r) & (protetti == con)
                    if sel.any():
                        ritorno[sel], scudo[sel] = per_regola[nome][int(con)].estrai(generatore, int(sel.sum()))
            salvati = (ritorno == 0) & protetti
            ritorno[salvati] = 1
            scudi[attive[salvati]] -= 1
            usati[attive[salvati]] += 1
        else:
            ritorno, scudo = normale.estrai(generatore, len(attive))
        f[attive] = fa - puntata + np.floor(puntata * ritorno)
        scudi[attive] = np.minimum(scudi[attive] + scudo, gara.scudi_max)
        for quando, probabilita in gara.sfide:
            if mano == quando:
                vinte = generatore.random(len(attive)) < probabilita
                scudi[attive] = np.minimum(scudi[attive] + vinte, gara.scudi_max)
        morte = f[attive] < 1
        durata[attive[morte]] = mano
        vive[attive[morte]] = False
        # Oltre FUGA i numeri in virgola mobile non bastano piu': la serie si
        # ferma e si conta arrivata al tetto.
        fuggite = f[attive] > FUGA
        vive[attive[fuggite]] = False
    return {nome: (durata[quale == p], usati[quale == p]) for p, nome in enumerate(nomi)}


def riassunto(durate, tetto=3000):
    d = np.sort(durate)
    n = len(d)
    return {
        "mediana": int(d[n // 2]),
        "decimo": int(d[n // 10]),
        "nono": int(d[9 * n // 10]),
        "oltre400": float((d >= 400).mean()),
        "tetto": float((d >= tetto).mean()),
        "media": float(d.mean()),
    }


def frazione(f, in_kh=0.0):
    """Punta la frazione f nelle mani normali e in_kh nelle Killer Hand, sempre almeno il minimo."""

    def politica(stato):
        quota = in_kh if stato["killer"] else f
        return stato["fiches"] * quota

    return politica


def adattiva(alta, bassa, soglia, in_kh=0.0):
    """Punta alta se le fiches superano soglia volte il minimo della prossima Killer Hand, bassa altrimenti."""

    def politica(stato):
        if stato["killer"]:
            return stato["fiches"] * in_kh
        sicuro = stato["fiches"] >= soglia * stato["minimo_kh"]
        return stato["fiches"] * np.where(sicuro, alta, bassa)

    return politica


def kelly(esito):
    """La frazione che massimizza la crescita logaritmica, e la crescita per mano."""
    migliore, crescita = 0.0, 0.0
    for i in range(1, 1000):
        quota = i / 1000
        g = float(esito.probabilita @ np.log(np.maximum(1 + quota * (esito.ritorni - 1), 1e-300)))
        if g > crescita:
            migliore, crescita = quota, g
    return migliore, crescita
