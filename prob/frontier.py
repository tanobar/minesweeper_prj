# Classe che si occupa di identificare le celle ignote "di frontiera", cioè quelle adiacenti a numeri rivelati,
# e di costruire i vincoli locali (del tipo: "tra queste celle ci sono esattamente N mine"),
# Dopodiché raggruppa le variabili e i vincoli in componenti connesse, per poter ragionare
# separatamente su sottoinsiemi indipendenti della frontiera.

from collections import defaultdict, deque

def neighbors(n_row, n_col, i, j):
    """
    Generatore che restituisce le coordinate delle 8 celle adiacenti a (i, j),
    restando nei limiti della griglia.
    """
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue # salto la cella centrale stessa
            r, c = i + di, j + dj
            if 0 <= r < n_row and 0 <= c < n_col:
                yield (r, c)

def build_constraints(knowledge, mine_cells):
    """
    Dallo stato di conoscenza costruisce i vincoli di somma per la frontiera.
    Per ogni cella rivelata con numero k:
      sum_{v in N_ignote} X_v = k - (#mine note adiacenti)
    Dove:
      - N_ignote: celle ignote adiacenti alla cella numerica
      - X_v: variabile booleana (1 se mina, 0 se safe)
    Ritorna:
      - constraints: lista di dict {"vars": set[(i,j)], "count": int}
      - unknowns: set di tutte le celle ignote coinvolte in almeno un vincolo
    In pratica, per ogni cella numerica già scoperta, costruisco un vincolo che dice:
    "la somma delle mine tra le celle ignote adiacenti deve essere uguale al numero richiesto
    meno le mine già note adiacenti". Ciò permette di tradurre la situazione locale in
    un sistema di vincoli booleani.
    """
    n_row = len(knowledge)
    n_col = len(knowledge[0])
    constraints = [] # lista dei vincoli locali (uno per ogni cella numerica)
    unknowns = set() # tutte le celle ignote che compaiono almeno in un vincolo
    mine_set = set(mine_cells or []) # per sicurezza, se mine_cells è None

    for i in range(n_row):
        for j in range(n_col):
            v = knowledge[i][j]
            # Considera solo le celle numeriche rivelate (int 0..8)
            if isinstance(v, int):
                unk = [] # lista delle celle ignote adiacenti
                known_mines = 0 # quante mine già note ci sono attorno
                # Conta le celle ignote e le mine note adiacenti
                for r, c in neighbors(n_row, n_col, i, j):
                    if knowledge[r][c] == "?":
                        unk.append((r, c))
                    elif knowledge[r][c] == "X" or (r, c) in mine_set:
                        known_mines += 1
                if unk:
                    # Il vincolo è: somma delle mine tra le ignote = numero richiesto - mine già note
                    count = int(v) - known_mines
                    # Clamp a [0, |unk|] per evitare errori numerici o input inconsistenti
                    count = max(0, min(count, len(unk)))
                    constraints.append({"vars": set(unk), "count": count})
                    unknowns.update(unk)

    return constraints, unknowns

def connected_components_from_constraints(constraints):
    """
    Raggruppa le variabili della frontiera in componenti connesse.
    Costruisce il grafo variabile-variabile: due variabili sono collegate se compaiono
    nello stesso vincolo. Ogni componente rappresenta un sottoinsieme indipendente
    della frontiera, che può essere risolto separatamente.
    Ritorna una lista di tuple (set di variabili, lista di vincoli relativi).
    In pratica, se due celle ignote compaiono nello stesso vincolo, sono collegate.
    Si costruisce il grafo delle adiacenze e si estraggono tutte le componenti connesse,
    in modo da poter risolvere ogni blocco indipendentemente dagli altri.
    """
    adj = defaultdict(set) # dizionario: variabile -> set di variabili adiacenti
    # Costruisce la lista di adiacenza tra variabili (se compaiono nello stesso vincolo)
    for cons in constraints:
        vars_list = list(cons["vars"])
        for idx, a in enumerate(vars_list):
            for b in vars_list[idx + 1:]:
                adj[a].add(b)
                adj[b].add(a)

    visited = set()
    components = []
    var_to_cons = defaultdict(list)
    # Mappa ogni variabile agli indici dei vincoli in cui compare
    for ci, cons in enumerate(constraints):
        for v in cons["vars"]:
            var_to_cons[v].append(ci)

    all_vars = set()
    for cons in constraints:
        all_vars.update(cons["vars"])
    # BFS per trovare tutte le componenti connesse
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
        # Raccoglie tutti i vincoli che coinvolgono almeno una variabile della componente
        comp_cons_idx = set()
        for var in comp_vars:
            comp_cons_idx.update(var_to_cons[var])
        comp_cons = [constraints[i] for i in sorted(comp_cons_idx)]
        components.append((comp_vars, comp_cons))
    return components

def frontier_components(knowledge, mine_cells):
    """
    Funzione di convenienza: costruisce i vincoli dalla knowledge e restituisce
    le componenti connesse della frontiera (variabili + vincoli).
    Se non ci sono vincoli, restituisce lista vuota.
    Punto di ingresso tipico: dato lo stato della griglia e le mine già note,
    restituisce una lista di componenti, ognuna delle quali può essere risolta separatamente.
    """
    constraints, _ = build_constraints(knowledge, mine_cells)
    if not constraints:
        return []
    comps = connected_components_from_constraints(constraints)
    # Filtra eventuali componenti vuote (dovrebbero essere rare)
    comps = [c for c in comps if c[0]]
    return comps