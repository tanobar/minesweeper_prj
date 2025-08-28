import random
import support
from prob.risk import pick_min_risk
from collections import deque


class Agent:
    def __init__(self, n_row, n_col, strategy="backtracking", total_mines=None):
        """
        Agente modulare per minesweeper.
        
        Args:
            n_row: numero di righe della griglia
            n_col: numero di colonne della griglia
            strategy: strategia principale ("backtracking", "backtracking_advanced", "backtracking_gac3", "random")
            total_mines: numero totale di mine nel gioco
        """
        self.n_row = n_row
        self.n_col = n_col
        self.knowledge = [["?" for _ in range(n_col)] for _ in range(n_row)]
        self.moves_made = set()
        self.safe_cells = set()
        self.mine_cells = set()
        self.total_mines = total_mines
        self.to_flag = total_mines
        
        # Configurazione strategia
        self.strategy = strategy
        
        # Ottimizzazione: mantieni set di celle sconosciute
        self.unknown_cells = {(i, j) for i in range(n_row) for j in range(n_col)}
        
        # Attributi specifici per CSP/backtracking
        if strategy in ["backtracking", "backtracking_advanced", "backtracking_gac3"]:
            self.constraints = []  # Lista di vincoli: [{"cell": tuple, " "neighbors": set(), "count": int}, ...]

        self.Domains = {(x, y): {0, 1} for x in range(n_row) for y in range(n_col)}
        self.gac_count = 0

    def observe(self, x, y, value):
        """
        Aggiorna la knowledge dell'agente con l'informazione osservata.
        """
        # Correzione errori precedenti
        if (x, y) in self.mine_cells and value != "M":
            self.mine_cells.remove((x, y))
            self.safe_cells.discard((x, y))
        
        self.knowledge[x][y] = value
        self.moves_made.add((x, y))
        
        # Ottimizzazione: rimuovi dalle celle sconosciute
        self.unknown_cells.discard((x, y))
        
        # Logica specifica per strategia
        if self.strategy in ["backtracking", "backtracking_advanced", "backtracking_gac3"]:
            self._observe_backtracking(x, y, value)
        elif self.strategy == "random":
            self._observe_random(x, y, value)


    def _observe_backtracking(self, x, y, value):
        """Logica di osservazione per strategia backtracking."""
        if isinstance(value, int) and value == 0:
            self._add_safe_neighbors(x, y)
            # Note: I vincoli vengono creati in infer_safe_and_mines(), non qui


    def _observe_random(self, x, y, value):
        """Logica di osservazione per strategia random."""
        if value == 0:
            self._add_safe_neighbors(x, y)


    def _add_safe_neighbors(self, x, y):
        """Aggiunge le celle adiacenti a (x,y) come sicure se non già esplorate."""
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.n_row and 0 <= ny < self.n_col:
                    if (nx, ny) not in self.moves_made:
                        self.safe_cells.add((nx, ny))


    def add_constraint(self, x, y, value):
        """
        Crea un vincolo per una cella numerica (solo per strategia backtracking).
        """
        if self.strategy not in ["backtracking", "backtracking_advanced", "backtracking_gac3"]:
            return
            
        adjacent_unknown = set()
        adjacent_mines = 0
        
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                    
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.n_row and 0 <= ny < self.n_col:
                    if (nx, ny) in self.mine_cells or self.knowledge[nx][ny] == "X":
                        adjacent_mines += 1
                    elif self.knowledge[nx][ny] == "?":
                        adjacent_unknown.add((nx, ny))
        
        remaining_mines = value - adjacent_mines
        
        if adjacent_unknown and 0 <= remaining_mines <= len(adjacent_unknown):
            self.constraints.append({
                "cell": (x,y),
                "neighbors": adjacent_unknown,
                "count": remaining_mines
            })


    def mark_mine(self, x, y):
        """
        Marca una cella come mina conosciuta.
        """
        self.mine_cells.add((x, y))
        self.knowledge[x][y] = "X"
        # Ottimizzazione: rimuovi dalle celle sconosciute se presente
        self.unknown_cells.discard((x, y))
        # Marca come mossa fatta e decrementa il contatore delle mine rimanenti
        if (x, y) not in self.moves_made:
            self.moves_made.add((x, y))
            self.to_flag -= 1


    def print_grid(self):
        """
        Stampa la griglia in modo leggibile.
        """
        for row in self.knowledge:
            print(" ".join(str(cell).rjust(2) for cell in row))


    def check_victory_status(self, env):
        """
        Verifica se l'agente ha raggiunto la condizione di vittoria.
        """
        return env.check_victory(self.knowledge, total_non_mine_cells = self.n_row*self.n_col - self.total_mines)
    

    def get_variables(self):
        """
        Raccoglie tutte le variabili (celle sconosciute) dai vincoli attivi.
        
        Returns:
            list: lista di tuple (r, c) delle celle sconosciute
        """
        if self.strategy not in ["backtracking", "backtracking_advanced", "backtracking_gac3"]:
            return []
            
        variables = set()
        for constraint in self.constraints:
            for cell in constraint["neighbors"]:
                if self.knowledge[cell[0]][cell[1]] == "?":
                    variables.add(cell)
        return list(variables)

    def gac3(self):
        """
        Generalized-arc-consistency-3, utile per pruning di domini.
        Ritorna True se consistente, False se un qualunque dominio rimane vuoto.
        Al termine di essa, i domini potrebbero essere stati ridotti.
        """
        self.gac_count = 0 
        # Build adjacency: for each var, which constraints mention it?
        var2cons = {}
        #queue di coppie (variabile, vincolo); inseriamo tutte le possibili coppie inizialmente
        #usiamo deque per performance e semplicità
        Q = deque()
        for C in self.constraints:
            for v in C["neighbors"]:
                var2cons.setdefault(v, []).append(C)
                Q.append((v, C))

       
        def revise(Xi, C):
            """ 
            funzione ausiliaria equivalente a Remove-Inconsistent-Values sulle slide
            Prende in input una coppia (X_i, C), dove X_i fa parte del vincolo C.
            Restituisce True se (e solo se) sono stati rimossi valori dal dominio di X_i
            """
            removed = False
            others = C["neighbors"] - {Xi}

            lo = sum(min(self.Domains[v]) for v in others) #lower bound di need
            hi = sum(max(self.Domains[v]) for v in others) #upper bound di need
            for x in tuple(self.Domains[Xi]):  #iteriamo su una copia immutabile, poiché il set cambierà
                need = C["count"] - x
                #lower/upper bound check per scartare x precocemente
                #x sta in [lo,hi] se e solo se ammette un assegnamento valido delle others
                if need < lo or need > hi:
                    self.Domains[Xi].discard(x)
                    removed = True
                    self.gac_count += 1
            return removed

        #finché la queue non è vuota
        while Q:
            Xi, C = Q.popleft()
            if revise(Xi, C):
                if not self.Domains[Xi]: #se il dominio di X_i è ora vuoto
                    return False    #gac3 fallisce e il CSP con gli assegnamenti attuali
                                    #non è risolvibile (ASSURDO)
                # riaggiungi (Xk, Ck) per vincoli che interessano Xi (tranne C stesso)
                for Ck in var2cons.get(Xi, []):
                    if Ck is C: 
                        continue
                    for Xk in Ck["neighbors"]:
                        if Xk != Xi:
                            Q.append((Xk, Ck))

        return True


    def infer_safe_and_mines(self):
        """
        Usa backtracking per inferire celle sicure e mine.
        """
        if self.strategy not in ["backtracking", "backtracking_advanced", "backtracking_gac3"]:
            return
            
        # Ricostruisci vincoli aggiornati
        self.constraints = []
        for i in range(self.n_row):
            for j in range(self.n_col):
                if isinstance(self.knowledge[i][j], int) and self.knowledge[i][j] > 0:
                    self.add_constraint(i, j, self.knowledge[i][j])
        
        variables = self.get_variables()
        if not variables:
            return
        """if not variables or len(variables) > 15:  # Limite per performance
            return"""
        
        gac = False
        # Usa GAC3 solo per la strategia backtracking_gac3
        if self.strategy == "backtracking_gac3":
            gac = self.gac3()
        
        
        # Se GAC3 è stato usato e è riuscito nel pruning
        if gac and self.gac_count > 0:
            # Per ogni variabile, testa se è sempre mina o sempre sicura
            for var in variables:
                if len(self.Domains[var]) == 1:
                    if next(iter(self.Domains[var])):
                        self.mine_cells.add(var)
                        self.knowledge[var[0]][var[1]] = "X"  # Marca anche nella knowledge per visualizzazione
                    else:
                        self.safe_cells.add(var)
        else:
            for var in variables:
                if var in self.safe_cells or var in self.mine_cells:
                    continue
                    
                # Testa se la variabile può essere sicura
                can_be_safe = self.backtrack({var: False}, [v for v in variables if v != var])
                # Testa se la variabile può essere mine
                can_be_mine = self.backtrack({var: True}, [v for v in variables if v != var])
                
                if can_be_safe and not can_be_mine:
                    self.safe_cells.add(var)
                elif can_be_mine and not can_be_safe:
                    self.mine_cells.add(var)
                    self.knowledge[var[0]][var[1]] = "X"


    def backtrack(self, assignment, unassigned):
        """
        Algoritmo di backtracking con euristiche configurabili.
        
        Args:
            assignment: dict con assegnazioni correnti
            unassigned: lista di variabili non ancora assegnate
            
        Returns:
            bool: True se esiste una soluzione consistente
        """
        if not unassigned:
            return support.is_consistent(self, assignment)
        
        # Selezione variabile (MRV + Degree se strategia avanzata o gac3)
        if self.strategy in ["backtracking_advanced", "backtracking_gac3"]:
            var = support.select_unassigned_variable(self, unassigned, assignment)
        else:
            var = unassigned[0]  # Prima variabile disponibile
        
        unassigned.remove(var)
        
        # Ordinamento valori (LCV se strategia avanzata o gac3)
        if self.strategy in ["backtracking_advanced", "backtracking_gac3"]:
            values = [False, True]  # Per ora ordine semplice
        else:
            values = [False, True]
        
        for value in values:
            assignment[var] = value
            if support.is_consistent_partial(self, assignment):
                if self.backtrack(assignment, unassigned[:]):
                    return True
            del assignment[var]
        
        unassigned.append(var)
        return False
    

    def choose_action(self):
        """
        Sceglie la prossima azione in base alla strategia configurata.
        """
        if self.strategy in ["backtracking", "backtracking_advanced", "backtracking_gac3"]:
            return self._choose_action_backtracking()
        elif self.strategy == "random":
            return self._choose_action_random()
        else:
            raise ValueError(f"Strategia non supportata: {self.strategy}")


    def _choose_action_backtracking(self):
        """
        Sceglie la prossima azione usando inferenza CSP e fallback a scelta casuale.
        """
        # Prima prova l'inferenza CSP usando metodi di istanza
        self.infer_safe_and_mines()
        
        # Prima priorità: flagga le mine che non sono ancora state flaggate
        unflagged_mines = []
        for x, y in self.mine_cells:
            if (x, y) not in self.moves_made and self.knowledge[x][y] == "X":
                unflagged_mines.append((x, y))
        
        if unflagged_mines:
            return ("flag_all", unflagged_mines)
        
        # Seconda priorità: celle sicure (rivela tutte quelle disponibili)
        available_safe = []
        for x, y in sorted(self.safe_cells):
            if (x, y) not in self.moves_made:
                available_safe.append((x, y))
        
        if available_safe:
            # Restituisce un'azione speciale per rivelare tutte le celle sicure
            return ("reveal_all_safe", available_safe)
        
        # Se non ci sono celle sicure, fallback basato sulla strategia
        if self.unknown_cells:
            # Tutte le strategie di backtracking usano PB come fallback
            if self.strategy in ["backtracking", "backtracking_advanced", "backtracking_gac3"]:
                pick = pick_min_risk(
                    self.knowledge,
                    moves_made=self.moves_made,
                    mine_cells=self.mine_cells,
                    max_vars_exact=18,      # puoi regolarlo
                    max_solutions=200000,    # idem
                    total_mines=self.total_mines
                )
                if pick is not None:
                    x, y = pick
                    return ("reveal", x, y)
            
            # Fallback per la strategia random: scelta casuale
            x, y = self.unknown_cells.pop()
            return ("reveal", x, y)
        
        else:
            return None
    

    def _choose_action_random(self):
        """
        Sceglie la prossima azione da fare casualmente.
        """
        # Prima priorità: flagga le mine che non sono ancora state flaggate (se ce ne sono)
        unflagged_mines = []
        for x, y in self.mine_cells:
            if (x, y) not in self.moves_made and self.knowledge[x][y] == "X":
                unflagged_mines.append((x, y))
        
        if unflagged_mines:
            return ("flag_all", unflagged_mines)
        
        # Seconda priorità: celle sicure (rivela tutte quelle disponibili)
        available_safe = []
        for x, y in sorted(self.safe_cells):
            if (x, y) not in self.moves_made:
                available_safe.append((x, y))
        
        if available_safe:
            return ("reveal_all_safe", available_safe)

        # Altrimenti esplora guidato dalla probabilità (fallback)
        if self.unknown_cells:
            x, y = self.unknown_cells.pop()
            return ("reveal", x, y)
        else:
            return None


