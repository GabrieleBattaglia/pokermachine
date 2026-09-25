# PokerMachine, le regole: valutazione della mano, tabella delle vincite,
# Killer Hand, puntata minima, traguardi e soglie.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 09/09/2026: revisione 1 del refactoring generale. Le regole escono dal
# programma principale; la tabella dei punteggi e' scritta una volta sola e
# da lei discendono l'ordine delle statistiche e la struttura del salvataggio.
# 24/09/2026: versione 5. Arrivano le categorie dei dieci mazzi: le carte
# gemelle, il Poker per valore e il Full a colore. Ogni punteggio diventa una
# condizione sulle cinque carte, e la mano paga il migliore che soddisfa. Le
# stesse condizioni lavorano su una mano sola e su milioni di mani insieme,
# per il motore della strategia: sono scritte una volta sola.

"""Le regole del video poker a fiches.

Il modulo non stampa e non legge niente: riceve carte e numeri, restituisce
punteggi e importi. E' il pezzo che le prove automatiche esercitano di piu'.
Le carte sono le Carta di Mazzo di GBUtils, con valore da 1, l'asso, a 13,
il re. Per valutarle diventano tipi, un numero da 0 a 51 che dice rango e
seme: due carte dello stesso tipo sono gemelle, identiche anche nel seme,
come con dieci mazzi capita spesso. L'asso vale piu' del re, e nelle scale
vale anche uno, cosi' si riconoscono sia la scala bassa dall'asso al cinque
sia la reale.
"""

from collections import namedtuple

import numpy as np

NUM_MAZZI = 10
CARTE_PER_MANO = 5
FICHES_INIZIALI = 200
PERCENTUALE_MINIMA_PUNTATA = 3
TRAGUARDO_MANI = 100
SOGLIE_FICHES = (1000, 10000, 100000, 1000000)
MANO_NON_VALIDA = "Mano non valida"

# La Killer Hand come gara, dalla versione 5 (issue 6). Arriva ogni
# KILLER_HAND_FREQUENZA mani della serie. Alla Killer Hand numero N, contata
# dall'ultimo fallimento, la puntata minima e' KILLER_HAND_BASE per
# KILLER_HAND_FATTORE alla N, in fiches, e chi ne ha meno punta tutto. Non
# c'e' piu' una penalita': la minaccia e' il minimo, che cresce piu' in
# fretta di quanto il gruzzolo possa seguirlo. Se la mano vince, la vincita
# netta si moltiplica per KILLER_HAND_MOLTIPLICATORE, salvo sorprese.
# Tarata il 25/09/2026 con il simulatore della cartella taratura: il minimo
# raddoppia a ogni Killer Hand, 4, 8, 16 fiches e cosi' via. Chi gioca al
# meglio fa crescere il gruzzolo al massimo di 1,67 volte ogni 25 mani, meno
# del doppio: nessuna serie scappa per sempre, ma chi punta bene resiste
# quasi il doppio di chi punta sempre il minimo.
KILLER_HAND_FREQUENZA = 25
KILLER_HAND_BASE = 2
KILLER_HAND_FATTORE = 2
KILLER_HAND_MOLTIPLICATORE = 3

# Gli scudi: ciascuno restituisce la puntata di una Killer Hand persa, e se
# ne tengono al massimo SCUDI_MAX. Li regalano le mani rarissime e le sfide.
SCUDI_MAX = 3
PUNTEGGI_SCUDO = ("Cinque gemelle", "Scala Reale", "Full a colore", "Scala a colore", "Poker gemello", "Super Poker")

# Il montepremi: MONTEPREMI_PERCENTUALE di ogni puntata vi si accumula, lo
# paga la macchina e non viene tolto dalla puntata. Lo vince chi fa uno dei
# PUNTEGGI_MONTEPREMI, e sopravvive al game over.
MONTEPREMI_PERCENTUALE = 1
PUNTEGGI_MONTEPREMI = ("Cinque gemelle", "Scala Reale", "Full a colore", "Scala a colore", "Poker gemello", "Super Poker")

COPPIE = ("Coppia pagata", "Coppia gemella pagata", "Coppia gemella")

# Le regole a sorpresa della Killer Hand: una si estrae quando la Killer
# Hand viene annunciata, prima della puntata. mute sono i punteggi che quella
# volta non pagano; moltiplicatore e' quello della vincita netta;
# pareggio_perde fa perdere la puntata a chi pareggia; cambio dice se si
# possono cambiare le carte.
Sorpresa = namedtuple("Sorpresa", ["chiave", "nome", "spiegazione", "mute", "moltiplicatore", "pareggio_perde", "cambio"])
SORPRESE = (
    Sorpresa("nessuna", "Nessuna sorpresa", "Si gioca come sempre.", (), KILLER_HAND_MOLTIPLICATORE, False, True),
    Sorpresa(
        "nessun_cambio",
        "Nessun cambio",
        "Non si cambiano carte: la mano servita è quella finale.",
        (),
        KILLER_HAND_MOLTIPLICATORE,
        False,
        False,
    ),
    Sorpresa(
        "coppie_mute", "Coppie mute", "Le coppie non pagano, nemmeno quelle gemelle.", COPPIE, KILLER_HAND_MOLTIPLICATORE, False, True
    ),
    Sorpresa(
        "tutto_o_niente",
        "Tutto o niente",
        "La vincita netta si moltiplica per cinque, ma il pareggio fa perdere la puntata.",
        (),
        5,
        True,
        True,
    ),
)
SORPRESE_PER_CHIAVE = {s.chiave: s for s in SORPRESE}

# Il tipo di una carta e' il rango per quattro piu' il seme. Il rango va da
# 0, il due, a 12, l'asso; il seme da 0 a 3, cioe' seme_id di Mazzo meno uno.
NUM_TIPI = 52
NUM_SEMI = 4
RANGO_CINQUE = 3
RANGO_DIECI = 8
RANGO_JACK = 9
RANGO_RE = 11
RANGO_ASSO = 12

# Nome del punteggio e multiplo della puntata che viene restituito: zero
# significa puntata persa, uno pareggio. Dal piu' alto al piu' basso, che e'
# anche l'ordine in cui le statistiche li elencano. Quando una mano soddisfa
# piu' punteggi paga il piu' alto, e a parita' di multiplo quello scritto
# prima: una doppia coppia con due jack gemelli si chiama doppia coppia, e un
# poker con tre carte gemelle si chiama poker.
# Tarata il 25/09/2026 con la strategia ottima: rende il 128,6 per cento, e il
# montepremi aggiunge circa un punto. Con dieci mazzi tris, doppia coppia,
# full e poker escono molto piu' spesso che con un mazzo solo, e pagano meno
# che nella 4.0.1; la scala invece e' piu' rara di full e colore, e paga di
# piu'. I conti e le proposte scartate stanno nelle issue 5 e 6.
PUNTEGGI = (
    ("Cinque gemelle", 2500),
    ("Scala Reale", 250),
    ("Full a colore", 55),
    ("Scala a colore", 55),
    ("Poker gemello", 50),
    ("Super Poker", 40),
    ("Poker d'assi", 25),
    ("Poker dal 2 al 4", 10),
    ("Poker", 6),
    ("Scala", 6),
    ("Tris gemello", 6),
    ("Full", 4),
    ("Colore", 4),
    ("Tris", 2),
    ("Doppia coppia", 2),
    ("Coppia gemella pagata", 2),
    ("Coppia pagata", 1),
    ("Coppia gemella", 1),
    ("Coppia non pagata", 0),
    ("Carta alta", 0),
)
TABELLA_VINCITE = dict(PUNTEGGI)
NOMI_PUNTEGGI = tuple(nome for nome, _ in PUNTEGGI)
POSIZIONE = {nome: i for i, nome in enumerate(NOMI_PUNTEGGI)}
PUNTEGGI_PAGATI = tuple(nome for nome, multiplo in PUNTEGGI if multiplo >= 1)


def rango_carta(carta):
    """Il rango della carta, da 0, il due, a 12, l'asso."""
    return RANGO_ASSO if carta.valore == 1 else carta.valore - 2


def tipo_carta(carta):
    """Il tipo della carta, da 0 a 51: rango per quattro piu' seme."""
    return rango_carta(carta) * NUM_SEMI + carta.seme_id - 1


def bandiere(tipi):
    """Per ogni punteggio, quali mani lo soddisfano.

    tipi e' una matrice di interi, una mano per riga, cinque tipi per mano
    in ordine crescente: con i tipi ordinati anche i ranghi lo sono, e le
    carte uguali stanno vicine. Restituisce un dizionario da nome del
    punteggio a vettore di vero o falso, una voce per mano.

    Ogni condizione dice se la mano contiene quella combinazione: un tris
    contiene una coppia, e un full con il tris gemello contiene un tris
    gemello. Quale punteggio paghi lo decide migliore_punteggio.
    """
    t = np.asarray(tipi, dtype=np.int16)
    rango = t >> 2
    seme = t & 3
    mani = t.shape[0]
    colore = (seme == seme[:, :1]).all(axis=1)
    # Per ogni carta, quante carte della mano hanno il suo rango e quante
    # sono sue gemelle, lei compresa.
    stesso_rango = np.zeros((mani, CARTE_PER_MANO), dtype=np.int8)
    gemelle = np.zeros((mani, CARTE_PER_MANO), dtype=np.int8)
    for i in range(CARTE_PER_MANO):
        stesso_rango += rango == rango[:, i : i + 1]
        gemelle += t == t[:, i : i + 1]
    distinti = 1 + (rango[:, 1:] != rango[:, :-1]).sum(axis=1)
    gruppo = stesso_rango.max(axis=1)
    gemelle_max = gemelle.max(axis=1)
    scala = (distinti == CARTE_PER_MANO) & (
        (rango[:, -1] - rango[:, 0] == CARTE_PER_MANO - 1) | ((rango[:, -2] == RANGO_CINQUE) & (rango[:, -1] == RANGO_ASSO))
    )
    reale = scala & (rango[:, 0] == RANGO_DIECI)
    full = (gruppo == 3) & (distinti == 2)
    # Il rango delle quattro carte uguali, -1 se non ci sono.
    rango_poker = np.where(stesso_rango >= 4, rango, -1).max(axis=1)
    return {
        "Cinque gemelle": gemelle_max == 5,
        "Scala Reale": reale & colore,
        "Full a colore": full & colore,
        "Scala a colore": scala & colore & ~reale,
        "Poker gemello": gemelle_max >= 4,
        "Super Poker": gruppo == 5,
        "Poker d'assi": rango_poker == RANGO_ASSO,
        "Poker dal 2 al 4": (rango_poker >= 0) & (rango_poker < RANGO_CINQUE),
        "Poker": (rango_poker >= RANGO_CINQUE) & (rango_poker <= RANGO_RE),
        "Tris gemello": gemelle_max >= 3,
        "Full": full,
        "Colore": colore,
        "Scala": scala,
        "Tris": gruppo >= 3,
        "Doppia coppia": ((gruppo == 2) & (distinti == 3)) | full,
        "Coppia gemella pagata": ((gemelle >= 2) & (rango >= RANGO_JACK)).any(axis=1),
        "Coppia pagata": ((stesso_rango >= 2) & (rango >= RANGO_JACK)).any(axis=1),
        "Coppia gemella": gemelle_max >= 2,
        "Coppia non pagata": gruppo >= 2,
        "Carta alta": np.ones(mani, dtype=bool),
    }


def migliore_punteggio(soddisfatti, tabella=None):
    """Fra i punteggi soddisfatti, quello che paga di piu'; a parita', il primo della tabella."""
    tabella = TABELLA_VINCITE if tabella is None else tabella
    return max(soddisfatti, key=lambda nome: (tabella[nome], -POSIZIONE[nome]))


def contenute(mano):
    """I nomi di tutti i punteggi che le cinque carte contengono, pagati o no."""
    riga = np.array([sorted(tipo_carta(c) for c in mano)])
    condizioni = bandiere(riga)
    return {nome for nome in NOMI_PUNTEGGI if condizioni[nome][0]}


def valuta_mano(mano, tabella=None):
    """Il nome del punteggio della mano, uno di NOMI_PUNTEGGI.

    tabella e' quella dei multipli in vigore, da nome a multiplo: serve alle
    regole a sorpresa della Killer Hand, che cambiano cio' che paga. Senza,
    vale TABELLA_VINCITE. Restituisce MANO_NON_VALIDA se le carte non sono
    cinque.
    """
    if not mano or len(mano) != CARTE_PER_MANO:
        return MANO_NON_VALIDA
    return migliore_punteggio(contenute(mano), tabella)


def calcola_vincita(punteggio, puntata, tabella=None):
    """L'importo restituito per quel punteggio, puntata compresa."""
    tabella = TABELLA_VINCITE if tabella is None else tabella
    return puntata * tabella.get(punteggio, 0)


def puntata_minima(fiches):
    """La puntata piu' bassa ammessa: una percentuale delle fiches, almeno una."""
    return max(fiches * PERCENTUALE_MINIMA_PUNTATA // 100, 1)


def e_killer_hand(numero_mano_serie):
    """Vero se quella mano della serie senza fallimenti e' una Killer Hand."""
    return numero_mano_serie > 0 and numero_mano_serie % KILLER_HAND_FREQUENZA == 0


def minimo_killer_hand(numero_killer_hand):
    """La puntata minima, in fiches, della Killer Hand numero N dall'ultimo fallimento."""
    return int(KILLER_HAND_BASE * KILLER_HAND_FATTORE**numero_killer_hand)


def puntata_minima_killer_hand(fiches, numero_killer_hand):
    """La puntata piu' bassa ammessa in una Killer Hand: il minimo della gara, o tutto se non basta."""
    return min(max(puntata_minima(fiches), minimo_killer_hand(numero_killer_hand)), fiches)


def tabella_sorpresa(sorpresa):
    """La tabella dei multipli in vigore con una regola a sorpresa: i punteggi muti e il pareggio che perde."""
    tabella = dict(TABELLA_VINCITE)
    for nome in sorpresa.mute:
        tabella[nome] = 0
    if sorpresa.pareggio_perde:
        tabella = {nome: (0 if multiplo == 1 else multiplo) for nome, multiplo in tabella.items()}
    return tabella


def guadagno_killer_hand(multiplo, moltiplicatore):
    """Quante puntate tornano in una Killer Hand per un punteggio: la vincita netta si moltiplica."""
    return 1 + moltiplicatore * (multiplo - 1) if multiplo > 1 else multiplo


def tabella_decisione(sorpresa=None, scudo=False):
    """I guadagni su cui scegliere la tenuta migliore, in puntate, da nome del punteggio.

    Nella mano normale sono i multipli della tabella. In una Killer Hand
    contano la vincita netta moltiplicata e la sorpresa, e con uno scudo in
    tasca la mano persa restituisce la puntata, quindi vale uno invece di
    zero.
    """
    if sorpresa is None:
        return dict(TABELLA_VINCITE)
    tabella = tabella_sorpresa(sorpresa)
    guadagni = {nome: guadagno_killer_hand(multiplo, sorpresa.moltiplicatore) for nome, multiplo in tabella.items()}
    if scudo:
        guadagni = {nome: max(valore, 1) for nome, valore in guadagni.items()}
    return guadagni


def soglia_raggiunta(fiches):
    """La soglia di fiches piu' alta che quel saldo ha raggiunto, zero se nessuna."""
    raggiunta = 0
    for soglia in SOGLIE_FICHES:
        if fiches >= soglia:
            raggiunta = soglia
    return raggiunta
