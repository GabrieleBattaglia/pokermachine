# PokerMachine, taratura: una proposta di tabella e Killer Hand, valutata per intero.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 24/09/2026: nasce con la versione 5 (issue 5 e 6). Strumento di misura, non
# fa parte del gioco.

"""Valuta una proposta completa: tabella, gara, scudi e regole a sorpresa.

esegui riceve la tabella dei multipli, i parametri della gara, i punteggi
che regalano uno scudo e le regole a sorpresa in uso, e restituisce un
rapporto con il ritorno della strategia ottima, le frequenze, la frazione di
Kelly e la durata delle serie per una batteria di modi di puntare: fissi,
adattivi e spericolati. giudica confronta il rapporto con i criteri della
taratura e dice quali sono rispettati.

Si usa da un altro script:
    from esplora import Campione, Gara, esegui, giudica
    campione = Campione()
    rapporto = esegui(campione, tabella, Gara(base=20, fattore=2.5), scudo_da, ["semplice", "coppie mute"])
    print(giudica(rapporto))
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import regole
from taratura import Campione, Gara, adattiva, esiti, frazione, kelly, riassunto, simula_serie

__all__ = ["Campione", "Gara", "esegui", "giudica", "politiche"]

TETTO = 3000
FISSE = (0.03, 0.06, 0.10, 0.15, 0.25)
SPERICOLATA = 0.40


def politiche(quota_kelly):
    """I modi di puntare della batteria: fissi, Kelly, spericolato, e la griglia degli adattivi."""
    scelte = {f"fissa {int(q * 100)}%": frazione(q) for q in FISSE}
    scelte[f"kelly {quota_kelly * 100:.0f}%"] = frazione(quota_kelly)
    scelte[f"spericolata {int(SPERICOLATA * 100)}%"] = frazione(SPERICOLATA)
    for alta in (0.06, 0.10, 0.15, 0.25):
        for bassa in (0.03, 0.10, 0.25, 0.40):
            for soglia in (3, 10):
                for in_kh in (0.0, 0.15):
                    scelte[f"adattiva {int(alta * 100)}/{int(bassa * 100)} soglia {soglia} kh {int(in_kh * 100)}%"] = adattiva(
                        alta, bassa, soglia, in_kh
                    )
    return scelte


def esegui(campione, tabella, gara, scudo_da, regole_kh, netta=3, serie=1500, seme=1, stampa=True, errore=0.0):
    """Il rapporto completo di una proposta. Vedi il docstring del modulo.

    errore e' la frequenza con cui si gioca la seconda tenuta migliore invece
    della prima: zero e' la strategia ottima.
    """
    normale, per_regola, base = esiti(campione, tabella, scudo_da, regole_kh, netta, errore)
    quota, crescita = kelly(normale)
    frequenze = base["frequenze"]
    rapporto = {
        "tabella": dict(tabella),
        "gara": {"base": gara.base, "fattore": gara.fattore, "sfide": list(gara.sfide), "scudi_max": gara.scudi_max},
        "netta": netta,
        "errore": errore,
        "scudo_da": sorted(scudo_da),
        "regole_kh": list(regole_kh),
        "ritorno": base["ritorno"],
        "kelly": quota,
        "crescita": crescita,
        "scudo_ogni": base["scudo_ogni"],
        "frequenze": {nome: float(f) for nome, f in zip(regole.NOMI_PUNTEGGI, frequenze, strict=True)},
        "perde": normale.perdita(),
        "killer": {nome: {"valore": coppia[0].valore() - 1, "perde": coppia[0].perdita()} for nome, coppia in per_regola.items()},
    }
    risultati = simula_serie(normale, per_regola, gara, politiche(quota), serie=serie, tetto=TETTO, seme=seme)
    rapporto["serie"] = {}
    for nome, (durate, usati) in risultati.items():
        r = riassunto(durate, TETTO)
        r["scudi_usati"] = float(usati.mean())
        rapporto["serie"][nome] = r
    if stampa:
        stampa_rapporto(rapporto)
    return rapporto


def _migliore(rapporto, prefisso):
    candidati = {n: r for n, r in rapporto["serie"].items() if n.startswith(prefisso)}
    nome = max(candidati, key=lambda n: (candidati[n]["mediana"], candidati[n]["media"]))
    return nome, candidati[nome]


def giudica(rapporto):
    """I criteri della taratura, ciascuno con vero o falso e il numero che lo decide."""
    serie = rapporto["serie"]
    minimo = serie["fissa 3%"]["mediana"]
    nome_fissa, fissa = _migliore(rapporto, "fissa")
    nome_adattiva, adatta = _migliore(rapporto, "adattiva")
    spericolata = serie[f"spericolata {int(SPERICOLATA * 100)}%"]["mediana"]
    tetto_max = max(r["tetto"] for r in serie.values())
    return [
        ("ritorno fra 125 e 130 per cento", 1.25 <= rapporto["ritorno"] <= 1.30, f"{rapporto['ritorno'] * 100:.1f}%"),
        ("chi punta il minimo cade fra 150 e 350 mani", 150 <= minimo <= 350, f"mediana {minimo}"),
        (
            "la migliore fissa dura almeno 1,3 volte il minimo",
            fissa["mediana"] >= 1.3 * minimo,
            f"{nome_fissa}, mediana {fissa['mediana']}",
        ),
        ("la migliore adattiva sta fra 450 e 1000 mani", 450 <= adatta["mediana"] <= 1000, f"{nome_adattiva}, mediana {adatta['mediana']}"),
        (
            "la migliore adattiva batte la migliore fissa di un quinto",
            adatta["mediana"] >= 1.2 * fissa["mediana"],
            f"{adatta['mediana']} contro {fissa['mediana']}",
        ),
        ("la spericolata cade entro 150 mani", spericolata <= 150, f"mediana {spericolata}"),
        ("nessun modo di puntare arriva al tetto piu' del 5 per cento", tetto_max <= 0.05, f"massimo {tetto_max * 100:.1f}%"),
        ("gli scudi usati dai migliori sono fra 1 e 4", 1 <= adatta["scudi_usati"] <= 4, f"{adatta['scudi_usati']:.1f}"),
    ]


def stampa_rapporto(rapporto):
    print(f"Ritorno con la strategia ottima: {rapporto['ritorno'] * 100:.2f}%.")
    print(
        f"Kelly {rapporto['kelly'] * 100:.1f}%, crescita {rapporto['crescita'] * 100:.2f}% a mano; si perde la puntata nel {rapporto['perde'] * 100:.1f}% delle mani."
    )
    print(f"Uno scudo dalle mani ogni {rapporto['scudo_ogni']:.0f} mani.")
    for nome, f in rapporto["frequenze"].items():
        if f > 0:
            multiplo = rapporto["tabella"][nome]
            print(f"  {nome} {multiplo}: una ogni {1 / f:.0f}, contributo {f * multiplo * 100:.2f} punti.")
    for nome, k in rapporto["killer"].items():
        print(f"Killer Hand {nome}: valore per fiche {k['valore'] * 100:+.0f}%, perde {k['perde'] * 100:.0f}%.")
    ordinati = sorted(rapporto["serie"].items(), key=lambda kv: -kv[1]["mediana"])
    adattive = [kv for kv in ordinati if kv[0].startswith("adattiva")][:8]
    altre = [kv for kv in ordinati if not kv[0].startswith("adattiva")]
    for nome, r in adattive + altre:
        print(
            f"  {nome}: mediana {r['mediana']}, decili {r['decimo']}-{r['nono']}, al tetto {r['tetto'] * 100:.0f}%, scudi {r['scudi_usati']:.1f}."
        )
    for criterio, rispettato, numero in giudica(rapporto):
        print(f"{'SI' if rispettato else 'NO'}: {criterio}, {numero}.")


def media_serie(rapporto):
    return float(np.mean([r["mediana"] for r in rapporto["serie"].values()]))
