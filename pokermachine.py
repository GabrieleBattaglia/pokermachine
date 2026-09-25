# PokerMachine, il video poker a fiches da riga di comando.
# Studiato per chi usa uno screen reader e per il display braille.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# Concepito il 2 ottobre 2024 con ChatGPT o1.
# 09/09/2026: revisione 1 del refactoring generale. Regole, dati, conti e
# suoni escono in moduli propri; qui restano il dialogo con chi gioca e le
# statistiche. Senza decorazioni, con dgt per gli ingressi, il manuale sul
# punto di domanda, un suono per ogni evento e il controllo aggiornamenti.
# 24/09/2026: versione 5. La Killer Hand annuncia minimo, sorpresa e scudi;
# al prompt delle carte c da' il consiglio, e a fine mano il gioco dice
# quanto valeva la tenuta migliore; dopo una vincita si puo' raddoppiare;
# t elenca i trofei, e ogni serie ha le sue sfide.

"""PokerMachine.

Si punta, si ricevono cinque carte, si sceglie quali tenere, si cambiano le
altre e la mano finale paga secondo la tabella dei punteggi. Ogni
venticinque mani senza fallimenti arriva una Killer Hand: la vincita netta
si moltiplica, ma la puntata minima cresce a ogni Killer Hand, e una regola
a sorpresa cambia il gioco. Il gruzzolo e le statistiche di sempre stanno in
pokermachine_data.json accanto al programma.
"""

import sys
from collections import Counter

from GBUtils import Mazzo, dgt, gestisci_aggiornamento, key, manuale

import partita
import regole
import sfide
import strategia
import trofei
from consiglio import Consigliere, in_fiches, maschera_di, tenuta_breve
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
CAMBIA_TUTTE = "0"
# I valori al plurale, per dire che cosa contiene la mano servita.
PLURALI = {
    1: "assi",
    2: "due",
    3: "tre",
    4: "quattro",
    5: "cinque",
    6: "sei",
    7: "sette",
    8: "otto",
    9: "nove",
    10: "dieci",
    11: "jack",
    12: "regine",
    13: "re",
}
SENZA_GRUPPI = ("Scala Reale", "Scala a colore", "Colore", "Scala", "Carta alta")
CONTINUA, USCITA, GAME_OVER = "continua", "uscita", "game_over"
SCOMMESSE = {"r": "rosso", "n": "nero", "c": "Cuori", "q": "Quadri", "f": "Fiori", "p": "Picche"}
SPIEGAZIONE_RADDOPPIO = (
    "Raddoppio: r rosso o n nero raddoppiano la posta; c cuori, q quadri, f fiori, p picche la quadruplicano; "
    "invio incassa. Se sbagli, la posta è persa."
)


def _per_cento(parte, totale):
    """Una percentuale con la virgola all'italiana, un decimale e il suo articolo: il 12,5, l'8,3, lo 0,0."""
    numero = f"{parte * 100 / totale:.1f}".replace(".", ",") if totale > 0 else "0,0"
    intero = numero.split(",")[0]
    if intero == "0":
        return f"lo {numero}"
    if intero.startswith("8") or intero in ("1", "11"):
        return f"l'{numero}"
    return f"il {numero}"


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
    print(f"Scudi: {dati['scudi']} su {regole.SCUDI_MAX}.")
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
    vinti = dati["montepremi_vinti"]
    print(f"Montepremi: {formatta_fiches(partita.montepremi(dati))} fiches, {'vinto ' + _volte(vinti) if vinti else 'mai vinto'}.")
    precisione = dati["precisione"]
    if precisione["tenute"]:
        print(
            f"Precisione: {precisione['ottime']} {'tenuta ottima' if precisione['ottime'] == 1 else 'tenute ottime'} su {precisione['tenute']}, {_per_cento(precisione['ottime'], precisione['tenute'])} per cento."
        )
        print(
            f"Fiches lasciate per strada con le tenute non ottime, in media attesa e in tutto: {in_fiches(precisione['valore_perso'], 1)}."
        )
    else:
        print("Precisione: ancora nessuna tenuta valutata.")
    raddoppi = dati["raddoppi"]
    if raddoppi["tentati"]:
        print(
            f"Raddoppi: {raddoppi['vinti']} {'riuscito' if raddoppi['vinti'] == 1 else 'riusciti'} su {raddoppi['tentati']}, "
            f"vinte {formatta_fiches(raddoppi['fiches_vinte'])} fiches, perse {formatta_fiches(raddoppi['fiches_perse'])}."
        )
    else:
        print("Raddoppi: ancora nessuno.")
    if dati["fiches_puntate"]:
        ritorno = f"{dati['fiches_restituite'] * 100 / dati['fiches_puntate']:.1f}".replace(".", ",")
        print(f"Ritorno personale dalla versione 5: {ritorno} fiches tornate ogni 100 puntate.")
    else:
        print("Ritorno personale: ancora nessuna puntata con la versione 5.")
    killer = dati["killer"]
    if killer["giocate"]:
        print(
            f"Killer Hand giocate: {killer['giocate']}; vinte {killer['vinte']}, pareggiate {killer['pareggiate']}, "
            f"perse {killer['perse']}, salvate dallo scudo {killer['salvate']}; bonus incassati {formatta_fiches(killer['bonus'])} fiches."
        )
    else:
        print("Killer Hand giocate: ancora nessuna con la versione 5.")
    if dati["ultime_serie"]:
        print("Ultime serie, dalla più recente:")
        for voce in reversed(dati["ultime_serie"]):
            mani = voce["mani"]
            print(
                f"{mani} {'mano' if mani == 1 else 'mani'}, al massimo {formatta_fiches(voce['fiches_massime'])} fiches, "
                f"finita {formatta_tempo_trascorso(voce['fine'])}."
            )
    print(f"Trofei: {len(trofei.conquistati(dati))} su {len(trofei.TROFEI)}. La lettera t li elenca.")
    for sfida, fatta in sfide.in_corso(dati):
        print(f"Sfida {'superata' if fatta else 'in corso'}: {sfida.testo}")
    mani = dati["mani_giocate"]
    pagate = dati["mani_pagate"]
    if mani:
        print(f"Mani pagate, che restituiscono almeno la puntata: {pagate} su {mani}, {_per_cento(pagate, mani)} per cento.")
    else:
        print("Mani pagate: ancora nessuna mano giocata.")
    print("Punteggi realizzati, dal più alto.")
    for nome in regole.NOMI_PUNTEGGI:
        voce = dati["punteggi"][nome]
        if voce["conteggio"] == 0:
            print(f"{nome}: mai.")
        else:
            print(
                f"{nome}: {_volte(voce['conteggio'])}, {_per_cento(voce['conteggio'], mani)} per cento, l'ultima {formatta_tempo_trascorso(voce['ultima_realizzazione'])}."
            )


def mostra_trofei(dati):
    """I trofei conquistati, con la data, e quelli ancora da conquistare."""
    play_event("trofei")
    presi = trofei.conquistati(dati)
    print(f"Trofei conquistati: {len(presi)} su {len(trofei.TROFEI)}.")
    for trofeo, data in presi:
        print(f"{trofeo.nome}, {formatta_tempo_trascorso(data)}.")
    mancano = trofei.da_conquistare(dati)
    if mancano:
        print("Da conquistare:")
        for trofeo in mancano:
            print(f"{trofeo.nome}.")


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


def prompt_puntata(dati, numero_mano_sessione):
    """Il prompt della puntata, entro trenta caratteri: F fiches, S serie, R primato, M mano, D scudi.

    Le lettere stanno attaccate ai numeri, F428 S110 R399 M1 D2: cosi' il
    prompt resta nelle trenta celle anche con milioni di fiches e serie da
    quattro cifre.
    """
    prompt = (
        f"F{formatta_fiches(dati['fiches_attuali'])} S{prossima_mano(dati)} R{dati['record_mani_senza_fallimenti']} M{numero_mano_sessione}"
    )
    if dati["scudi"]:
        prompt += f" D{dati['scudi']}"
    return prompt + "> "


def chiedi_puntata(dati, numero_mano_sessione, killer=None):
    """La puntata scelta, oppure None se chi gioca vuole uscire.

    Il prompt porta i numeri che servono a ogni mano, una lettera ciascuno
    per stare in trenta caratteri: F fiches, S mano della serie senza
    fallimenti, R primato, M mano di questa sessione e, se ce ne sono, D
    gli scudi. Oltre alla cifra si accettano le scorciatoie in
    percentuale, m per il minimo, r per le statistiche, t per i trofei e il
    punto di domanda per la guida. In una Killer Hand il minimo e' quello
    della gara, e chi ne ha meno punta tutto.
    """
    while True:
        fiches = dati["fiches_attuali"]
        risposta = dgt(prompt_puntata(dati, numero_mano_sessione), kind="s").strip()
        if risposta == "":
            return None
        if risposta == "?":
            mostra_manuale()
            continue
        if risposta.lower() == "r":
            mostra_report(dati)
            continue
        if risposta.lower() == "t":
            mostra_trofei(dati)
            continue
        minima = regole.puntata_minima_killer_hand(fiches, killer.numero) if killer else regole.puntata_minima(fiches)
        if risposta.lower() == "m":
            puntata = minima
        elif risposta in SCORCIATOIE:
            puntata = fiches * SCORCIATOIE[risposta] // 100
        else:
            try:
                puntata = leggi_fiches(risposta)
            except ValueError:
                play_event("errore")
                print("Non ho capito: un numero anche con k o m, una scorciatoia, m, r, t, punto di domanda o invio per uscire.")
                continue
        if puntata > fiches:
            play_event("errore")
            print(f"Hai solo {formatta_fiches(fiches)} fiches.")
            continue
        if puntata < minima:
            play_event("puntata_minima")
            if killer and minima >= fiches:
                print(
                    f"In questa Killer Hand il minimo è {formatta_fiches(killer.minimo)} fiches e non li hai: punti tutto, {formatta_fiches(fiches)}."
                )
            elif killer:
                print(f"La puntata minima di questa Killer Hand è {formatta_fiches(minima)} fiches: correggo.")
            else:
                print(f"La puntata minima è {formatta_fiches(minima)}, il {regole.PERCENTUALE_MINIMA_PUNTATA} per cento: correggo.")
            puntata = minima
        return puntata


def chiedi_carte_da_tenere(breve, consiglia=None, proposta=None):
    """Gli indici, da zero, delle carte da tenere.

    Il prompt e' la mano in forma breve, fatta per il braille, seguita
    dalla domanda con la tenuta proposta, quella del consiglio scritta come
    la si scriverebbe: QC 9Q JQ 6F 8F tieni 13? Sta tutto in trenta
    caratteri. Invio da solo accetta la proposta, 0 cambia tutte le carte,
    c chiede il consiglio a parole, che consiglia stampa. Senza proposta,
    se il calcolo non c'e', la proposta e' 0.
    """
    proposta = proposta or CAMBIA_TUTTE
    while True:
        risposta = dgt(f"{breve} tieni {proposta}? ", kind="s", default=proposta).strip()
        if risposta.lower() == "c" and consiglia:
            consiglia()
            continue
        if risposta == CAMBIA_TUTTE:
            return set()
        if risposta and set(risposta) <= CIFRE and all(1 <= int(c) <= regole.CARTE_PER_MANO for c in risposta):
            return {int(c) - 1 for c in risposta}
        play_event("errore")
        print(
            f"Scrivi i numeri delle carte da tenere, da 1 a {regole.CARTE_PER_MANO}, tutti attaccati; "
            "0 per cambiarle tutte; c per il consiglio; invio da solo per accettare la proposta."
        )


def _ordina(mano):
    """Le carte in ordine di valore, dal due all'asso, e a parita' di valore per seme: coppie e gemelle stanno vicine."""
    return sorted(mano, key=lambda c: (regole.rango_carta(c), c.seme_id))


def descrivi(mano, tabella=None):
    """Il punteggio di una mano, con i valori dei gruppi quando contano: Coppia pagata, di jack."""
    punteggio = regole.valuta_mano(mano, tabella)
    if punteggio in SENZA_GRUPPI:
        return punteggio
    conta = Counter(c.valore for c in mano)
    rango = {c.valore: regole.rango_carta(c) for c in mano}
    gruppi = sorted((v for v, q in conta.items() if q >= 2), key=lambda v: (-conta[v], -rango[v]))
    if not gruppi:
        return punteggio
    return f"{punteggio}, di " + " e di ".join(PLURALI[v] for v in gruppi)


def proposta_di(consigliere):
    """La tenuta consigliata come la si scrive al prompt, oppure None se il calcolo non c'e'."""
    tenute = consigliere.tenute()
    if tenute is None:
        return None
    posizioni = strategia.carte_tenute(strategia.migliore(tenute).maschera)
    return "".join(str(i + 1) for i in posizioni) or CAMBIA_TUTTE


def _pesca(mazzo, quante):
    """Pesca annunciando il rimescolamento, se c'e' stato."""
    carte = mazzo.pesca(quante)
    if mazzo.ultimo_rimescolo:
        play_event("rimescolo")
        print("Il mazzo era finito: rimescolo gli scarti.")
    return carte


def annuncia_killer_hand(dati, killer):
    """Numero, minimo, moltiplicatore, sorpresa e scudi della Killer Hand in arrivo."""
    play_event("killer_hand")
    print(f"Killer Hand numero {killer.numero}, mano {prossima_mano(dati)} della serie.")
    fiches = dati["fiches_attuali"]
    minima = regole.puntata_minima_killer_hand(fiches, killer.numero)
    if minima >= fiches:
        print(f"La puntata minima è {formatta_fiches(killer.minimo)} fiches: non ne hai di più, e punterai tutto.")
    else:
        print(f"La puntata minima è {formatta_fiches(minima)} fiches.")
    sorpresa = killer.sorpresa
    play_event(f"sorpresa_{sorpresa.chiave}")
    print(f"Sorpresa: {sorpresa.nome}. {sorpresa.spiegazione}")
    print(f"Se vinci con un punteggio pagato, la vincita netta si moltiplica per {sorpresa.moltiplicatore}.")
    scudi = dati["scudi"]
    if scudi:
        print(f"Hai {scudi} {'scudo' if scudi == 1 else 'scudi'}: se perdi, uno ti restituisce la puntata.")
    else:
        print("Non hai scudi.")
    print(f"Montepremi: {formatta_fiches(partita.montepremi(dati))} fiches.")


def consiglia(consigliere, mano, puntata):
    """Stampa la tenuta migliore, se il calcolo e' riuscito."""
    tenute = consigliere.tenute()
    play_event("consiglio")
    if tenute is None:
        print("Il consiglio non è disponibile per questa mano.")
        return
    migliore = strategia.migliore(tenute)
    print(f"Consiglio: {tenuta_breve(migliore.maschera, mano)}. Rende in media {in_fiches(migliore.valore, puntata)} fiches.")


def _di_piu(fiches):
    """Quanto rendeva di piu' la tenuta migliore, detto anche quando e' meno di un decimo di fiche."""
    if fiches < 0.05:
        return "appena di più, meno di un decimo di fiche,"
    return f"{in_fiches(fiches, 1)} fiches più"


def valuta_tenuta(dati, consigliere, mano, tenute_scelte, puntata):
    """Conta la precisione della tenuta scelta e, se non era la migliore, dice quanto valeva in meno."""
    tenute = consigliere.tenute()
    if tenute is None:
        return []
    maschera = maschera_di(tenute_scelte)
    migliore = strategia.migliore(tenute)
    ottima = strategia.e_ottima(tenute, maschera)
    perso = 0.0 if ottima else (migliore.valore - tenute[maschera].valore) * puntata
    eventi = partita.registra_tenuta(dati, ottima, perso)
    if not ottima:
        eventi.insert(
            0,
            partita.Evento(
                "tenuta_migliore",
                f"La tenuta migliore era {tenuta_breve(migliore.maschera, mano)}: rendeva in media {_di_piu(perso)} della tua.",
            ),
        )
    return eventi


def di(eventi):
    """Suona e dice gli eventi, uno dopo l'altro. Vero se fra loro c'e' il game over."""
    for evento in eventi:
        play_event(evento.nome)
        print(evento.testo)
    return any(evento.nome == "game_over" for evento in eventi)


def offri_raddoppio(dati, mazzo, posta, puntata, spiegato):
    """Il raddoppio dopo una vincita, fino a cinque volte. Restituisce CONTINUA oppure GAME_OVER.

    spiegato e' un dizionario della sessione che ricorda se la spiegazione
    completa e' gia' stata detta: si dice la prima volta, poi basta il
    prompt, e il punto di domanda la ripete.
    """
    for _ in range(partita.RADDOPPI_MAX):
        play_event("raddoppio_offerto")
        if not spiegato.get("raddoppio"):
            print(SPIEGAZIONE_RADDOPPIO)
            spiegato["raddoppio"] = True
        while True:
            risposta = dgt(f"Posta {formatta_fiches(posta)} rn cqfp? ", kind="s").strip().lower()
            if risposta == "?":
                print(SPIEGAZIONE_RADDOPPIO)
                continue
            if risposta == "" or risposta in SCOMMESSE:
                break
            play_event("errore")
            print("Scrivi r o n per il colore, c, q, f o p per il seme, oppure invio per incassare.")
        if risposta == "":
            play_event("raddoppio_incassato")
            print(f"Incassi {formatta_fiches(posta)} fiches.")
            return CONTINUA
        carte = _pesca(mazzo, 1)
        if not carte:
            print(f"Il mazzo è vuoto: incassi {formatta_fiches(posta)} fiches.")
            return CONTINUA
        carta = carte[0]
        mazzo.scarta_carte(carte)
        play_event("raddoppio_carta")
        print(f"Esce {carta.nome}.")
        vinta, posta, eventi = partita.raddoppio(dati, posta, SCOMMESSE[risposta], carta, puntata)
        if di(eventi):
            return GAME_OVER
        if not vinta:
            return CONTINUA
    play_event("raddoppio_incassato")
    print(f"Raddoppi finiti: incassi {formatta_fiches(posta)} fiches.")
    return CONTINUA


def gioca_mano(dati, mazzo, numero_mano_sessione, consigliere, spiegato):
    """Una mano intera. Restituisce CONTINUA, USCITA oppure GAME_OVER."""
    killer = killer_hand_in_arrivo(dati)
    if killer:
        # La sorpresa estratta si salva subito: uscire e rientrare non la cambia.
        salva(dati)
        annuncia_killer_hand(dati, killer)
    puntata = chiedi_puntata(dati, numero_mano_sessione, killer)
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
    si_cambia = not killer or killer.sorpresa.cambio
    consigliere.dimentica()
    if si_cambia:
        consigliere.calcola(mano, mazzo, partita.tabella_decisione(dati, killer, puntata))
        print(f"Servita: {descrivi(mano, partita.tabella_in_vigore(killer))}.")
        tenute = chiedi_carte_da_tenere(
            " ".join(c.desc_breve for c in mano), lambda: consiglia(consigliere, mano, puntata), proposta_di(consigliere)
        )
    else:
        print("Nessun cambio: la mano servita è quella finale.")
        tenute = set(range(regole.CARTE_PER_MANO))
    da_tenere = [c for i, c in enumerate(mano) if i in tenute]
    da_cambiare = [c for i, c in enumerate(mano) if i not in tenute]
    servita = mano
    nuove = []
    if da_cambiare:
        play_event("scarto")
        print(f"Cambi {len(da_cambiare)} carte." if len(da_cambiare) > 1 else "Cambi una carta.")
        mazzo.scarta_carte(da_cambiare)
        nuove = _pesca(mazzo, len(da_cambiare))
        mano = _ordina(da_tenere + nuove)
    elif si_cambia:
        play_event("tieni_tutte")
        print("Tieni tutte le carte.")
    print("Mano finale:")
    for carta in mano:
        # Le carte gemelle sono uguali anche come tuple: la nuova si riconosce per identita'.
        nuova = any(carta is n for n in nuove)
        print(f"{carta.nome}{', nuova' if nuova else ''}.")
    punteggio = regole.valuta_mano(mano, partita.tabella_in_vigore(killer))
    # La mano finale torna negli scarti: e' cio' che tiene in gioco tutte le
    # carte e lascia al mazzo di rimescolarle quando servono.
    mazzo.scarta_carte(mano)
    print(f"Risultato: {punteggio}.")
    incasso = partita.incasso(puntata, punteggio, killer)
    eventi = esito_mano(dati, puntata, punteggio, killer, carte=mano)
    if si_cambia:
        # La tenuta si commenta prima del game over, che chiude sempre la mano.
        fine = [e for e in eventi if e.nome == "game_over"]
        eventi = [e for e in eventi if e.nome != "game_over"] + valuta_tenuta(dati, consigliere, servita, tenute, puntata) + fine
    finita = di(eventi)
    if not finita and incasso > puntata:
        salva(dati)
        finita = offri_raddoppio(dati, mazzo, incasso, puntata, spiegato) == GAME_OVER
    salva(dati)
    return GAME_OVER if finita else CONTINUA


def annuncia_serie(dati):
    """All'inizio di una serie, o al primo avvio della versione 5, estrae e dice le sfide."""
    if dati["serie"]["sfide"]:
        return
    play_event("sfide")
    for riga in partita.inizia_serie(dati):
        print(riga)
    salva(dati)


def gioca(dati):
    """La partita, dal mazzo nuovo all'uscita o al game over."""
    print(f"Preparo un mazzo di {regole.NUM_MAZZI} confezioni, {52 * regole.NUM_MAZZI} carte, e lo mescolo.")
    mazzo = Mazzo(tipo_francese=True, num_mazzi=regole.NUM_MAZZI)
    mazzo.mescola_mazzo()
    play_event("mescola")
    print(f"Montepremi: {formatta_fiches(partita.montepremi(dati))} fiches.")
    consigliere = Consigliere()
    spiegato = {}
    saldo_iniziale = dati["fiches_attuali"]
    numero_mano_sessione = 1
    try:
        annuncia_serie(dati)
        while (esito := gioca_mano(dati, mazzo, numero_mano_sessione, consigliere, spiegato)) == CONTINUA:
            numero_mano_sessione += 1
    finally:
        consigliere.chiudi()
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
    print("Punto di domanda per la guida, r per le statistiche, t per i trofei, invio per uscire.")
    gioca(dati)
    play_event("chiusura")
    key("\rPremi un tasto per chiudere.\r")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
