# tests/test_prob_fallback.py
# Esegui da root del progetto:  python -m tests.test_prob_fallback

import sys
from pprint import pprint

# Aggiusta il path se necessario (dipende da dove lanci il file)
sys.path.append(".")

from prob.risk import compute_cell_probs, pick_min_risk

def show_probs(n, probs):
    grid = [["." for _ in range(n)] for _ in range(n)]
    for (i, j), p in probs.items():
        grid[i][j] = f"{p:.3f}"
    return grid

def test_case_1():
    """
    3x3:
      1 ? ?
      ? ? ?
      ? ? 1
    Nessuna mina nota. Ci sono 2 vincoli: somma=1 sui due angoli.
    Risultato atteso: la cella centrale (1,1) risulta la meno rischiosa.
    """
    n = 3
    knowledge = [
        [1, "?", "?" ],
        ["?","?","?"],
        ["?","?",  1 ],
    ]
    mine_cells = set()
    moves_made = set()

    probs = compute_cell_probs(knowledge, mine_cells)
    print("\n=== Test 1: Probabilità sulla frontiera ===")
    pprint(probs)
    print("Mappa probabilità:")
    for row in show_probs(n, probs):
        print(" ".join(row))

    pick = pick_min_risk(knowledge, moves_made, mine_cells)
    print("Pick min risk:", pick)
    assert pick == (1,1), "Mi aspetto che scelga la cella centrale (1,1)."

def test_case_2_no_frontier():
    """
    Griglia tutta ignota: nessun vincolo.
    Il picker deve restituire una qualunque cella '?' (di solito la prima non vietata).
    """
    n = 3
    knowledge = [
        ["?","?","?"],
        ["?","?","?"],
        ["?","?","?"],
    ]
    mine_cells = set()
    moves_made = set()

    probs = compute_cell_probs(knowledge, mine_cells)
    print("\n=== Test 2: Nessuna frontiera ===")
    pprint(probs)  # dovrebbe essere {}
    pick = pick_min_risk(knowledge, moves_made, mine_cells)
    print("Pick (nessuna frontiera):", pick)
    assert pick is not None and knowledge[pick[0]][pick[1]] == "?"

def test_case_3_forbidden_and_known_mines():
    """
    Verifica che moves_made / mine_cells / forbidden vengano rispettati.
    - Mark una mina nota.
    - Escludi una cella con moves_made.
    """
    n = 3
    knowledge = [
        [1, "?", "?" ],
        ["?","?","?"],
        ["?","?",  1 ],
    ]
    mine_cells = {(0,1)}      # supponiamo sia nota
    knowledge[0][1] = "X"     # riflette la conoscenza
    moves_made = {(1,1)}      # l'abbiamo già provata

    probs = compute_cell_probs(knowledge, mine_cells)
    print("\n=== Test 3: mine note e mosse già fatte ===")
    pprint(probs)
    pick = pick_min_risk(knowledge, moves_made, mine_cells)
    print("Pick con vincoli:", pick)
    assert pick is not None and pick != (1,1) and pick != (0,1)

if __name__ == "__main__":
    test_case_1()
    test_case_2_no_frontier()
    test_case_3_forbidden_and_known_mines()
    print("\nTutti i test locali sono passati.")
