# Classe che fornisce le funzioni principali per il reasoning probabilistico:
# - compute_cell_probs: calcola la probabilità che ogni cella "?" sia una mina,
#   combinando enumerazione esatta, prior globale e pressione locale.
# - pick_min_risk: sceglie la cella "?" a rischio minimo, con tie-break informativo.
#
# Il reasoning si basa su:
#   - Enumerazione esatta per componenti di frontiera piccole (tramite ExactEnumeration)
#   - Prior globale per celle fuori dalla frontiera o in componenti troppo grandi
#   - Pressione locale per affinare la stima sulle celle non coperte da enumerazione esatta
#   - Ricalibrazione soft per rispettare il budget di mine rimaste

DEBUG_RISK = False

import random

EPS = 1e-12

from .frontier import frontier_components
from .exact import ExactEnumeration

def compute_cell_probs(knowledge, mine_cells=None, total_mines=None,
                       max_vars_exact=22, max_solutions=200000, calibrate=True):
    """
    Calcola la probabilità P(mina) per ogni cella "?" della griglia.

    - Per componenti di frontiera piccole (<= max_vars_exact): enumerazione esatta.
    - Per componenti grandi: prior p0 e raffinamento con pressione locale.
    - Celle fuori frontiera: prior p0 OUTSIDE calcolato rispettando il budget di mine.
    - Ricalibrazione soft SOLO sulle celle non-esatte per rispettare il budget totale.

    knowledge: griglia di stato (numeri, "?", "X")
    mine_cells: celle già note come mine (set)
    total_mines: numero totale di mine nella partita (se noto)
    max_vars_exact: soglia per usare enumerazione esatta
    max_solutions: limite di soluzioni per enumerazione esatta
    calibrate: se True, ricalibra le probabilità per rispettare il budget di mine
    
    Restituisce:
        - probs: dizionario {(i,j): p} con la probabilità che la cella sia mina
    """
    n_row = len(knowledge)
    n_col = len(knowledge[0])
    mine_cells = set(mine_cells or [])

    # --- helper locali ---
    def neighbors8(i, j):
        # Generatore delle 8 celle adiacenti a (i,j)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                r, c = i + di, j + dj # Calcolo coordinate della cella vicina
                if 0 <= r < n_row and 0 <= c < n_col:
                    yield (r, c) # Ritorno solo se dentro i limiti della griglia

    def local_pressure_prob(v):
        """
        Calcola la pressione locale su una cella v, cioè una stima della probabilità che sia mina
        basata solo sulle informazioni numeriche locali attorno a v.

        - Per ogni cella numerica adiacente a v (cioè ogni cella rivelata con un numero 0..8),
            si considera il vincolo locale: "tra le sue celle ignote adiacenti devono esserci esattamente N mine".
        - Per ciascuna di queste celle numeriche, si calcola il rapporto:
            (mine-da-mettere) / (numero di ignote adiacenti)
            dove:
            - mine-da-mettere = numero richiesto dalla cella numerica meno le mine già note attorno
            - numero di ignote adiacenti = quante celle "?" (non già marcate come mine) ci sono attorno a quella cella numerica
        - Si raccolgono tutti questi rapporti (uno per ogni cella numerica adiacente a v).
        - La pressione locale su v è la media di questi rapporti.
            Se v è adiacente a più numeri, la sua pressione sarà la media delle pressioni locali "percepite" da ciascun numero.

        Questo valore serve come stima locale della probabilità che v sia mina,
        utile quando non si può fare enumerazione esatta (ad esempio per celle fuori dalla frontiera o in componenti troppo grandi).

        Se v non è adiacente a nessuna cella numerica, la funzione restituisce None.

        Esempio pratico:
        Se v è adiacente a una cella numerica 2 che ha 3 ignote attorno e 0 mine già note,
        la pressione locale sarà 2/3 ≈ 0.67.
        Se v è adiacente a più numeri, si fa la media.

        Parametri:
            v: tupla (i, j) della cella di cui stimare la pressione locale.

        Restituisce:
            float: pressione locale stimata (tra 0 e 1), oppure None se non ci sono numeri adiacenti.
        """
        i, j = v # Estraggo le coordinate della cella da valutare
        ratios = [] # Lista dei rapporti pressione calcolati per ogni numero adiacente
        for r, c in neighbors8(i, j): # Scorro tutte le celle adiacenti a v
            cell = knowledge[r][c] # Prendo il valore della cella adiacente
            if isinstance(cell, int) and cell >= 0: # Se è una cella numerica rivelata
                neigh = list(neighbors8(r, c)) # Prendo tutte le celle adiacenti a questa cella numerica
                # Conta quante mine già note ci sono attorno a (r, c)
                known_mines = sum((nr, nc) in mine_cells for (nr, nc) in neigh) # Conteggio mine già note attorno
                # Lista delle celle ignote (non ancora marcate come mine) attorno a (r, c)
                unknowns = [(nr, nc) for (nr, nc) in neigh
                            if knowledge[nr][nc] == "?" and (nr, nc) not in mine_cells]
                need = max(0, cell - known_mines) # Numero di mine che mancano ancora da mettere attorno a (r, c)
                denom = max(1, len(unknowns)) # Numero di ignote attorno (almeno 1 per evitare divisione per zero)
                ratio = need / denom # Rapporto pressione locale
                # Clamp tra 0 e 1 per sicurezza numerica
                if ratio < 0.0: ratio = 0.0
                if ratio > 1.0: ratio = 1.0
                ratios.append(ratio) # Aggiungo il rapporto alla lista
        if not ratios:
            return None # Nessuna informazione locale: v non è adiacente a nessun numero
        return sum(ratios) / len(ratios) # Faccio la media delle pressioni locali

    # --- ignote candidate ---
    unknown = [(i, j) for i in range(n_row) for j in range(n_col)
               if knowledge[i][j] == "?" and (i, j) not in mine_cells] # Tutte le celle "?" non già marcate come mine
    if not unknown:
        return {} # Se non ci sono celle ignote, ritorno dizionario vuoto

    # --- prior grezzo (fallback) ---
    if total_mines is not None:
        mines_remaining = max(0.0, float(total_mines - len(mine_cells))) # Mine rimaste da piazzare
        p0_fallback = mines_remaining / max(1.0, float(len(unknown))) # Prior uniforme sulle ignote
    else:
        mines_remaining = None # Se non so il totale, non posso calcolare il budget
        p0_fallback = 0.5  # Prior di default se non si sa nulla

    # --- frontiera: enumerazione esatta dove possibile ---
    comps = frontier_components(knowledge, mine_cells)  # Trovo le componenti di frontiera
    probs = {} # Dizionario delle probabilità finali per ogni cella
    frontier_vars = set() # Celle che fanno parte della frontiera
    exact_vars = set() # Celle per cui ho una marginale esatta

    for vars_set, cons in comps: # Scorro ogni componente di frontiera
        if not vars_set:
            continue  # Salto componenti vuote
        frontier_vars |= vars_set # Aggiungo tutte le celle della componente alla frontiera

        if len(vars_set) <= max_vars_exact:
            # Se la componente è piccola, uso enumerazione esatta
            res = ExactEnumeration(vars_set, cons, max_solutions=max_solutions).run()
            if res and res.get("solutions", 0) > 0:
                for v, p in res["marginals"].items(): # Scorro tutte le marginali trovate
                    probs[v] = float(p) # Salvo la probabilità esatta
                    exact_vars.add(v) # Segno che questa cella ha una stima esatta
            else:
                # Se enumerazione fallisce, fallback su prior
                for v in vars_set:
                    probs[v] = p0_fallback
        else:
            # Componenti troppo grandi: fallback su prior
            for v in vars_set:
                probs[v] = p0_fallback

    # --- fuori frontiera: prior che rispetta (per quanto possibile) il budget ---
    outside = [v for v in unknown if v not in frontier_vars] # Celle ignote fuori dalla frontiera
    if outside:
        if mines_remaining is None:
            p0_out = p0_fallback # Se non so il budget, uso prior di default
        else:
            E_frontier = sum(probs.get(v, p0_fallback) for v in frontier_vars)  # Somma delle mine "attese" in frontiera
            left_for_outside = max(0.0, mines_remaining - E_frontier) # Quante mine restano per le celle fuori frontiera
            p0_out = left_for_outside / max(1.0, float(len(outside))) # Prior uniforme sulle celle fuori frontiera
            p0_out = min(max(p0_out, 0.0), 1.0) # Clamp tra 0 e 1
        for v in outside:
            probs[v] = p0_out # Assegno la prior alle celle fuori frontiera

    # --- raffinamento locale (solo celle non-esatte) ---
    ALPHA = 0.7  # Peso della pressione locale rispetto al prior
    for v in unknown:
        if v in exact_vars:
            continue # Salto le celle già coperte da enumerazione esatta
        pv = probs.get(v, p0_fallback) # Prior corrente per la cella
        lp = local_pressure_prob(v) # Calcolo la pressione locale
        if lp is not None:
            probs[v] = (1.0 - ALPHA) * pv + ALPHA * lp  # Media pesata tra prior e pressione locale
        else:
            probs[v] = pv # Se non ho pressione locale, lascio il prior

    # --- ricalibrazione soft SOLO su celle non-esatte ---
    if calibrate and (mines_remaining is not None) and unknown:
        flex = [u for u in unknown if u not in exact_vars] # Celle su cui posso ancora agire
        if flex:
            S_exact = sum(probs[u] for u in exact_vars)  # Somma delle probabilità esatte
            S_flex  = sum(probs.get(u, p0_fallback) for u in flex) # Somma delle probabilità flessibili
            target_flex = max(0.0, mines_remaining - S_exact) # Quante mine dovrebbero essere sulle celle flessibili
            tol = 0.10 * max(1.0, target_flex)  # Tolleranza per evitare ricalibrazioni inutili
            if S_flex > 0.0 and abs(S_flex - target_flex) > tol:
                scale = target_flex / S_flex # Fattore di scala per ricalibrare le probabilità
                for u in flex:
                    p = probs.get(u, p0_fallback) * scale  # Applico la scala
                    # Clamp
                    if p < 0.0: p = 0.0
                    if p > 1.0: p = 1.0
                    probs[u] = p # Aggiorno la probabilità
    return probs # Ritorno il dizionario finale delle probabilità


def pick_min_risk(knowledge, moves_made=None, mine_cells=None, **kwargs):
    """
    Sceglie la cella "?" con probabilità di mina minima.
    - Esclude celle già rivelate (moves_made) e mine note (mine_cells).
    - In caso di parità, usa un tie-break informativo (sceglie la cella con più ignote adiacenti).
    - Se nessuna candidata, ritorna la prima "?" libera trovata (fallback).

    knowledge: griglia di stato (numeri, "?", "X")
    moves_made: celle già rivelate (set)
    mine_cells: celle già note come mine (set)
    kwargs: parametri aggiuntivi per compute_cell_probs

    Restituisce:
        - (i, j): coordinata della cella scelta
        - None se nessuna cella candidata
    """
    n_row = len(knowledge)
    n_col = len(knowledge[0])
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

    # Filtra le celle candidate (non vietate e ancora ignote)
    candidates = [(p, v) for v, p in probs.items()
              if v not in forbidden and knowledge[v[0]][v[1]] == "?"]
    if candidates:
        # tie-break: tra le celle a rischio minimo, scegli quella più "informativa"
        pmin = min(p for p, _ in candidates)
        bucket = [v for p, v in candidates if abs(p - pmin) <= EPS]
        #choice = random.choice(bucket)  # tie-break casuale (disabilitato)
        choice = max(bucket, key=lambda v: _info_score(knowledge, v))
        if DEBUG_RISK:
            top = sorted(candidates, key=lambda x: x[0])[:5]
            print("[RISK] min=", round(pmin, 4), "bucket=", bucket, "top5=", [(v, round(p,3)) for p, v in top])
        return choice

    # fallback: prima "?" libera trovata (in ordine di scansione)
    for i in range(n_row):
        for j in range(n_col):
            if knowledge[i][j] == "?" and (i, j) not in forbidden:
                return (i, j)
    return None

# --- utilità locali ---

def _info_score(knowledge, v):
    """
    Score informativo di una cella: quante "?" adiacenti ha.
    Utile per il tie-break: scegliere la cella che, se rivelata, fornisce più informazione.
    """
    n_row = len(knowledge) 
    n_col = len(knowledge[0])
    i, j = v 
    s = 0  # Contatore delle celle ignote adiacenti
    for di in (-1,0,1): 
        for dj in (-1,0,1): 
            if di==0 and dj==0: continue  # Salto la cella centrale
            r, c = i+di, j+dj  # Coordinate della cella vicina
            if 0<=r<n_row and 0<=c<n_col and knowledge[r][c] == "?":
                s += 1  # Incremento se la cella è ignota
    return s  # Ritorno il numero di ignote adiacenti

def neighbors8(i, j, n_row, n_col):
    """
    Generatore delle 8 celle adiacenti a (i,j), restando nei limiti della griglia.
    """
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0: 
                continue
            r, c = i + di, j + dj
            if 0 <= r < n_row and 0 <= c < n_col:
                return_cell = (r, c)
                yield return_cell

def local_pressure_prob(knowledge, mine_cells, v):
    """
    Calcola la pressione locale su una cella v rispetto alla knowledge e alle mine note.
    Utile per test e debugging.
    """
    n_row = len(knowledge)
    n_col = len(knowledge[0])
    i, j = v
    ratios = []
    for r, c in neighbors8(i, j, n_row, n_col):  # Scorro tutte le celle adiacenti a v
        cell = knowledge[r][c]  # Prendo il valore della cella adiacente
        if isinstance(cell, int) and cell >= 0:  # Se è un numero rivelato
            neigh = list(neighbors8(r, c, n_row, n_col))  # Celle adiacenti al numero
            known_mines = sum((nr, nc) in mine_cells for (nr, nc) in neigh)  # Mine note attorno
            unknowns = [(nr, nc) for (nr, nc) in neigh if knowledge[nr][nc] == "?" and (nr, nc) not in mine_cells]  # Ignote attorno
            need = max(0, cell - known_mines)  # Mine ancora da mettere
            denom = max(1, len(unknowns))  # Numero di ignote (evito divisione per zero)
            ratios.append(need / denom)  # Aggiungo il rapporto alla lista
    if not ratios:
        return None  # Nessuna informazione locale
    return sum(ratios) / len(ratios)  # Media delle pressioni locali