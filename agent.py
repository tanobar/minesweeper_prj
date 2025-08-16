import random
from prob.risk import pick_min_risk


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
    
class RandomAgent(Agent):
    def observe(self, x, y, value):
        """
        Aggiorna la knowledge dell'agente con l'informazione osservata.
        """
        self.knowledge[x][y] = value
        self.moves_made.add((x, y))

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


    def choose_action(self):
        """
        Sceglie la prossima azione da fare:
        - Se ci sono celle sicure: rivela una
        - Altrimenti: esplora una cella sconosciuta a caso
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