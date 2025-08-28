# Classe che si occupa di calcolare le probabilità marginali delle mine
# sulle celle di frontiera in una partita di Minesweeper.
# L'approccio è quello di enumerare tutte le possibili configurazioni compatibili
# con i vincoli locali (cioè i numeri già scoperti sulla griglia).
# È pensato per funzionare bene su componenti di frontiera piccole, dove
# l'enumerazione completa è fattibile senza esplosione combinatoria.
# Per componenti più grandi, viene usato un backtracking con propagazione e pruning.
# 
# Ogni vincolo è del tipo: "tra queste celle ci sono esattamente N mine".
# L'obiettivo è restituire, per ogni cella, la probabilità che sia mina,
# cioè (# soluzioni in cui è mina) / (# soluzioni totali compatibili).

from collections import defaultdict, deque
import math

class ExactEnumeration:
    def __init__(self, variables, constraints, max_solutions=200000):
        """
        Costruttore della classe.
        - variables: insieme di celle (i,j) che rappresentano le variabili booleane (mina/safe)
        - constraints: lista di vincoli, ciascuno come dict {"vars": set[(i,j)], "count": int}
          che significa: tra queste celle ci sono esattamente 'count' mine.
        - max_solutions: limite massimo di soluzioni da enumerare (per evitare esplosioni)
        """
        # Ordino le variabili per avere sempre lo stesso ordine (utile per debug e test)
        self.vars = list(sorted(variables))
        # Faccio una copia dei vincoli per evitare effetti collaterali
        self.cons = [{"vars": set(c["vars"]), "count": int(c["count"])} for c in constraints]
        self.max_solutions = max_solutions

        # Inizializzo i contatori che mi servono per calcolare le marginali
        self.solution_count = 0  # quante soluzioni compatibili ho trovato
        self.true_counts = {v: 0 for v in self.vars}  # per ogni variabile, quante volte è mina

        # Preparo strutture di supporto per la propagazione dei vincoli
        self._build_indices()

    def _build_indices(self):
        """
        Costruisco strutture di supporto per la propagazione:
        - cons_vars: lista delle variabili coinvolte in ciascun vincolo
        - var_to_cons: per ogni variabile, lista degli indici dei vincoli in cui compare
        Esempio:
        Se la variabile (2,3) compare nei vincoli 0, 2 e 5, allora var_to_cons[(2,3)] = [0,2,5].
        Così, quando assegno (2,3), so subito quali vincoli devo aggiornare.
        """
        self.cons_vars = [list(c["vars"]) for c in self.cons] #lista di liste, dove ogni elemento è la lista delle variabili coinvolte in un vincolo
        self.var_to_cons = {v: [] for v in self.vars} # dizionario che mappa ogni variabile alla lista degli indici dei vincoli in cui compare
        for ci, c in enumerate(self.cons):
            for v in c["vars"]:
                # aggiungo l'indice del vincolo ci alla lista delle occorrenze della variabile v
                self.var_to_cons[v].append(ci)

    def _feasible(self, assign, cons_state):
        """
        Controllo veloce di fattibilità: per ogni vincolo deve valere t <= req <= t+u,
        dove:
          - t = mine già assegnate
          - u = variabili ancora ignote
          - req = mine richieste dal vincolo
        Se anche solo un vincolo non è soddisfatto, posso scartare subito la configurazione.
        """
        for (t, u, req) in cons_state:
            if not (t <= req <= t + u): # Se il vincolo non può essere soddisfatto
                return False
        return True

    def _init_cons_state(self, assign):
        """
        Inizializzo lo stato dei vincoli.
        Per ogni vincolo tengo traccia di:
        - t: quante mine già assegnate
        - u: quante variabili ancora ignote
        - req: mine richieste dal vincolo
        Lo stato viene aggiornato dinamicamente durante la ricerca.
        """
        state = []  # Lista dello stato dei vincoli
        for c in self.cons:  # Scorro tutti i vincoli
            t = 0  # Mine già assegnate
            u = 0  # Variabili ancora ignote
            for v in c["vars"]:  # Scorro tutte le variabili del vincolo
                av = assign.get(v, None)  # Valore assegnato alla variabile (se presente)
                if av is None:
                    u += 1  # Variabile ancora ignota
                elif av == 1:
                    t += 1  # Variabile assegnata a mina
            state.append([t, u, c["count"]])  # Stato del vincolo: [mine assegnate, ignote, richieste]
        return state  # Ritorno lo stato di tutti i vincoli
    
    def _propagate(self, assign, cons_state):
        """
        Propagazione dei vincoli (forward-checking).
        Se in un vincolo il numero di mine richieste è già stato raggiunto (req == t),
        allora tutte le variabili ancora ignote devono essere safe (0).
        Se invece il numero di mine richieste è pari al numero di ignote più le mine già assegnate (req == t + u),
        allora tutte le ignote devono essere mine (1).
        Se trova una contraddizione (ad esempio, troppe mine già assegnate), ritorna False.
        Viene ripetuta finché trova nuove assegnazioni forzate.
        """
        changed = True  # Flag per sapere se ci sono state modifiche
        while changed:  # Ripeto finché trovo nuove assegnazioni forzate
            changed = False
            for ci, c in enumerate(self.cons):  # Scorro tutti i vincoli
                t, u, req = cons_state[ci]  # Estraggo lo stato del vincolo
                if u == 0:
                    # Tutte le variabili del vincolo sono già assegnate: controllo che il conteggio torni
                    if t != req:
                        return False  # Contraddizione: tutte assegnate ma il conteggio non torna
                    continue  # Passo al prossimo vincolo
                if req < t or req > t + u:
                    return False  # Contraddizione: impossibile soddisfare il vincolo
                if req == t:
                    # Tutte le ignote devono essere safe (0)
                    for v in c["vars"]:
                        if assign.get(v, None) is None:  # Se la variabile non è ancora assegnata
                            assign[v] = 0  # Assegno 0 (safe)
                            cons_state[ci][1] -= 1  # Una ignota in meno in questo vincolo
                            # Aggiorna anche gli altri vincoli che contengono v
                            for cj in self.var_to_cons[v]:
                                if cj == ci:
                                    continue  # Salto il vincolo corrente
                                cons_state[cj][1] -= 1  # Una ignota in meno anche negli altri vincoli
                    changed = True  # Ho fatto una modifica, quindi ripeto il ciclo
                elif req == t + u:
                    # Tutte le ignote devono essere mine (1)
                    for v in c["vars"]:
                        if assign.get(v, None) is None:  # Se la variabile non è ancora assegnata
                            assign[v] = 1  # Assegno 1 (mina)
                            cons_state[ci][0] += 1  # Una mina in più in questo vincolo
                            cons_state[ci][1] -= 1  # Una ignota in meno in questo vincolo
                            for cj in self.var_to_cons[v]:
                                if cj == ci:
                                    continue  # Salto il vincolo corrente
                                cons_state[cj][0] += 1  # Una mina in più anche negli altri vincoli
                                cons_state[cj][1] -= 1  # Una ignota in meno anche negli altri vincoli
                    changed = True  # Ho fatto una modifica, quindi ripeto il ciclo
        return True  # Propagazione completata senza contraddizioni

    def _select_var(self, assign):
        """
        Sceglie la prossima variabile da assegnare.
        L'euristica è quella di scegliere la variabile non ancora assegnata che compare
        nel maggior numero di vincoli (grado massimo). Questo aiuta a ridurre più rapidamente
        lo spazio delle soluzioni possibili, perché si va a lavorare sulle variabili più "vincolate".
        """
        best_v = None  # Migliore variabile trovata finora
        best_deg = -1  # Grado massimo trovato finora
        for v, cons_list in self.var_to_cons.items():  # Scorro tutte le variabili
            if v in assign:
                continue  # Salto quelle già assegnate
            deg = len(cons_list)  # Numero di vincoli in cui compare
            if deg > best_deg:
                best_deg = deg  # Aggiorno il grado massimo
                best_v = v  # Aggiorno la variabile migliore
        return best_v  # Ritorno la variabile scelta

    def _search(self, assign, cons_state):
        """
        Ricerca ricorsiva con backtracking e propagazione dei vincoli.
        Se tutte le variabili sono assegnate, verifica che tutti i vincoli siano soddisfatti.
        Altrimenti, seleziona una variabile, prova entrambi i valori (0 e 1),
        aggiorna lo stato dei vincoli e ricorre.
        Se un vincolo non può più essere soddisfatto, interrompe il ramo (pruning).
        """
        if self.solution_count >= self.max_solutions:
            # Se ho già trovato troppe soluzioni, mi fermo per evitare esplosioni di tempo/memoria
            return

        # Caso base: tutte assegnate → verifica finale dei vincoli
        if len(assign) == len(self.vars):
            for (t, u, req) in cons_state:  # Scorro tutti i vincoli
                if not (u == 0 and t == req):  # Se anche solo un vincolo non è soddisfatto
                    return  # Scarto la soluzione
            self.solution_count += 1  # Soluzione valida trovata
            for v, val in assign.items():  # Scorro tutte le variabili assegnate
                if val == 1:
                    self.true_counts[v] += 1  # Incremento il contatore se la variabile è mina
            return

        # Propagazione dei vincoli prima di scegliere la prossima variabile
        if not self._propagate(assign, cons_state):
            # Se la propagazione trova una contraddizione, scarto subito il ramo
            return

        # Scegli la prossima variabile da assegnare
        v = self._select_var(assign)
        if v is None:
            return

        # Prova entrambi i valori (0 = safe, 1 = mina)
        for val in (0, 1):
            assign[v] = val  # Assegno il valore alla variabile
            saved = [c.copy() for c in cons_state]  # Salva lo stato per backtracking
            for ci in self.var_to_cons[v]:  # Aggiorna lo stato dei vincoli che coinvolgono v
                if val == 1:
                    cons_state[ci][0] += 1  # Una mina in più
                cons_state[ci][1] -= 1  # Una ignota in meno
            ok = True  # Flag per verificare se i vincoli sono ancora soddisfatti
            for (t, u, req) in cons_state:
                if not (t <= req <= t + u):
                    ok = False  # Vincolo non più soddisfatto
                    break
            if ok:
                self._search(assign, cons_state)  # Ricorsione
            assign.pop(v, None)  # Backtracking: rimuovo l'assegnazione
            cons_state = saved  # Ripristina lo stato

    # ------- fallback semplice per componenti molto piccole -------
    def _check_constraints(self, assign):
        """
        Controlla che una assegnazione soddisfi tutti i vincoli.
        Questa funzione viene usata nella versione semplice (brute-force) per componenti piccole.
        Scorre tutti i vincoli e verifica che il numero di mine assegnate sia esattamente quello richiesto.
        """
        for c in self.cons:  # Scorro tutti i vincoli
            s = 0  # Contatore delle mine assegnate
            for v in c["vars"]:  # Scorro tutte le variabili del vincolo
                s += 1 if assign.get(v, 0) == 1 else 0  # Incremento se la variabile è mina
            if s != c["count"]:  # Se il conteggio non torna
                return False  # Vincolo non soddisfatto
        return True  # Tutti i vincoli soddisfatti

    def _search_simple(self, idx, order, assign):
        """
        Enumerazione esaustiva semplice (senza propagazione) per componenti piccole.
        Prova tutte le possibili assegnazioni delle variabili, una per una.
        Quando arriva in fondo, controlla se la soluzione è valida e aggiorna i contatori.
        """
        if idx == len(order):  # Se ho assegnato tutte le variabili
            if self._check_constraints(assign):  # Controllo se la soluzione è valida
                self.solution_count += 1  # Soluzione valida trovata
                for v, val in assign.items():  # Scorro tutte le variabili assegnate
                    if val == 1:
                        self.true_counts[v] += 1  # Incremento il contatore se la variabile è mina
            return
        if self.solution_count >= self.max_solutions:
            return
        v = order[idx]  # Prendo la prossima variabile da assegnare
        assign[v] = 0  # Prova valore 0 (safe)
        self._search_simple(idx + 1, order, assign)  # Ricorsione
        assign[v] = 1  # Prova valore 1 (mina)
        self._search_simple(idx + 1, order, assign)  # Ricorsione
        assign.pop(v, None)  # Backtracking: rimuovo l'assegnazione

    def marginals(self):
        """
        Esegue l'enumerazione e restituisce le marginali come dict {(i,j): p}.
        Utile come shortcut per ottenere solo le probabilità marginali.
        Se non ci sono soluzioni compatibili, restituisce un dizionario vuoto.
        """
        res = self.run()  # Esegue l'enumerazione completa
        if res is None:
            return {}  # Nessuna soluzione compatibile trovata
        return res["marginals"]  # Ritorno le marginali

    def run(self):
        """
        Esegue l'enumerazione delle soluzioni compatibili.
        Sceglie la strategia in base alla dimensione della componente:
        - Per <=20 variabili: enumerazione esaustiva semplice (robusta)
        - Per >20 variabili: backtracking con propagazione e pruning
        Restituisce:
            - "solutions": numero di soluzioni compatibili trovate
            - "marginals": dict {(i,j): p} con la probabilità marginale di mina per ogni cella
        """
        assign = {}  # Dizionario delle assegnazioni correnti
        if len(self.vars) <= 20:  # Se la componente è piccola, uso la brute-force semplice
            order = list(self.vars)  # Ordine delle variabili
            self._search_simple(0, order, assign)  # Avvio la ricerca semplice
        else:
            cons_state = self._init_cons_state(assign)  # Stato iniziale dei vincoli
            if not self._feasible(assign, cons_state):  # Se già all'inizio i vincoli sono impossibili
                return None  # Esco subito
            self._search(assign, cons_state)  # Avvio la ricerca con propagazione

        if self.solution_count == 0:  # Nessuna soluzione compatibile trovata
            return None
        marginals = {v: self.true_counts[v] / self.solution_count for v in self.vars}  # Calcolo la probabilità marginale per ogni variabile
        return {"solutions": self.solution_count, "marginals": marginals}  # Ritorno il risultato