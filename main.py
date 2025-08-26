from minesweeper_env import MinesweeperEnv
from agent import Agent
import time
from gui import MinesweeperGUI
import tkinter as tk
#from sound import play_melody


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
    for i in range(env.n_row):
        for j in range(env.n_col):
            if env.grid[i][j] == 0:
                print(f"Prima mossa sicura: cella ({i}, {j}) con valore 0")
                value = env.reveal(i, j)
                agent.observe(i, j, value)
                return i, j, value
    
    # Seconda prova: cerca celle con valore 1
    for i in range(env.n_row):
        for j in range(env.n_col):
            if env.grid[i][j] == 1:
                print(f"Prima mossa sicura: cella ({i}, {j}) con valore 1")
                value = env.reveal(i, j)
                agent.observe(i, j, value)
                return i, j, value
    
    # Ultima prova: cerca qualsiasi cella che non sia mina
    for i in range(env.n_row):
        for j in range(env.n_col):
            if env.grid[i][j] != "M":
                print(f"Prima mossa sicura: cella ({i}, {j}) con valore {env.grid[i][j]}")
                value = env.reveal(i, j)
                agent.observe(i, j, value)
                return i, j, value
    
    # Questo non dovrebbe mai succedere in una griglia valida
    raise Exception("Impossibile trovare una prima mossa sicura!")


def choose_agent_configuration():
    """Permette all'utente di configurare l'agente."""
    print("=== CONFIGURAZIONE AGENTE ===")
    print("1. Random Agent")
    print("2. Backtracking CSP (base)")
    print("3. Backtracking CSP (con euristiche)")
    print("4. Backtracking CSP (con euristiche + GAC3)")
    print("5. Backtracking CSP (con euristiche + GAC3 + PB)")
    
    while True:
        choice = input("Scegli configurazione (1-5): ").strip()
        if choice == "1":
            return Agent(n_row, n_col, strategy="random")
        elif choice == "2":
            return Agent(n_row, n_col, strategy="backtracking")
        elif choice == "3":
            return Agent(n_row, n_col, strategy="backtracking_advanced")
        elif choice == "4":
            return Agent(n_row, n_col, strategy="backtracking_gac3")
        elif choice == "5":
            return Agent(n_row, n_col, strategy="backtracking_pb")
        else:
            print("Scelta non valida. Inserisci un numero da 1 a 5.")


n_row, n_col, m = 16, 30, 100  # Dimensione della griglia (r x c) e numero di mine m

# Configura l'agente
agent = choose_agent_configuration()

env = MinesweeperEnv(n_row, n_col, m)

agent.total_mines = m
agent.to_flag = m

print(f"\nUsando strategia: {agent.strategy}")
"""print("\nGriglia reale:")
env.print_grid()
print()"""

# Convenzione minesweeper: la prima mossa è sempre sicura
safe_first_move(env, agent)

"""print("Stato agente dopo prima mossa:")
agent.print_grid()
print()"""

"""#suoni
MINE_SOUND = [(523, 0.2), (440, 0.2), (330, 0.4)]
WIN_SOUND  = [(659, 0.2), (784, 0.2), (880, 0.4)]"""

move_count = 0
# ciclo di gioco
root = tk.Tk()
root.title('Minesweeper')
# Bring window to front
root.lift()
root.attributes("-topmost", True)
root.after(0, lambda: root.attributes("-topmost", False))
gui = MinesweeperGUI(root, n_row, n_col, m)
start = time.time()
while True:

    root.update()   

    action = agent.choose_action()
    if action is None:
        print("Nessuna mossa da fare.")
        break

    move = action[0]
    if move == "reveal":
        x, y = action[1], action[2]
        value = env.reveal(x, y)
        if value == "M":
            print(f"BOOM! Cella ({x}, {y}) era una mina!")
            agent.observe(x, y, value)
            print("\nStato finale:")
            #agent.print_grid()
            gui.draw_grid(agent.knowledge,  agent.to_flag, 'n')
            #play_melody(MINE_SOUND)
            print("\nGAME OVER.")
            break

        if value is not None:
            agent.observe(x, y, value)

    elif move == "reveal_all_safe":
        safe_cells = action[1]
        game_over = False
        for x, y in safe_cells:
            value = env.reveal(x, y)
            if value == "M":
                print(f"ERRORE: Cella ({x}, {y}) doveva essere sicura ma era una mina!")
                agent.observe(x, y, value)
                print("\nStato finale:")
                gui.draw_grid(agent.knowledge, agent.to_flag, 'n')
                print("\nGAME OVER.")
                game_over = True
                break
            
            if value is not None:
                agent.observe(x, y, value)
        
        if game_over:
            break

    elif move == "flag":
        x, y = action[1], action[2]
        env.flag(x, y)
        agent.mark_mine(x, y)

    #agent.print_grid()
    gui.draw_grid(agent.knowledge, agent.to_flag, '')

    # Controlla se l'agente ha vinto
    if agent.check_victory_status(env):
        #agent.print_grid()
        gui.draw_grid(agent.knowledge, agent.to_flag, 'y')
        #play_melody(WIN_SOUND)
        print(f"\n HAI VINTO IN {move_count} MOSSE!")
        break
    
    move_count += 1

    #print()
    time.sleep(0.3)
end = time.time()
print("\n Tempo trascorso:", end - start - move_count*0.3, "secondi")
root.mainloop()
