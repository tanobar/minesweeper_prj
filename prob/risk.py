# prob/risk.py — S1: frontier + exact only (NO sampler)
DEBUG_RISK = False

import random

EPS = 1e-12

from .frontier import frontier_components
from .exact import ExactEnumeration

def compute_cell_probs(knowledge, mine_cells=None, total_mines=None,
                       max_vars_exact=22, max_solutions=200000, calibrate=True):
    """
    Restituisce P(mina) per ogni cella "?".

    - Componenti di frontiera piccole (<= max_vars_exact): enumerazione esatta.
    - Componenti grandi: prior p0 e poi raffinamento con "pressione locale".
    - Celle fuori frontiera: prior p0 OUTSIDE calcolato rispettando il budget di mine.
    - Ricalibrazione soft SOLO sulle celle non-esatte.
    """
    n = len(knowledge)
    mine_cells = set(mine_cells or [])

    # --- helper locali ---
    def neighbors8(i, j):
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                r, c = i + di, j + dj
                if 0 <= r < n and 0 <= c < n:
                    yield (r, c)

    def local_pressure_prob(v):
        """Media dei rapporti (mine-da-mettere)/(ignote) sui numeri adiacenti a v."""
        i, j = v
        ratios = []
        for r, c in neighbors8(i, j):
            cell = knowledge[r][c]
            if isinstance(cell, int) and cell >= 0:
                neigh = list(neighbors8(r, c))
                known_mines = sum((nr, nc) in mine_cells for (nr, nc) in neigh)
                unknowns = [(nr, nc) for (nr, nc) in neigh
                            if knowledge[nr][nc] == "?" and (nr, nc) not in mine_cells]
                need = max(0, cell - known_mines)
                denom = max(1, len(unknowns))
                ratio = need / denom
                if ratio < 0.0: ratio = 0.0
                if ratio > 1.0: ratio = 1.0
                ratios.append(ratio)
        if not ratios:
            return None
        return sum(ratios) / len(ratios)

    # --- ignote candidate ---
    unknown = [(i, j) for i in range(n) for j in range(n)
               if knowledge[i][j] == "?" and (i, j) not in mine_cells]
    if not unknown:
        return {}

    # --- prior grezzo (fallback) ---
    if total_mines is not None:
        mines_remaining = max(0.0, float(total_mines - len(mine_cells)))
        p0_fallback = mines_remaining / max(1.0, float(len(unknown)))
    else:
        mines_remaining = None
        p0_fallback = 0.5

    # --- fronte: esatto dove possibile ---
    from .frontier import frontier_components
    from .exact import ExactEnumeration

    comps = frontier_components(knowledge, mine_cells)
    probs = {}
    frontier_vars = set()
    exact_vars = set()   # <- celle con marginale "bloccata" da enumerazione esatta

    for vars_set, cons in comps:
        if not vars_set:
            continue
        frontier_vars |= vars_set

        if len(vars_set) <= max_vars_exact:
            res = ExactEnumeration(vars_set, cons, max_solutions=max_solutions).run()
            if res and res.get("solutions", 0) > 0:
                for v, p in res["marginals"].items():
                    probs[v] = float(p)
                    exact_vars.add(v)
            else:
                for v in vars_set:
                    probs[v] = p0_fallback
        else:
            for v in vars_set:
                probs[v] = p0_fallback

    # --- fuori frontiera: prior che rispetta (per quanto possibile) il budget ---
    outside = [v for v in unknown if v not in frontier_vars]
    if outside:
        if mines_remaining is None:
            p0_out = p0_fallback
        else:
            # aspettativa di mine già "impegnata" sulla frontiera (esatto + fallback)
            E_frontier = sum(probs.get(v, p0_fallback) for v in frontier_vars)
            left_for_outside = max(0.0, mines_remaining - E_frontier)
            p0_out = left_for_outside / max(1.0, float(len(outside)))
            p0_out = min(max(p0_out, 0.0), 1.0)
        for v in outside:
            probs[v] = p0_out

    # --- raffinamento locale (solo celle non-esatte) ---
    ALPHA = 0.7
    for v in unknown:
        if v in exact_vars:
            continue
        pv = probs.get(v, p0_fallback)
        lp = local_pressure_prob(v)
        if lp is not None:
            probs[v] = (1.0 - ALPHA) * pv + ALPHA * lp
        else:
            probs[v] = pv  # resta il prior corrente

    # --- ricalibrazione soft SOLO su celle non-esatte ---
    if calibrate and (mines_remaining is not None) and unknown:
        flex = [u for u in unknown if u not in exact_vars]
        if flex:
            S_exact = sum(probs[u] for u in exact_vars)
            S_flex  = sum(probs.get(u, p0_fallback) for u in flex)
            target_flex = max(0.0, mines_remaining - S_exact)
            tol = 0.10 * max(1.0, target_flex)  # ricalibra solo se scarto significativo
            if S_flex > 0.0 and abs(S_flex - target_flex) > tol:
                scale = target_flex / S_flex
                for u in flex:
                    p = probs.get(u, p0_fallback) * scale
                    if p < 0.0: p = 0.0
                    if p > 1.0: p = 1.0
                    probs[u] = p

    return probs


def pick_min_risk(knowledge, moves_made=None, mine_cells=None, **kwargs):
    """
    Sceglie la '?' con P(mina) minima (tie-break per coordinate).
    """
    n = len(knowledge)
    moves_made = set(moves_made or [])
    mine_cells = set(mine_cells or [])
    forbidden = moves_made | mine_cells

    
    # Costruisci i parametri per compute_cell_probs
    max_vars_exact = kwargs.get("max_vars_exact", 22)
    max_solutions  = kwargs.get("max_solutions", 200000)
    total_mines    = kwargs.get("total_mines", None)

    probs = compute_cell_probs(
        knowledge,
        mine_cells,
        total_mines=total_mines,
        max_vars_exact=max_vars_exact,
        max_solutions=max_solutions,
        calibrate=True
    )

    candidates = [(p, v) for v, p in probs.items()
              if v not in forbidden and knowledge[v[0]][v[1]] == "?"]
    if candidates:
        # tie-break RANDOM tra i minimi (invece di ordinare per coordinate)
        pmin = min(p for p, _ in candidates)
        bucket = [v for p, v in candidates if abs(p - pmin) <= EPS]
        #choice = random.choice(bucket)
        choice = max(bucket, key=lambda v: _info_score(knowledge, v))
        if DEBUG_RISK:
            top = sorted(candidates, key=lambda x: x[0])[:5]
            print("[RISK] min=", round(pmin, 4), "bucket=", bucket, "top5=", [(v, round(p,3)) for p, v in top])
        return choice

    # fallback: prima "?" libera
    for i in range(n):
        for j in range(n):
            if knowledge[i][j] == "?" and (i, j) not in forbidden:
                return (i, j)
    return None

# --- util locali ---

def _info_score(knowledge, v):
    n = len(knowledge); i, j = v
    s = 0
    for di in (-1,0,1):
        for dj in (-1,0,1):
            if di==0 and dj==0: continue
            r, c = i+di, j+dj
            if 0<=r<n and 0<=c<n and knowledge[r][c] == "?":
                s += 1
    return s

def neighbors8(i, j, n):
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0: 
                continue
            r, c = i + di, j + dj
            if 0 <= r < n and 0 <= c < n:
                return_cell = (r, c)
                yield return_cell

def local_pressure_prob(knowledge, mine_cells, v):
    n = len(knowledge)
    i, j = v
    ratios = []
    for r, c in neighbors8(i, j, n):
        cell = knowledge[r][c]
        if isinstance(cell, int) and cell >= 0:  # è un numero rivelato
            # quante mine note attorno a (r,c)?
            neigh = list(neighbors8(r, c, n))
            known_mines = sum((nr, nc) in mine_cells for (nr, nc) in neigh)
            unknowns = [(nr, nc) for (nr, nc) in neigh if knowledge[nr][nc] == "?" and (nr, nc) not in mine_cells]
            need = max(0, cell - known_mines)
            denom = max(1, len(unknowns))
            ratios.append(need / denom)
    if not ratios:
        return None  # nessuna informazione locale
    return sum(ratios) / len(ratios)
