import random


def generate_grid(n_row, n_col, m):
    """
    Genera una griglia n_row x n_col per il minesweeper con m mine posizionate casualmente.
    
    Args:
        n_row, n_col (int): Dimensioni della griglia (n_row x n_col)
        m (int): Numero di mine da posizionare
    
    Returns:
        list: Matrice n x n con mine ("M") e numeri che indicano le mine adiacenti
    """
    # Verifica che il numero di mine non superi il numero di celle disponibili
    if m > n_row * n_col:
        raise ValueError("Il numero di mine non può superare il numero di celle disponibili")
    
    # Inizializza la griglia con zeri
    grid = [[0 for _ in range(n_col)] for _ in range(n_row)]
    
    # Genera posizioni casuali per le mine
    positions = [(i, j) for i in range(n_row) for j in range(n_col)]
    #random.seed(41) #NOTA: random.seed() ha scope GLOBALE per il modulo random.
    #random.Random(41) # questo ha scope locale, solo per la generazione della griglia.
    mine_positions = random.sample(positions, m)
    
    # Posiziona le mine
    for row, col in mine_positions:
        grid[row][col] = "M"

    # Calcola i numeri per le celle intorno alle mine
    for i,j in mine_positions:
        # Controlla tutte le 8 direzioni adiacenti
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                # Salta la cella centrale
                if di == 0 and dj == 0:
                    continue
                        
                ni, nj = i + di, j + dj
                # Verifica che la posizione sia valida
                if 0 <= ni < n_row and 0 <= nj < n_col:
                    if isinstance(grid[ni][nj], int):
                        grid[ni][nj] += 1
   
    return grid



class MinesweeperEnv:
    def __init__(self, n_row, n_col, m):
        self.n_row = n_row
        self.n_col = n_col
        self.m = m
        self.grid = generate_grid(n_row, n_col, m)


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
        if not (0 <= x < self.n_row and 0 <= y < self.n_col):
            raise ValueError(f"Coordinate non valide: ({x}, {y}). La griglia è {self.n_row}x{self.n_col}")
        
        # Rivela il valore reale
        revealed_value = self.grid[x][y]
        return revealed_value
    

    def flag(self, x, y):
        """
        Contrassegna una cella come flaggata (contenente una mina).
        Questo metodo per ora non fa nulla, ma può essere esteso in futuro.
        
        Args:
            x (int): Coordinata riga (0-based)
            y (int): Coordinata colonna (0-based)
        """
        # Verifica che le coordinate siano valide
        if not (0 <= x < self.n_row and 0 <= y < self.n_col):
            raise ValueError(f"Coordinate non valide: ({x}, {y}). La griglia è {self.n_row}x{self.n_col}")
        
        # Per ora questo metodo non fa nulla, la logica del flag è gestita dall'agente
        pass
    

    def check_victory(self, agent_knowledge, total_non_mine_cells):
        """
        Verifica se l'agente ha raggiunto la condizione di vittoria.
        La vittoria si ottiene quando tutte le celle non-mine sono state rivelate.
        
        Args:
            agent_knowledge: La griglia di conoscenza dell'agente
            
        Returns:
            bool: True se l'agente ha vinto, False altrimenti
        """
        
        # Conta quante celle non-mine sono state rivelate dall'agente
        revealed_non_mine_cells = 0
        for i in range(self.n_row):
            for j in range(self.n_col):
                if (self.grid[i][j] != "M" and 
                    agent_knowledge[i][j] != "?" and 
                    agent_knowledge[i][j] != "X"):
                    revealed_non_mine_cells += 1
        
        return revealed_non_mine_cells == total_non_mine_cells


    def print_grid(self): # per debugging
        """
        Stampa la griglia (ground truth) in modo leggibile.
        """
        for row in self.grid:
            print(" ".join(str(cell).rjust(2) for cell in row))


