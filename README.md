# Poker Machine - ottobre 2024.

## Descrizione

La **Poker Machine** è un'applicazione testuale in Python che simula un gioco di video poker. Il giocatore inizia con un certo numero di fiches e può continuare a giocare fino a esaurirle o uscire volontariamente. Durante ogni mano, il giocatore può piazzare una puntata, ricevere cinque carte, decidere quali mantenere o cambiare, e infine ottenere un punteggio basato sulla mano finale. Il gioco tiene traccia delle vittorie, delle sconfitte e delle mani giocate.

Il mazzo di carte viene gestito tramite una classe personalizzata, `Mazzo`, che implementa tutte le operazioni di gestione delle carte, compreso il mescolamento, la pesca e la reintegrazione degli scarti.

## Funzionalità

- **Gestione delle carte**:
  - Un mazzo di carte francesi (con o senza jolly).
  - Rimozione delle carte basse (2, 3, 4, 5) per mantenere il gioco più orientato al poker.
  - Possibilità di reintegrare gli scarti quando le carte stanno per finire.
  - Mescolamento del mazzo solo quando necessario (inizio partita o reintegrazione degli scarti).

- **Interazione con il giocatore**:
  - Il giocatore può piazzare una puntata e scegliere quali carte mantenere o cambiare.
  - Il programma calcola automaticamente il punteggio della mano finale e assegna le fiches in base alla vincita.
  
- **Gestione dei dati**:
  - Il gioco tiene traccia del numero di fiches guadagnate e perse, delle mani giocate e dei punteggi realizzati.
  - Viene anche registrata la vincita e la perdita massima, insieme alla data di ciascun evento.

## Requisiti

Per eseguire la **Poker Machine**, è necessario avere installato Python 3.6+ sul proprio sistema e procurarsi, nel caso eseguiate i sorgenti in python, la mia utility GBUtils che trovate qui su github, fra i miei progetti. GBUtils contiene la classe Mazzo usata in pokermachine. Salvate GBUtils nella stessa cartella di pokermachine.py E' anche possibile scaricare l'eseguibile compilato per Windows che trovate nella cartella dist di questo progetto.

## Istruzioni per l'installazione e l'uso

1. **Clonare il repository**:

   ```bash
   git clone https://github.com/gabrielebattaglia/poker-machine.git
   ```

2. **Accedere alla directory del progetto**:

   ```bash
   cd poker-machine
   ```

3. **Eseguire il programma**:

   Esegui il programma direttamente dal terminale:

   ```bash
   python pokermachine.py
   ```

4. **Giocare**:

   - Inserisci la tua puntata o premi Enter per uscire.
   - Scegli quali carte mantenere inserendo i numeri delle carte (senza spazi) o premi Enter per sostituirle tutte.
   - Continua a giocare fino a esaurire le fiches o fino a quando desideri uscire.

## Regole del Gioco

- Il gioco segue le regole standard del video poker.
- I punteggi possibili sono:
  - **Scala Reale**
  - **Scala a Colore**
  - **Poker**
  - **Full**
  - **Colore**
  - **Scala**
  - **Tris**
  - **Doppia Coppia**
  - **Coppia Pagata**
  - **Coppia Non Pagata**
  - **Carta Alta**
  
  Ogni combinazione assegna una vincita differente in base alla puntata.

## Struttura del Progetto

- `pokermachine.py`: Il file principale che contiene il loop di gioco e tutte le interazioni con il giocatore.
- `GBUtils - Mazzo`: La classe `Mazzo`, che gestisce le operazioni sul mazzo di carte.
- `pokermachine_data.pkl`: Un file di dati che memorizza lo stato del gioco tra una sessione e l'altra (viene creato automaticamente).
  
## Come Funziona

1. **Creazione del Mazzo**: All'inizio del gioco, viene creato un mazzo con 52 carte (senza jolly) e vengono rimosse le carte di valore basso (2, 3, 4, 5).
   
2. **Gioco**: In ogni mano, puoi piazzare una puntata e ricevere 5 carte. Puoi scegliere di mantenerne alcune o cambiarle.
   
3. **Calcolo del Punteggio**: Alla fine di ogni mano, il punteggio viene calcolato in base alla mano finale, e ti verranno assegnate o tolte fiches a seconda della vincita o della perdita.

4. **Rimescolamento degli Scarti**: Se le carte nel mazzo stanno per finire, gli scarti vengono reintegrati nel mazzo e il mazzo viene rimescolato.

5. **Salvataggio dei Dati**: I dati di gioco vengono salvati automaticamente in un file per tenere traccia delle tue partite.

## Licenza

Questo progetto è rilasciato sotto la licenza MIT. Consulta il file `LICENSE` per maggiori dettagli.

---

### Autore

Sviluppato da **Gabriele Battaglia** e **ChatGPT-o1**.
