# PokerMachine, il video poker a fiches da riga di comando.
# Studiato per chi usa uno screen reader e per il display braille.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# Concepito il 2 ottobre 2024 con ChatGPT o1.
# 09/09/2026: revisione 1 del refactoring generale. Regole, dati, conti e
# suoni escono in moduli propri; qui restano il dialogo con chi gioca e le
# statistiche. Senza decorazioni, con dgt per gli ingressi, il manuale sul
# punto di domanda, un suono per ogni evento e il controllo aggiornamenti.

"""PokerMachine.

Si punta, si ricevono cinque carte, si sceglie quali tenere, si cambiano le
altre e la mano finale paga secondo la tabella dei punteggi. Ogni
venticinque mani senza fallimenti arriva una Killer Hand, che triplica la
vincita netta o toglie una percentuale crescente delle fiches. Il gruzzolo
e le statistiche di sempre stanno in pokermachine_data.json accanto al
programma.
"""

import sys

from GBUtils import Mazzo, dgt, gestisci_aggiornamento, key, manuale

import regole
from dati import carica_dati, formatta_tempo_trascorso, percorso_risorsa, salva_dati
from numeri import formatta_bilancio, formatta_fiches, leggi_fiches
from partita import bilancio_sessione, esito_mano, killer_hand_in_arrivo, prossima_mano
from suoni import play_event
from version import AUTHOR, DATE, VERSION

APP_NAME = "pokermachine"
API_RELEASE = "https://api.github.com/repos/GabrieleBattaglia/pokermachine/releases/latest"
MANUALE = "manuale.txt"
SCORCIATOIE = {"-": 10, ",": 25, ".": 50, ";": 75, "+": 100}
CIFRE = set("0123456789")
CONTINUA, USCITA, GAME_OVER = "continua", "uscita", "game_over"


def _per_cento(parte, totale):
    """Una percentuale con la virgola all'italiana e un decimale."""
    if totale <= 0:
        return "0,0"
    return f"{parte * 100 / totale:.1f}".replace(".", ",")


def _volte(n):
    return "1 volta" if n == 1 else f"{n} volte"


def mostra_report(dati):
    """Le statistiche di sempre, una per riga, in frasi corte."""
    play_event("statistiche")
    print("Statistiche.")
    print(f"Lanci del programma: {dati['launches']}.")
    print(f"Mani giocate in totale: {dati['mani_giocate']}.")
    print(f"Mani dall'ultimo fallimento: {dati['mani_dall_ultimo_fallimento']}.")
    print(f"Record di mani senza fallimenti: {dati['record_mani_senza_fallimenti']}.")
    if dati["fallimenti"]:
        print(f"Fallimenti: {dati['fallimenti']}, l'ultimo {formatta_tempo_trascorso(dati['data_ultimo_fallimento'])}.")
    else:
        print("Fallimenti: nessuno.")
    print(f"Fiches attuali: {formatta_fiches(dati['fiches_attuali'])}.")
    print(f"Fiches guadagnate in totale: {formatta_fiches(dati['fiches_guadagnate'])}.")
    print(f"Fiches perdute in totale: {formatta_fiches(dati['fiches_perdute'])}.")
    bilancio = dati["fiches_guadagnate"] - dati["fiches_perdute"]
    print(f"Bilancio di sempre: {formatta_bilancio(bilancio)} fiches.")
    for etichetta, valore, data in (
        ("Vincita massima in una mano", dati["vincita_massima"], dati["data_vincita_massima"]),
        ("Perdita massima in una mano", dati["perdita_massima"], dati["data_perdita_massima"]),
    ):
        if valore:
            print(f"{etichetta}: {formatta_fiches(valore)}, {formatta_tempo_trascorso(data)}.")
        else:
            print(f"{etichetta}: ancora nessuna.")
    print(f"Ultima giocata: {formatta_tempo_trascorso(dati['data_ultima_giocata'])}.")
    mani = dati["mani_giocate"]
    pagate = sum(dati["punteggi"][nome]["conteggio"] for nome in regole.PUNTEGGI_PAGATI)
    if mani:
        print(f"Mani pagate, dalla coppia pagata in su: {pagate} su {mani}, il {_per_cento(pagate, mani)} per cento.")
    else:
        print("Mani pagate: ancora nessuna mano giocata.")
    print("Punteggi realizzati, dal più alto.")
    for nome in regole.NOMI_PUNTEGGI:
        voce = dati["punteggi"][nome]
        if voce["conteggio"] == 0:
            print(f"{nome}: mai.")
        else:
            print(
                f"{nome}: {_volte(voce['conteggio'])}, il {_per_cento(voce['conteggio'], mani)} per cento, l'ultima {formatta_tempo_trascorso(voce['ultima_realizzazione'])}."
            )


def mostra_manuale():
    play_event("manuale")
    try:
        manuale(nf=percorso_risorsa(MANUALE), nome="Guida")
    except OSError as e:
        print(f"La guida non si apre: {e}")


def salva(dati):
    try:
        salva_dati(dati)
    except OSError as e:
        play_event("errore")
        print(f"Salvataggio non riuscito: {e}")


def chiedi_puntata(dati, numero_mano_sessione):
    """La puntata scelta, oppure None se chi gioca vuole uscire.

    Il prompt porta i numeri che servono a ogni mano, una lettera ciascuno
    per stare in trenta caratteri: F fiches, S mano della serie senza
    fallimenti, R primato, M mano di questa sessione. Oltre alla
    cifra si accettano le scorciatoie in percentuale, m per il minimo,
    r per le statistiche e il punto di domanda per la guida.
    """
    while True:
        fiches = dati["fiches_attuali"]
        prompt = f"F {formatta_fiches(fiches)} S {prossima_mano(dati)} R {dati['record_mani_senza_fallimenti']} M {numero_mano_sessione}> "
        risposta = dgt(prompt, kind="s", smax=12).strip()
        if risposta == "":
            return None
        if risposta == "?":
            mostra_manuale()
            continue
        if risposta.lower() == "r":
            mostra_report(dati)
            continue
        minima = regole.puntata_minima(fiches)
        if risposta.lower() == "m":
            puntata = minima
        elif risposta in SCORCIATOIE:
            puntata = fiches * SCORCIATOIE[risposta] // 100
        else:
            try:
                puntata = leggi_fiches(risposta)
            except ValueError:
                play_event("errore")
                print("Non ho capito: un numero anche con k o m, una scorciatoia, m, r, punto di domanda o invio per uscire.")
                continue
        if puntata > fiches:
            play_event("errore")
            print(f"Hai solo {formatta_fiches(fiches)} fiches.")
            continue
        if puntata < minima:
            play_event("puntata_minima")
            print(f"La puntata minima è {formatta_fiches(minima)}, il {regole.PERCENTUALE_MINIMA_PUNTATA} per cento: correggo.")
            puntata = minima
        return puntata


def chiedi_carte_da_tenere(breve):
    """Gli indici, da zero, delle carte da tenere. Invio le cambia tutte.

    Il prompt e' la mano in forma breve, fatta per il braille, seguita
    dalla domanda: sta tutto in trenta caratteri.
    """
    while True:
        risposta = dgt(f"{breve} tieni? ", kind="s", smax=regole.CARTE_PER_MANO).strip()
        if risposta == "":
            return set()
        if set(risposta) <= CIFRE and all(1 <= int(c) <= regole.CARTE_PER_MANO for c in risposta):
            return {int(c) - 1 for c in risposta}
        play_event("errore")
        print(f"Scrivi i numeri delle carte da tenere, da 1 a {regole.CARTE_PER_MANO}, tutti attaccati, oppure invio per cambiarle tutte.")


def _ordina(mano):
    return sorted(mano, key=lambda c: (c.seme_id, regole.valore_alto(c)))


def _pesca(mazzo, quante):
    """Pesca annunciando il rimescolamento, se c'e' stato."""
    carte = mazzo.pesca(quante)
    if mazzo.ultimo_rimescolo:
        play_event("rimescolo")
        print("Il mazzo era finito: rimescolo gli scarti.")
    return carte


def gioca_mano(dati, mazzo, numero_mano_sessione):
    """Una mano intera. Restituisce CONTINUA, USCITA oppure GAME_OVER."""
    numero_kh, penalita = killer_hand_in_arrivo(dati)
    if numero_kh:
        play_event("killer_hand")
        print(f"Killer Hand numero {numero_kh}, mano {prossima_mano(dati)} della serie.")
        print(f"Se perdi, paghi anche il {penalita} per cento delle fiches con cui entri nella mano.")
        print("Se vinci con un punteggio pagato, la vincita netta viene triplicata.")
    puntata = chiedi_puntata(dati, numero_mano_sessione)
    if puntata is None:
        return USCITA
    play_event("puntata")
    print(f"Punti {formatta_fiches(puntata)} fiches.")
    mano = _pesca(mazzo, regole.CARTE_PER_MANO)
    if len(mano) < regole.CARTE_PER_MANO:
        play_event("errore")
        print("Il mazzo non ha abbastanza carte: la puntata torna indietro e la partita si chiude.")
        mazzo.scarta_carte(mano)
        return USCITA
    play_event("distribuzione")
    mano = _ordina(mano)
    print("Le tue carte:")
    for numero, carta in enumerate(mano, 1):
        print(f"{numero}. {carta.nome}.")
    tenute = chiedi_carte_da_tenere(" ".join(c.desc_breve for c in mano))
    da_tenere = [c for i, c in enumerate(mano) if i in tenute]
    da_cambiare = [c for i, c in enumerate(mano) if i not in tenute]
    if da_cambiare:
        play_event("scarto")
        print(f"Cambi {len(da_cambiare)} carte." if len(da_cambiare) > 1 else "Cambi una carta.")
        mazzo.scarta_carte(da_cambiare)
        nuove = _pesca(mazzo, len(da_cambiare))
        mano = _ordina(da_tenere + nuove)
    else:
        play_event("tieni_tutte")
        print("Tieni tutte le carte.")
    print("Mano finale:")
    for carta in mano:
        print(f"{carta.nome}.")
    punteggio = regole.valuta_mano(mano)
    # La mano finale torna negli scarti: e' cio' che tiene in gioco tutte le
    # carte e lascia al mazzo di rimescolarle quando servono.
    mazzo.scarta_carte(mano)
    print(f"Risultato: {punteggio}.")
    eventi = esito_mano(dati, puntata, punteggio, killer=bool(numero_kh))
    for evento in eventi:
        play_event(evento.nome)
        print(evento.testo)
    salva(dati)
    return GAME_OVER if any(evento.nome == "game_over" for evento in eventi) else CONTINUA


def gioca(dati):
    """La partita, dal mazzo nuovo all'uscita o al game over."""
    print(f"Preparo un mazzo di {regole.NUM_MAZZI} confezioni, {52 * regole.NUM_MAZZI} carte, e lo mescolo.")
    mazzo = Mazzo(tipo_francese=True, num_mazzi=regole.NUM_MAZZI)
    mazzo.mescola_mazzo()
    play_event("mescola")
    saldo_iniziale = dati["fiches_attuali"]
    numero_mano_sessione = 1
    while (esito := gioca_mano(dati, mazzo, numero_mano_sessione)) == CONTINUA:
        numero_mano_sessione += 1
    # Dopo il game over il saldo e' gia' quello della prossima partita: la
    # sessione, pero', si e' chiusa a zero.
    saldo_finale = 0 if esito == GAME_OVER else dati["fiches_attuali"]
    for riga in bilancio_sessione(saldo_iniziale, saldo_finale):
        print(riga)
    salva(dati)
    mostra_report(dati)


def main():
    play_event("avvio")
    print(f"PokerMachine, versione {VERSION} del {DATE}.")
    print(f"Autori: {AUTHOR}.")
    if gestisci_aggiornamento(APP_NAME, VERSION, API_RELEASE):
        play_event("chiusura")
        return 0
    dati, avvisi = carica_dati()
    for avviso in avvisi:
        print(avviso)
    print(f"Lancio numero {dati['launches']}.")
    mostra_report(dati)
    print("Punto di domanda per la guida, r per le statistiche, invio per uscire.")
    gioca(dati)
    play_event("chiusura")
    key("\rPremi un tasto per chiudere.\r")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
