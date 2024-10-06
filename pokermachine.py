# Poker Machine by Gabriele Battaglia (IZ4APU) and ChatGPT-o1
# Data di concepimento 2 ottobre 2024

import pickle
from datetime import datetime
from dateutil.relativedelta import relativedelta
from GBUtils import Mazzo

def carica_dati():
	try:
		with open('pokermachine_data.pkl', 'rb') as f:
			dati = pickle.load(f)
			dati['launches'] += 1
	except FileNotFoundError:
		dati = {
			'launches': 1,
			'mani_giocate': 0,
			'data_ultimo_fallimento': None,
			'record_mani_senza_fallimenti': 0,
			'mani_dall_ultimo_fallimento': 0,
			'fiches_guadagnate': 0,
			'fiches_perdute': 0,
			'fiches_attuali': 100,
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
				"Scala a colore": {'conteggio': 0, 'ultima_realizzazione': None},
				"Scala Reale": {'conteggio': 0, 'ultima_realizzazione': None}
			},
			'vincita_massima': 0,
			'data_vincita_massima': None,
			'perdita_massima': 0,
			'data_perdita_massima': None,
			'data_ultima_giocata': None
		}
	if 'killer_hand_count' not in dati:
		dati['killer_hand_count'] = 0
	if dati['fiches_attuali'] <= 0:
		print("Le fiches sono state esaurite. Ricevi 100 fiches.")
		dati['fiches_attuali'] = 100
		dati['fiches_perdute'] -= 100
		dati['fallimenti'] += 1
		dati['mani_dall_ultimo_fallimento'] = 0
	return dati
def salva_dati(dati):
	with open('pokermachine_data.pkl', 'wb') as f:
		pickle.dump(dati, f)
def mostra_report(dati):
	print("== Report ==")
	print(f"Mani giocate totali: {dati['mani_giocate']}")
	print(f"Mani dall'ultimo fallimento: {dati['mani_dall_ultimo_fallimento']}")
	if dati['data_ultimo_fallimento']:
		data_ultimo_fallimento = datetime.strptime(dati['data_ultimo_fallimento'], "%Y-%m-%d %H:%M:%S")
		diff_fallimento = relativedelta(datetime.now(), data_ultimo_fallimento)
		print(f"Ultimo fallimento avvenuto {diff_fallimento.years} anni, {diff_fallimento.months} mesi, "
								f"{diff_fallimento.days} giorni fa")
	print(f"Record mani senza fallimenti: {dati['record_mani_senza_fallimenti']}")
	print(f"Fiches totali guadagnate: {dati['fiches_guadagnate']}")
	print(f"Fiches totali perdute: {dati['fiches_perdute']}")
	print(f"Fiches attuali: {dati['fiches_attuali']}")
	print(f"Fallimenti (fiches esaurite): {dati['fallimenti']}")
	if dati['vincita_massima']:
		ora = datetime.now()
		data_vincita = datetime.strptime(dati['data_vincita_massima'], "%Y-%m-%d %H:%M:%S")
		diff_vincita = relativedelta(ora, data_vincita)
		print(f"Vincita massima: {dati['vincita_massima']} fiches, {diff_vincita.years} anni, "
			  f"{diff_vincita.months} mesi e {diff_vincita.days} giorni fa")
	if dati['perdita_massima']:
		ora = datetime.now()
		data_perdita = datetime.strptime(dati['data_perdita_massima'], "%Y-%m-%d %H:%M:%S")
		diff_perdita = relativedelta(ora, data_perdita)
		print(f"Perdita massima: {dati['perdita_massima']} fiches, {diff_perdita.years} anni, "
			  f"{diff_perdita.months} mesi e {diff_perdita.days} giorni fa")
	if dati['data_ultima_giocata']:
		print(f"Data ultima giocata: {dati['data_ultima_giocata']}")
	print("== Tabella dei punteggi ==")
	ora = datetime.now()
	for punteggio, info in dati['punteggi'].items():
		conteggio = info['conteggio']
		ultima_realizzazione = info['ultima_realizzazione']
		if ultima_realizzazione:
			data_ultima = datetime.strptime(ultima_realizzazione, "%Y-%m-%d %H:%M:%S")
			diff = relativedelta(ora, data_ultima)
			tempo_trascorso = (f"{diff.years} anni, {diff.months} mesi e {diff.days} giorni fa")
		else:
			tempo_trascorso = "Mai realizzato"
		print(f"{punteggio}, realizzato {conteggio} volte, l'ultima {tempo_trascorso}.")
def ricostruisci_mazzo(mazzo, mano_corrente):
	'''
	Ricostruisce il mazzo senza duplicare le carte in mano o scartate permanentemente.
	'''
	mazzo = Mazzo(tipo=True, num_mazzi=10)
	carte_in_mano = [carta[1][0] for carta in mano_corrente]
	mazzo.carte = [carta for carta in mazzo.carte if carta[1][0] not in carte_in_mano]
	carte_scartate_permanenti = [carta[1][0] for carta in mazzo.scarti_permanenti]
	mazzo.carte = [carta for carta in mazzo.carte if carta[1][0] not in carte_scartate_permanenti]
	print("Mescolamento del mazzo in corso per 5 secondi...")
	mazzo.MescolaMazzo(5000)
def poker_machine():
	dati = carica_dati()
	fiches = dati['fiches_attuali']
	mazzo = Mazzo(tipo=True, num_mazzi=10)
	print("Mescolamento del mazzo in corso per 5 secondi...")
	mazzo.MescolaMazzo(5000)
	mostra_report(dati)
	print(f"== Benvenuto alla Poker Machine!\n\tVersione {VERSIONE} by Gabry (IZ4APU). ==")
	numero_mano = dati['mani_dall_ultimo_fallimento'] + 1
	killer_hand_count = dati['killer_hand_count']
	while fiches > 0:
		is_mano_speciale = (numero_mano % KILLER_HAND_FREQUENZA == 0)
		if is_mano_speciale:
			killer_hand_count += 1
			penalita_attuale = min(killer_hand_count * 10, MAX_PENALITA_KH)
			print(f"Attenzione! Questa è una Killer Hand (mano speciale #{numero_mano}). Se perdi, perderai il {penalita_attuale}% delle tue fiches!")
		puntata=""
		while True:
			puntata = input(f"Mano #{numero_mano}, Fiches: {fiches}. Quante? ")
			if (puntata == "" or puntata.isdigit() or (len(puntata) == 1 and puntata in '-.,;+')): break
			else: print("Inserisci il numero di fiches che vuoi puntare o usa una scorciatoia:\n\t- 10% , 25% . 50% ; 75% + 100%.")
		if puntata == "":
			print("Grazie per aver giocato!")
			dati['fiches_attuali'] = fiches
			dati['data_ultima_giocata'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			dati['killer_hand_count'] = killer_hand_count  
			salva_dati(dati)
			mostra_report(dati)
			return
		elif puntata=="-": puntata=int(fiches/100*10)
		elif puntata=="+": puntata=int(fiches)
		elif puntata==".": puntata=int(fiches/100*50)
		elif puntata==",": puntata=int(fiches/100*25)
		elif puntata==";": puntata=int(fiches/100*75)
		puntata_minima = max(int(fiches * PERCENTUALE_MINIMA_PUNTATA), 1)
		if int(puntata) < puntata_minima:
			print(f"La puntata è inferiore al 10%, corretta con {puntata_minima}.")
			puntata = puntata_minima
		else:
			puntata = int(puntata)
		if len(mazzo.carte) < CARTE_NECESSARIE:
			print("Le carte stanno per finire. Rimescoliamo gli scarti.")
			mazzo.Rimescola()
			print("Mescolamento del mazzo in corso per 5 secondi...")
			mazzo.MescolaMazzo(5000)
			if len(mazzo.carte) < CARTE_NECESSARIE:
				print("Non ci sono abbastanza carte per continuare. Ricostruiamo il mazzo.")
				ricostruisci_mazzo(mazzo, [])
		mano_mazzo = mazzo.Pesca(5)
		mano = mano_mazzo.carte
		if len(mano) < 5:
			print("Non ci sono abbastanza carte per completare la mano. Ricostruiamo il mazzo.")
			ricostruisci_mazzo(mazzo, mano)
			nuove_carte = mazzo.Pesca(5 - len(mano)).carte
			mano.extend(nuove_carte)
		print("Le tue carte:")
		brevi=""
		for idx, (_, carta) in enumerate(mano, 1):
			print(f"{idx}: {carta[0]}")
			brevi+=carta[6]+" "
		mantenere = input(f"{brevi} - Quali tieni? >  ")
		if mantenere != "":
			carte_da_mantenere = []
			indici_mantenere = set()
			for ch in mantenere:
				if ch.isdigit():
					idx = int(ch)
					if 1 <= idx <= len(mano):
						indici_mantenere.add(idx - 1)
			carte_da_mantenere = [mano[idx] for idx in indici_mantenere]
			carte_da_sostituire = [carta for idx, carta in enumerate(mano) if idx not in indici_mantenere]
			for carta in carte_da_sostituire:
				mazzo.scarti.append(carta)
			mano = carte_da_mantenere
			numero_carte_da_sostituire = len(carte_da_sostituire)
			if len(mazzo.carte) < numero_carte_da_sostituire:
				print("Le carte stanno per finire. Rimescoliamo gli scarti.")
				mazzo.Rimescola()
				print("Mescolamento del mazzo in corso per 5 secondi...")
				mazzo.MescolaMazzo(5000)
				if len(mazzo.carte) < numero_carte_da_sostituire:
					print("Non ci sono abbastanza carte per sostituire le tue carte. Ricostruiamo il mazzo.")
					ricostruisci_mazzo(mazzo, mano)
			nuove_carte = mazzo.Pesca(numero_carte_da_sostituire).carte
			mano.extend(nuove_carte)
		else:
			for carta in mano:
				mazzo.scarti.append(carta)
			mano.clear()
			if len(mazzo.carte) < 5:
				print("Le carte stanno per finire. Rimescoliamo gli scarti.")
				mazzo.Rimescola()
				print("Mescolamento del mazzo in corso per 5 secondi...")
				mazzo.MescolaMazzo(5000)
				if len(mazzo.carte) < 5:
					print("Non ci sono abbastanza carte per continuare. Ricostruiamo il mazzo.")
					ricostruisci_mazzo(mazzo, mano)
			nuove_carte = mazzo.Pesca(5).carte
			mano.extend(nuove_carte)
		print("La tua mano finale:")
		for _, carta in mano:
			print(carta[0])
		punteggio = valuta_mano(mano)
		vincita = calcola_vincita(punteggio, puntata)
		print(f"Risultato ottenuto: puntata {puntata}, {punteggio}, vincita: {vincita-puntata} fiches.")
		if is_mano_speciale and vincita < puntata:
			perdita_kh = int(fiches * (penalita_attuale / 100))
			fiches -= perdita_kh
			print(f"Hai perso la Killer Hand! Perdi il {penalita_attuale}% delle tue fiches: {perdita_kh}.")
		if vincita > 0:
			fiches += (vincita - puntata)
			dati['fiches_guadagnate'] += vincita
			if vincita > dati['vincita_massima']:
				dati['vincita_massima'] = vincita
				dati['data_vincita_massima'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				print("Congratulazioni, nuovo record nelle fiches vinte!")
		else:
			fiches -= puntata
			dati['fiches_perdute'] += puntata
			if puntata > dati['perdita_massima']:
				dati['perdita_massima'] = puntata
				dati['data_perdita_massima'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				print("ahi ahi ahi, questo purtroppo è il peggior colpo subito!")
		dati['fiches_attuali'] = fiches
		dati['mani_giocate'] += 1
		dati['mani_dall_ultimo_fallimento'] += 1
		dati['punteggi'][punteggio]['conteggio'] += 1
		dati['punteggi'][punteggio]['ultima_realizzazione'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		numero_mano += 1
		if fiches <= 0:
			print("Hai esaurito le fiches. Grazie per aver giocato!")
			if dati['mani_dall_ultimo_fallimento'] > dati['record_mani_senza_fallimenti']:
				dati['record_mani_senza_fallimenti'] = dati['mani_dall_ultimo_fallimento']
				print("Congratulazioni, questa è la tua striscia di mani vincenti più lunga mai realizzata!")
			dati['fiches_attuali'] = fiches
			dati['mani_dall_ultimo_fallimento'] = 0
			dati['data_ultimo_fallimento'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			dati['killer_hand_count'] = 0
			dati['data_ultima_giocata'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			salva_dati(dati)
			mostra_report(dati)
			return
	dati['fiches_attuali'] = fiches
	dati['data_ultima_giocata'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	salva_dati(dati)
	mostra_report(dati)
def valuta_mano(mano):
	valori = []
	semi = []
	valori_numerici = []
	valori_numerici_seq = []
	valori_figura = {'Jack': 11, 'Regina': 12, 'Re': 13, 'Asso': 14}
	for _, carta in mano:
		nome_carta = carta[0]
		nome_valore, seme_carta = nome_carta.split(' di ')
		semi.append(seme_carta)
		if nome_valore.isdigit():
			valore = int(nome_valore)
		else:
			valore = valori_figura.get(nome_valore, 0)
		valori_numerici.append(valore)
		if nome_valore == 'Asso':
			valori_numerici_seq.extend([1, 14])
		else:
			valori_numerici_seq.append(valore)
		valori.append(nome_valore)
	conta_valori = {}
	for val in valori_numerici:
		conta_valori[val] = conta_valori.get(val, 0) + 1
	conta_semi = {}
	for s in semi:
		conta_semi[s] = conta_semi.get(s, 0) + 1

	def is_sequenza(valori):
		valori_unici = sorted(set(valori))
		for i in range(len(valori_unici) - 4):
			sequenza = valori_unici[i:i + 5]
			if all(sequenza[j] + 1 == sequenza[j + 1] for j in range(4)):
				return True
		return False
	def is_colore():
		return max(conta_semi.values()) >= 5
	if is_sequenza(valori_numerici_seq) and is_colore():
		if set([10, 11, 12, 13, 14]).issubset(valori_numerici):
			return "Scala Reale"
		else:
			return "Scala a colore"
	if 4 in conta_valori.values():
		return "Poker"
	if sorted(conta_valori.values()) == [2, 3]:
		return "Full"
	if is_colore():
		return "Colore"
	if is_sequenza(valori_numerici_seq):
		return "Scala"
	if 3 in conta_valori.values():
		return "Tris"
	if list(conta_valori.values()).count(2) >= 2:
		return "Doppia coppia"
	if 2 in conta_valori.values():
		for val, count in conta_valori.items():
			if count == 2 and val >= 11:
				return "Coppia pagata"
		return "Coppia non pagata"
	return "Carta alta"
def calcola_vincita(punteggio, puntata):
	tabella_vincite = {
		"Carta alta": 0,
		"Coppia non pagata": 0,
		"Coppia pagata": 1,
		"Doppia coppia": 2,
		"Tris": 3,
		"Scala": 4,
		"Colore": 6,
		"Full": 9,
		"Poker": 25,
		"Scala a colore": 50,
		"Scala Reale": 250
	}
	moltiplicatore = tabella_vincite.get(punteggio, 0)
	return puntata * moltiplicatore

CARTE_NECESSARIE = 10
KILLER_HAND_FREQUENZA = 20
PERCENTUALE_MINIMA_PUNTATA = 0.10  # Puntata minima del 10% delle F
penalita_killer_hand = 10
MAX_PENALITA_KH = 90
VERSIONE="2.1.1 del 6 ottobre 2024"
if __name__ == "__main__":
	poker_machine()
