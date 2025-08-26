import random
import support
import copy
from prob.risk import pick_min_risk
from collections import deque
from itertools import product


class Agent:
    def __init__(self, n_row, n_col, strategy="backtracking", total_mines=None):
        """
        Agente modulare per minesweeper.
        
        Args:
            n_row, n_col: dimensioni della griglia (n_row x n_col)
            strategy: strategia principale ("backtracking", "backtracking_advanced", "backtracking_gac3", "backtracking_pb", "random")
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
        
        # Attributi specifici per CSP/backtracking
        if strategy in ["backtracking", "backtracking_advanced", "backtracking_gac3", "backtracking_pb"]:
            self.constraints = []  # Lista di vincoli: [{"cell": tuple, " "neighbors": set(), "count": int}, ...]

        self.Domains = {(x, y): {0, 1} for x in range(n_row) for y in range(n_col)}    
        self.pruned = 0

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
        
        # Logica specifica per strategia
        if self.strategy in ["backtracking", "backtracking_advanced", "backtracking_gac3", "backtracking_pb"]:
            self._observe_backtracking(x, y, value)
        elif self.strategy == "random":
            self._observe_random(x, y, value)


    def _observe_backtracking(self, x, y, value):
        """Logica di osservazione per strategia backtracking."""
        if isinstance(value, int):
            if value == 0:
                # Se il valore è 0, tutte le celle adiacenti sono sicure
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.n_row and 0 <= ny < self.n_col:
                            if (nx, ny) not in self.moves_made:
                                self.safe_cells.add((nx, ny))
            elif value > 0:
                self.add_constraint(x, y, value)


    def _observe_random(self, x, y, value):
        """Logica di osservazione per strategia random."""
        if value == 0:
            # Le celle adiacenti sono probabilmente sicure: da rivelare
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
        if self.strategy not in ["backtracking", "backtracking_advanced", "backtracking_gac3", "backtracking_pb"]:
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
        if self.strategy not in ["backtracking", "backtracking_advanced", "backtracking_gac3", "backtracking_pb"]:
            return []
            
        variables = set()
        for constraint in self.constraints:
            for cell in constraint["neighbors"]:
                if self.knowledge[cell[0]][cell[1]] == "?":
                    variables.add(cell)
        return list(variables)

    def gac3(self):
        """
        Generalized-arc-consistency-3, utile per pruning di domini

        Sfrutta i campi Domains e constraints dell'agente

        domains: dict[var] -> sottoinsieme di {0,1}
        constraints: lista di dizionari composti da cella, vicini non assegnati e vincolo 
        Ritorna True se consistente, False se un qualunque dominio rimane vuoto.
        """
        pruned_count = [0]  # counter per controllare se gac3 aiuta sui domini, solo per debug
        domains = copy.deepcopy(self.Domains)
        constraints = copy.deepcopy(self.constraints)
        # Build adjacency: for each var, which constraints mention it?
        var2cons = {}
        Q = deque()
        for C in constraints:
            for v in C["neighbors"]:
                var2cons.setdefault(v, []).append(C)
                Q.append((v, C))

       
        def revise(Xi, C):
            removed = False
            others = C["neighbors"] - {Xi}

            for x in tuple(domains[Xi]):  #iteriamo su una copia immutabile, poiché il set cambierà
                need = C["count"] - x
                # quick bound check
                lo = sum(min(domains[v]) for v in others)
                hi = sum(max(domains[v]) for v in others)
                if need < lo or need > hi:
                    domains[Xi].discard(x)
                    removed = True
                    pruned_count[0] += 1
                    continue
                # si cerca una qualunque tupla sui domini degli "others" la cui somma è "need"
                dom_lists = [tuple(domains[v]) for v in others]
                supported = False
                for choices in product(*dom_lists):
                    if sum(choices) == need:
                        supported = True
                        break
                if not supported:
                    domains[Xi].discard(x)
                    removed = True
                    pruned_count[0] += 1
            return removed

        while Q:
            Xi, C = Q.popleft()
            if revise(Xi, C):
                if not domains[Xi]: #se il dominio di X_i è ora vuoto
                    return False    #gac3 fallisce
                # riaggiungi (Xk, Ck) per vincoli che interessano Xi (tranne C stesso)
                for Ck in var2cons.get(Xi, []):
                    if Ck is C: 
                        continue
                    for Xk in Ck["neighbors"]:
                        if Xk != Xi:
                            Q.append((Xk, Ck))
        self.Domains = domains
        #print(f"{pruned_count[0]} pruned domains by gac3")
        return True


    def infer_safe_and_mines(self):
        """
        Usa backtracking per inferire celle sicure e mine.
        """
        if self.strategy not in ["backtracking", "backtracking_advanced", "backtracking_gac3", "backtracking_pb"]:
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
        
        # Usa GAC3 solo per le strategie backtracking_gac3 e backtracking_pb
        if self.strategy in ["backtracking_gac3", "backtracking_pb"]:
            self.gac3()
        
        # Per ogni variabile, testa se è sempre mina o sempre sicura
        for var in variables:
            # Se GAC3 è stato usato e è riuscito nel pruning
            if self.strategy in ["backtracking_gac3", "backtracking_pb"] and len(self.Domains[var]) == 1:
                if next(iter(self.Domains[var])):
                    self.mine_cells.add(var)
                    self.knowledge[var[0]][var[1]] = "X"  # Marca anche nella knowledge per visualizzazione
                else:
                    self.safe_cells.add(var)
                self.pruned += 1
            else:
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
        
        # Selezione variabile (MRV + Degree se strategia avanzata, gac3 o pb)
        if self.strategy in ["backtracking_advanced", "backtracking_gac3", "backtracking_pb"]:
            var = support.select_unassigned_variable(self, unassigned, assignment)
        else:
            var = unassigned[0]  # Prima variabile disponibile
        
        unassigned.remove(var)
        
        # Ordinamento valori (LCV se strategia avanzata, gac3 o pb)
        if self.strategy in ["backtracking_advanced", "backtracking_gac3", "backtracking_pb"]:
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
        if self.strategy in ["backtracking", "backtracking_advanced", "backtracking_gac3", "backtracking_pb"]:
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
            # Marca tutte le mine come mosse fatte e decrementa il contatore
            for x, y in unflagged_mines:
                self.moves_made.add((x, y))
                self.to_flag -= 1
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
        unknown = [
            (i, j)
            for i in range(self.n_row)
            for j in range(self.n_col)
            if self.knowledge[i][j] == "?"
               and (i, j) not in self.mine_cells
               and (i, j) not in self.moves_made
        ]

        if unknown:
            # Solo la strategia backtracking_pb usa PB come fallback
            if self.strategy == "backtracking_pb":
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
            
            # Fallback per tutte le altre strategie: scelta casuale
            x, y = random.choice(unknown)
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
            # Marca tutte le mine come mosse fatte e decrementa il contatore
            for x, y in unflagged_mines:
                self.moves_made.add((x, y))
                self.to_flag -= 1
            return ("flag_all", unflagged_mines)
        
        # Seconda priorità: celle sicure (rivela tutte quelle disponibili)
        available_safe = []
        for x, y in sorted(self.safe_cells):
            if (x, y) not in self.moves_made:
                available_safe.append((x, y))
        
        if available_safe:
            return ("reveal_all_safe", available_safe)

        # Altrimenti esplora guidato dalla probabilità (fallback)
        unknown = [
            (i, j)
            for i in range(self.n_row)
            for j in range(self.n_col)
            if self.knowledge[i][j] == "?"
               and (i, j) not in self.mine_cells
               and (i, j) not in self.moves_made
        ]

        if unknown:
            x, y = random.choice(unknown)
            return ("reveal", x, y)
        else:
            return None


