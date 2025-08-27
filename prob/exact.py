# prob/exact.py
from collections import defaultdict, deque
import math

class ExactEnumeration:
    def __init__(self, variables, constraints, max_solutions=200000):
        """
        variables: set di (i,j)
        constraints: list di dict {"vars": set[(i,j)], "count": int}
        """
        self.vars = list(sorted(variables))
        self.cons = [{"vars": set(c["vars"]), "count": int(c["count"])} for c in constraints]
        self.max_solutions = max_solutions

        # conteggi per le marginali
        self.solution_count = 0
        self.true_counts = {v: 0 for v in self.vars}

        # strutture di supporto
        self._build_indices()

    def _build_indices(self):
        self.cons_vars = [list(c["vars"]) for c in self.cons]
        self.var_to_cons = {v: [] for v in self.vars}
        for ci, c in enumerate(self.cons):
            for v in c["vars"]:
                self.var_to_cons[v].append(ci)

    def _feasible(self, assign, cons_state):
        """Controllo rapido: per ogni vincolo deve valere t <= req <= t+u."""
        for (t, u, req) in cons_state:
            if not (t <= req <= t + u):
                return False
        return True

    def _init_cons_state(self, assign):
        # Per ciascun vincolo, stato = (true_count, unknown_count, required)
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
        Forward-checking elementare:
          - se req == t      → tutte le ignote del vincolo sono 0
          - se req == t + u  → tutte le ignote del vincolo sono 1
        Ritorna False se scopre contraddizioni.
        """
        changed = True
        while changed:
            changed = False
            for ci, c in enumerate(self.cons):
                t, u, req = cons_state[ci]
                if u == 0:
                    if t != req:
                        return False
                    continue
                if req < t or req > t + u:
                    return False
                if req == t:
                    # tutte le ignote -> 0
                    for v in c["vars"]:
                        if assign.get(v, None) is None:
                            assign[v] = 0
                            cons_state[ci][1] -= 1
                            # aggiorna gli altri vincoli che contengono v
                            for cj in self.var_to_cons[v]:
                                if cj == ci:
                                    continue
                                cons_state[cj][1] -= 1
                    changed = True
                elif req == t + u:
                    # tutte le ignote -> 1
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
        """Euristica di grado: scegli la variabile non assegnata con più vincoli."""
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
        if self.solution_count >= self.max_solutions:
            return

        # tutte assegnate → possibile soluzione
        if len(assign) == len(self.vars):
            # verifica esatta
            for (t, u, req) in cons_state:
                if not (u == 0 and t == req):
                    return
            self.solution_count += 1
            for v, val in assign.items():
                if val == 1:
                    self.true_counts[v] += 1
            return

        # Propagazione
        if not self._propagate(assign, cons_state):
            return

        # variabile successiva
        v = self._select_var(assign)
        if v is None:
            return

        # branch 0 / 1 con pruning
        for val in (0, 1):
            assign[v] = val
            saved = [c.copy() for c in cons_state]
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
            cons_state = saved

    # ------- fallback semplice per componenti molto piccole -------
    def _check_constraints(self, assign):
        for c in self.cons:
            s = 0
            for v in c["vars"]:
                s += 1 if assign.get(v, 0) == 1 else 0
            if s != c["count"]:
                return False
        return True

    def _search_simple(self, idx, order, assign):
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
        # prova 0
        assign[v] = 0
        self._search_simple(idx + 1, order, assign)
        # prova 1
        assign[v] = 1
        self._search_simple(idx + 1, order, assign)
        assign.pop(v, None)

    def marginals(self):
        """
        Esegue l'enumerazione e restituisce le marginali come dict {(i,j): p}.
        """
        res = self.run()
        if res is None:
            return {}
        return res["marginals"]


    def run(self):
        assign = {}
        # Per componenti piccole, enumerazione completa semplice (robusta)
        if len(self.vars) <= 20:
            order = list(self.vars)
            self._search_simple(0, order, assign)
        else:
            # Per componenti più grandi, backtracking con propagazione
            cons_state = self._init_cons_state(assign)
            if not self._feasible(assign, cons_state):
                return None
            self._search(assign, cons_state)

        if self.solution_count == 0:
            return None
        marginals = {v: self.true_counts[v] / self.solution_count for v in self.vars}
        return {"solutions": self.solution_count, "marginals": marginals}
