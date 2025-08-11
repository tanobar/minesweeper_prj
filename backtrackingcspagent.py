from agent import Agent
import random

class BacktrackingCSPAgent(Agent):
    def __init__(self, n):
        super().__init__(n)
        self.constraints = []  # Lista di vincoli: [{"cells": set(), "count": int}, ...]
    
    
    def observe(self, x, y, value):
        """
        Aggiorna la knowledge dell'agente e i vincoli CSP.
        """
        # Se avevamo inferito per sbaglio che questa cella fosse una mina, correggi
        # non dovrebbe mai sbagliare ma un check in più non fa mai male!
        if (x, y) in self.mine_cells and value != "M":
            self.mine_cells.remove((x, y))
            self.safe_cells.discard((x, y))
        
        super().observe(x, y, value)
        
        # Se il valore è numerico, aggiorna i vincoli
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
    
    
    def add_constraint(self, x, y, value):
        """
        Crea un vincolo per una cella numerica.
        """
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
                "cells": adjacent_unknown,
                "count": remaining_mines
            })
    
    
    def get_variables(self):
        """
        Raccoglie tutte le variabili (celle sconosciute) dai vincoli attivi.
        """
        variables = set()
        for constraint in self.constraints:
            for cell in constraint["cells"]:
                if self.knowledge[cell[0]][cell[1]] == "?":
                    variables.add(cell)
        return list(variables)
    
    
    def infer_safe_and_mines(self):
        """
        Usa backtracking per inferire celle sicure e mine.
        """
        # Ricostruisci vincoli aggiornati
        self.constraints = []
        for i in range(self.n):
            for j in range(self.n):
                if isinstance(self.knowledge[i][j], int) and self.knowledge[i][j] > 0:
                    self.add_constraint(i, j, self.knowledge[i][j])
        
        variables = self.get_variables()
        if not variables or len(variables) > 15:  # Limite per performance
            return
        
        # Per ogni variabile, testa se è sempre mina o sempre sicura
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
        Algoritmo di backtracking con MRV e LCV.
        """
        if not unassigned:
            return self.is_consistent(assignment)
        
        # MRV: scegli la variabile con meno valori possibili
        var = self.select_unassigned_variable(unassigned, assignment)
        unassigned.remove(var)
        
        # LCV: ordina i valori (False=sicura prima, True=mina dopo)
        for value in [False, True]:
            assignment[var] = value
            if self.is_consistent_partial(assignment):
                if self.backtrack(assignment, unassigned[:]):
                    return True
            del assignment[var]
        
        unassigned.append(var)
        return False
    
    
    def select_unassigned_variable(self, unassigned, assignment):
        """
        MRV: seleziona la variabile con meno valori nel dominio.
        """
        min_values = float('inf')
        best_var = unassigned[0]
        
        for var in unassigned:
            legal_values = 0
            for value in [False, True]:
                test_assignment = assignment.copy()
                test_assignment[var] = value
                if self.is_consistent_partial(test_assignment):
                    legal_values += 1
            
            if legal_values < min_values:
                min_values = legal_values
                best_var = var
        
        return best_var
  #SOLO LA PRIMA MRV VIENE CONSIDERATA
  # VA FATTO DEGREE HEURISTIC  
    
    def is_consistent_partial(self, assignment):
        """
        Verifica se un'assegnazione parziale è consistente.
        """
        for constraint in self.constraints:
            assigned_in_constraint = 0
            mines_assigned = 0
            unassigned_in_constraint = 0
            
            for cell in constraint["cells"]:
                if cell in assignment:
                    assigned_in_constraint += 1
                    if assignment[cell]:
                        mines_assigned += 1
                elif self.knowledge[cell[0]][cell[1]] == "?":
                    unassigned_in_constraint += 1
            
            # Controlla vincoli
            remaining_mines = constraint["count"] - mines_assigned
            if remaining_mines < 0 or remaining_mines > unassigned_in_constraint:
                return False
        
        return True
    
    
    def is_consistent(self, assignment):
        """
        Verifica se un'assegnazione completa è consistente.
        """
        for constraint in self.constraints:
            mine_count = 0
            for cell in constraint["cells"]:
                if cell in assignment and assignment[cell]:
                    mine_count += 1
            if mine_count != constraint["count"]:
                return False
        return True
    
    
    def choose_action(self):
        """
        Sceglie la prossima azione usando inferenza CSP e fallback a scelta casuale.
        """
        # Prima prova l'inferenza CSP
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
