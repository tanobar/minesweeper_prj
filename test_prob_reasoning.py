"""
Questo file contiene una suite di test che verifica la correttezza e la robustezza
delle funzioni di calcolo delle probabilità di mina nelle celle sconosciute, 
nonché la scelta della cella a rischio minimo.

Ogni test è pensato per coprire un aspetto specifico del ragionamento probabilistico,
dalla gestione dei casi banali (prior uniforme) a situazioni di simmetria, blending,
calibrazione, enumerazione esatta, gestione di inconsistenze e rispetto di vincoli
come mosse già fatte o mine già note.

I test sono pensati sia per validare la correttezza matematica delle probabilità
calcolate, sia per assicurare che la funzione di scelta (pick_min_risk) si comporti
in modo ragionevole e deterministico nei casi di parità o simmetria.
"""

import sys
from pprint import pprint
from copy import deepcopy
from math import isclose

sys.path.append(".")  # Permette di importare moduli locali dal progetto

from prob.risk import compute_cell_probs, pick_min_risk  # Funzioni principali da testare
from prob.frontier import frontier_components            # Per decomporre la frontiera in componenti
from prob.exact import ExactEnumeration                  # Per enumerazione esatta delle soluzioni

EPS = 1e-12  # Tolleranza numerica per confronti tra float


# ---------------------------
# Helper
# ---------------------------

def show_probs(nr, nc, probs):
    # Crea una griglia testuale delle probabilità, formattando ogni cella con 3 decimali
    grid = [["." for _ in range(nc)] for _ in range(nr)]
    for (i, j), p in probs.items():
        grid[i][j] = f"{p:.3f}"
    return grid

def print_prob_map(title, nr, nc, probs, extra=None):
    # Stampa un titolo, eventuali informazioni extra, il dict delle probabilità e la griglia formattata
    print(f"\n=== {title} ===")
    if extra:
        for k, v in extra.items():
            print(f"{k}: {v}")
    print("Probabilità (dict):")
    pprint(probs)
    print("Mappa probabilità (grid):")
    for row in show_probs(nr, nc, probs):
        print(" ".join(row))

def neighbors8(i, j, n_row, n_col):
    # Generatore che restituisce le coordinate delle 8 celle adiacenti a (i, j), restando nei limiti della griglia
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            r, c = i + di, j + dj
            if 0 <= r < n_row and 0 <= c < n_col:
                yield (r, c)

def count_adj_unknowns(knowledge, v):
    # Conta quante celle sconosciute ("?") sono adiacenti a una cella v
    n_row, n_col = len(knowledge), len(knowledge[0])
    i, j = v
    return sum(1 for r, c in neighbors8(i, j, n_row, n_col)
               if knowledge[r][c] == "?")

# Replica minimale della local pressure del modulo (per un test mirato)
def local_pressure_prob_test(knowledge, mine_cells, v):
    # Calcola una stima della probabilità di mina in una cella v usando la "pressione locale"
    n_row, n_col = len(knowledge), len(knowledge[0])
    i, j = v
    ratios = []
    for r, c in neighbors8(i, j, n_row, n_col):
        cell = knowledge[r][c]
        if isinstance(cell, int) and cell >= 0:
            neigh = list(neighbors8(r, c, n_row, n_col))
            known_mines = sum((nr, nc) in mine_cells for (nr, nc) in neigh)
            unknowns = [(nr, nc) for (nr, nc) in neigh
                        if knowledge[nr][nc] == "?" and (nr, nc) not in mine_cells]
            need = max(0, cell - known_mines)
            denom = max(1, len(unknowns))
            ratio = need / denom
            ratio = min(max(ratio, 0.0), 1.0)
            ratios.append(ratio)
    if not ratios:
        return None
    return sum(ratios) / len(ratios)

def dump_exact_marginals(knowledge, mine_cells=set(), max_vars_exact=22):
    # Per ogni componente della frontiera con poche variabili, calcola e stampa le marginali esatte tramite enumerazione
    comps = frontier_components(knowledge, mine_cells)
    printed = False
    for vars_, cons in comps:
        if vars_ and len(vars_) <= max_vars_exact:
            res = ExactEnumeration(vars_, cons, max_solutions=200_000).run()
            if res and res.get("solutions", 0) > 0:
                print("Marginali esatte su componente piccola:")
                print({v: round(p, 3) for v, p in res["marginals"].items()})
                printed = True
    if not printed:
        print("Nessuna componente piccola per dump esatto.")


# ===================== TEST: FEATURE-BY-FEATURE ========================

# ----------------------------------------------------------------------
# TEST 1: Prior uniforme in assenza di frontiera
# ----------------------------------------------------------------------
def test_no_frontier_prior_uniform():
    """
    Caso base: nessuna cella numerica visibile, quindi nessuna informazione locale.
    Si vuole testare che, in assenza di vincoli, la probabilità di mina sia
    distribuita uniformemente su tutte le celle sconosciute (prior globale).
    """
    # Griglia 3x3 tutta sconosciuta
    K = [["?","?","?"],["?","?","?"],["?","?","?"]]
    total_mines = 3  # prior = 3/9
    # Calcola le probabilità: tutte uguali
    P = compute_cell_probs(K, mine_cells=set(), total_mines=total_mines)

    print_prob_map("Test: no frontier ⇒ prior uniforme",
                   3, 3, P,
                   extra={"atteso p0": f"{total_mines/9:.6f}"})

    # Tutte le probabilità devono essere uguali a 3/9
    for p in P.values():
        assert isclose(p, 3/9, abs_tol=1e-12)
    # pick_min_risk deve restituire una cella sconosciuta
    pick = pick_min_risk(K, moves_made=set(), mine_cells=set(), total_mines=total_mines)
    print("Pick:", pick)
    assert pick is not None and K[pick[0]][pick[1]] == "?"


# ----------------------------------------------------------------------
# TEST 2: Pressione locale + blending (senza calibrazione)
# ----------------------------------------------------------------------
def test_local_pressure_blending_no_calibration():
    """
    Si testa il blending tra prior globale e pressione locale (senza calibrazione).
    Caso: un solo numero '1' con due celle sconosciute adiacenti.
    Ci si aspetta che la probabilità di mina sulle due celle sia una media pesata
    tra prior globale e pressione locale, secondo il parametro alpha.
    """
    # Griglia 3x10: solo la prima riga ha un '1' e due '?'
    K = []
    K.append(["?", 1, "?", "?", "?", "?", "?", "?", "?", "?"])
    K.append([0, 0, 0, "?", "?", "?", "?", "?", "?", "?"])
    K.append(["?"] * 10)

    mine_cells = set()
    total_unknown = sum(1 for i in range(3) for j in range(10) if K[i][j] == "?")
    total_mines = 3
    p0 = total_mines / total_unknown
    alpha = 0.7

    # Calcola le probabilità con blending pressione locale (senza calibrazione)
    P = compute_cell_probs(K, mine_cells, total_mines=total_mines,
                           max_vars_exact=0, calibrate=False)

    # Calcola la pressione locale teorica per due celle simmetriche
    lp_00 = local_pressure_prob_test(K, mine_cells, (0,0))
    lp_02 = local_pressure_prob_test(K, mine_cells, (0,2))
    expected_00 = (1 - alpha) * p0 + alpha * lp_00
    expected_02 = (1 - alpha) * p0 + alpha * lp_02

    print_prob_map("Test: pressione locale (no calibrazione)",
                   3, 10, P,
                   extra={
                       "unknown_tot": total_unknown,
                       "p0": f"{p0:.6f}",
                       "alpha": alpha,
                       "lp(0,0)": f"{lp_00:.6f}",
                       "lp(0,2)": f"{lp_02:.6f}",
                       "expected(0,0)": f"{expected_00:.6f}",
                       "expected(0,2)": f"{expected_02:.6f}",
                   })

    # Verifica che le probabilità calcolate corrispondano a quelle attese
    for v, exp in [((0,0), expected_00), ((0,2), expected_02)]:
        assert isclose(P[v], exp, rel_tol=0, abs_tol=5e-12), (v, P[v], exp)


# ----------------------------------------------------------------------
# TEST 3: Frontiera semplice e scelta min-risk
# ----------------------------------------------------------------------
def test_frontier_min_risk_pick():
    """
    Si testa che, in presenza di una piccola frontiera con due numeri agli angoli,
    la cella centrale sia riconosciuta come quella a rischio minimo.
    Questo verifica la capacità di ragionamento locale e la simmetria.
    """
    # Griglia 3x3 con due '1' agli angoli opposti
    K = [
        [1, "?", "?" ],
        ["?","?","?"],
        ["?","?",  1 ],
    ]
    # Calcola le probabilità
    P = compute_cell_probs(K, mine_cells=set(), total_mines=3)
    print_prob_map("Test: frontiera semplice (min-risk al centro)",
                   3, 3, P)
    dump_exact_marginals(K)
    # La cella centrale deve essere quella a rischio minimo
    pick = pick_min_risk(K, moves_made=set(), mine_cells=set(), total_mines=3)
    print("Pick:", pick)
    assert pick == (1,1)


# ----------------------------------------------------------------------
# TEST 4: Rispetto di mine note e mosse già fatte
# ----------------------------------------------------------------------
def test_forbidden_and_known_mines_respected():
    """
    Si verifica che le celle già rivelate (moves_made) e quelle marcate come mine note
    (mine_cells) vengano escluse sia dal calcolo delle probabilità che dalla scelta.
    """
    # Griglia 3x3 con una mina nota e una mossa già fatta
    K = [
        [1, "?", "?" ],
        ["?","?","?"],
        ["?","?",  1 ],
    ]
    mine_cells = {(0,1)}
    K[0][1] = "X"  # Marca la mina nota
    moves_made = {(1,1)}  # Cella già rivelata

    # Calcola le probabilità
    P = compute_cell_probs(K, mine_cells)
    print_prob_map("Test: rispetto di mine note e mosse fatte",
                   3, 3, P,
                   extra={"mine_cells": mine_cells, "moves_made": moves_made})
    # pick_min_risk non deve restituire né la mina nota né la cella già rivelata
    pick = pick_min_risk(K, moves_made, mine_cells)
    print("Pick:", pick)
    assert pick is not None and pick != (1,1) and pick != (0,1)


# ----------------------------------------------------------------------
# TEST 5: Ricalibrazione soft (budget alignment)
# ----------------------------------------------------------------------
def test_soft_calibration_budget_alignment():
    """
    Si testa che la ricalibrazione soft delle probabilità (calibration) porti la somma
    delle probabilità a coincidere (entro il 10%) con il numero di mine rimaste.
    Inoltre, si verifica che tutte le probabilità siano clampate in [0,1].
    """
    # Griglia 3x3 con molti vincoli
    K = [
        [1, "?", "?"],
        [1, "?", "?"],
        [1,  1 ,  1 ],
    ]
    total_mines = 2
    # Calcola le probabilità
    P = compute_cell_probs(K, mine_cells=set(), total_mines=total_mines)
    S = sum(P.values())
    print_prob_map("Test: ricalibrazione soft (budget alignment)",
                   3, 3, P,
                   extra={"total_mines": total_mines, "sum(p)": f"{S:.6f}"})
    # Tutte le probabilità devono essere tra 0 e 1, e la somma vicina al numero di mine
    assert all(0.0 <= p <= 1.0 for p in P.values())
    assert abs(S - total_mines) <= 0.2  # 10% di 2


# ----------------------------------------------------------------------
# TEST 6: Accordo con enumerazione esatta su micro-frontiera
# ----------------------------------------------------------------------
def test_exact_enumeration_agreement_on_small_component():
    """
    Si verifica che, su una micro-frontiera (pochi '?' e vincoli), il calcolo
    delle probabilità tramite il metodo principale coincida con quello ottenuto
    tramite enumerazione esatta di tutte le soluzioni compatibili.
    """
    # Griglia 3x3 con simmetria centrale
    K = [
        [1, "?", 1],
        ["?", 2, "?"],
        [1, "?", 1],
    ]
    # Calcola le probabilità con enumerazione esatta abilitata
    P = compute_cell_probs(K, mine_cells=set(), total_mines=4, max_vars_exact=22)
    print_prob_map("Test: accordo con enumerazione esatta (micro-frontiera)",
                   3, 3, P)
    # Calcola anche le marginali esatte per confronto
    comps = frontier_components(K, set())
    vars_, cons = comps[0]
    res = ExactEnumeration(vars_, cons, max_solutions=200_000).run()
    marg = res["marginals"]
    print("Marginali esatte:", {v: round(p, 6) for v, p in marg.items()})
    # Le probabilità devono coincidere
    for v, p_star in marg.items():
        assert abs(P[v] - p_star) <= 1e-9, (v, P[v], p_star)


# ----------------------------------------------------------------------
# TEST 7: Monotonia delle probabilità con nuova informazione
# ----------------------------------------------------------------------
def test_monotonicity_with_new_information():
    """
    Si verifica che, aggiungendo nuova informazione corretta (es. rivelando una safe
    o flaggando una mina adiacente), la probabilità di mina in una cella non aumenti.
    Questo garantisce la coerenza del reasoning rispetto all'evidenza.
    """
    # Griglia 3x3 simmetrica
    K = [
        [1, "?", 1],
        ["?", 2, "?"],
        [1, "?", 1],
    ]
    v = (1, 0)
    # Calcola le probabilità iniziali
    P = compute_cell_probs(K, mine_cells=set(), total_mines=5)
    p_before = P[v]
    print_prob_map("Test: monotonia (stato iniziale)",
                   3, 3, P, extra={"v": v, "p_before": f"{p_before:.6f}"})

    # Rivela una safe adiacente
    K2 = deepcopy(K)
    K2[0][0] = 1
    P2 = compute_cell_probs(K2, mine_cells=set(), total_mines=5)
    print_prob_map("Test: monotonia (dopo reveal safe adiacente)",
                   3, 3, P2, extra={"v": v, "p_after": f"{P2[v]:.6f}"})
    assert P2[v] <= p_before + EPS

    # Flagga una mina ADIACENTE a v
    mines = {(0, 1)}
    P3 = compute_cell_probs(K, mine_cells=mines, total_mines=5)
    print_prob_map("Test: monotonia (dopo flag mina adiacente)",
                   3, 3, P3, extra={"v": v, "p_after": f"{P3[v]:.6f}", "mine_cells": mines})
    assert P3[v] <= p_before + EPS


# ----------------------------------------------------------------------
# TEST 8: Prior uniforme sulle vere celle "outside"
# ----------------------------------------------------------------------
def test_outside_prior_uniform_true_outside_cells():
    """
    Si verifica che le celle davvero fuori dalla frontiera (cioè non adiacenti a
    nessun numero) ricevano tutte la stessa probabilità (prior uniforme).
    """
    # Griglia 4x4 con un solo numero al centro
    K = [
        ["?", "?", "?", "?"],
        ["?",  1 , "?", "?"],
        ["?", "?", "?", "?"],
        ["?", "?", "?", "?"],
    ]
    total_mines = 5
    # Calcola le probabilità
    P = compute_cell_probs(K, mine_cells=set(), total_mines=total_mines)

    # Celle fuori dalla 8-neighborhood del numero
    outside = [(i, j) for i in range(4) for j in range(4)
               if not (abs(i-1) <= 1 and abs(j-1) <= 1) and K[i][j] == "?"]
    vals = [P[v] for v in outside]
    info = {"outside_cells": outside, "outside_values": [round(x,6) for x in vals]}
    print_prob_map("Test: outside prior uniforme (vere outside)", 4, 4, P, extra=info)

    # Tutte le celle outside devono avere la stessa probabilità
    assert max(vals) - min(vals) <= 1e-12


# ----------------------------------------------------------------------
# TEST 9: Scelta forzata probabilistica in caso di parità
# ----------------------------------------------------------------------
def test_forced_probabilistic_choice():
    """
    Si verifica che, in assenza di deduzioni certe, le probabilità siano uguali
    e la scelta della cella a rischio minimo sia deterministica tra i minimi.
    """
    # Griglia 2x2 simmetrica
    K = [
        ["?", 1],
        [1, "?"],
    ]
    # Calcola le probabilità
    P = compute_cell_probs(K, mine_cells=set(), total_mines=1)
    print_prob_map("Test: tie probabilistico (2x2 simmetrico)",
                   2, 2, P)

    # Le due celle sconosciute devono avere probabilità 0.5
    assert isclose(P[(0,0)], 0.5, abs_tol=1e-12)
    assert isclose(P[(1,1)], 0.5, abs_tol=1e-12)
    # pick_min_risk deve scegliere una delle due
    pick = pick_min_risk(K, moves_made=set(), mine_cells=set(), total_mines=1)
    print("Pick:", pick)
    assert pick in [(0,0), (1,1)]


# ----------------------------------------------------------------------
# TEST 10: Simmetria 3x3 e tie-break informativo
# ----------------------------------------------------------------------
def test_symmetry_3x3_and_informative_tiebreak():
    """
    Si verifica che, in una situazione simmetrica, tutte le celle interne abbiano
    la stessa probabilità, ma il tie-break informativo favorisca la cella centrale
    (quella con più '?' adiacenti).
    """
    # Griglia 3x3 con simmetria centrale
    K = [
        [1, "?", 1],
        ["?", "?", "?"],
        [1, "?", 1],
    ]
    # Calcola le probabilità
    P = compute_cell_probs(K, mine_cells=set(), total_mines=2)
    print_prob_map("Test: simmetria 3x3 + tie-break informativo",
                   3, 3, P)

    # Tutte le celle interne devono avere probabilità 1/3
    for v in [(0,1),(1,0),(1,1),(1,2),(2,1)]:
        assert isclose(P[v], 1/3, abs_tol=1e-12)
    # pick_min_risk deve scegliere il centro
    pick = pick_min_risk(K, moves_made=set(), mine_cells=set(), total_mines=2)
    print("Pick:", pick)
    assert pick == (1,1)
    # sanity: il centro ha più '?' adiacenti
    center = count_adj_unknowns(K, (1,1))
    for v in [(0,1),(1,0),(1,2),(2,1)]:
        assert center > count_adj_unknowns(K, v)


# ----------------------------------------------------------------------
# TEST 11: Simmetria 4x4, tutte le interne uguali
# ----------------------------------------------------------------------
def test_symmetry_4x4_internals_equal():
    """
    Si verifica che, in una griglia 4x4 simmetrica con 4 mine, tutte le celle
    interne abbiano la stessa probabilità e che la scelta cada su una di esse.
    """
    # Griglia 4x4 con simmetria centrale
    K = [
        [1, "?", "?", 1],
        ["?", "?", "?", "?"],
        ["?", "?", "?", "?"],
        [1, "?", "?", 1],
    ]
    # Calcola le probabilità
    P = compute_cell_probs(K, mine_cells=set(), total_mines=4)
    print_prob_map("Test: simmetria 4x4 (interne uguali a 1/3)",
                   4, 4, P)

    # Tutte le celle interne devono avere probabilità 1/3
    internals = [
        (0,1), (0,2),
        (1,0), (1,1), (1,2), (1,3),
        (2,0), (2,1), (2,2), (2,3),
        (3,1), (3,2)
    ]
    for v in internals:
        assert isclose(P[v], 1/3, abs_tol=1e-12)
    # pick_min_risk deve scegliere una delle interne
    pick = pick_min_risk(K, moves_made=set(), mine_cells=set(), total_mines=4)
    print("Pick:", pick)
    assert pick in internals


# ----------------------------------------------------------------------
# TEST 12: Fallback su prior simmetrico in caso di inconsistenza
# ----------------------------------------------------------------------
def test_inconsistency_fallback_prior():
    """
    Si verifica che, in presenza di vincoli incompatibili (es. due numeri che
    impongono condizioni impossibili sugli stessi '?'), il sistema ricada su un
    prior simmetrico per le celle coinvolte, senza crashare.
    """
    # Griglia 2x3 con vincoli incompatibili
    K = [
        [2, "?", "?"],
        [0, "?", "?"],
    ]
    # Calcola le probabilità
    P = compute_cell_probs(K, mine_cells=set(), total_mines=None)
    vals = [P[(0,1)], P[(0,2)], P[(1,1)], P[(1,2)]]
    print_prob_map("Test: fallback su inconsistenza (prior simmetrico)",
                   2, 3, P,
                   extra={"valori_celle_coinvolte": [round(x,6) for x in vals]})

    # Tutte le celle coinvolte devono avere la stessa probabilità
    assert max(vals) - min(vals) <= 1e-12
    for p in vals:
        assert 0.0 <= p <= 1.0


# ---------------------------
# Main manuale
# ---------------------------
if __name__ == "__main__":
    # Lista di tutti i test da eseguire
    tests = [
        test_no_frontier_prior_uniform,
        test_local_pressure_blending_no_calibration,
        test_frontier_min_risk_pick,
        test_forbidden_and_known_mines_respected,
        test_soft_calibration_budget_alignment,
        test_exact_enumeration_agreement_on_small_component,
        test_monotonicity_with_new_information,
        test_outside_prior_uniform_true_outside_cells,
        test_forced_probabilistic_choice,
        test_symmetry_3x3_and_informative_tiebreak,
        test_symmetry_4x4_internals_equal,
        test_inconsistency_fallback_prior,
    ]
    failures = 0
    # Esegue ogni test e stampa il risultato
    for t in tests:
        try:
            print(f"\nRunning {t.__name__}...")
            t()
        except AssertionError as e:
            failures += 1
            print(f"{t.__name__} failed: {e}")
        else:
            print(f"{t.__name__} passed")
    if failures == 0:
        print("\nTutti i test reasoning PB sono passati.")
    else:
        print(f"\n{failures} test falliti su {len(tests)}.")