# PokerMachine, i numeri: le fiches con i prefissi K e M, come in Terminal Beast.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).
# 09/09/2026: copiata da format_money di Terminal Beast su richiesta di
# Gabriele, per il display braille: 3.52K occupa cinque celle, 3520 ne
# occupa quattro ma 602390 sei, e la lunghezza fissa e' cio' che conta in
# un prompt da trenta caratteri. E' una candidata per GBUtils, issue 9.

"""Le fiches in forma compatta.

Sotto mille il numero esatto; da mille in su le migliaia con la K, i
milioni con la M e i miliardi con la B, con due decimali quando servono
e uno quando il numero e' tondo, e il segno davanti se e' negativo.
"""


def formatta_fiches(valore):
    """La stringa compatta di un importo: 428, 3.52K, 12.3K, 195K, 1.23M."""
    try:
        val = float(valore)
    except (TypeError, ValueError):
        return "0"
    assoluto = abs(val)
    segno = "-" if val < 0 else ""
    if assoluto < 1000:
        return f"{segno}{int(assoluto)}"
    if assoluto < 1_000_000:
        migliaia = assoluto / 1000.0
        if migliaia < 10 and int(assoluto) % 100 != 0:
            testo = f"{migliaia:.2f}K".replace(".00K", "K")
        else:
            testo = f"{migliaia:.1f}K".replace(".0K", "K")
        return f"{segno}{testo}"
    if assoluto < 1_000_000_000:
        return f"{segno}{assoluto / 1_000_000.0:.2f}M".replace(".00M", "M")
    return f"{segno}{assoluto / 1_000_000_000.0:.2f}B".replace(".00B", "B")


def formatta_bilancio(valore):
    """Come formatta_fiches, ma con il piu' davanti ai valori positivi e allo zero."""
    testo = formatta_fiches(valore)
    return testo if testo.startswith("-") else f"+{testo}"


MOLTIPLICATORI = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}


def leggi_fiches(testo):
    """L'intero scritto da chi gioca: 428, 1k, 1.5K, 2m, anche con la virgola.

    E' la strada inversa di formatta_fiches, copiata da parse_money di
    Terminal Beast: il prefisso finale, senza badare alle maiuscole,
    moltiplica il numero, i decimali si troncano. Solleva ValueError su
    tutto cio' che non e' un importo, compresi i negativi.
    """
    import math

    s = str(testo).strip().lower()
    if not s:
        raise ValueError("importo vuoto")
    moltiplicatore = MOLTIPLICATORI.get(s[-1], 1)
    if moltiplicatore != 1:
        s = s[:-1]
    s = s.replace(",", ".")
    if not s or s[0] not in "0123456789." or " " in s:
        raise ValueError(f"importo non valido: {testo!r}")
    try:
        valore = float(s)
    except ValueError:
        raise ValueError(f"importo non valido: {testo!r}") from None
    if not math.isfinite(valore):
        raise ValueError(f"importo non valido: {testo!r}")
    return int(valore * moltiplicatore)
