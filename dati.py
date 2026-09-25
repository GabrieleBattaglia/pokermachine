# PokerMachine, i dati: il salvataggio su disco e le date.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 09/09/2026: revisione 1 del refactoring generale. Il salvataggio passa da
# pickle a JSON, vive accanto al programma e non nella cartella da cui lo si
# lancia, si scrive su file temporaneo con copia di riserva, e al caricamento
# ogni campo viene controllato. Il vecchio pickle si converte una volta sola.
# 24/09/2026: versione 5, formato 2. Arrivano scudi, sorpresa della Killer
# Hand in arrivo, montepremi, stato della serie con le sfide, precisione delle
# tenute, raddoppi e trofei; un salvataggio della versione 4 li riceve vuoti.

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
VERSIONE_FORMATO = 2
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
    "scudi",
    "montepremi_centesimi",
    "montepremi_vinti",
    "mani_pagate",
)
# I gruppi di contatori della versione 5, ciascuno un dizionario di interi.
GRUPPI = {
    "precisione": ("tenute", "ottime", "di_fila"),
    "raddoppi": ("tentati", "vinti", "di_fila", "fiches_vinte", "fiches_perse"),
}
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


def dati_nuova_serie():
    """Lo stato di una serie appena cominciata."""
    return {"pagate_di_fila": 0, "ottime_di_fila": 0, "fiches_minime": regole.FICHES_INIZIALI, "sfide": []}


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
        "sorpresa_kh": None,
        "soglia_fiches": 0,
        "record_battuto": False,
        "scudi": 0,
        "montepremi_centesimi": 0,
        "montepremi_vinti": 0,
        "mani_pagate": 0,
        "punteggi": {nome: {"conteggio": 0, "ultima_realizzazione": None} for nome in regole.NOMI_PUNTEGGI},
        "vincita_massima": 0,
        "data_vincita_massima": None,
        "perdita_massima": 0,
        "data_perdita_massima": None,
        "data_ultima_giocata": None,
        "serie": dati_nuova_serie(),
        "precisione": {"tenute": 0, "ottime": 0, "di_fila": 0, "valore_perso": 0.0},
        "raddoppi": {"tentati": 0, "vinti": 0, "di_fila": 0, "fiches_vinte": 0, "fiches_perse": 0},
        "trofei": {},
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
    _completa_versione_5(dati, grezzi)
    return dati


def _completa_versione_5(dati, grezzi):
    """I campi nati con la versione 5: scudi, sorpresa, serie, precisione, raddoppi e trofei.

    Un salvataggio della versione 4 non li ha e riceve i predefiniti; la
    serie in corso prende come minimo le fiches di adesso, cosi' una rimonta
    si conta da qui in avanti.
    """
    dati["scudi"] = min(dati["scudi"], regole.SCUDI_MAX)
    if "mani_pagate" not in grezzi:
        # Fino alla versione 4 le mani pagate si contavano dai punteggi, e
        # fino ad allora nessun punteggio pagato poteva pagare zero.
        dati["mani_pagate"] = sum(dati["punteggi"][nome]["conteggio"] for nome in regole.PUNTEGGI_PAGATI)
    sorpresa = grezzi.get("sorpresa_kh")
    dati["sorpresa_kh"] = sorpresa if sorpresa in regole.SORPRESE_PER_CHIAVE else None
    for gruppo, chiavi in GRUPPI.items():
        voce = grezzi.get(gruppo)
        if isinstance(voce, dict):
            for chiave in chiavi:
                dati[gruppo][chiave] = _intero(voce.get(chiave), 0)
    precisione = grezzi.get("precisione")
    if isinstance(precisione, dict):
        perso = precisione.get("valore_perso")
        if isinstance(perso, (int, float)) and not isinstance(perso, bool) and perso >= 0:
            dati["precisione"]["valore_perso"] = float(perso)
    serie = grezzi.get("serie")
    if isinstance(serie, dict):
        dati["serie"]["pagate_di_fila"] = _intero(serie.get("pagate_di_fila"), 0)
        dati["serie"]["ottime_di_fila"] = _intero(serie.get("ottime_di_fila"), 0)
        dati["serie"]["fiches_minime"] = _intero(serie.get("fiches_minime"), dati["fiches_attuali"])
        voci = serie.get("sfide")
        if isinstance(voci, list):
            dati["serie"]["sfide"] = [
                {"chiave": v["chiave"], "fatta": v.get("fatta") is True}
                for v in voci
                if isinstance(v, dict) and isinstance(v.get("chiave"), str)
            ]
    else:
        dati["serie"]["fiches_minime"] = dati["fiches_attuali"]
    voci = grezzi.get("trofei")
    if isinstance(voci, dict):
        dati["trofei"] = {chiave: data for chiave, data in voci.items() if isinstance(chiave, str) and _data(data)}


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


def _carica_copia(percorso_file, avvisi):
    """Il salvataggio principale manca, ma c'e' una sua copia: la piu' recente che si legge.

    Succede se un salvataggio si interrompe fra le due sostituzioni di
    salva_dati, per esempio perche' un antivirus tiene aperto il file
    temporaneo: il file temporaneo ha lo stato piu' recente, la riserva quello
    di prima. Senza questo controllo il gioco ripartirebbe da zero e al
    salvataggio dopo cancellerebbe anche la riserva.
    """
    for suffisso, quale in ((".tmp", "temporanea"), (".bak", "di riserva")):
        copia = percorso_file + suffisso
        if not os.path.exists(copia):
            continue
        try:
            grezzi = _leggi_json(copia)
        except (OSError, ValueError):
            continue
        avvisi.append(f"Il salvataggio principale manca: uso la copia {quale}.")
        return grezzi
    avvisi.append("Il salvataggio principale manca e le copie non si leggono: riparto da un salvataggio nuovo.")
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
    elif os.path.exists(percorso_json + ".tmp") or os.path.exists(percorso_json + ".bak"):
        grezzi = _carica_copia(percorso_json, avvisi)
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
        dati["sorpresa_kh"] = None
        dati["soglia_fiches"] = 0
        dati["record_battuto"] = False
        dati["scudi"] = 0
        dati["serie"] = dati_nuova_serie()
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
