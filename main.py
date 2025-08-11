from minesweeper_env import MinesweeperEnv
from agent import *
import time


def safe_first_move(env, agent):
    """
    Garantisce una prima mossa sicura per qualsiasi agente.
    Cerca in ordine: celle con 0, celle con 1, poi qualsiasi cella non-mina.
    
    Args:
        env: L'environment di gioco
        agent: L'agente a cui dare la prima mossa
        
    Returns:
        tuple: (x, y, value) della cella rivelata
    """
    # Prima prova: cerca celle con valore 0
    for i in range(env.n):
        for j in range(env.n):
            if env.grid[i][j] == 0:
                print(f"Prima mossa sicura: cella ({i}, {j}) con valore 0")
                value = env.reveal(i, j)
                agent.observe(i, j, value)
                return i, j, value
    
    # Seconda prova: cerca celle con valore 1
    for i in range(env.n):
        for j in range(env.n):
            if env.grid[i][j] == 1:
                print(f"Prima mossa sicura: cella ({i}, {j}) con valore 1")
                value = env.reveal(i, j)
                agent.observe(i, j, value)
                return i, j, value
    
    # Ultima prova: cerca qualsiasi cella che non sia mina
    for i in range(env.n):
        for j in range(env.n):
            if env.grid[i][j] != "M":
                print(f"Prima mossa sicura: cella ({i}, {j}) con valore {env.grid[i][j]}")
                value = env.reveal(i, j)
                agent.observe(i, j, value)
                return i, j, value
    
    # Questo non dovrebbe mai succedere in una griglia valida
    raise Exception("Impossibile trovare una prima mossa sicura!")


n, m = 10, 10  # Dimensione della griglia (n x n) e numero di mine m

env = MinesweeperEnv(n, m)
agent = BacktrackingCSPAgent(n)

print("Griglia reale:")
env.print_grid()
print()

# Convenzione minesweeper: la prima mossa è sempre sicura
safe_first_move(env, agent)

print("Stato agente dopo prima mossa:")
agent.print_grid()
print()

# ciclo di gioco
move_count = 0
while True:
    move_count += 1
    
    action = agent.choose_action()
    if action is None:
        print("Nessuna mossa da fare.")
        break

    move, x, y = action
    if move == "reveal":
        value = env.reveal(x, y)
        if value == "M":
            print(f"BOOM! Cella ({x}, {y}) era una mina!")
            agent.observe(x, y, value)
            print("\nStato finale:")
            agent.print_grid()
            print("\nGAME OVER.")
            break

        if value is not None:
            agent.observe(x, y, value)

    elif move == "flag":
        env.flag(x, y)
        agent.mark_mine(x, y)

    agent.print_grid()
    
    # Controlla se l'agente ha vinto
    if agent.check_victory_status(env):
        print(f"\nVINTO in {move_count} mosse!")
        break
    
    print()
    time.sleep(1)


