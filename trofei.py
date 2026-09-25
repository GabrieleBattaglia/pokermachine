# PokerMachine, i trofei: traguardi da conquistare una volta sola, per sempre.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 24/09/2026: nasce con la versione 5, tappa 7 del piano (issue 10).

"""I trofei di PokerMachine.

Ogni trofeo si conquista una volta sola e resta nel salvataggio con la data,
anche dopo il game over. controlla riceve i dati del giocatore e i fatti
appena accaduti, e restituisce un evento per ogni trofeo nuovo, con il nome
del suono della sua famiglia e la frase da dire. Il modulo non stampa e non
suona: come partita, restituisce eventi.

I fatti sono un dizionario che chi chiama riempie con cio' che sa. Le chiavi
che mancano valgono come non accadute: la contabilita' della mano, la
registrazione della tenuta e il raddoppio chiamano controlla ciascuno con i
fatti propri.
"""

from collections import namedtuple

import regole
from dati import adesso
from numeri import formatta_fiches

Evento = namedtuple("Evento", ["nome", "testo"])
Trofeo = namedtuple("Trofeo", ["chiave", "nome", "famiglia", "condizione"])

SEMI = ("Cuori", "Quadri", "Fiori", "Picche")
SOGLIE = (1_000, 10_000, 100_000, 1_000_000)
RIMONTA_SOTTO = 50
RIMONTA_SOPRA = 1_000
PAGATE_DI_FILA = 10
OTTIME_DI_FILA = 100
RADDOPPI_DI_FILA = 5
# Cinque gemelle esce una volta ogni milione di mani circa: il trofeo di
# tutti i punteggi non la chiede, perche' sarebbe irraggiungibile.
PUNTEGGI_PER_TUTTI = tuple(nome for nome in regole.NOMI_PUNTEGGI if nome != "Cinque gemelle")


def _colore(seme):
    return lambda dati, fatti: fatti.get("seme_unico") == seme


def _punteggio(nome):
    return lambda dati, fatti: fatti.get("punteggio") == nome


def _killer(numero):
    return lambda dati, fatti: fatti.get("killer") == numero and fatti.get("fiches", 0) > 0


def _soglia(soglia):
    return lambda dati, fatti: fatti.get("fiches", 0) >= soglia


def _serie(mani):
    return lambda dati, fatti: fatti.get("serie", 0) >= mani


def _tutti_i_punteggi(dati, fatti):
    return all(dati["punteggi"][nome]["conteggio"] > 0 for nome in PUNTEGGI_PER_TUTTI)


TROFEI = (
    *(Trofeo(f"colore_{seme.lower()}", f"Colore di {seme.lower()}", "trofeo_mano", _colore(seme)) for seme in SEMI),
    Trofeo("tris_gemello", "Tris gemello", "trofeo_mano", _punteggio("Tris gemello")),
    Trofeo("poker_assi", "Poker d'assi", "trofeo_mano", _punteggio("Poker d'assi")),
    Trofeo("tutti_i_punteggi", "Tutti i punteggi, tranne le cinque gemelle", "trofeo_mano", _tutti_i_punteggi),
    Trofeo("killer_5", "Sopravvissuto alla Killer Hand numero 5", "trofeo_killer", _killer(5)),
    Trofeo("killer_9", "Sopravvissuto alla Killer Hand numero 9", "trofeo_killer", _killer(9)),
    Trofeo("tre_scudi", "Tre scudi insieme", "trofeo_killer", lambda dati, fatti: dati["scudi"] >= regole.SCUDI_MAX),
    *(Trofeo(f"fiches_{s}", f"{formatta_fiches(s)} fiches", "trofeo_fiches", _soglia(s)) for s in SOGLIE),
    Trofeo(
        "rimonta",
        f"Rimonta, da meno di {RIMONTA_SOTTO} a più di {formatta_fiches(RIMONTA_SOPRA)} fiches nella stessa serie",
        "trofeo_fiches",
        lambda dati, fatti: dati["serie"]["fiches_minime"] < RIMONTA_SOTTO and fatti.get("fiches", 0) > RIMONTA_SOPRA,
    ),
    Trofeo(
        "tutto_vinto", "Vinto puntando tutto", "trofeo_fiches", lambda dati, fatti: bool(fatti.get("tutto")) and bool(fatti.get("vinta"))
    ),
    Trofeo("montepremi", "Montepremi vinto", "trofeo_fiches", lambda dati, fatti: fatti.get("montepremi", 0) > 0),
    Trofeo("serie_500", "500 mani in una serie", "trofeo_serie", _serie(500)),
    Trofeo("serie_1000", "1000 mani in una serie", "trofeo_serie", _serie(1000)),
    Trofeo(
        "dieci_pagate",
        f"{PAGATE_DI_FILA} mani pagate di fila",
        "trofeo_serie",
        lambda dati, fatti: dati["serie"]["pagate_di_fila"] >= PAGATE_DI_FILA,
    ),
    Trofeo(
        "cento_ottime",
        f"{OTTIME_DI_FILA} tenute ottime di fila",
        "trofeo_abilita",
        lambda dati, fatti: dati["precisione"]["di_fila"] >= OTTIME_DI_FILA,
    ),
    Trofeo(
        "cinque_raddoppi",
        f"{RADDOPPI_DI_FILA} raddoppi riusciti di fila",
        "trofeo_abilita",
        lambda dati, fatti: dati["raddoppi"]["di_fila"] >= RADDOPPI_DI_FILA,
    ),
)
CHIAVI = tuple(t.chiave for t in TROFEI)
FAMIGLIE = tuple(dict.fromkeys(t.famiglia for t in TROFEI))


def controlla(dati, fatti):
    """I trofei conquistati adesso, segnati nei dati con la data, come eventi da dire."""
    eventi = []
    for trofeo in TROFEI:
        if trofeo.chiave in dati["trofei"]:
            continue
        if trofeo.condizione(dati, fatti):
            dati["trofei"][trofeo.chiave] = adesso()
            eventi.append(Evento(trofeo.famiglia, f"Trofeo conquistato: {trofeo.nome}."))
    return eventi


def conquistati(dati):
    """I trofei gia' conquistati, nell'ordine dell'elenco, con la loro data."""
    return [(t, dati["trofei"][t.chiave]) for t in TROFEI if t.chiave in dati["trofei"]]


def da_conquistare(dati):
    return [t for t in TROFEI if t.chiave not in dati["trofei"]]
