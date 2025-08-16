# prob/risk.py

DEBUG_RISK = False  # o mettilo a False se vuoi silenzio

from .frontier import frontier_components
from .exact import ExactEnumeration
from .approximate import RandomizedSampler

def compute_cell_probs(knowledge, mine_cells=None, max_vars_exact=18, max_solutions=200000):
    """
    Calcola P(mina) per le celle di frontiera usando enumerazione esatta per
    ciascuna componente connessa (se piccola), altrimenti un fallback euristico.
    Ritorna: dict {(i,j): p_mina in [0,1]}
    """
    comps = frontier_components(knowledge, mine_cells or set())
    if not comps:
        return {}
    probs = {}
    for vars_set, cons in comps:
        if len(vars_set) <= max_vars_exact:
            solver = ExactEnumeration(vars_set, cons, max_solutions=max_solutions)
            result = solver.run()
            if result and result["solutions"] > 0:
                marg = result["marginals"]
                for v in vars_set:
                    probs[v] = marg.get(v, 0.0)  # P(X=1) = P(mine)
            else:
                # fallback: prior non informativo
                for v in vars_set:
                    probs[v] = 0.5
        else:
            sampler = RandomizedSampler(vars_set, cons, max_samples=10000, max_nodes=500000, seed=0)
            result = sampler.run()
            if result and result["solutions"] > 0:
                marg = result["marginals"]
                for v in vars_set:
                    probs[v] = marg.get(v, 0.0)
            else:
                # fallback prudenziale se non riesce a trovare soluzioni
                for v in vars_set:
                    probs[v] = 0.5
    return probs

def pick_min_risk(knowledge, moves_made=None, mine_cells=None, forbidden=None):
    """
    Sceglie la cella ignota con P(mina) minima tra quelle in frontiera.
    Se non esistono vincoli di frontiera o candidati, sceglie la prima "?" non vietata.
    Ritorna: (i,j) o None.
    """
    n = len(knowledge)
    moves_made = set(moves_made or [])
    mine_cells = set(mine_cells or [])
    forbidden = set(forbidden or []) | moves_made | mine_cells

    probs = compute_cell_probs(knowledge, mine_cells)

    if DEBUG_RISK:
        ranked = sorted([(p,v) for v,p in probs.items()], key=lambda x: x[0])
        print("[RISK] top candidates:", [(v, round(p,3)) for p,v in ranked[:5]])

    if probs:
        candidates = [(p, v) for v, p in probs.items()
                      if v not in forbidden and knowledge[v[0]][v[1]] == "?"]
        if candidates:
            candidates.sort(key=lambda x: (x[0], x[1]))  # (p, tie-break per coordinate)
            return candidates[0][1]

    # Nessuna frontiera o nessun candidato: qualunque "?" non vietata
    for i in range(n):
        for j in range(n):
            if knowledge[i][j] == "?" and (i, j) not in forbidden:
                return (i, j)
    return None
