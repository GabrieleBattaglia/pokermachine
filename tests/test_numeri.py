# PokerMachine, prove sulle fiches in forma compatta.
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Fable 5.1, UltraCode).

import pytest

from numeri import formatta_bilancio, formatta_fiches, leggi_fiches


def test_lettura_dei_prefissi():
    assert leggi_fiches("428") == 428
    assert leggi_fiches(" 1k ") == 1000
    assert leggi_fiches("1.5K") == 1500
    assert leggi_fiches("1,5k") == 1500
    assert leggi_fiches("0.5k") == 500
    assert leggi_fiches("2m") == 2_000_000
    assert leggi_fiches("1.25M") == 1_250_000
    assert leggi_fiches("1b") == 1_000_000_000
    assert leggi_fiches("2.9") == 2
    assert leggi_fiches("0") == 0


@pytest.mark.parametrize("testo", ["", "   ", "abc", "-5", "-1k", "k", "m", "1kk", "1.2.3", "inf", "nan", "+5", "5 k"])
def test_cio_che_non_e_un_importo_solleva(testo):
    with pytest.raises(ValueError):
        leggi_fiches(testo)


def test_sotto_mille_il_numero_esatto():
    assert formatta_fiches(0) == "0"
    assert formatta_fiches(428) == "428"
    assert formatta_fiches(999) == "999"
    assert formatta_fiches(-600) == "-600"


def test_migliaia_con_la_k():
    assert formatta_fiches(1000) == "1K"
    assert formatta_fiches(1050) == "1.05K"
    assert formatta_fiches(2500) == "2.5K"
    assert formatta_fiches(3520) == "3.52K"
    assert formatta_fiches(12345) == "12.3K"
    assert formatta_fiches(195000) == "195K"
    assert formatta_fiches(602390) == "602.4K"
    assert formatta_fiches(-223958) == "-224K"


def test_milioni_e_miliardi():
    assert formatta_fiches(1_000_000) == "1M"
    assert formatta_fiches(1_234_567) == "1.23M"
    assert formatta_fiches(2_500_000) == "2.50M"
    assert formatta_fiches(2_500_000_000) == "2.50B"


def test_valori_non_numerici():
    assert formatta_fiches("tanti") == "0"
    assert formatta_fiches(None) == "0"


def test_bilancio_con_il_segno():
    assert formatta_bilancio(28) == "+28"
    assert formatta_bilancio(0) == "+0"
    assert formatta_bilancio(-100) == "-100"
    assert formatta_bilancio(28636) == "+28.6K"
