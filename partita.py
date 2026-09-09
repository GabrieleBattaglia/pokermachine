# PokerMachine, la partita: la contabilita' di una mano sui dati del giocatore.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 09/09/2026: revisione 1 del refactoring generale. Nasce per separare i
# conti dall'interfaccia: il bonus della Killer Hand entra nel saldo, la
# penalita' si calcola sulle fiches con cui si e' entrati nella mano, il
# fallimento si conta una volta sola, il primato conta anche l'ultima mano
# e viene annunciato quando si supera, e con lui i traguardi e le soglie.

"""La contabilita' di una mano di PokerMachine.

esito_mano riceve i dati del giocatore, la puntata e il punteggio, aggiorna
saldo e statistiche e restituisce la lista degli eventi accaduti, ciascuno
con un nome, che e' anche il nome del suono, e una frase da mostrare. Non
stampa e non suona: e' cio' che rende le prove automatiche possibili.
"""

from collections import namedtuple

import regole
from dati import adesso
from numeri import formatta_bilancio, formatta_fiches

Evento = namedtuple("Evento", ["nome", "testo"])


def prossima_mano(dati):
    """Il numero, nella serie senza fallimenti, della mano che sta per cominciare."""
    return dati["mani_dall_ultimo_fallimento"] + 1


def killer_hand_in_arrivo(dati):
    """(numero della Killer Hand, penalita' per cento) se la prossima mano lo e', altrimenti (0, 0).

    Il numero cresce solo quando la mano viene giocata davvero: chi esce sul
    prompt di una Killer Hand e rientra la ritrova con la stessa penalita'.
    """
    if not regole.e_killer_hand(prossima_mano(dati)):
        return 0, 0
    numero = dati["killer_hand_count"] + 1
    return numero, regole.penalita_percentuale(numero)


def _registra_punteggio(dati, punteggio):
    voce = dati["punteggi"].get(punteggio)
    if voce is not None:
        voce["conteggio"] += 1
        voce["ultima_realizzazione"] = adesso()


def _vincita(dati, puntata, restituito, killer, eventi):
    """Il saldo cresce di quanto viene restituito piu' l'eventuale bonus."""
    netta = restituito - puntata
    eventi.append(Evento(None, f"Vinci {formatta_fiches(netta)} fiches, restituite {formatta_fiches(restituito)}."))
    bonus = 0
    if killer:
        bonus = netta * (regole.KILLER_HAND_MOLTIPLICATORE - 1)
        eventi.append(Evento("kh_bonus", f"Bonus Killer Hand: vincita triplicata, {formatta_fiches(bonus)} fiches in più."))
    vinte = netta + bonus
    dati["fiches_guadagnate"] += vinte
    if vinte > dati["vincita_massima"]:
        dati["vincita_massima"] = vinte
        dati["data_vincita_massima"] = adesso()
        eventi.append(Evento("record_vincita", f"Nuovo record di vincita in una mano: {formatta_fiches(vinte)} fiches."))
    return restituito + bonus


def _perdita(dati, puntata, fiches_prima, fiches_dopo_puntata, killer, eventi):
    """La perdita e' la puntata piu', in una Killer Hand, la penalita'. Restituisce quanto va tolto oltre la puntata."""
    eventi.append(Evento(None, f"Perdi la puntata di {formatta_fiches(puntata)} fiches."))
    penalita = 0
    if killer:
        per_cento = regole.penalita_percentuale(dati["killer_hand_count"])
        penalita = min(fiches_prima * per_cento // 100, fiches_dopo_puntata)
        eventi.append(
            Evento(
                "kh_penalita",
                f"Penalità Killer Hand: il {per_cento} per cento delle {formatta_fiches(fiches_prima)} fiches con cui sei entrato, {formatta_fiches(penalita)} fiches.",
            )
        )
    perdita = puntata + penalita
    dati["fiches_perdute"] += perdita
    if perdita > dati["perdita_massima"]:
        dati["perdita_massima"] = perdita
        dati["data_perdita_massima"] = adesso()
        eventi.append(Evento("record_perdita", f"Nuovo record di perdita in una mano: {formatta_fiches(perdita)} fiches."))
    return penalita


def esito_mano(dati, puntata, punteggio, killer=False):
    """Contabilizza una mano conclusa e restituisce gli eventi, nell'ordine in cui vanno detti.

    dati['fiches_attuali'] e' il saldo con cui il giocatore e' entrato nella
    mano, puntata compresa. Il primo evento porta il nome del punteggio,
    che e' anche il nome del suo suono; gli altri, quando ci sono, sono il
    bonus o la penalita' della Killer Hand, i record, il traguardo di mani,
    la soglia di fiches e il game over.
    """
    fiches_prima = dati["fiches_attuali"]
    fiches = fiches_prima - puntata
    eventi = []
    if killer:
        dati["killer_hand_count"] += 1
    restituito = regole.calcola_vincita(punteggio, puntata)
    if restituito > puntata:
        fiches += _vincita(dati, puntata, restituito, killer, eventi)
    elif restituito == puntata:
        fiches += restituito
        eventi.append(Evento(None, f"Pareggio: la puntata di {formatta_fiches(puntata)} torna indietro."))
    else:
        fiches -= _perdita(dati, puntata, fiches_prima, fiches, killer, eventi)
    eventi[0] = Evento(punteggio, eventi[0].testo)
    dati["fiches_attuali"] = fiches
    dati["mani_giocate"] += 1
    dati["mani_dall_ultimo_fallimento"] += 1
    dati["data_ultima_giocata"] = adesso()
    _registra_punteggio(dati, punteggio)
    serie = dati["mani_dall_ultimo_fallimento"]
    record = dati["record_mani_senza_fallimenti"]
    if serie > record:
        dati["record_mani_senza_fallimenti"] = serie
        # Si annuncia una volta per serie, nel momento in cui il primato
        # viene superato: da li' in poi ogni mano lo alza e non fa notizia.
        if not dati["record_battuto"]:
            dati["record_battuto"] = True
            if record > 0:
                eventi.append(Evento("record_mani", f"Nuovo primato: {serie} mani senza fallimenti."))
    if serie % regole.TRAGUARDO_MANI == 0:
        eventi.append(Evento("traguardo_mani", f"Traguardo: {serie} mani senza fallimenti."))
    soglia = regole.soglia_raggiunta(fiches)
    if soglia > dati["soglia_fiches"]:
        dati["soglia_fiches"] = soglia
        eventi.append(Evento("soglia_fiches", f"Superata la soglia di {formatta_fiches(soglia)} fiches."))
    if fiches <= 0:
        eventi.append(game_over(dati))
    return eventi


def game_over(dati):
    """Chiude la serie: conta il fallimento e prepara il saldo per la prossima partita.

    Riassegnare qui le fiches iniziali e' cio' che impedisce al caricamento
    successivo di scambiare il saldo a zero per un secondo fallimento.
    """
    serie = dati["mani_dall_ultimo_fallimento"]
    dati["fallimenti"] += 1
    dati["data_ultimo_fallimento"] = adesso()
    dati["mani_dall_ultimo_fallimento"] = 0
    dati["killer_hand_count"] = 0
    dati["soglia_fiches"] = 0
    dati["record_battuto"] = False
    dati["fiches_attuali"] = regole.FICHES_INIZIALI
    testo = (
        f"Fiches esaurite, game over.\nSerie chiusa a {serie} mani, primato {dati['record_mani_senza_fallimenti']}.\n"
        f"Alla prossima partita riparti con {formatta_fiches(regole.FICHES_INIZIALI)} fiches."
    )
    return Evento("game_over", testo)


def bilancio_sessione(saldo_iniziale, saldo_finale):
    """Le due frasi di congedo: da quanto si e' partiti e come si chiude."""
    differenza = saldo_finale - saldo_iniziale
    variazione = differenza * 100 / saldo_iniziale if saldo_iniziale > 0 else 0.0
    segno = "+" if differenza >= 0 else "-"
    per_cento = f"{abs(variazione):.1f}".replace(".", ",")
    return (
        f"Hai iniziato la sessione con {formatta_fiches(saldo_iniziale)} fiches.",
        f"Chiudi con {formatta_fiches(saldo_finale)} fiches: {formatta_bilancio(differenza)}, cioè {segno}{per_cento} per cento.",
    )
