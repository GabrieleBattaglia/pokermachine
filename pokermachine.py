# POKERMACHINE - Data di concepimento 2 ottobre 2024

import pickle
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import Counter
from GBUtils	import Mazzo
# --- Costanti Globali ---
NUM_MAZZI = 10 # Numero di mazzi standard da 52 carte usati
CARTE_PER_MANO = 5
# Soglia sotto la quale ricostruire e rimescolare tutto (5 iniziali + 5 sostituzioni = 10)
# Usiamo un margine di sicurezza
SOGLIA_RIMESCOLAMENTO_TOTALE = 15
KILLER_HAND_FREQUENZA = 25
PERCENTUALE_MINIMA_PUNTATA = 0.03 # 3%
MAX_PENALITA_KH = 90 # Penalità massima in % per perdita Killer Hand
VERSIONE = "3.1.0 del 9 aprile 2025"
FILE_DATI = 'pokermachine_data.pkl'
# Costanti per i valori delle carte (per chiarezza in valuta_mano)
VALORE_JACK = 11
VALORE_REGINA = 12
VALORE_RE = 13
VALORE_ASSO = 14 # Usiamo 14 per confronti, 1 per sequenza A-5

def carica_dati():
	try:
		with open(FILE_DATI, 'rb') as f:
			dati = pickle.load(f)
			# Incrementa lanci all'avvio
			dati['launches'] = dati.get('launches', 0) + 1
			# Assicura che tutte le chiavi esistano (per compatibilità con vecchi save)
			dati.setdefault('mani_giocate', 0)
			dati.setdefault('data_ultimo_fallimento', None)
			dati.setdefault('record_mani_senza_fallimenti', 0)
			dati.setdefault('mani_dall_ultimo_fallimento', 0)
			dati.setdefault('fiches_guadagnate', 0)
			dati.setdefault('fiches_perdute', 0)
			dati.setdefault('fiches_attuali', 200) # Default se non presente
			dati.setdefault('fallimenti', 0)
			dati.setdefault('killer_hand_count', 0)
			dati.setdefault('punteggi', {
				"Carta alta": {'conteggio': 0, 'ultima_realizzazione': None},
				"Coppia non pagata": {'conteggio': 0, 'ultima_realizzazione': None},
				"Coppia pagata": {'conteggio': 0, 'ultima_realizzazione': None},
				"Doppia coppia": {'conteggio': 0, 'ultima_realizzazione': None},
				"Tris": {'conteggio': 0, 'ultima_realizzazione': None},
				"Scala": {'conteggio': 0, 'ultima_realizzazione': None},
				"Colore": {'conteggio': 0, 'ultima_realizzazione': None},
				"Full": {'conteggio': 0, 'ultima_realizzazione': None},
				"Poker": {'conteggio': 0, 'ultima_realizzazione': None},
				"Super Poker": {'conteggio': 0, 'ultima_realizzazione': None},
				"Scala a colore": {'conteggio': 0, 'ultima_realizzazione': None},
				"Scala Reale": {'conteggio': 0, 'ultima_realizzazione': None}
			})
			dati.setdefault('vincita_massima', 0)
			dati.setdefault('data_vincita_massima', None)
			dati.setdefault('perdita_massima', 0)
			dati.setdefault('data_perdita_massima', None)
			dati.setdefault('data_ultima_giocata', None)
			# Aggiusta la struttura punteggi se mancano chiavi (es. Super Poker)
			punteggi_default = {
				"Carta alta": {'conteggio': 0, 'ultima_realizzazione': None},
				"Coppia non pagata": {'conteggio': 0, 'ultima_realizzazione': None},
				"Coppia pagata": {'conteggio': 0, 'ultima_realizzazione': None},
				"Doppia coppia": {'conteggio': 0, 'ultima_realizzazione': None},
				"Tris": {'conteggio': 0, 'ultima_realizzazione': None},
				"Scala": {'conteggio': 0, 'ultima_realizzazione': None},
				"Colore": {'conteggio': 0, 'ultima_realizzazione': None},
				"Full": {'conteggio': 0, 'ultima_realizzazione': None},
				"Poker": {'conteggio': 0, 'ultima_realizzazione': None},
				"Super Poker": {'conteggio': 0, 'ultima_realizzazione': None},
				"Scala a colore": {'conteggio': 0, 'ultima_realizzazione': None},
				"Scala Reale": {'conteggio': 0, 'ultima_realizzazione': None}
			}
			for key, value in punteggi_default.items():
				dati['punteggi'].setdefault(key, value)

	except FileNotFoundError:
		# Se il file non esiste, crea la struttura dati da zero
		dati = {
			'launches': 1,
			'mani_giocate': 0,
			'data_ultimo_fallimento': None,
			'record_mani_senza_fallimenti': 0,
			'mani_dall_ultimo_fallimento': 0,
			'fiches_guadagnate': 0,
			'fiches_perdute': 0,
			'fiches_attuali': 200,
			'fallimenti': 0,
			'killer_hand_count': 0,
			'punteggi': {
				"Carta alta": {'conteggio': 0, 'ultima_realizzazione': None},
				"Coppia non pagata": {'conteggio': 0, 'ultima_realizzazione': None},
				"Coppia pagata": {'conteggio': 0, 'ultima_realizzazione': None},
				"Doppia coppia": {'conteggio': 0, 'ultima_realizzazione': None},
				"Tris": {'conteggio': 0, 'ultima_realizzazione': None},
				"Scala": {'conteggio': 0, 'ultima_realizzazione': None},
				"Colore": {'conteggio': 0, 'ultima_realizzazione': None},
				"Full": {'conteggio': 0, 'ultima_realizzazione': None},
				"Poker": {'conteggio': 0, 'ultima_realizzazione': None},
				"Super Poker": {'conteggio': 0, 'ultima_realizzazione': None}, # 5 carte uguali
				"Scala a colore": {'conteggio': 0, 'ultima_realizzazione': None},
				"Scala Reale": {'conteggio': 0, 'ultima_realizzazione': None}
			},
			'vincita_massima': 0,
			'data_vincita_massima': None,
			'perdita_massima': 0,
			'data_perdita_massima': None,
			'data_ultima_giocata': None
		}
	# Logica di refill se le fiches sono esaurite al caricamento
	if dati.get('fiches_attuali', 0) <= 0:
		print("Le fiches erano esaurite. Ricevi 200 fiches per ricominciare.")
		dati['fiches_attuali'] = 200
		# NON si diminuiscono le perdite totali -> rimossa dati['fiches_perdute'] -= 200
		dati['fallimenti'] = dati.get('fallimenti', 0) + 1
		dati['mani_dall_ultimo_fallimento'] = 0
		# Resetta anche il conteggio KH all'inizio di una nuova "vita"
		dati['killer_hand_count'] = 0
		# Aggiorna la data dell'ultimo fallimento se non è già impostata per questa sessione
		# (potrebbe essere già fallito e aver chiuso senza salvare)
		dati['data_ultimo_fallimento'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	return dati

def salva_dati(dati):
	try:
		with open(FILE_DATI, 'wb') as f:
			pickle.dump(dati, f)
	except IOError as e:
		print(f"Errore durante il salvataggio dei dati: {e}")

def formatta_tempo_trascorso(data_evento_str):
	if not data_evento_str:
		return "Mai"
	try:
		ora = datetime.now()
		data_evento = datetime.strptime(data_evento_str, "%Y-%m-%d %H:%M:%S")
		diff = relativedelta(ora, data_evento)
		parts = []
		# Aggiunge anni se presenti
		if diff.years > 0:
			parts.append(f"{diff.years} ann{'i' if diff.years > 1 else 'o'}")
		# Aggiunge mesi se presenti
		if diff.months > 0:
			parts.append(f"{diff.months} mes{'i' if diff.months > 1 else 'e'}")
		# Aggiunge giorni se presenti (indipendentemente da anni/mesi)
		if diff.days > 0:
			parts.append(f"{diff.days} giorn{'i' if diff.days > 1 else 'o'}")

		# Gestisce il caso in cui l'evento sia avvenuto oggi o ieri
		if not parts:
			if ora.date() == data_evento.date():
				# Potrebbe essere più preciso e mostrare ore/minuti se la differenza è piccola
				# Calcola la differenza in secondi
				diff_secondi = (ora - data_evento).total_seconds()
				if diff_secondi < 60:
					return "Pochi istanti fa"
				elif diff_secondi < 3600:
					minuti = int(diff_secondi // 60)
					return f"{minuti} minut{'i' if minuti > 1 else 'o'} fa"
				else:
					ore = int(diff_secondi // 3600)
					return f"{ore} or{'e' if ore > 1 else 'a'} fa" # Più preciso di "Oggi"
			elif (ora.date() - data_evento.date()).days == 1:
				return "Ieri"
			else: # Caso strano, data futura? O errore?
				return "Data non gestita"
		# Se ci sono parti (anni/mesi/giorni), costruisce la stringa
		return ", ".join(parts) + " fa"
	except ValueError:
		return "Data non valida"
	except Exception as e: # Cattura altri possibili errori
		print(f"Errore in formatta_tempo_trascorso: {e}")
		return "Errore data"
def mostra_report(dati):
	print("\n== Report Statistiche ==")
	print(f"Lanci dell'applicazione: {dati.get('launches', 'N/A')}")
	print(f"Mani giocate totali: {dati['mani_giocate']}")
	print(f"Mani dall'ultimo fallimento: {dati['mani_dall_ultimo_fallimento']}")
	if dati['data_ultimo_fallimento']:
		print(f"Ultimo fallimento: {formatta_tempo_trascorso(dati['data_ultimo_fallimento'])}")
	print(f"Record mani senza fallimenti: {dati['record_mani_senza_fallimenti']}")
	print(f"Fallimenti (fiches esaurite): {dati['fallimenti']}")
	print(f"Fiches totali guadagnate: {dati['fiches_guadagnate']}")
	print(f"Fiches totali perdute: {dati['fiches_perdute']}")
	print(f"Fiches attuali: {dati['fiches_attuali']}")
	if dati['vincita_massima']:
		print(f"Vincita massima in una mano: {dati['vincita_massima']} ({formatta_tempo_trascorso(dati['data_vincita_massima'])})")
	if dati['perdita_massima']:
		print(f"Perdita massima in una mano: {dati['perdita_massima']} ({formatta_tempo_trascorso(dati['data_perdita_massima'])})")
	if dati['data_ultima_giocata']:
		print(f"Ultima giocata: {formatta_tempo_trascorso(dati['data_ultima_giocata'])}")
	mani_totali = dati['mani_giocate']
	if mani_totali > 0:
		# Elenca i nomi dei punteggi considerati "vincenti" (che pagano almeno la puntata)
		punteggi_vincenti_keys = [
			"Coppia pagata", "Doppia coppia", "Tris", "Scala",
			"Colore", "Full", "Poker", "Super Poker",
			"Scala a colore", "Scala Reale"
		]
		# Somma i conteggi per questi punteggi
		mani_vincenti_conteggio = sum(dati['punteggi'].get(key, {}).get('conteggio', 0) for key in punteggi_vincenti_keys)
		# Calcola la percentuale
		percentuale_vincenti = (mani_vincenti_conteggio / mani_totali) * 100
		print(f"Percentuale mani pagate (Coppia Pagata+): {percentuale_vincenti:.2f}% ({mani_vincenti_conteggio} su {mani_totali})")
	else:
		print("Percentuale mani pagate (Coppia Pagata+): N/A (nessuna mano giocata)")
	print("\n== Tabella dei Punteggi Realizzati ==")
	# Ordina per una qualche logica, es. per vincita decrescente o per nome
	punteggi_ordinati = sorted(dati['punteggi'].items(), key=lambda item: calcola_vincita(item[0], 1), reverse=True)
	for punteggio, info in punteggi_ordinati:
		conteggio = info['conteggio']
		if conteggio > 0:
			tempo_trascorso = formatta_tempo_trascorso(info['ultima_realizzazione'])
			print(f"- {punteggio}: {conteggio} volte (Ultima: {tempo_trascorso})")
		else:
			print(f"- {punteggio}: Mai realizzato")
	print("==========================")

def valuta_mano(mano: list): # Accetta list[Mazzo.Carta]
	if not mano or len(mano) != CARTE_PER_MANO:
		return "Mano non valida" # Controllo di sicurezza
	# Estrai valori e semi usando la nuova struttura Carta
	# Gestisce Asso come 14 per confronti e 1 per scale A-5
	valori_numerici = sorted([c.valore if c.valore != 1 else VALORE_ASSO for c in mano], reverse=True)
	valori_numerici_per_scala = sorted(list(set(
		[c.valore for c in mano if c.valore != 1] + \
		([1] if any(c.valore == 1 for c in mano) else []) + \
		([VALORE_ASSO] if any(c.valore == 1 for c in mano) else [])
	)))
	semi = [c.seme_nome for c in mano]
	# Usa Counter per efficienza e leggibilità
	conta_valori = Counter(valori_numerici) # Conta gli Assi come 14 qui
	conta_semi = Counter(semi)
	conteggi = sorted(conta_valori.values(), reverse=True)
	# Verifica Scala
	is_scala = False
	if len(valori_numerici_per_scala) >= 5:
		for i in range(len(valori_numerici_per_scala) - 4):
			# Controlla sequenza di 5 consecutivi
			if all(valori_numerici_per_scala[i+j] == valori_numerici_per_scala[i] + j for j in range(5)):
				is_scala = True
				# Controlla se è Scala Reale (10, J, Q, K, A)
				# L'asso è 14 in valori_numerici, quindi cerchiamo 10, 11, 12, 13, 14
				if set(valori_numerici_per_scala[i:i+5]) == {10, VALORE_JACK, VALORE_REGINA, VALORE_RE, VALORE_ASSO}:
					is_scala_reale_potenziale = True
				else:
					is_scala_reale_potenziale = False
				break # Trovata la scala più alta possibile
	# Verifica Colore
	is_colore = len(conta_semi) == 1 # Se c'è un solo seme, è colore

	# Valutazione gerarchica
	if is_scala and is_colore:
		if is_scala_reale_potenziale:
			return "Scala Reale"
		else:
			return "Scala a colore"
	# Super Poker (5 carte uguali - possibile con 10 mazzi)
	if conteggi[0] >= 5:
		return "Super Poker"
	if conteggi[0] == 4:
		return "Poker"
	if conteggi == [3, 2]:
		return "Full"
	if is_colore:
		return "Colore"
	if is_scala:
		return "Scala"
	if conteggi[0] == 3:
		return "Tris"
	if conteggi == [2, 2, 1]:
		return "Doppia coppia"
	if conteggi[0] == 2:
		# Trova il valore della coppia
		valore_coppia = [v for v, count in conta_valori.items() if count == 2][0]
		# Coppia pagata se Jack (11), Regina (12), Re (13), Asso (14)
		if valore_coppia >= VALORE_JACK:
			return "Coppia pagata"
		else:
			return "Coppia non pagata"
	return "Carta alta"

def calcola_vincita(punteggio, puntata):
	# Tabella vincite (multipli della puntata, 0 significa perdita della puntata)
	# Es: Coppia pagata -> 1*puntata restituita (quindi vincita netta 0)
	# Es: Doppia coppia -> 2*puntata restituita (quindi vincita netta = puntata)
	tabella_vincite = {
		"Carta alta": 0,
		"Coppia non pagata": 0,
		"Coppia pagata": 1, # Pareggio
		"Doppia coppia": 2,
		"Tris": 3,
		"Scala": 4,
		"Colore": 6,
		"Full": 9,
		"Poker": 25,
		"Super Poker": 40, # Vincita per 5 carte uguali
		"Scala a colore": 55, # Era 50, aumentato leggermente
		"Scala Reale": 250
	}
	moltiplicatore = tabella_vincite.get(punteggio, 0)
	return puntata * moltiplicatore # Ritorna l'importo totale restituito

def poker_machine():
	dati = carica_dati()
	fiches = dati['fiches_attuali']
	# Crea il mazzo multi-confezione
	print(f"Creo un mazzo con {NUM_MAZZI} confezioni (totale {52*NUM_MAZZI} carte).")
	mazzo = Mazzo(tipo_francese=True, num_mazzi=NUM_MAZZI)
	print("Mescolo il mazzo...")
	mazzo.mescola_mazzo()
	mostra_report(dati)
	print(f"\n== Benvenuto alla Poker Machine! ==")
	print(f"\tVersione {VERSIONE}")
	print(f"\tLancio App #{dati['launches']}.")
	numero_mano_sessione = 1 # Contatore mani in questa sessione
	killer_hand_count = dati['killer_hand_count'] # Contatore KH dall'ultimo fallimento
	saldo_iniziale_sessione = fiches
	while fiches > 0:
		# --- Controllo Rimescolamento Totale ---
		carte_totali_disponibili = len(mazzo.carte) + len(mazzo.scarti)
		if carte_totali_disponibili < SOGLIA_RIMESCOLAMENTO_TOTALE:
			print("\n--- Attenzione: Carte quasi esaurite! ---")
			print(f"Ricostruisco e rimescolo le {52*NUM_MAZZI} carte totali...")
			mazzo = Mazzo(tipo_francese=True, num_mazzi=NUM_MAZZI)
			mazzo.mescola_mazzo()
			print("Rimescolamento completato. Si continua a giocare!")
		# Determina se è una Killer Hand
		mani_totali_senza_fallimenti = dati['mani_dall_ultimo_fallimento'] + 1
		is_mano_speciale = (mani_totali_senza_fallimenti % KILLER_HAND_FREQUENZA == 0)
		if is_mano_speciale:
			killer_hand_count += 1
			penalita_attuale = min(killer_hand_count * 10, MAX_PENALITA_KH)
			print(f"\n*** KILLER HAND #{killer_hand_count} (Mano {mani_totali_senza_fallimenti}) ***")
			print(f"Se perdi questa mano, perdi un extra {penalita_attuale}% delle tue fiches!")
			print(f"Se vinci con un punteggio pagato, la vincita (netta) viene TRIPLICATA!")
			print("****************************************")
		# --- Input Puntata ---
		puntata_valida = False
		puntata = 0
		while not puntata_valida:
			record_mani = dati['record_mani_senza_fallimenti']
			prompt_puntata = f"\nMani: #{numero_mano_sessione}/{mani_totali_senza_fallimenti}/{record_mani} | F: {fiches}> "
			raw_puntata = input(prompt_puntata)
			# --- NUOVA GESTIONE HELP '?' ---
			if raw_puntata == '?':
				puntata_min_calcolata = max(int(fiches * PERCENTUALE_MINIMA_PUNTATA), 1)
				print("\n--- Aiuto Puntate ---")
				print("Inserisci l'importo da puntare o usa gli shortcut:")
				print(f"  m : Puntata minima ({PERCENTUALE_MINIMA_PUNTATA*100:.0f}%, attuale: {puntata_min_calcolata})")
				print("  - : 10% delle fiches")
				print("  , : 25% delle fiches")
				print("  . : 50% delle fiches")
				print("  ; : 75% delle fiches")
				print("  + : 100% delle fiches (All-in)")
				print("INVIO: Esci dal gioco")
				print("--------------------")
				continue # Richiedi nuovamente l'input
			# --- FINE GESTIONE HELP ---
			if raw_puntata == "": # Uscita volontaria
				print("\nUscita dal gioco.")
				bilancio_sessione = fiches - saldo_iniziale_sessione
				if saldo_iniziale_sessione > 0:
					percentuale_variazione = (bilancio_sessione / saldo_iniziale_sessione) * 100
				else:
					percentuale_variazione = 0
				print(f"Hai iniziato la sessione con {saldo_iniziale_sessione} fiches.")
				print(f"Concludi con {fiches} fiches (Bilancio: {bilancio_sessione:+} | Variazione: {percentuale_variazione:+.1f}%).")
				dati['fiches_attuali'] = fiches
				dati['data_ultima_giocata'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				dati['killer_hand_count'] = killer_hand_count
				salva_dati(dati)
				mostra_report(dati)
				return # Termina la funzione poker_machine
			# Gestione shortcut
			shortcut_map = {'-': 0.10, ',': 0.25, '.': 0.50, ';': 0.75, '+': 1.0}
			# --- NUOVO SHORTCUT 'm' ---
			if raw_puntata == 'm':
				puntata = max(int(fiches * PERCENTUALE_MINIMA_PUNTATA), 1)
				# Non impostare puntata_valida = True qui, lascia che la validazione sotto controlli
			# --- FINE SHORTCUT 'm' ---
			elif raw_puntata in shortcut_map:
				puntata = int(fiches * shortcut_map[raw_puntata])
			elif raw_puntata.isdigit():
				puntata = int(raw_puntata)
			else:
				print(f"Input non valido. Inserisci un numero, uno shortcut (m, -, ,, ., ;, +), '?' per aiuto o INVIO per uscire.")
				continue # Richiedi input di nuovo
			# Validazione puntata
			puntata_minima = max(int(fiches * PERCENTUALE_MINIMA_PUNTATA), 1)
			if puntata < 1:
				print("La puntata deve essere almeno 1.")
			elif puntata > fiches:
				print("Non hai abbastanza fiches per questa puntata.")
			elif puntata < puntata_minima and fiches > 1: # Non forzare se hai solo 1 fiche
				print(f"La puntata minima è {puntata_minima} ({PERCENTUALE_MINIMA_PUNTATA*100:.0f}%). Correggo.")
				puntata = puntata_minima
				puntata_valida = True
			else:
				puntata_valida = True
		print(f"Puntata: {puntata}")
		fiches -= puntata # Sottrai subito la puntata
		# --- Distribuzione e Cambio Carte ---
		print("Distribuisco le carte...")
		mano = mazzo.pesca(CARTE_PER_MANO)
		if len(mano) < CARTE_PER_MANO:
			print("ERRORE CRITICO: Non è stato possibile pescare 5 carte nonostante il controllo!")
			dati['fiches_attuali'] = fiches + puntata # Restituisce la puntata
			salva_dati(dati)
			return
		# Ordina la mano per la visualizzazione e il prompt
		mano_ordinata = sorted(mano, key=lambda c: (c.seme_id, c.valore if c.valore != 1 else VALORE_ASSO))
		print("La tua mano:")
		mano_str_display = []
		for idx, carta in enumerate(mano_ordinata):
			mano_str_display.append(f"{idx+1}: {carta.nome} ({carta.desc_breve})")
		print("\n".join(mano_str_display))
		mano_breve_prompt = " ".join([c.desc_breve for c in mano_ordinata])
		# Chiedi quali carte tenere
		while True:
			prompt_testo = f"{mano_breve_prompt} - Quali tieni? "
			mantenere_input = input(prompt_testo)
			indici_mantenere_validi = True
			indici_mantenere = set()
			if mantenere_input == "": # Cambia tutte
				break
			if not mantenere_input.isdigit():
				print("Input non valido. Inserisci solo i numeri delle carte da tenere (es. 125).")
				indici_mantenere_validi = False
			else:
				for char_idx in mantenere_input:
					idx = int(char_idx)
					if 1 <= idx <= CARTE_PER_MANO:
						indici_mantenere.add(idx - 1)
					else:
						print(f"Numero carta non valido: {idx}. Inserisci numeri da 1 a {CARTE_PER_MANO}.")
						indici_mantenere_validi = False
						break
				if indici_mantenere_validi:
					break
		# Ricostruzione basata su mano_ordinata e indici selezionati
		carte_da_mantenere = []
		carte_da_sostituire = []
		for i, carta in enumerate(mano_ordinata):
			if i in indici_mantenere:
				carte_da_mantenere.append(carta)
			else:
				carte_da_sostituire.append(carta)
		num_da_sostituire = len(carte_da_sostituire)
		if num_da_sostituire > 0:
			print(f"Scarto {num_da_sostituire} carte.")
			mazzo.scarta_carte(carte_da_sostituire)
			nuove_carte = mazzo.pesca(num_da_sostituire)
			if len(nuove_carte) < num_da_sostituire:
				print("ERRORE CRITICO: Non è stato possibile pescare le carte sostitutive!")
				dati['fiches_attuali'] = fiches + puntata
				salva_dati(dati)
				return
			mano = carte_da_mantenere + nuove_carte
		else:
			print("Tieni tutte le carte.")
			mano = mano_ordinata
		# --- Valutazione Mano Finale ---
		print("\nMano finale:")
		mano_finale_str = [f"- {carta.nome} ({carta.desc_breve})" for carta in mano]
		print("\n".join(mano_finale_str))
		punteggio = valuta_mano(mano)
		importo_restituito = calcola_vincita(punteggio, puntata)
		vincita_netta = importo_restituito - puntata
		print(f"\nRisultato: {punteggio}!")
		# Gestione Vincita/Perdita Normale e Killer Hand
		if vincita_netta >= 0:
			fiches_vinte = vincita_netta
			print(f"Vinci {fiches_vinte} fiches (restituite {importo_restituito}).")
			if is_mano_speciale and fiches_vinte > 0:
				bonus_kh = fiches_vinte * 2
				print(f"*** Bonus Killer Hand! Vinci {bonus_kh} fiches extra! ***")
				fiches_vinte += bonus_kh
			fiches += importo_restituito
			dati['fiches_guadagnate'] += fiches_vinte
			if fiches_vinte > dati['vincita_massima']:
				dati['vincita_massima'] = fiches_vinte
				dati['data_vincita_massima'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				print("--> Nuovo Record Vincita Massima in una mano!")
		else:
			print(f"Perdi la puntata di {puntata} fiches.")
			perdita_totale_mano = puntata
			if is_mano_speciale:
				penalita_kh_importo = int(fiches * (penalita_attuale / 100))
				penalita_kh_importo = min(penalita_kh_importo, fiches)
				print(f"*** Penalità Killer Hand! Perdi un extra {penalita_attuale}% ({penalita_kh_importo} fiches)! ***")
				fiches -= penalita_kh_importo
				perdita_totale_mano += penalita_kh_importo
			dati['fiches_perdute'] += perdita_totale_mano
			if perdita_totale_mano > dati['perdita_massima']:
				dati['perdita_massima'] = perdita_totale_mano
				dati['data_perdita_massima'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				print("--> Nuovo Record Perdita Massima in una mano!")
		# --- Aggiornamento Statistiche ---
		dati['fiches_attuali'] = fiches
		dati['mani_giocate'] += 1
		dati['mani_dall_ultimo_fallimento'] += 1
		if fiches > 0 and dati['mani_dall_ultimo_fallimento'] > dati['record_mani_senza_fallimenti']:
			dati['record_mani_senza_fallimenti'] = dati['mani_dall_ultimo_fallimento']
		if punteggio != "Mano non valida":
			dati['punteggi'][punteggio]['conteggio'] += 1
			dati['punteggi'][punteggio]['ultima_realizzazione'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		numero_mano_sessione += 1
		# --- Controllo Game Over ---
		if fiches <= 0:
			print("\n**************** GAME OVER ****************")
			print("Hai esaurito le fiches!")
			if dati['mani_dall_ultimo_fallimento'] == dati['record_mani_senza_fallimenti']:
				print(f"Hai stabilito il tuo nuovo record di {dati['record_mani_senza_fallimenti']} mani senza fallimenti!")
			dati['fallimenti'] += 1
			dati['data_ultimo_fallimento'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			dati['mani_dall_ultimo_fallimento'] = 0
			dati['killer_hand_count'] = 0
			dati['data_ultima_giocata'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			salva_dati(dati)
			mostra_report(dati)
			return
		salva_dati(dati) # Salva dopo ogni mano completata
if __name__ == "__main__":
	poker_machine()