import random


def generate_grid(n, m):
    """
    Genera una griglia n x n per il minesweeper con m mine posizionate casualmente.
    
    Args:
        n (int): Dimensione della griglia (n x n)
        m (int): Numero di mine da posizionare
    
    Returns:
        list: Matrice n x n con mine ("M") e numeri che indicano le mine adiacenti
    """
    # Verifica che il numero di mine non superi il numero di celle disponibili
    if m > n * n:
        raise ValueError("Il numero di mine non può superare il numero di celle disponibili")
    
    # Inizializza la griglia con zeri
    grid = [[0 for _ in range(n)] for _ in range(n)]
    
    # Genera posizioni casuali per le mine
    positions = [(i, j) for i in range(n) for j in range(n)]
    mine_positions = random.sample(positions, m)
    
    # Posiziona le mine
    for row, col in mine_positions:
        grid[row][col] = "M"
    
    # Calcola i numeri per le celle non-mine
    for i in range(n):
        for j in range(n):
            if grid[i][j] != "M":
                count = 0
                # Controlla tutte le 8 direzioni adiacenti
                for di in [-1, 0, 1]:
                    for dj in [-1, 0, 1]:
                        # Salta la cella centrale
                        if di == 0 and dj == 0:
                            continue
                        
                        ni, nj = i + di, j + dj
                        # Verifica che la posizione sia valida
                        if 0 <= ni < n and 0 <= nj < n:
                            if grid[ni][nj] == "M":
                                count += 1
                
                grid[i][j] = count
    
    return grid


def create_covered_grid(original_grid):
    """
    Crea una griglia coperta dove tutte le celle sono "X" tranne una cella 
    con valore 0 che viene rivelata casualmente.
    
    Args:
        original_grid (list): La griglia originale generata da generate_grid
    
    Returns:
        list: Griglia coperta con una sola cella 0 rivelata
    """
    n = len(original_grid)
    
    # Trova tutte le posizioni con valore 0
    zero_positions = []
    for i in range(n):
        for j in range(n):
            if original_grid[i][j] == 0:
                zero_positions.append((i, j))
    
    # Se non ci sono celle con valore 0, solleva un errore
    if not zero_positions:
        raise ValueError("Non ci sono celle con valore 0 nella griglia")

    # Crea la griglia coperta (tutte "?")
    covered_grid = [["?" for _ in range(n)] for _ in range(n)]
    
    # Sceglie casualmente una posizione con valore 0 da rivelare
    revealed_pos = random.choice(zero_positions)
    row, col = revealed_pos
    covered_grid[row][col] = original_grid[row][col]  # Rivela il valore 0
    
    return covered_grid


