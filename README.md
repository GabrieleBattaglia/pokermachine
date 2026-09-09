# PokerMachine

Un video poker a fiches da riga di comando. Si punta, si ricevono cinque carte da un mazzo di dieci confezioni, si sceglie quali tenere e la mano finale paga secondo la tabella dei punteggi, dalla coppia pagata alla scala reale. Ogni venticinque mani arriva la Killer Hand, che triplica la vincita netta o toglie una percentuale crescente delle fiches. Lo scopo è durare più a lungo possibile senza esaurire le fiches, battendo il proprio primato di mani.

È pensato per chi usa uno screen reader e il display braille: ogni cosa viene detta a parole, ogni evento ha un suono, con un jingle diverso per ciascuno dei dodici punteggi, e il prompt di gioco sta in una riga corta.

La guida completa è in `manuale.txt`, e si apre durante il gioco con il punto di domanda. Le novità di ogni versione sono in `CHANGELOG.md`.

## Avvio dal sorgente

Serve Python 3 con i pacchetti di `requirements.txt` e la libreria condivisa GBUtils, raggiungibile da Python, con accanto la sua collezione dei suoni `Acu_Collection.json`.

```bash
python pokermachine.py
```

## Il salvataggio

Il gruzzolo e le statistiche di sempre stanno in `pokermachine_data.json`, accanto al programma, scritto dopo ogni mano con una copia di riserva. Il salvataggio della versione 3, in formato pickle, viene convertito al primo avvio.

## Strumenti

- `tests` contiene le prove automatiche, da lanciare con `python -m pytest tests`.
- `ascolta_suoni.py` fa sentire uno per uno i suoni del gioco, con il nome dell'evento e la descrizione del preset.
- `pokermachine.spec` e `zip_maker.py` compilano e impacchettano la release.

Autori: Gabriele Battaglia (IZ4APU) & ClaudIA. Concepito il 2 ottobre 2024 con ChatGPT o1.
