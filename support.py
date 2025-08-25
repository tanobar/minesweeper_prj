"""
Modulo support.py - Funzioni di supporto per CSP nel minesweeper.
Contiene funzioni di utilità per euristiche, vincoli e controlli di consistenza.
"""

def select_unassigned_variable(agent, unassigned, assignment):
    """
    MRV + Degree Heuristic: seleziona la variabile con meno valori nel dominio.
    
    Args:
        agent: istanza dell'agente
        unassigned: lista di variabili non assegnate
        assignment: dict con assegnazioni correnti
        
    Returns:
        tuple: (r, c) della variabile selezionata
    """
    min_values = float('inf')
    candidates = []
    
    # Prima fase: trova il minimo MRV
    for var in unassigned:
        legal_values = 0
        for value in agent.Domains[var]:
            test_assignment = assignment.copy()
            test_assignment[var] = value
            if is_consistent_partial(agent, test_assignment):
                legal_values += 1
        
        if legal_values < min_values:
            min_values = legal_values
            candidates = [var]
        elif legal_values == min_values:
            candidates.append(var)
    
    # Seconda fase: degree heuristic se strategia avanzata, gac3 o pb e necessario
    if len(candidates) == 1 or agent.strategy not in ["backtracking_advanced", "backtracking_gac3", "backtracking_pb"]:
        return candidates[0]
    
    max_degree = -1
    best_var = candidates[0]
    
    for var in candidates:
        degree = calculate_degree(agent, var, unassigned, assignment)
        if degree > max_degree:
            max_degree = degree
            best_var = var
    
    return best_var


def calculate_degree(agent, var, unassigned, assignment):
    """
    Calcola il degree di una variabile.
    
    Args:
        agent: istanza dell'agente
        var: variabile di cui calcolare il degree
        unassigned: lista di variabili non assegnate
        assignment: dict con assegnamenti correnti
        
    Returns:
        int: degree della variabile
    """
    degree = 0
    unassigned_set = set(unassigned)
    x, y = var
    
    # Ottimizzazione: controlla solo i constraints delle celle adiacenti a var
    # Invece di iterare su tutti i constraints, guardiamo solo quelli che potrebbero contenere var
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
                
            nx, ny = x + dx, y + dy
            if 0 <= nx < agent.n_row and 0 <= ny < agent.n_col:
                # Trova constraint che ha come cella centrale (nx, ny)
                for constraint in agent.constraints:
                    if constraint["cell"] == (nx, ny) and var in constraint["neighbors"]:
                        # Calcola direttamente l'intersezione escludendo var
                        other_unassigned = (constraint["neighbors"] & unassigned_set) - {var}
                        degree += len(other_unassigned)
    
    return degree


def is_consistent_partial(agent, assignment):
    """
    Verifica se un'assegnazione parziale è consistente.
    
    Args:
        agent: istanza dell'agente
        assignment: dict con assegnazioni parziali
        
    Returns:
        bool: True se l'assegnazione è consistente
    """
    for constraint in agent.constraints:
        assigned_in_constraint = 0
        mines_assigned = 0
        unassigned_in_constraint = 0
        
        for cell in constraint["neighbors"]:
            if cell in assignment:
                assigned_in_constraint += 1
                if assignment[cell]:
                    mines_assigned += 1
            elif agent.knowledge[cell[0]][cell[1]] == "?":
                unassigned_in_constraint += 1
        
        remaining_mines = constraint["count"] - mines_assigned
        if remaining_mines < 0 or remaining_mines > unassigned_in_constraint:
            return False
    
    return True


def is_consistent(agent, assignment):
    """
    Verifica se un'assegnazione completa è consistente.
    
    Args:
        agent: istanza dell'agente
        assignment: dict con assegnazioni complete
        
    Returns:
        bool: True se l'assegnazione è consistente
    """
    for constraint in agent.constraints:
        mine_count = 0
        for cell in constraint["neighbors"]:
            if cell in assignment and assignment[cell]:
                mine_count += 1
        if mine_count != constraint["count"]:
            return False
    return True
