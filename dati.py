# PokerMachine, i dati: il salvataggio su disco e le date.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 09/09/2026: revisione 1 del refactoring generale. Il salvataggio passa da
# pickle a JSON, vive accanto al programma e non nella cartella da cui lo si
# lancia, si scrive su file temporaneo con copia di riserva, e al caricamento
# ogni campo viene controllato. Il vecchio pickle si converte una volta sola.

"""Il salvataggio di PokerMachine.

Un solo file JSON accanto al programma, pokermachine_data.json, con il
gruzzolo, le statistiche di sempre e i conteggi dei punteggi. Il modulo non
stampa: carica_dati restituisce gli avvisi come testo, salva_dati solleva
OSError, e chi chiama decide come dirlo.
"""

import json
import os
import pickle
from datetime import datetime

from dateutil.relativedelta import relativedelta
from GBUtils import cartella_applicazione
from GBUtils import percorso_risorsa as percorso_risorsa_condivisa

import regole

NOME_SALVATAGGIO = "pokermachine_data.json"
NOME_SALVATAGGIO_VECCHIO = "pokermachine_data.pkl"
FORMATO_DATA = "%Y-%m-%d %H:%M:%S"
VERSIONE_FORMATO = 1
CHIAVI_INTERE = (
    "launches",
    "mani_giocate",
    "record_mani_senza_fallimenti",
    "mani_dall_ultimo_fallimento",
    "fiches_guadagnate",
    "fiches_perdute",
    "fiches_attuali",
    "fallimenti",
    "killer_hand_count",
    "vincita_massima",
    "perdita_massima",
    "soglia_fiches",
)
CHIAVI_DATE = (
    "data_ultimo_fallimento",
    "data_vincita_massima",
    "data_perdita_massima",
    "data_ultima_giocata",
)


def adesso():
    """L'istante presente nel formato del salvataggio."""
    return datetime.now().strftime(FORMATO_DATA)


def cartella_programma():
    """La cartella dell'eseguibile compilato, oppure quella del sorgente.
    La logica sta in GBUtils, come tutte le utilita' condivise: qui resta il
    nome con cui il programma la chiama."""
    return cartella_applicazione()


def percorso(nome=NOME_SALVATAGGIO, cartella=None):
    return os.path.join(cartella or cartella_programma(), nome)


def percorso_risorsa(nome):
    """Un file che viaggia dentro l'eseguibile, come la guida.

    PyInstaller in file unico scompatta le risorse in una cartella
    temporanea, sys._MEIPASS, e non accanto all'eseguibile: da sorgente la
    cartella e' quella del programma. La ricerca sta in GBUtils.
    """
    return percorso_risorsa_condivisa(nome)


def nuovi_dati():
    """La struttura di un giocatore appena arrivato."""
    return {
        "versione_formato": VERSIONE_FORMATO,
        "launches": 0,
        "mani_giocate": 0,
        "data_ultimo_fallimento": None,
        "record_mani_senza_fallimenti": 0,
        "mani_dall_ultimo_fallimento": 0,
        "fiches_guadagnate": 0,
        "fiches_perdute": 0,
        "fiches_attuali": regole.FICHES_INIZIALI,
        "fallimenti": 0,
        "killer_hand_count": 0,
        "soglia_fiches": 0,
        "record_battuto": False,
        "punteggi": {nome: {"conteggio": 0, "ultima_realizzazione": None} for nome in regole.NOMI_PUNTEGGI},
        "vincita_massima": 0,
        "data_vincita_massima": None,
        "perdita_massima": 0,
        "data_perdita_massima": None,
        "data_ultima_giocata": None,
    }


def _intero(valore, predefinito):
    if isinstance(valore, bool) or not isinstance(valore, int) or valore < 0:
        return predefinito
    return valore


def _data(valore):
    if not isinstance(valore, str):
        return None
    try:
        datetime.strptime(valore, FORMATO_DATA)
    except ValueError:
        return None
    return valore


def completa(grezzi):
    """Un salvataggio risanato: cio' che manca o ha il tipo sbagliato torna al predefinito.

    Restituisce un dizionario nuovo e non tocca quello ricevuto.
    """
    dati = nuovi_dati()
    if not isinstance(grezzi, dict):
        return dati
    for chiave in CHIAVI_INTERE:
        dati[chiave] = _intero(grezzi.get(chiave), dati[chiave])
    for chiave in CHIAVI_DATE:
        dati[chiave] = _data(grezzi.get(chiave))
    punteggi = grezzi.get("punteggi")
    if isinstance(punteggi, dict):
        for nome in regole.NOMI_PUNTEGGI:
            voce = punteggi.get(nome)
            if isinstance(voce, dict):
                dati["punteggi"][nome] = {
                    "conteggio": _intero(voce.get("conteggio"), 0),
                    "ultima_realizzazione": _data(voce.get("ultima_realizzazione")),
                }
    if "soglia_fiches" not in grezzi:
        # Salvataggio di prima delle soglie: si parte da quella gia' raggiunta,
        # cosi' non viene annunciata come nuova.
        dati["soglia_fiches"] = regole.soglia_raggiunta(dati["fiches_attuali"])
    battuto = grezzi.get("record_battuto")
    if isinstance(battuto, bool):
        dati["record_battuto"] = battuto
    else:
        # Salvataggio di prima dell'annuncio del primato: se la serie in corso
        # e' gia' il primato, lo ha gia' battuto e non va annunciato di nuovo.
        serie, record = dati["mani_dall_ultimo_fallimento"], dati["record_mani_senza_fallimenti"]
        dati["record_battuto"] = serie > 0 and serie >= record
    return dati


def _leggi_json(percorso_file):
    with open(percorso_file, encoding="utf-8") as f:
        return json.load(f)


def _leggi_pickle(percorso_file):
    # Il pickle e' il formato della versione 3, scritto da questo stesso
    # programma: si legge una volta sola per convertirlo, poi il file viene
    # rinominato e non si tocca piu'.
    with open(percorso_file, "rb") as f:
        return pickle.load(f)  # noqa: S301


def _metti_da_parte(percorso_file, suffisso):
    """Rinomina un file che non va piu' letto. Vero se ci e' riuscito."""
    try:
        os.replace(percorso_file, percorso_file + suffisso)
    except OSError:
        return False
    return True


def _carica_json(percorso_file, avvisi):
    """Il contenuto del salvataggio, o della sua copia di riserva, oppure None."""
    try:
        return _leggi_json(percorso_file)
    except (OSError, ValueError) as e:
        avvisi.append(f"Il salvataggio non si legge: {e}.")
    riserva = percorso_file + ".bak"
    if os.path.exists(riserva):
        try:
            grezzi = _leggi_json(riserva)
        except (OSError, ValueError):
            pass
        else:
            avvisi.append("Uso la copia di riserva.")
            return grezzi
    if _metti_da_parte(percorso_file, ".illeggibile"):
        avvisi.append(f"Il file illeggibile è stato rinominato in {NOME_SALVATAGGIO}.illeggibile.")
    avvisi.append("Riparto da un salvataggio nuovo.")
    return None


def _carica_pickle(percorso_file, avvisi):
    """Il salvataggio della versione 3, convertito e messo da parte, oppure None."""
    try:
        grezzi = _leggi_pickle(percorso_file)
    except (OSError, EOFError, pickle.UnpicklingError, AttributeError, ImportError, IndexError, TypeError) as e:
        avvisi.append(f"Il vecchio salvataggio non si legge: {e}. Riparto da un salvataggio nuovo.")
        return None
    _metti_da_parte(percorso_file, ".migrato")
    avvisi.append("Salvataggio della versione 3 convertito nel formato nuovo.")
    return grezzi


def carica_dati(cartella=None):
    """Restituisce il salvataggio e la lista degli avvisi da mostrare.

    Il file JSON ha la precedenza; se manca si converte il pickle della
    versione 3; se manca anche quello si parte da zero. Il conteggio dei
    lanci cresce di uno. Un saldo a zero, che puo' arrivare solo da un
    salvataggio della versione 3 chiuso con il game over, viene riportato
    alle fiches iniziali senza contare un secondo fallimento: quello lo
    aveva gia' contato la versione 3.
    """
    avvisi = []
    percorso_json = percorso(NOME_SALVATAGGIO, cartella)
    percorso_pickle = percorso(NOME_SALVATAGGIO_VECCHIO, cartella)
    convertito = False
    if os.path.exists(percorso_json):
        grezzi = _carica_json(percorso_json, avvisi)
    elif os.path.exists(percorso_pickle):
        grezzi = _carica_pickle(percorso_pickle, avvisi)
        convertito = grezzi is not None
    else:
        grezzi = None
        avvisi.append(f"Primo avvio: si parte con {regole.FICHES_INIZIALI} fiches.")
    dati = completa(grezzi)
    dati["launches"] += 1
    if dati["fiches_attuali"] <= 0:
        dati["fiches_attuali"] = regole.FICHES_INIZIALI
        dati["mani_dall_ultimo_fallimento"] = 0
        dati["killer_hand_count"] = 0
        dati["soglia_fiches"] = 0
        dati["record_battuto"] = False
        avvisi.append(f"Le fiches erano esaurite: ricevi {regole.FICHES_INIZIALI} fiches per ricominciare.")
    if convertito:
        try:
            salva_dati(dati, cartella)
        except OSError as e:
            avvisi.append(f"Il salvataggio convertito non si scrive: {e}.")
    return dati, avvisi


def salva_dati(dati, cartella=None):
    """Scrive su file temporaneo e sostituisce, tenendo la copia di riserva.

    Solleva OSError se il disco non collabora: chi chiama lo dice.
    """
    percorso_file = percorso(NOME_SALVATAGGIO, cartella)
    temporaneo = percorso_file + ".tmp"
    with open(temporaneo, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4, ensure_ascii=False)
    if os.path.exists(percorso_file):
        os.replace(percorso_file, percorso_file + ".bak")
    os.replace(temporaneo, percorso_file)


def _conta(n, singolare, plurale):
    return f"{n} {singolare if n == 1 else plurale}"


def formatta_tempo_trascorso(data_str):
    """Quanto tempo e' passato da quella data, a parole."""
    if not data_str:
        return "mai"
    try:
        data_evento = datetime.strptime(data_str, FORMATO_DATA)
    except (ValueError, TypeError):
        return "data non valida"
    ora = datetime.now()
    if data_evento > ora:
        return "in una data futura"
    diff = relativedelta(ora, data_evento)
    parti = []
    if diff.years:
        parti.append(_conta(diff.years, "anno", "anni"))
    if diff.months:
        parti.append(_conta(diff.months, "mese", "mesi"))
    if diff.days:
        parti.append(_conta(diff.days, "giorno", "giorni"))
    if parti:
        return ", ".join(parti) + " fa"
    secondi = (ora - data_evento).total_seconds()
    if secondi < 60:
        return "pochi istanti fa"
    if secondi < 3600:
        return _conta(int(secondi // 60), "minuto", "minuti") + " fa"
    return _conta(int(secondi // 3600), "ora", "ore") + " fa"
