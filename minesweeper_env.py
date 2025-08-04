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



class MinesweeperEnv:
    def __init__(self, n, m):
        self.n = n
        self.m = m
        self.grid = generate_grid(n, m)


    def reveal(self, x, y):
        """
        Rivela il valore reale di una cella nella griglia coperta.
        
        Args:
            x (int): Coordinata riga (0-based)
            y (int): Coordinata colonna (0-based)
        
        Returns:
            int | str: Il valore della cella rivelata (0-8, "M")
        """
        # Verifica che le coordinate siano valide
        if not (0 <= x < self.n and 0 <= y < self.n):
            raise ValueError(f"Coordinate non valide: ({x}, {y}). La griglia è {self.n}x{self.n}")
        
        # Rivela il valore reale
        revealed_value = self.grid[x][y]
        return revealed_value
    

    def print_grid(self): # per debugging
        """
        Stampa la griglia (ground truth) in modo leggibile.
        """
        for row in self.grid:
            print(" ".join(str(cell).rjust(2) for cell in row))


