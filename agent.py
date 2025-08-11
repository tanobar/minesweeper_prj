import random

class Agent:
    def __init__(self, n):
        self.n = n
        self.knowledge = [["?" for _ in range(n)] for _ in range(n)]
        self.moves_made = set()
        self.safe_cells = set()
        self.mine_cells = set()


    def observe(self, x, y, value):
        """
        Aggiorna la knowledge dell'agente con l'informazione osservata.
        """
        self.knowledge[x][y] = value
        self.moves_made.add((x, y))


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
        Verifica se l'agente ha raggiunto la condizione di vittoria
        utilizzando il metodo check_victory dell'environment.
        
        Args:
            env: L'environment di gioco (MinesweeperEnv)
            
        Returns:
            bool: True se l'agente ha vinto, False altrimenti
        """
        return env.check_victory(self.knowledge)
    