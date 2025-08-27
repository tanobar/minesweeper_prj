# Questo modulo implementa la classe ExactEnumeration, che permette di calcolare
# le probabilità marginali (cioè la probabilità che una cella sia mina) enumerando
# tutte le possibili assegnazioni compatibili con i vincoli locali della frontiera.
#
# È usato per componenti di frontiera piccole, dove l'enumerazione completa è fattibile.
# Per componenti più grandi, viene usato un backtracking con propagazione e pruning.
#
# I vincoli sono del tipo: "tra queste celle ci sono esattamente N mine".
# L'output principale è un dizionario che, per ogni cella, fornisce la probabilità
# che sia mina, calcolata come (# soluzioni in cui è mina) / (# soluzioni totali).

from collections import defaultdict, deque
import math

class ExactEnumeration:
    def __init__(self, variables, constraints, max_solutions=200000):
        """
        Inizializza l'oggetto per l'enumerazione esatta.

        variables: insieme di celle (i,j) da considerare come variabili booleane (mina/safe)
        constraints: lista di vincoli, ciascuno come dict {"vars": set[(i,j)], "count": int}
                     che significa: tra queste celle ci sono esattamente 'count' mine.
        max_solutions: limite massimo di soluzioni da enumerare (per evitare esplosioni)
        """
        self.vars = list(sorted(variables))  # Lista ordinata delle variabili (celle da assegnare)
        # Copia profonda dei vincoli per sicurezza
        self.cons = [{"vars": set(c["vars"]), "count": int(c["count"])} for c in constraints]
        self.max_solutions = max_solutions

        # Conteggi per le marginali: quante volte ogni variabile è mina nelle soluzioni valide
        self.solution_count = 0
        self.true_counts = {v: 0 for v in self.vars}

        # Strutture di supporto per velocizzare la propagazione
        self._build_indices()

    def _build_indices(self):
        """
        Prepara strutture di supporto:
        - cons_vars: lista delle variabili coinvolte in ciascun vincolo
        - var_to_cons: per ogni variabile, lista degli indici dei vincoli in cui compare
        """
        self.cons_vars = [list(c["vars"]) for c in self.cons]
        self.var_to_cons = {v: [] for v in self.vars}
        for ci, c in enumerate(self.cons):
            for v in c["vars"]:
                self.var_to_cons[v].append(ci)

    def _feasible(self, assign, cons_state):
        """
        Controllo rapido di fattibilità: per ogni vincolo deve valere t <= req <= t+u,
        dove t = mine già assegnate, u = variabili ancora ignote, req = mine richieste.
        """
        for (t, u, req) in cons_state:
            if not (t <= req <= t + u):
                return False
        return True

    def _init_cons_state(self, assign):
        """
        Inizializza lo stato dei vincoli:
        Per ciascun vincolo, tiene traccia di:
        - t: quante mine già assegnate
        - u: quante variabili ancora ignote
        - req: mine richieste dal vincolo
        """
        state = []
        for c in self.cons:
            t = 0
            u = 0
            for v in c["vars"]:
                av = assign.get(v, None)
                if av is None:
                    u += 1
                elif av == 1:
                    t += 1
            state.append([t, u, c["count"]])
        return state

    def _propagate(self, assign, cons_state):
        """
        Propagazione elementare dei vincoli (forward-checking):
        - Se req == t      → tutte le ignote del vincolo sono safe (0)
        - Se req == t + u  → tutte le ignote sono mine (1)
        Ritorna False se trova una contraddizione.
        """
        changed = True
        while changed:
            changed = False
            for ci, c in enumerate(self.cons):
                t, u, req = cons_state[ci]
                if u == 0:
                    if t != req:
                        return False  # Contraddizione: tutte assegnate ma il conteggio non torna
                    continue
                if req < t or req > t + u:
                    return False  # Contraddizione: impossibile soddisfare il vincolo
                if req == t:
                    # Tutte le ignote devono essere safe (0)
                    for v in c["vars"]:
                        if assign.get(v, None) is None:
                            assign[v] = 0
                            cons_state[ci][1] -= 1
                            # Aggiorna anche gli altri vincoli che contengono v
                            for cj in self.var_to_cons[v]:
                                if cj == ci:
                                    continue
                                cons_state[cj][1] -= 1
                    changed = True
                elif req == t + u:
                    # Tutte le ignote devono essere mine (1)
                    for v in c["vars"]:
                        if assign.get(v, None) is None:
                            assign[v] = 1
                            cons_state[ci][0] += 1
                            cons_state[ci][1] -= 1
                            for cj in self.var_to_cons[v]:
                                if cj == ci:
                                    continue
                                cons_state[cj][0] += 1
                                cons_state[cj][1] -= 1
                    changed = True
        return True

    def _select_var(self, assign):
        """
        Euristica di scelta della variabile: seleziona la variabile non assegnata
        che compare nel maggior numero di vincoli (grado massimo).
        Questo tende a ridurre più rapidamente lo spazio delle soluzioni.
        """
        best_v = None
        best_deg = -1
        for v, cons_list in self.var_to_cons.items():
            if v in assign:
                continue
            deg = len(cons_list)
            if deg > best_deg:
                best_deg = deg
                best_v = v
        return best_v

    def _search(self, assign, cons_state):
        """
        Ricerca ricorsiva con backtracking e propagazione.
        - Se tutte le variabili sono assegnate, verifica che tutti i vincoli siano soddisfatti.
        - Altrimenti, seleziona una variabile, prova entrambi i valori (0 e 1),
          aggiorna lo stato dei vincoli e ricorre.
        - Pruning: se un vincolo non può più essere soddisfatto, interrompe il ramo.
        """
        if self.solution_count >= self.max_solutions:
            return

        # Caso base: tutte assegnate → verifica finale dei vincoli
        if len(assign) == len(self.vars):
            for (t, u, req) in cons_state:
                if not (u == 0 and t == req):
                    return
            self.solution_count += 1
            for v, val in assign.items():
                if val == 1:
                    self.true_counts[v] += 1
            return

        # Propagazione dei vincoli
        if not self._propagate(assign, cons_state):
            return

        # Scegli la prossima variabile da assegnare
        v = self._select_var(assign)
        if v is None:
            return

        # Prova entrambi i valori (0 = safe, 1 = mina)
        for val in (0, 1):
            assign[v] = val
            saved = [c.copy() for c in cons_state]  # Salva lo stato per backtracking
            for ci in self.var_to_cons[v]:
                if val == 1:
                    cons_state[ci][0] += 1
                cons_state[ci][1] -= 1
            ok = True
            for (t, u, req) in cons_state:
                if not (t <= req <= t + u):
                    ok = False
                    break
            if ok:
                self._search(assign, cons_state)
            assign.pop(v, None)
            cons_state = saved  # Ripristina lo stato

    # ------- fallback semplice per componenti molto piccole -------
    def _check_constraints(self, assign):
        """
        Verifica che una assegnazione soddisfi tutti i vincoli.
        Usato nella versione semplice per componenti molto piccole.
        """
        for c in self.cons:
            s = 0
            for v in c["vars"]:
                s += 1 if assign.get(v, 0) == 1 else 0
            if s != c["count"]:
                return False
        return True

    def _search_simple(self, idx, order, assign):
        """
        Enumerazione esaustiva semplice (senza propagazione) per componenti piccole.
        Prova tutte le possibili assegnazioni delle variabili.
        """
        if idx == len(order):
            if self._check_constraints(assign):
                self.solution_count += 1
                for v, val in assign.items():
                    if val == 1:
                        self.true_counts[v] += 1
            return
        if self.solution_count >= self.max_solutions:
            return
        v = order[idx]
        # Prova valore 0 (safe)
        assign[v] = 0
        self._search_simple(idx + 1, order, assign)
        # Prova valore 1 (mina)
        assign[v] = 1
        self._search_simple(idx + 1, order, assign)
        assign.pop(v, None)

    def marginals(self):
        """
        Esegue l'enumerazione e restituisce le marginali come dict {(i,j): p}.
        Utile come shortcut per ottenere solo le probabilità marginali.
        """
        res = self.run()
        if res is None:
            return {}
        return res["marginals"]

    def run(self):
        """
        Metodo principale: esegue l'enumerazione delle soluzioni compatibili.
        Sceglie la strategia in base alla dimensione della componente:
        - Per <=20 variabili: enumerazione esaustiva semplice (robusta)
        - Per >20 variabili: backtracking con propagazione e pruning
        Restituisce:
            - "solutions": numero di soluzioni compatibili trovate
            - "marginals": dict {(i,j): p} con la probabilità marginale di mina per ogni cella
        """
        assign = {}
        # Per componenti piccole, enumerazione completa semplice
        if len(self.vars) <= 20:
            order = list(self.vars)
            self._search_simple(0, order, assign)
        else:
            # Per componenti più grandi, usa backtracking con propagazione
            cons_state = self._init_cons_state(assign)
            if not self._feasible(assign, cons_state):
                return None
            self._search(assign, cons_state)

        if self.solution_count == 0:
            return None
        marginals = {v: self.true_counts[v] / self.solution_count for v in self.vars}
        return {"solutions": self.solution_count, "marginals": marginals}