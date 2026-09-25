# PokerMachine, la partita: la contabilita' di una mano sui dati del giocatore.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 09/09/2026: revisione 1 del refactoring generale. Nasce per separare i
# conti dall'interfaccia: il bonus della Killer Hand entra nel saldo, la
# penalita' si calcola sulle fiches con cui si e' entrati nella mano, il
# fallimento si conta una volta sola, il primato conta anche l'ultima mano
# e viene annunciato quando si supera, e con lui i traguardi e le soglie.
# 24/09/2026: versione 5. La Killer Hand diventa una gara senza penalita',
# con la puntata minima che cresce, gli scudi e le regole a sorpresa; arrivano
# il montepremi, il raddoppio, la precisione delle tenute, i trofei e le sfide.

"""La contabilita' di una mano di PokerMachine.

esito_mano riceve i dati del giocatore, la puntata e il punteggio, aggiorna
saldo e statistiche e restituisce la lista degli eventi accaduti, ciascuno
con un nome, che e' anche il nome del suono, e una frase da mostrare. Lo
stesso fanno raddoppio, per la scommessa sulla carta dopo una vincita, e
registra_tenuta, per la precisione. Il modulo non stampa e non suona: e' cio'
che rende le prove automatiche possibili.
"""

import random
from collections import namedtuple

import regole
import sfide
import trofei
from dati import ULTIME_SERIE, adesso, dati_nuova_serie
from numeri import formatta_bilancio, formatta_fiches

Evento = namedtuple("Evento", ["nome", "testo"])
KillerHand = namedtuple("KillerHand", ["numero", "minimo", "sorpresa"])

ROSSI = ("Cuori", "Quadri")
NERI = ("Fiori", "Picche")
SCOMMESSE_COLORE = {"rosso": ROSSI, "nero": NERI}
SEMI = ROSSI + NERI
MOLTIPLICATORE_COLORE = 2
MOLTIPLICATORE_SEME = 4
RADDOPPI_MAX = 5
# Il suono di una mano che di solito paga, ma che una sorpresa ha reso muta.
MUTA = "Coppia non pagata"


def prossima_mano(dati):
    """Il numero, nella serie senza fallimenti, della mano che sta per cominciare."""
    return dati["mani_dall_ultimo_fallimento"] + 1


def killer_hand_in_arrivo(dati, generatore=None):
    """La KillerHand della prossima mano, oppure None se la prossima mano e' normale.

    Il numero cresce solo quando la mano viene giocata davvero, e la regola a
    sorpresa, estratta la prima volta, resta nei dati finche' la mano non si
    gioca: chi esce sul prompt di una Killer Hand e rientra la ritrova
    uguale, e non puo' cambiare sorpresa uscendo e rientrando.
    """
    if not regole.e_killer_hand(prossima_mano(dati)):
        return None
    numero = dati["killer_hand_count"] + 1
    chiave = dati.get("sorpresa_kh")
    if chiave not in regole.SORPRESE_PER_CHIAVE:
        chiave = (generatore or random).choice(regole.SORPRESE).chiave
        dati["sorpresa_kh"] = chiave
    return KillerHand(numero, regole.minimo_killer_hand(numero), regole.SORPRESE_PER_CHIAVE[chiave])


def tabella_in_vigore(killer=None):
    """La tabella dei multipli che paga questa mano: quella della sorpresa, se e' una Killer Hand."""
    return regole.tabella_sorpresa(killer.sorpresa) if killer else regole.TABELLA_VINCITE


def incasso(puntata, punteggio, killer=None):
    """Le fiches che la mano rende, puntata e bonus della Killer Hand compresi."""
    restituito = regole.calcola_vincita(punteggio, puntata, tabella_in_vigore(killer))
    if killer and restituito > puntata:
        restituito += (restituito - puntata) * (killer.sorpresa.moltiplicatore - 1)
    return restituito


def _registra_punteggio(dati, punteggio):
    voce = dati["punteggi"].get(punteggio)
    if voce is not None:
        voce["conteggio"] += 1
        voce["ultima_realizzazione"] = adesso()


def _record_vincita(dati, vinte, eventi):
    if vinte > dati["vincita_massima"]:
        dati["vincita_massima"] = vinte
        dati["data_vincita_massima"] = adesso()
        eventi.append(Evento("record_vincita", f"Nuovo record di vincita in una mano: {formatta_fiches(vinte)} fiches."))


def _vincita(dati, puntata, restituito, killer, eventi):
    """Il saldo cresce di quanto viene restituito piu' l'eventuale bonus. Restituisce il totale."""
    netta = restituito - puntata
    eventi.append(Evento(None, f"Vinci {formatta_fiches(netta)} fiches, restituite {formatta_fiches(restituito)}."))
    bonus = 0
    if killer:
        moltiplicatore = killer.sorpresa.moltiplicatore
        bonus = netta * (moltiplicatore - 1)
        eventi.append(Evento("kh_bonus", f"Bonus Killer Hand: vincita netta per {moltiplicatore}, {formatta_fiches(bonus)} fiches in più."))
    vinte = netta + bonus
    dati["fiches_guadagnate"] += vinte
    _record_vincita(dati, vinte, eventi)
    return restituito + bonus


def _perdita(dati, puntata, eventi):
    """La puntata persa, con il suo record."""
    eventi.append(Evento(None, f"Perdi la puntata di {formatta_fiches(puntata)} fiches."))
    dati["fiches_perdute"] += puntata
    if puntata > dati["perdita_massima"]:
        dati["perdita_massima"] = puntata
        dati["data_perdita_massima"] = adesso()
        eventi.append(Evento("record_perdita", f"Nuovo record di perdita in una mano: {formatta_fiches(puntata)} fiches."))


def _scudo_usato(dati, puntata, eventi):
    dati["scudi"] -= 1
    restano = dati["scudi"]
    coda = "Non te ne restano." if restano == 0 else ("Te ne resta uno." if restano == 1 else f"Te ne restano {restano}.")
    eventi.append(Evento("scudo_usato", f"Lo scudo ti restituisce la puntata di {formatta_fiches(puntata)} fiches. {coda}"))


def guadagna_scudo(dati, motivo, eventi):
    """Uno scudo in piu', se non se ne hanno gia' il massimo."""
    if dati["scudi"] >= regole.SCUDI_MAX:
        eventi.append(Evento("scudi_pieni", f"{motivo} Avresti uno scudo, ma ne hai già {regole.SCUDI_MAX}, il massimo."))
        return
    dati["scudi"] += 1
    eventi.append(Evento("scudo_guadagnato", f"{motivo} Guadagni uno scudo: ne hai {dati['scudi']}."))


def montepremi(dati):
    """Il montepremi in fiches intere."""
    return dati["montepremi_centesimi"] // 100


def tabella_decisione(dati, killer, puntata):
    """I guadagni, in puntate, su cui scegliere la tenuta migliore di questa mano.

    Sono quelli delle regole, con la Killer Hand, la sorpresa e lo scudo se
    ci sono, piu' il montepremi, che le mani rarissime vincono per intero:
    quando e' grande rispetto alla puntata, inseguirlo diventa giusto.
    """
    guadagni = regole.tabella_decisione(killer.sorpresa if killer else None, scudo=bool(killer) and dati["scudi"] > 0)
    premio = montepremi(dati)
    if premio and puntata:
        for nome in regole.PUNTEGGI_MONTEPREMI:
            guadagni[nome] += premio / puntata
    return guadagni


def _montepremi(dati, puntata, punteggio, eventi):
    """Accumula la percentuale della puntata e, con le mani rarissime, paga. Restituisce quanto ha pagato.

    Se accumulando supera una soglia, lo annuncia: una volta sola per soglia,
    finche' qualcuno non lo vince e il conto riparte.
    """
    dati["montepremi_centesimi"] += puntata * regole.MONTEPREMI_PERCENTUALE
    premio = montepremi(dati)
    if punteggio not in regole.PUNTEGGI_MONTEPREMI or premio < 1:
        soglia = max((s for s in regole.MONTEPREMI_SOGLIE if premio >= s), default=0)
        if soglia > dati["montepremi_soglia"]:
            dati["montepremi_soglia"] = soglia
            eventi.append(Evento("montepremi_soglia", f"Il montepremi supera {formatta_fiches(soglia)} fiches."))
        return 0
    dati["montepremi_centesimi"] -= premio * 100
    dati["montepremi_vinti"] += 1
    dati["montepremi_soglia"] = 0
    dati["fiches_guadagnate"] += premio
    eventi.append(Evento("montepremi_vinto", f"Vinci il montepremi: {formatta_fiches(premio)} fiches."))
    return premio


def _conta_killer(dati, killer, puntata, restituito, salvata):
    """Il bilancio delle Killer Hand: giocate, vinte, pareggiate, perse, salvate dallo scudo, bonus incassati."""
    conti = dati["killer"]
    conti["giocate"] += 1
    if restituito > puntata:
        conti["vinte"] += 1
        conti["bonus"] += (restituito - puntata) * (killer.sorpresa.moltiplicatore - 1)
    elif restituito == puntata:
        conti["pareggiate"] += 1
    elif salvata:
        conti["salvate"] += 1
    else:
        conti["perse"] += 1


def _seme_unico(carte):
    semi = {c.seme_nome for c in carte}
    return semi.pop() if len(semi) == 1 else None


def _gemelle(carte):
    """Quante carte identiche, anche nel seme, ci sono al massimo nella mano."""
    conteggio = {}
    for c in carte:
        conteggio[regole.tipo_carta(c)] = conteggio.get(regole.tipo_carta(c), 0) + 1
    return max(conteggio.values(), default=0)


def _nuovo_saldo(dati, fiches, eventi):
    """Cio' che il saldo nuovo tocca, dopo una mano o un raddoppio: il minimo della serie e le soglie."""
    stato = dati["serie"]
    stato["fiches_minime"] = min(stato["fiches_minime"], fiches)
    stato["fiches_massime"] = max(stato["fiches_massime"], fiches)
    soglia = regole.soglia_raggiunta(fiches)
    if soglia > dati["soglia_fiches"]:
        dati["soglia_fiches"] = soglia
        eventi.append(Evento("soglia_fiches", f"Superata la soglia di {formatta_fiches(soglia)} fiches."))


def premi(dati, fatti, eventi):
    """Trofei e sfide conquistati con quei fatti, aggiunti agli eventi."""
    for sfida in sfide.controlla(dati, fatti):
        eventi.append(Evento("sfida_vinta", f"Sfida superata: {sfida.testo}"))
        guadagna_scudo(dati, "Premio della sfida.", eventi)
    eventi.extend(trofei.controlla(dati, fatti))


def esito_mano(dati, puntata, punteggio, killer=None, carte=()):
    """Contabilizza una mano conclusa e restituisce gli eventi, nell'ordine in cui vanno detti.

    dati['fiches_attuali'] e' il saldo con cui il giocatore e' entrato nella
    mano, puntata compresa. killer e' la KillerHand se la mano lo e', con la
    sua sorpresa, altrimenti None. carte sono quelle della mano finale, che
    servono ai trofei e alle sfide. Il primo evento porta il nome del
    punteggio, che e' anche il nome del suo suono, salvo che una sorpresa lo
    abbia reso muto; seguono, quando ci sono, il bonus della Killer Hand con il
    record di vincita, oppure il record di perdita o lo scudo che salva la
    puntata, gli scudi guadagnati, il montepremi, il primato, il traguardo di
    mani, la soglia di fiches, le sfide con il loro scudo, i trofei e il game
    over.
    """
    fiches_prima = dati["fiches_attuali"]
    fiches = fiches_prima - puntata
    eventi = []
    if killer:
        dati["killer_hand_count"] += 1
        dati["sorpresa_kh"] = None
    restituito = regole.calcola_vincita(punteggio, puntata, tabella_in_vigore(killer))
    vinta = restituito > puntata
    salvata = False
    if restituito >= puntata:
        dati["mani_pagate"] += 1
    if vinta:
        fiches += _vincita(dati, puntata, restituito, killer, eventi)
    elif restituito == puntata:
        fiches += restituito
        eventi.append(Evento(None, f"Pareggio: la puntata di {formatta_fiches(puntata)} torna indietro."))
    elif killer and dati["scudi"] > 0:
        eventi.append(Evento(None, f"Perdi la puntata di {formatta_fiches(puntata)} fiches, ma hai uno scudo."))
        _scudo_usato(dati, puntata, eventi)
        fiches += puntata
        salvata = True
    else:
        _perdita(dati, puntata, eventi)
    if killer:
        _conta_killer(dati, killer, puntata, restituito, salvata)
    # Con le coppie mute, o con tutto o niente, una coppia pagata non paga:
    # il suono dev'essere quello della mano persa, non quello del pareggio.
    muta = restituito < puntata and regole.TABELLA_VINCITE.get(punteggio, 0) >= 1
    eventi[0] = Evento(MUTA if muta else punteggio, eventi[0].testo)
    if punteggio in regole.PUNTEGGI_SCUDO:
        guadagna_scudo(dati, f"{punteggio}!", eventi)
    vinto_montepremi = _montepremi(dati, puntata, punteggio, eventi)
    fiches += vinto_montepremi
    # Il ritorno personale: quanto e' tornato indietro, per ogni fiche puntata.
    dati["fiches_puntate"] += puntata
    dati["fiches_restituite"] += fiches - (fiches_prima - puntata)
    dati["fiches_attuali"] = fiches
    dati["mani_giocate"] += 1
    dati["mani_dall_ultimo_fallimento"] += 1
    dati["data_ultima_giocata"] = adesso()
    _registra_punteggio(dati, punteggio)
    serie = dati["mani_dall_ultimo_fallimento"]
    stato = dati["serie"]
    stato["pagate_di_fila"] = stato["pagate_di_fila"] + 1 if restituito >= puntata else 0
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
    _nuovo_saldo(dati, fiches, eventi)
    fatti = {
        "punteggio": punteggio,
        "seme_unico": _seme_unico(carte) if carte else None,
        "gemelle": _gemelle(carte),
        "contiene": regole.contenute(carte) if carte else set(),
        "vinta": vinta,
        "tutto": puntata == fiches_prima,
        "killer": killer.numero if killer else 0,
        "fiches": fiches,
        "serie": serie,
        "montepremi": vinto_montepremi,
    }
    premi(dati, fatti, eventi)
    if fiches <= 0:
        eventi.append(game_over(dati))
    return eventi


def raddoppio(dati, posta, scommessa, carta, puntata):
    """Contabilizza una scommessa del raddoppio. Restituisce (vinta, posta nuova, eventi).

    posta sono le fiches appena vinte che si rischiano, gia' nel saldo, e
    puntata quella della mano, che serve al record di vincita. scommessa e'
    rosso, nero oppure il nome di un seme; carta e' quella scoperta. Il
    colore giusto raddoppia la posta, il seme giusto la quadruplica;
    altrimenti la posta e' persa, e se il saldo arriva a zero e' game over.
    Le scommesse sono eque: in media valgono quanto costano.
    """
    stato = dati["raddoppi"]
    stato["tentati"] += 1
    eventi = []
    if scommessa in SCOMMESSE_COLORE:
        vinta = carta.seme_nome in SCOMMESSE_COLORE[scommessa]
        moltiplicatore = MOLTIPLICATORE_COLORE
    else:
        vinta = carta.seme_nome == scommessa
        moltiplicatore = MOLTIPLICATORE_SEME
    if vinta:
        guadagno = posta * (moltiplicatore - 1)
        nuova = posta * moltiplicatore
        stato["vinti"] += 1
        stato["di_fila"] += 1
        stato["fiches_vinte"] += guadagno
        dati["fiches_attuali"] += guadagno
        dati["fiches_restituite"] += guadagno
        dati["fiches_guadagnate"] += guadagno
        eventi.append(Evento("raddoppio_vinto", f"Indovinato: la posta sale a {formatta_fiches(nuova)} fiches."))
        _record_vincita(dati, nuova - puntata, eventi)
    else:
        nuova = 0
        stato["di_fila"] = 0
        stato["fiches_perse"] += posta
        dati["fiches_attuali"] -= posta
        dati["fiches_restituite"] -= posta
        dati["fiches_perdute"] += posta
        eventi.append(Evento("raddoppio_perso", f"Sbagliato: perdi la posta di {formatta_fiches(posta)} fiches."))
    fiches = dati["fiches_attuali"]
    _nuovo_saldo(dati, fiches, eventi)
    fatti = {"fiches": fiches, "raddoppio_seme": vinta and scommessa not in SCOMMESSE_COLORE}
    premi(dati, fatti, eventi)
    if fiches <= 0:
        eventi.append(game_over(dati))
    return vinta, nuova, eventi


def registra_tenuta(dati, ottima, perso):
    """Conta la precisione di una tenuta: se era la migliore e quante fiches valeva in meno."""
    stato = dati["precisione"]
    stato["tenute"] += 1
    if ottima:
        stato["ottime"] += 1
        stato["di_fila"] += 1
        dati["serie"]["ottime_di_fila"] += 1
    else:
        stato["di_fila"] = 0
        dati["serie"]["ottime_di_fila"] = 0
        stato["valore_perso"] += perso
    eventi = []
    premi(dati, {}, eventi)
    return eventi


def inizia_serie(dati, generatore=None):
    """Estrae le sfide della serie. Restituisce le frasi che le annunciano."""
    dati["serie"]["sfide"] = sfide.estrai(generatore, dati)
    righe = ["Sfide della serie, ciascuna vale uno scudo:"]
    righe.extend(sfida.testo for sfida, _ in sfide.in_corso(dati))
    return righe


def game_over(dati):
    """Chiude la serie: conta il fallimento e prepara il saldo per la prossima partita.

    Riassegnare qui le fiches iniziali e' cio' che impedisce al caricamento
    successivo di scambiare il saldo a zero per un secondo fallimento. Le
    sfide della serie nuova si estraggono alla prima mano.
    """
    serie = dati["mani_dall_ultimo_fallimento"]
    dati["ultime_serie"] = [
        *dati["ultime_serie"],
        {"mani": serie, "fiches_massime": dati["serie"]["fiches_massime"], "fine": adesso()},
    ][-ULTIME_SERIE:]
    dati["fallimenti"] += 1
    dati["data_ultimo_fallimento"] = adesso()
    dati["mani_dall_ultimo_fallimento"] = 0
    dati["killer_hand_count"] = 0
    dati["sorpresa_kh"] = None
    dati["soglia_fiches"] = 0
    dati["record_battuto"] = False
    dati["scudi"] = 0
    dati["fiches_attuali"] = regole.FICHES_INIZIALI
    dati["serie"] = dati_nuova_serie()
    testo = (
        f"Fiches esaurite, game over.\nSerie chiusa a {serie} {'mano' if serie == 1 else 'mani'}, primato {dati['record_mani_senza_fallimenti']}.\n"
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
