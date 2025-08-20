# prob/risk.py — S1: frontier + exact only (NO sampler)
DEBUG_RISK = False

from .frontier import frontier_components
from .exact import ExactEnumeration

def compute_cell_probs(knowledge, mine_cells=None, max_vars_exact=18, max_solutions=200000):
    """
    P(mina) per le '?'.
    - Componenti di frontiera piccole (<= max_vars_exact): enumerazione esatta.
    - Componenti grandi: fallback neutro 0.5 (nessun sampler).
    - Celle '?' fuori dalla frontiera: 0.5.
    """
    n = len(knowledge)
    mine_cells = set(mine_cells or [])
    unknown = [(i, j) for i in range(n) for j in range(n)
               if knowledge[i][j] == "?" and (i, j) not in mine_cells]
    if not unknown:
        return {}

    comps = frontier_components(knowledge, mine_cells)
    probs = {}
    frontier_vars = set()

    for vars_set, cons in comps:
        if not vars_set:
            continue
        frontier_vars |= vars_set

        if len(vars_set) <= max_vars_exact:
            res = ExactEnumeration(vars_set, cons, max_solutions=max_solutions).run()
            if res and res.get("solutions", 0) > 0:
                probs.update({v: float(p) for v, p in res["marginals"].items()})
            else:
                for v in vars_set: probs[v] = 0.5
        else:
            for v in vars_set: probs[v] = 0.5

    # Fuori frontiera: 0.5
    for v in unknown:
        if v not in frontier_vars:
            probs[v] = 0.5

    return probs

def pick_min_risk(knowledge, moves_made=None, mine_cells=None, **kwargs):
    """
    Sceglie la '?' con P(mina) minima (tie-break per coordinate).
    """
    n = len(knowledge)
    moves_made = set(moves_made or [])
    mine_cells = set(mine_cells or [])
    forbidden = moves_made | mine_cells

    probs = compute_cell_probs(knowledge, mine_cells, **{k: kwargs[k] for k in ("max_vars_exact","max_solutions") if k in kwargs})

    candidates = [(p, v) for v, p in probs.items()
                  if v not in forbidden and knowledge[v[0]][v[1]] == "?"]
    if candidates:
        candidates.sort(key=lambda x: (x[0], x[1]))
        if DEBUG_RISK:
            print("[RISK] top:", [(v, round(p,3)) for p, v in candidates[:5]])
        return candidates[0][1]

    # fallback: prima "?" libera
    for i in range(n):
        for j in range(n):
            if knowledge[i][j] == "?" and (i, j) not in forbidden:
                return (i, j)
    return None
