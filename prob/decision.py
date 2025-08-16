# prob/decision.py
from .risk import compute_cell_probs

def pick_by_expected_utility(knowledge, moves_made=None, mine_cells=None, u_safe=+1.0, u_mine=-10.0):
    """
    Sceglie la cella che massimizza l'utilità attesa:
      EU(cell) = (1 - p_mine) * u_safe + p_mine * u_mine
    """
    n = len(knowledge)
    moves_made = set(moves_made or [])
    mine_cells = set(mine_cells or [])
    forbidden = moves_made | mine_cells

    probs = compute_cell_probs(knowledge, mine_cells)
    best = None
    best_eu = None
    for (i,j), p in probs.items():
        if (i,j) in forbidden: 
            continue
        if knowledge[i][j] != "?":
            continue
        eu = (1.0 - p) * u_safe + p * u_mine
        if best_eu is None or eu > best_eu:
            best_eu = eu
            best = (i,j)
    if best is not None:
        return best

    # fallback: nessuna frontiera o tutto vietato → prima "?" disponibile
    for i in range(n):
        for j in range(n):
            if knowledge[i][j] == "?" and (i,j) not in forbidden:
                return (i,j)
    return None
