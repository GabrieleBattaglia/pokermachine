# PokerMachine

Un video poker a fiches da riga di comando. Si punta, si ricevono cinque carte da un mazzo di dieci confezioni, si sceglie quali tenere e la mano finale paga secondo la tabella dei punteggi, dalla coppia alle cinque carte gemelle, identiche anche nel seme, che con dieci mazzi possono capitare. Ogni venticinque mani arriva la Killer Hand, una gara contro una puntata minima che cresce sempre più in fretta, con una regola a sorpresa e gli scudi che salvano la puntata. Lo scopo è durare più a lungo possibile senza esaurire le fiches, battendo il proprio primato di mani.

Al prompt delle carte un tasto dà il consiglio, calcolato in modo esatto sul mazzo vero; dopo una vincita si può raddoppiare; ci sono un montepremi, tre sfide per ogni serie e ventidue trofei da conquistare.

È pensato per chi usa uno screen reader e il display braille: ogni cosa viene detta a parole, ogni evento ha un suono, con un jingle diverso per ciascuno dei venti punteggi, e i prompt di gioco stanno in una riga corta.

La guida completa è in `manuale.txt`, e si apre durante il gioco con il punto di domanda. Le novità di ogni versione sono in `CHANGELOG.md`.

## Avvio dal sorgente

Serve Python 3 con i pacchetti di `requirements.txt` e la libreria condivisa GBUtils, raggiungibile da Python, con accanto la sua collezione dei suoni `Acu_Collection.json`.

```bash
python pokermachine.py
```

## Il salvataggio

Il gruzzolo e le statistiche di sempre stanno in `pokermachine_data.json`, accanto al programma, scritto dopo ogni mano con una copia di riserva. I salvataggi delle versioni precedenti si leggono senza perdere niente.

## Strumenti

- `tests` contiene le prove automatiche, da lanciare con `python -m pytest tests`.
- `ascolta_suoni.py` fa sentire uno per uno i suoni del gioco, con il nome dell'evento e la descrizione del preset; con l'argomento `nuovi` solo quelli della versione 5.
- `taratura` contiene gli strumenti che tarano tabella e Killer Hand con la strategia ottima. `dati_tenute.py` calcola le probabilità esatte delle tenute su un campione di mani e le salva, circa un gigabyte, in `E:\git\tmp\pokermachine_taratura`; `taratura.py` ed `esplora.py` sono le librerie che valutano una proposta e simulano migliaia di serie; `conferma.py` rilancia il tutto con la tabella e la gara scritte in `regole.py`. Ogni ritocco alla tabella o alla Killer Hand va provato lì prima di entrare nel gioco.
- `pokermachine.spec` e `zip_maker.py` compilano e impacchettano la release.

Autori: Gabriele Battaglia (IZ4APU) & ClaudIA. Concepito il 2 ottobre 2024 con ChatGPT o1.
