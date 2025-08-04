from funx import *


class MinesweeperEnv:
    def __init__(self, n, m):
        self.n = n
        self.m = m
        self.grid = generate_grid(n, m)
        self.covered_grid = create_covered_grid(self.grid)


    def reveal(self, x, y):
        """
        Rivela il valore reale di una cella nella griglia coperta.
        
        Args:
            x (int): Coordinata riga (0-based)
            y (int): Coordinata colonna (0-based)
        
        Returns:
            int | str | None: Il valore della cella rivelata (0-8, "M") o None se già rivelata
        """
        # Verifica che le coordinate siano valide
        if not (0 <= x < self.n and 0 <= y < self.n):
            raise ValueError(f"Coordinate non valide: ({x}, {y}). La griglia è {self.n}x{self.n}")
        
        # Se la cella è già rivelata, restituisce None
        if self.covered_grid[x][y] != "?":
            return None
        
        # Rivela il valore reale
        revealed_value = self.grid[x][y]
        self.covered_grid[x][y] = revealed_value
        return revealed_value


    def flag(self, x, y):
        """
        Piazza una bandiera (flag) su una cella coperta nella griglia di gioco.
        Sostituisce "?" con "X" solo se la cella è ancora coperta.
        
        Args:
            x (int): Coordinata riga (0-based)
            y (int): Coordinata colonna (0-based)
        
        Returns:
            bool: True se la bandiera è stata piazzata, False se la cella non era coperta
        """
        # Verifica che le coordinate siano valide
        if not (0 <= x < self.n and 0 <= y < self.n):
            raise ValueError(f"Coordinate non valide: ({x}, {y}). La griglia è {self.n}x{self.n}")

        # Se la cella è coperta ("?"), piazza la bandiera
        if self.covered_grid[x][y] == "?":
            self.covered_grid[x][y] = "X"
            return True
        
        # Se la cella non è coperta, non modificare nulla
        return False
    

    def print_grid(self):
        """
        Stampa la griglia (ground truth) in modo leggibile.
        """
        for row in self.grid:
            print(" ".join(str(cell).rjust(2) for cell in row))


