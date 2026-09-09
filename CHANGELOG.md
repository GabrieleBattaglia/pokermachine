# Changelog - PokerMachine

Tutti i cambiamenti e le novità introdotte nelle versioni di PokerMachine.
Il changelog nasce con la versione 4.0.0. Per le versioni precedenti il resoconto sta nella cronologia dei commit su GitHub.

## [4.0.0] - 2026-09-09

Revisione 1 del refactoring generale del parco software. La contabilità del gioco, che era rotta in tre punti, torna giusta; ogni evento ha un suono; il programma parla senza decorazioni.

### Aggiunto
- **Un suono per ogni cosa.** Ventisei preset nuovi della famiglia pokermachine nella collezione condivisa Acu_Collection.json, più quattro già esistenti. Ognuno dei dodici punteggi ha il suo jingle, che cresce di lunghezza e di ricchezza con il valore della mano: due note gravi per la carta alta, due note uguali per il pareggio della coppia pagata, una scala musicale per la scala, la stessa nota su tre ottave per il colore, e tre secondi di fanfara per la scala reale. Hanno il loro suono anche la Killer Hand in arrivo, il suo bonus e la sua penalità, i tre record, il traguardo di cento mani, le soglie di fiches, il game over, la puntata, la distribuzione, lo scarto, il rimescolamento del mazzo, l'avvio e la chiusura.
- **Traguardi e soglie.** Ogni cento mani senza fallimenti il gioco lo annuncia. La prima volta che le fiches superano mille, diecimila, centomila e un milione dall'ultimo fallimento, anche.
- **Il primato annunciato quando si supera.** Fino alla 3.1.1 il record di mani senza fallimenti non contava la mano del fallimento e veniva annunciato quasi solo quando era pareggiato: ora si aggiorna a ogni mano e si sente nel momento in cui viene battuto.
- **La guida.** Il punto di domanda, al prompt della puntata, apre il manuale a pagine. È il file manuale.txt, che viaggia anche dentro l'eseguibile.
- **Le statistiche durante il gioco**, con r al prompt della puntata. Hanno anche il bilancio di sempre e, per ogni punteggio, la percentuale sulle mani giocate.
- **Controllo degli aggiornamenti** all'avvio del programma compilato, con gestisci_aggiornamento di GBUtils, come negli altri programmi del parco.
- **Prove automatiche** in tests, settantasette, su regole, contabilità della mano, salvataggio, formato e lettura dei numeri, prompt della puntata con tutte le scorciatoie, e una sessione intera senza console.
- I file per compilare e distribuire: pokermachine.spec, con la collezione dei suoni e la guida dentro l'eseguibile, e zip_maker.py aggiornato. Il ruff.toml con la configurazione del validatore, e requirements.txt.

### Corretto
- **Il bonus della Killer Hand arriva davvero.** Fino alla 3.1.1 la vincita triplicata veniva annunciata e contata fra le fiches guadagnate di sempre, ma il saldo riceveva solo la vincita normale. Ora il bonus entra nel gruzzolo.
- **I fallimenti contavano doppio.** Il game over contava il fallimento e lasciava il saldo a zero, e al lancio successivo il saldo a zero faceva contare un secondo fallimento, con la data sbagliata. Ora il game over riassegna subito le duecento fiches, e un salvataggio della versione 3 chiuso con il game over viene riconosciuto e non conta di nuovo. I numeri già accumulati restano come sono.
- **La partita non si chiude più alla mano centocinque.** Le carte della mano finale non tornavano mai nel mazzo, che si esauriva, e il gioco si chiudeva con un messaggio di errore. Ora la mano finale torna fra gli scarti e il mazzo si rimescola da solo quando serve, dicendolo.
- **La penalità della Killer Hand si calcola sulle fiches con cui si entra nella mano**, puntata compresa, e il messaggio dice su quale importo. Fino alla 3.1.1 si calcolava su ciò che restava dopo la puntata, quindi valeva meno di quanto annunciato.
- **Il numero delle Killer Hand cresce solo quando la mano viene giocata.** Chi usciva sul prompt di una Killer Hand e rientrava la ritrovava con la penalità aumentata.
- Un carattere che sembra una cifra ma non lo è non chiude più il programma con una traccia di errore: gli ingressi passano da dgt di GBUtils e vengono controllati cifra per cifra.

### Modificato
- **Il salvataggio è JSON**, pokermachine_data.json, accanto al programma e non nella cartella da cui lo si lancia. Si scrive su file temporaneo con sostituzione atomica e copia di riserva .bak; se il file si rompe si riparte dalla riserva e lo si dice; ogni campo viene controllato al caricamento. Il vecchio pokermachine_data.pkl viene convertito al primo avvio e rinominato con l'estensione .migrato.
- **Niente decorazioni.** Spariti gli asterischi, gli uguali e i trattini ripetuti che lo screen reader leggeva uno per uno a ogni Killer Hand e a ogni game over. Le frasi sono corte, una per riga, senza righe vuote.
- **Prompt corti per il display braille.** Il prompt della puntata sta in trenta caratteri, con una lettera per ogni numero: F 428 S 110 R 399 M 1, cioè fiches, serie, record e mano della sessione. Le carte si chiedono con la mano in forma breve seguita da tieni?, per esempio QC 9Q JQ 6F 8F tieni?, così restano dieci celle per scrivere.
- **Fiches con i prefissi K e M**, come in Terminal Beast: 3.52K sono 3520 fiches, 195K centonovantacinquemila, 1.23M un milione e duecentotrentamila. La forma compatta vale nel prompt, nei messaggi e nelle statistiche; i conteggi di mani e di punteggi restano esatti. Anche la puntata si può scrivere così: 1k, 1.5k o 1,5k, 2m.
- **Le scorciatoie di puntata** restano quelle di sempre, verificate una per una dalle prove automatiche: trattino il dieci per cento, virgola il venticinque, punto il cinquanta, punto e virgola il settantacinque, più tutto, m il minimo. Un simbolo diverso viene rifiutato con il suono di errore e la frase che elenca le possibilità.
- **La puntata sotto il minimo viene alzata al minimo** in ogni caso, anche con le scorciatoie, invece di essere rifiutata quando valeva zero.
- Il codice è diviso in moduli: regole, dati, partita, suoni e version, con il programma principale che tiene solo il dialogo con chi gioca. La tabella dei punteggi è scritta in un posto solo e da lei discendono l'ordine delle statistiche e la struttura del salvataggio. La versione e la data di rilascio stanno in version.py.
- Il README descrive il gioco com'è: la puntata minima è il tre per cento, non il dieci, e la Killer Hand c'è.
- L'eseguibile compilato e il salvataggio pickle escono dal repository. Il salvataggio JSON resta tracciato, per portarlo fra le macchine.
- Tutti i moduli portano l'intestazione con gli autori nel formato del parco software, e il codice passa il validatore ruff.
