# prob/approximate.py
import random, time

class RandomizedSampler:
    """
    Stima P(mina) con backtracking randomizzato + forward-checking.
    Si ferma dopo: max_samples soluzioni, max_nodes espansioni, oppure max_time_sec secondi.
    """

    def __init__(self, variables, constraints, max_samples=2000, max_nodes=100000, max_time_sec=2.0, seed=None):
        self.vars = list(sorted(variables))
        self.cons = [{"vars": set(c["vars"]), "count": int(c["count"])} for c in constraints]
        self.max_samples = max_samples
        self.max_nodes = max_nodes
        self.max_time_sec = max_time_sec
        self.solution_count = 0
        self.true_counts = {v: 0 for v in self.vars}
        self.nodes = 0
        self.rng = random.Random(seed)
        self.t0 = None

        self.var_to_cons = {v: [] for v in self.vars}
        for ci, c in enumerate(self.cons):
            for v in c["vars"]:
                self.var_to_cons[v].append(ci)

    def _init_cons_state(self, assign):
        state = []
        for c in self.cons:
            t = 0
            u = 0
            for v in c["vars"]:
                av = assign.get(v, None)
                if av is None: u += 1
                elif av == 1:  t += 1
            state.append([t, u, c["count"]])
        return state

    @staticmethod
    def _feasible_state(state):
        for (t,u,req) in state:
            if not (t <= req <= t+u):
                return False
        return True

    def _propagate(self, assign, state):
        changed = True
        while changed:
            if time.time() - self.t0 > self.max_time_sec:
                return False
            changed = False
            for ci, c in enumerate(self.cons):
                t, u, req = state[ci]
                if u == 0:
                    if t != req: return False
                    continue
                if req < t or req > t + u: return False
                if req == t:
                    for v in c["vars"]:
                        if assign.get(v) is None:
                            assign[v] = 0
                            state[ci][1] -= 1
                            for cj in self.var_to_cons[v]:
                                if cj != ci:
                                    state[cj][1] -= 1
                    changed = True
                elif req == t + u:
                    for v in c["vars"]:
                        if assign.get(v) is None:
                            assign[v] = 1
                            state[ci][0] += 1
                            state[ci][1] -= 1
                            for cj in self.var_to_cons[v]:
                                if cj != ci:
                                    state[cj][0] += 1
                                    state[cj][1] -= 1
                    changed = True
        return True

    def _select_var(self, assign):
        unassigned = [v for v in self.vars if v not in assign]
        if not unassigned: return None
        degs = [(len(self.var_to_cons[v]), v) for v in unassigned]
        min_deg = min(d for d,_ in degs)
        candidates = [v for d,v in degs if d == min_deg]
        return self.rng.choice(candidates)

    def _search(self, assign, state):
        import time
        if (self.solution_count >= self.max_samples or
            self.nodes >= self.max_nodes or
            time.time() - self.t0 > self.max_time_sec):
            return
        self.nodes += 1

        if not self._propagate(assign, state):
            return

        if all(v in assign for v in self.vars):
            for (t,u,req) in state:
                if not (u == 0 and t == req):
                    return
            self.solution_count += 1
            for v,val in assign.items():
                if val == 1:
                    self.true_counts[v] += 1
            return

        v = self._select_var(assign)
        if v is None:
            return

        first = 1 if self.rng.random() < 0.5 else 0
        for val in (first, 1-first):
            # >>> SALVA assegnazioni correnti <<<
            saved_assign = assign.copy()
            saved_state = [c.copy() for c in state]

            assign[v] = val
            for ci in self.var_to_cons[v]:
                if val == 1:
                    state[ci][0] += 1
                state[ci][1] -= 1

            if self._feasible_state(state):
                self._search(assign, state)

            # >>> RIPRISTINA assegnazioni e stato (incluso ciò che _propagate ha aggiunto) <<<
            assign.clear(); assign.update(saved_assign)
            state = saved_state

            if (self.solution_count >= self.max_samples or
                self.nodes >= self.max_nodes or
                time.time() - self.t0 > self.max_time_sec):
                return

    # prob/approximate.py (aggiungi in fondo)
    def sample_component_stats(vars_set, constraints, max_samples=5000, max_nodes=200000, max_time_sec=2.0, seed=0):
        """
        Usa il RandomizedSampler per raccogliere soluzioni e costruire:
        - hist[k] ~ #soluzioni con k mine (stimata dai campioni)
        - g_per_var[v][k] ~ #soluzioni con k mine e v=1 (stimata)
        """
        sampler = RandomizedSampler(vars_set, constraints,
                                    max_samples=max_samples,
                                    max_nodes=max_nodes,
                                    max_time_sec=max_time_sec,
                                    seed=seed)
        # Piccolo wrap su RandomizedSampler per esporre anche i campioni:
        sampler.t0 = None  # garantiamo run "fresh"
        # Reimplementiamo run leggendo la logica interna:
        # Più semplice: chiamiamo run() e poi rilanciamo una seconda ricerca con raccolta esplicita.
        res = sampler.run()
        if not res or res["solutions"] == 0:
            # fallback prudente: tutto 0 eccetto hist[0]=1
            n = len(vars_set)
            return [0]*n + [1], {v:[0]*(n+1) for v in vars_set}, 0

        # Per ottenere gli istogrammi, rifacciamo una ricerca con raccolta esplicita
        # (riutilizzando le stesse routine interne).
        # Nota: per semplicità/tempo, ricostruiamo un piccolo enumeratore randomizzato qui.

        import time, random
        rng = random.Random(seed)
        vars_list = sorted(vars_set)
        n = len(vars_list)
        cons = [{"vars": set(c["vars"]), "count": int(c["count"])} for c in constraints]

        def init_state(assign):
            st = []
            for c in cons:
                t = u = 0
                for v in c["vars"]:
                    av = assign.get(v, None)
                    if av is None: u += 1
                    elif av == 1:  t += 1
                st.append([t,u,c["count"]])
            return st

        def feasible(st):
            for (t,u,req) in st:
                if not (t <= req <= t+u): return False
            return True

        def propagate(assign, st, t0):
            changed = True
            while changed:
                if time.time() - t0 > max_time_sec:
                    return False
                changed = False
                for ci,(t,u,req) in enumerate(st):
                    if u == 0:
                        if t != req: return False
                        continue
                    if req < t or req > t+u: return False
                    if req == t or req == t+u:
                        set_to = 1 if req == t+u else 0
                        for v in cons[ci]["vars"]:
                            if v in assign: continue
                            assign[v] = set_to
                            for cj, (tt,uu,rr) in enumerate(st):
                                if v in cons[cj]["vars"]:
                                    if set_to == 1: st[cj][0] += 1
                                    st[cj][1] -= 1
                        changed = True
            return True

        def select_var(assign):
            un = [v for v in vars_list if v not in assign]
            if not un: return None
            # MRV randomizzata: scegli una variabile con grado minimo
            degs = [(sum(v in c["vars"] for c in cons), v) for v in un]
            mind = min(d for d,_ in degs)
            cand = [v for d,v in degs if d == mind]
            return rng.choice(cand)

        t0 = time.time()
        hist = [0]*(n+1)
        g_per_var = {v:[0]*(n+1) for v in vars_list}
        samples = 0
        nodes = 0

        def search(assign, st):
            nonlocal samples, nodes, t0
            if (samples >= max_samples or nodes >= max_nodes or time.time() - t0 > max_time_sec):
                return
            nodes += 1
            if not propagate(assign, st, t0):
                return
            if len(assign) == n:
                for (t,u,req) in st:
                    if not (u == 0 and t == req): return
                k = sum(assign[v] for v in vars_list)
                hist[k] += 1
                for v in vars_list:
                    if assign[v] == 1:
                        g_per_var[v][k] += 1
                samples += 1
                return
            v = select_var(assign)
            if v is None: return
            first = 1 if rng.random() < 0.5 else 0
            for val in (first, 1-first):
                saved_assign = assign.copy()
                saved_state = [c.copy() for c in st]
                assign[v] = val
                for ci in range(len(st)):
                    if v in cons[ci]["vars"]:
                        if val == 1: st[ci][0] += 1
                        st[ci][1] -= 1
                if feasible(st):
                    search(assign, st)
                assign.clear(); assign.update(saved_assign)
                st = saved_state
                if (samples >= max_samples or nodes >= max_nodes or time.time() - t0 > max_time_sec):
                    return

        st0 = init_state({})
        if not feasible(st0):
            return [0]*(n+1), {v:[0]*(n+1) for v in vars_list}, 0

        search({}, st0)
        return hist, g_per_var, samples


    def run(self):
        self.t0 = time.time()
        assign = {}
        state = self._init_cons_state(assign)
        if not self._feasible_state(state): return None
        self._search(assign, state)
        if self.solution_count == 0: return None
        marg = {v: self.true_counts[v]/self.solution_count for v in self.vars}
        return {"solutions": self.solution_count, "marginals": marg}
