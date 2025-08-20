import random
import support
import copy
from prob.risk import pick_min_risk
from collections import deque
from itertools import product


class Agent:
    def __init__(self, n, strategy="backtracking", heuristics=None):
        """
        Agente modulare per minesweeper.
        
        Args:
            n: dimensione della griglia (n x n)
            strategy: strategia principale ("backtracking", "random")
            heuristics: lista di euristiche ["mrv", "lcv", "degree"]
            techniques: lista di tecniche ["arc_consistency", "forward_checking"]
        """
        self.n = n
        self.knowledge = [["?" for _ in range(n)] for _ in range(n)]
        self.moves_made = set()
        self.safe_cells = set()
        self.mine_cells = set()
        
        # Configurazione strategia
        self.strategy = strategy
        self.heuristics = heuristics or []
        
        # Attributi specifici per CSP/backtracking
        if strategy == "backtracking":
            self.constraints = []  # Lista di vincoli: [{"cell": tuple, " "neighbors": set(), "count": int}, ...]

        self.Domains = {(x, y): {0, 1} for x in range(n) for y in range(n)}    
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
        if self.strategy == "backtracking":
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
                        if 0 <= nx < self.n and 0 <= ny < self.n:
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
                    if 0 <= nx < self.n and 0 <= ny < self.n:
                        if (nx, ny) not in self.moves_made:
                            self.safe_cells.add((nx, ny))


    def add_constraint(self, x, y, value):
        """
        Crea un vincolo per una cella numerica (solo per strategia backtracking).
        """
        if self.strategy != "backtracking":
            return
            
        adjacent_unknown = set()
        adjacent_mines = 0
        
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                    
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.n and 0 <= ny < self.n:
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
        return env.check_victory(self.knowledge)
    

    def get_variables(self):
        """
        Raccoglie tutte le variabili (celle sconosciute) dai vincoli attivi.
        
        Returns:
            list: lista di tuple (r, c) delle celle sconosciute
        """
        if self.strategy != "backtracking":
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
        if self.strategy != "backtracking":
            return
            
        # Ricostruisci vincoli aggiornati
        self.constraints = []
        for i in range(self.n):
            for j in range(self.n):
                if isinstance(self.knowledge[i][j], int) and self.knowledge[i][j] > 0:
                    self.add_constraint(i, j, self.knowledge[i][j])
        
        variables = self.get_variables()
        if not variables or len(variables) > 15:  # Limite per performance
            return
        
        self.gac3()
        # Per ogni variabile, testa se è sempre mina o sempre sicura
        for var in variables:
            #se gac3 è riuscito nel pruning
            if len(self.Domains[var])==1:
                if next(iter(self.Domains[var])):
                    self.mine_cells.add(var)
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
        
        # Selezione variabile (MRV + Degree se configurato)
        if "mrv" in self.heuristics:
            var = support.select_unassigned_variable(self, unassigned, assignment)
        else:
            var = unassigned[0]  # Prima variabile disponibile
        
        unassigned.remove(var)
        
        # Ordinamento valori (LCV se configurato)
        if "lcv" in self.heuristics:
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
        if self.strategy == "backtracking":
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
            x, y = unflagged_mines[0]
            # Marca come mossa fatta per evitare di flaggare di nuovo
            self.moves_made.add((x, y))
            return ("flag", x, y)
        
        # Seconda priorità: celle sicure
        available_safe = []
        for x, y in sorted(self.safe_cells):
            if (x, y) not in self.moves_made:
                available_safe.append((x, y))
        
        if available_safe:
            x, y = available_safe[0]
            return ("reveal", x, y)
        
        # Se non ci sono celle sicure, scegli casualmente
        unknown = [
            (i, j)
            for i in range(self.n)
            for j in range(self.n)
            if self.knowledge[i][j] == "?"
               and (i, j) not in self.mine_cells
               and (i, j) not in self.moves_made
        ]
        
        if unknown:
            choice = random.choice(unknown)
            x, y = choice
            return ("reveal", x, y)
        else:
            return None


    def _choose_action_random(self):
        """
        Sceglie la prossima azione da fare casualmente.
        """
        # Priorità: celle sicure
        for x, y in sorted(self.safe_cells):
            if (x, y) not in self.moves_made:
                return ("reveal", x, y)

        # Altrimenti esplora guidato dalla probabilità (fallback)
        unknown = [
            (i, j)
            for i in range(self.n)
            for j in range(self.n)
            if self.knowledge[i][j] == "?"
               and (i, j) not in self.mine_cells
               and (i, j) not in self.moves_made
        ]

        if unknown:
            # return ("reveal", *random.choice(unknown))
            # MIN-RISK (consigliato come default)
            pick = pick_min_risk(self.knowledge, self.moves_made, self.mine_cells)

            if pick is not None:
                x, y = pick
            else:
                # extrema ratio: proprio se non abbiamo info
                x, y = random.choice(unknown)
            return ("reveal", x, y)
        else:
            return None


