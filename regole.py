# PokerMachine, le regole: valutazione della mano, tabella delle vincite,
# Killer Hand, puntata minima, traguardi e soglie.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 09/09/2026: revisione 1 del refactoring generale. Le regole escono dal
# programma principale; la tabella dei punteggi e' scritta una volta sola e
# da lei discendono l'ordine delle statistiche e la struttura del salvataggio.

"""Le regole del video poker a fiches.

Il modulo non stampa e non legge niente: riceve carte e numeri, restituisce
punteggi e importi. E' il pezzo che le prove automatiche esercitano di piu'.
Le carte sono le Carta di Mazzo di GBUtils, con valore da 1, l'asso, a 13,
il re. Per confrontare le mani l'asso vale 14, e per le scale vale anche 1,
cosi' si riconoscono sia la scala bassa dall'asso al cinque sia la reale.
"""

from collections import Counter

NUM_MAZZI = 10
CARTE_PER_MANO = 5
FICHES_INIZIALI = 200
PERCENTUALE_MINIMA_PUNTATA = 3
KILLER_HAND_FREQUENZA = 25
KILLER_HAND_PASSO = 10
KILLER_HAND_PENALITA_MAX = 90
KILLER_HAND_MOLTIPLICATORE = 3
TRAGUARDO_MANI = 100
SOGLIE_FICHES = (1000, 10000, 100000, 1000000)
VALORE_JACK = 11
VALORE_REGINA = 12
VALORE_RE = 13
VALORE_ASSO = 14
MANO_NON_VALIDA = "Mano non valida"

# Nome del punteggio e multiplo della puntata che viene restituito: zero
# significa puntata persa, uno pareggio. Dal piu' alto al piu' basso, che e'
# anche l'ordine in cui le statistiche li elencano.
PUNTEGGI = (
    ("Scala Reale", 250),
    ("Scala a colore", 55),
    ("Super Poker", 40),
    ("Poker", 25),
    ("Full", 9),
    ("Colore", 6),
    ("Scala", 4),
    ("Tris", 3),
    ("Doppia coppia", 2),
    ("Coppia pagata", 1),
    ("Coppia non pagata", 0),
    ("Carta alta", 0),
)
TABELLA_VINCITE = dict(PUNTEGGI)
NOMI_PUNTEGGI = tuple(nome for nome, _ in PUNTEGGI)
PUNTEGGI_PAGATI = tuple(nome for nome, multiplo in PUNTEGGI if multiplo >= 1)


def valore_alto(carta):
    """Il valore per i confronti: l'asso vale 14, il resto vale quanto dice."""
    return VALORE_ASSO if carta.valore == 1 else carta.valore


def _valore_piu_alto_della_scala(valori_distinti):
    """Il valore in cima alla scala di cinque, oppure None se non c'e'.

    Con cinque carte i valori distinti sono al massimo sei, e due scale
    insieme non ci stanno; si tiene comunque l'ultima trovata, cioe' la
    piu' alta, cosi' il conto resta giusto anche se un giorno le carte per
    mano diventassero di piu'.
    """
    ordinati = sorted(valori_distinti)
    cima = None
    for i in range(len(ordinati) - 4):
        if all(ordinati[i + j] == ordinati[i] + j for j in range(5)):
            cima = ordinati[i + 4]
    return cima


def valuta_mano(mano):
    """Il nome del punteggio della mano, uno di NOMI_PUNTEGGI.

    Restituisce MANO_NON_VALIDA se le carte non sono cinque.
    """
    if not mano or len(mano) != CARTE_PER_MANO:
        return MANO_NON_VALIDA
    valori = [valore_alto(c) for c in mano]
    conta_valori = Counter(valori)
    conteggi = sorted(conta_valori.values(), reverse=True)
    is_colore = len({c.seme_nome for c in mano}) == 1
    # La scala si cerca sui valori distinti, cosi' una coppia non puo'
    # spacciarsi per una sequenza, e con l'asso che vale anche uno.
    distinti = set(valori)
    if VALORE_ASSO in distinti:
        distinti.add(1)
    cima_scala = _valore_piu_alto_della_scala(distinti)
    is_scala = cima_scala is not None
    if is_scala and is_colore:
        return "Scala Reale" if cima_scala == VALORE_ASSO else "Scala a colore"
    if conteggi[0] >= 5:
        return "Super Poker"
    if conteggi[0] == 4:
        return "Poker"
    if conteggi[:2] == [3, 2]:
        return "Full"
    if is_colore:
        return "Colore"
    if is_scala:
        return "Scala"
    if conteggi[0] == 3:
        return "Tris"
    if conteggi[:2] == [2, 2]:
        return "Doppia coppia"
    if conteggi[0] == 2:
        valore_coppia = next(v for v, quante in conta_valori.items() if quante == 2)
        return "Coppia pagata" if valore_coppia >= VALORE_JACK else "Coppia non pagata"
    return "Carta alta"


def calcola_vincita(punteggio, puntata):
    """L'importo restituito per quel punteggio, puntata compresa."""
    return puntata * TABELLA_VINCITE.get(punteggio, 0)


def puntata_minima(fiches):
    """La puntata piu' bassa ammessa: una percentuale delle fiches, almeno una."""
    return max(fiches * PERCENTUALE_MINIMA_PUNTATA // 100, 1)


def e_killer_hand(numero_mano_serie):
    """Vero se quella mano della serie senza fallimenti e' una Killer Hand."""
    return numero_mano_serie > 0 and numero_mano_serie % KILLER_HAND_FREQUENZA == 0


def penalita_percentuale(numero_killer_hand):
    """La penalita' per cento della Killer Hand numero N dall'ultimo fallimento."""
    return min(numero_killer_hand * KILLER_HAND_PASSO, KILLER_HAND_PENALITA_MAX)


def soglia_raggiunta(fiches):
    """La soglia di fiches piu' alta che quel saldo ha raggiunto, zero se nessuna."""
    raggiunta = 0
    for soglia in SOGLIE_FICHES:
        if fiches >= soglia:
            raggiunta = soglia
    return raggiunta
