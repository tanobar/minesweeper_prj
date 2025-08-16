# prob/frontier.py
from collections import defaultdict, deque

def neighbors(n, i, j):
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            r, c = i + di, j + dj
            if 0 <= r < n and 0 <= c < n:
                yield (r, c)

def build_constraints(knowledge, mine_cells):
    """
    Dallo stato di conoscenza costruisce vincoli di somma:
      Per ogni cella rivelata con numero k:
        sum_{v in N_ignote} X_v = k - (#mine note adiacenti)

    Ritorna:
      constraints: list di dict {"vars": set[(i,j)], "count": int}
      unknowns: set di tutte le celle ignote coinvolte in almeno un vincolo
    """
    n = len(knowledge)
    constraints = []
    unknowns = set()
    mine_set = set(mine_cells or [])

    for i in range(n):
        for j in range(n):
            v = knowledge[i][j]
            # Una cella rivelata numerica è un int (0..8)
            if isinstance(v, int):
                unk = []
                known_mines = 0
                for r, c in neighbors(n, i, j):
                    if knowledge[r][c] == "?":
                        unk.append((r, c))
                    elif knowledge[r][c] == "X" or (r, c) in mine_set:
                        known_mines += 1
                if unk:
                    count = int(v) - known_mines
                    # Clamp a [0, |unk|] per sicurezza
                    count = max(0, min(count, len(unk)))
                    constraints.append({"vars": set(unk), "count": count})
                    unknowns.update(unk)

    return constraints, unknowns

def connected_components_from_constraints(constraints):
    """
    Costruisce il grafo variabile-variabile (arco se due variabili co-occorrono
    nello stesso vincolo) e ritorna le componenti connesse come
    (vars_set, constraints_subset).
    """
    adj = defaultdict(set)
    for cons in constraints:
        vars_list = list(cons["vars"])
        for idx, a in enumerate(vars_list):
            for b in vars_list[idx + 1:]:
                adj[a].add(b)
                adj[b].add(a)

    visited = set()
    components = []
    var_to_cons = defaultdict(list)
    for ci, cons in enumerate(constraints):
        for v in cons["vars"]:
            var_to_cons[v].append(ci)

    all_vars = set()
    for cons in constraints:
        all_vars.update(cons["vars"])
    for v in adj.keys() | all_vars:
        if v in visited:
            continue
        q = deque([v])
        comp_vars = {v}
        visited.add(v)
        while q:
            u = q.popleft()
            for w in adj[u]:
                if w not in visited:
                    visited.add(w)
                    comp_vars.add(w)
                    q.append(w)
        comp_cons_idx = set()
        for var in comp_vars:
            comp_cons_idx.update(var_to_cons[var])
        comp_cons = [constraints[i] for i in sorted(comp_cons_idx)]
        components.append((comp_vars, comp_cons))
    return components

def frontier_components(knowledge, mine_cells):
    """Convenience: costruisce vincoli e restituisce le componenti della frontiera."""
    constraints, _ = build_constraints(knowledge, mine_cells)
    if not constraints:
        return []
    comps = connected_components_from_constraints(constraints)
    comps = [c for c in comps if c[0]]
    return comps
