# PokerMachine, le sfide: tre obiettivi per ogni serie, ciascuno vale uno scudo.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 24/09/2026: nasce con la versione 5, tappa 7 del piano (issue 10).

"""Le sfide di PokerMachine.

All'inizio di ogni serie se ne estraggono tre dall'elenco, e restano nel
salvataggio finche' la serie dura. Ogni sfida superata regala uno scudo, che
restituisce la puntata di una Killer Hand persa. Il modulo non stampa e non
assegna scudi: estrai sceglie le sfide, controlla dice quali sono state
appena superate, e la contabilita' di partita fa il resto.

I fatti sono gli stessi dei trofei: un dizionario con cio' che e' appena
accaduto, dove le chiavi che mancano valgono come non accadute.
"""

import random
from collections import namedtuple

import regole

Sfida = namedtuple("Sfida", ["chiave", "testo", "condizione"])

QUANTE = 3
# Le sfide chiedono che la mano contenga la combinazione, anche se paga come
# un'altra: un full con il tris gemello e' sempre un full.
POKER = frozenset(("Cinque gemelle", "Poker gemello", "Super Poker", "Poker d'assi", "Poker dal 2 al 4", "Poker"))
SCALE = frozenset(("Scala Reale", "Scala a colore", "Scala"))
FULL = frozenset(("Full a colore", "Full"))
KILLER_SFIDA = 6

ELENCO = (
    Sfida("full", "Fai un Full.", lambda dati, fatti: bool(FULL & fatti.get("contiene", set()))),
    Sfida("colore", "Fai cinque carte dello stesso seme.", lambda dati, fatti: fatti.get("seme_unico") is not None),
    Sfida("scala", "Fai una Scala.", lambda dati, fatti: bool(SCALE & fatti.get("contiene", set()))),
    Sfida("poker", "Fai un Poker, di qualunque valore.", lambda dati, fatti: bool(POKER & fatti.get("contiene", set()))),
    Sfida("tris_gemello", "Fai tre carte gemelle.", lambda dati, fatti: fatti.get("gemelle", 0) >= 3),
    Sfida("cinque_pagate", "Fai cinque mani pagate di fila.", lambda dati, fatti: dati["serie"]["pagate_di_fila"] >= 5),
    Sfida("vinci_killer", "Vinci una Killer Hand.", lambda dati, fatti: bool(fatti.get("killer")) and bool(fatti.get("vinta"))),
    Sfida(
        "doppio",
        f"Porta le fiches a {2 * regole.FICHES_INIZIALI}.",
        lambda dati, fatti: fatti.get("fiches", 0) >= 2 * regole.FICHES_INIZIALI,
    ),
    Sfida(
        "killer_6",
        f"Supera la Killer Hand numero {KILLER_SFIDA}.",
        lambda dati, fatti: fatti.get("killer") == KILLER_SFIDA and fatti.get("fiches", 0) > 0,
    ),
    Sfida("raddoppio_seme", "Vinci un raddoppio indovinando il seme.", lambda dati, fatti: bool(fatti.get("raddoppio_seme"))),
    Sfida("dieci_ottime", "Fai dieci tenute ottime di fila.", lambda dati, fatti: dati["serie"]["ottime_di_fila"] >= 10),
)
PER_CHIAVE = {s.chiave: s for s in ELENCO}


def possibili(dati):
    """Le sfide che hanno senso con la serie com'e' adesso.

    All'inizio di una serie vanno bene tutte. Con un salvataggio della
    versione 4 le sfide si estraggono a serie gia' avviata: quella delle
    fiches raddoppiate potrebbe essere gia' superata, e quella della Killer
    Hand gia' passata non si potrebbe piu' vincere.
    """
    if dati is None:
        return list(ELENCO)
    escluse = set()
    if dati["fiches_attuali"] >= 2 * regole.FICHES_INIZIALI:
        escluse.add("doppio")
    if dati["killer_hand_count"] >= KILLER_SFIDA:
        escluse.add("killer_6")
    return [s for s in ELENCO if s.chiave not in escluse]


def estrai(generatore=None, dati=None):
    """Tre sfide diverse, come le si salva: una lista di dizionari con chiave e fatta."""
    generatore = generatore or random.Random()
    return [{"chiave": s.chiave, "fatta": False} for s in generatore.sample(possibili(dati), QUANTE)]


def in_corso(dati):
    """Le sfide della serie, come coppie (Sfida, fatta)."""
    return [(PER_CHIAVE[v["chiave"]], v["fatta"]) for v in dati["serie"]["sfide"] if v["chiave"] in PER_CHIAVE]


def controlla(dati, fatti):
    """Le sfide della serie superate adesso, segnate come fatte."""
    superate = []
    for voce in dati["serie"]["sfide"]:
        sfida = PER_CHIAVE.get(voce["chiave"])
        if sfida is None or voce["fatta"]:
            continue
        if sfida.condizione(dati, fatti):
            voce["fatta"] = True
            superate.append(sfida)
    return superate
