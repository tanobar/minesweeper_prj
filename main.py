from minesweeper_env import MinesweeperEnv
from agent import *
import time


n, m = 5, 1  # Dimensione della griglia (n x n) e numero di mine m

env = MinesweeperEnv(n, m)
agent = RandomAgent(n)

env.print_grid()  # Stampa la griglia iniziale, per ora solo come riferimento e debugging
print("\n")

# primo passo: rivela una cella già scoperta nell'env (quella iniziale con 0)
found = False
for i in range(env.n):
    for j in range(env.n):
        if env.grid[i][j] == 0:
            agent.observe(i, j, 0)
            found = True
            break
    if found:
        break

agent.print_grid()
print("\n")

# ciclo di gioco
while True:
    action = agent.choose_action()
    if action is None:
        print("Nessuna mossa da fare.")
        break

    move, x, y = action
    if move == "reveal":
        value = env.reveal(x, y)
        if value == "M":
            agent.observe(x, y, value)
            agent.print_grid()
            print("BOOM, GAME OVER.")
            break

        if value is not None:
            agent.observe(x, y, value)

    elif move == "flag":
        env.flag(x, y)
        agent.mark_mine(x, y)

    agent.print_grid()
    
    # Controlla se l'agente ha vinto
    if agent.check_victory_status(env):
        print("CONGRATULAZIONI! HAI VINTO!")
        break
    
    print("\n")
    #aspetta 2 secondi prima di continuare, così visualizzo lo stato corrente
    time.sleep(1)


    