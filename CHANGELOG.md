# Changelog - PokerMachine

Tutti i cambiamenti e le novità introdotte nelle versioni di PokerMachine.
Il changelog nasce con la versione 4.0.0. Per le versioni precedenti il resoconto sta nella cronologia dei commit su GitHub.

## [5.0.0] - 2026-09-24

La versione 5 ripensa l'equilibrio del gioco. Con dieci mazzi la tabella della 4.0.1 restituiva in media 1,66 fiches per ogni fiche puntata, e con la strategia migliore quasi 1,7: chi puntava con giudizio non perdeva mai, e l'intera partita la decideva la Killer Hand, che era una tassa più che una scelta. Adesso la tabella è più moderata e la Killer Hand è una gara, e per durare conta come si punta. Il piano sta nella issue 3, le tappe nelle issue dalla 4 alla 11.

### Aggiunto
- **Le categorie dei dieci mazzi.** Con dieci mazzi ogni carta esiste in dieci copie, e due carte possono essere identiche anche nel seme: sono le carte gemelle. Arrivano la Coppia gemella, la Coppia gemella pagata, il Tris gemello, il Poker gemello e le Cinque gemelle; il Poker si divide per valore: nascono il Poker d'assi e il Poker dal 2 al 4, e il Poker resta quello dal cinque al re; e c'è il Full a colore, tris e coppia tutti dello stesso seme. I punteggi passano da dodici a venti, ciascuno con il suo suono; quelli gemelli suonano allo specchio, una nota a sinistra e la sua gemella a destra.
- **La mano paga la combinazione migliore che contiene.** Un Colore con dentro tre carte gemelle, o un Full il cui tris è gemello, paga ciò che vale di più, come in tutti i video poker.
- **La Killer Hand come gara.** Ogni venticinque mani la Killer Hand chiede una puntata minima che raddoppia a ogni gara: 4 fiches alla prima, 8 alla seconda, 1024 alla nona. Chi ne ha meno punta tutto. Il gruzzolo di chi gioca al meglio cresce al massimo di 1,67 volte ogni venticinque mani, meno del doppio: nessuna serie scappa per sempre, ma nelle simulazioni chi punta con giudizio dura quasi il doppio di chi punta sempre il minimo, circa 500 mani contro 300 di mediana. La vincita netta si moltiplica ancora per tre.
- **Le regole a sorpresa.** A ogni Killer Hand, prima della puntata, il gioco estrae e annuncia una regola: nessuna sorpresa; nessun cambio, con la mano servita che è quella finale; coppie mute, in cui le coppie non pagano; tutto o niente, con la vincita netta per cinque ma il pareggio che perde. Chi esce e rientra la ritrova uguale.
- **Gli scudi.** Uno scudo restituisce la puntata di una Killer Hand persa. Se ne tengono al massimo tre; arrivano dalle mani rarissime e dalle sfide. Il prompt della puntata li mostra con la lettera D.
- **Il consiglio.** Al prompt delle carte la lettera c dice la tenuta migliore, calcolata in modo esatto su tutte le carte che possono arrivare dal mazzo com'è in quel momento, con la tabella in vigore, la Killer Hand, la sorpresa, gli scudi e il montepremi. Dopo ogni mano, se la tenuta scelta non era la migliore, il gioco dice quante fiches in media rendeva di più, e le statistiche contano la precisione. Il motore del calcolo è stato verificato sul Jacks or Better a un mazzo, dove dà il ritorno teorico noto del 99,5439 per cento.
- **Il raddoppio.** Dopo ogni vincita si può giocare quanto è appena tornato indietro: rosso o nero raddoppia la posta, il seme giusto la quadruplica, altrimenti la posta è persa. Le scommesse sono eque, fino a cinque di fila.
- **Il montepremi.** L'uno per cento di ogni puntata va in un premio pagato dalla macchina, che resta salvato fra le sessioni e dopo il game over e si vince con le mani rarissime e con il Poker d'assi, circa una mano ogni 460. Il gioco lo ricorda all'avvio, a ogni Killer Hand e nelle statistiche, e annuncia con un suono quando supera mille, diecimila, centomila e un milione di fiches.
- **La tenuta proposta nel prompt.** Il prompt delle carte propone la tenuta migliore dopo la parola tieni, per esempio 6F 8F 9Q JQ QC tieni 45?, e invio da solo la accetta. Lo zero cambia tutte le carte.
- **La mano servita annunciata**, per esempio Servita: Coppia pagata, di jack, e le carte appena arrivate segnate con la parola nuova nella mano finale.
- **Statistiche nuove**: il ritorno personale, cioè le fiches tornate ogni cento puntate, il bilancio delle Killer Hand e le ultime dieci serie.
- **Le sfide.** All'inizio di ogni serie il gioco estrae tre sfide; ciascuna superata regala uno scudo.
- **I trofei.** Ventidue traguardi da conquistare una volta sola, ciascuno con il suo annuncio e il suo suono; la lettera t al prompt della puntata li elenca.
- Cinquantadue suoni nuovi della famiglia pokermachine nella collezione condivisa Acu_Collection.json, e ascolta_suoni.py che con l'argomento nuovi fa sentire solo quelli. Ogni evento ha il suo suono e nessuno si ripete: una prova automatica controlla che due eventi non condividano un preset, né per nome né per contenuto.
- La cartella taratura, con gli strumenti che hanno tarato tabella e Killer Hand con la strategia ottima: servono a rifare i conti prima di ogni ritocco.

### Modificato
- **La tabella dei punteggi.** Tarata con il motore della strategia ottima e con migliaia di serie simulate, rende il 128,6 per cento, e il montepremi aggiunge circa un punto. Restano come prima Coppia pagata 1, Doppia coppia 2, Super Poker 40, Scala a colore 55 e Scala Reale 250. Cambiano il Tris, da 3 a 2, il Full da 9 a 4, il Colore da 6 a 4 e il Poker, che si divide: 25 quello d'assi, 10 dal 2 al 4, 6 dal 5 al re. La Scala sale da 4 a 6, perché con dieci mazzi è più rara di full e colore. Le gemelle: Coppia gemella 1, Coppia gemella pagata 2, Tris gemello 6, Poker gemello 50, Cinque gemelle 2500; il Full a colore 55.
- **Le statistiche** hanno gli scudi, il montepremi, la precisione delle tenute, i raddoppi, i trofei e le sfide in corso. Le mani pagate si contano con un contatore loro, perché con la sorpresa delle coppie mute una coppia può pagare zero.
- Il salvataggio passa al formato 2. Un salvataggio della versione 4 si legge senza perdere niente: i conteggi dei punteggi restano nelle categorie dove sono stati fatti, e le novità partono da zero.
- **La guida e l'elenco dei trofei** non suonano più come le statistiche, e il rimescolamento degli scarti non suona più come il mazzo mescolato all'inizio.
- **Le carte in ordine di valore**, dal due all'asso, invece che per seme: coppie, tris e gemelle stanno vicine.
- **Il prompt della puntata** tiene le lettere attaccate ai numeri, F428 S110 R399 M1, e così resta nelle trenta celle anche con milioni di fiches e serie lunghe.
- **Invio al prompt delle carte** accetta la tenuta proposta; per cambiare tutte le carte si scrive zero.
- La guida è riscritta per la versione 5, un paragrafo per riga.

### Tolto
- **La penalità della Killer Hand.** Non serve più: la minaccia è il minimo della gara. Con lei sparisce la falla per cui puntare tutto in una Killer Hand annullava la penalità.

## [4.0.1] - 2026-09-12

I percorsi dei file passano da GBUtils, che dalla V138 li offre a tutti con cartella_applicazione e percorso_risorsa: la logica che dice dove stanno i dati e le risorse era riscritta in dieci progetti, e adesso e' scritta in un posto solo. Il comportamento non cambia, tranne che una risorsa che nel pacchetto non c'e' viene ora cercata anche accanto all'eseguibile.

## [4.0.0] - 2026-09-09

Pubblicata su GitHub il 9 settembre 2026 come release `v4.0.0`, con il solo archivio `pokermachine.zip` in allegato.

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
