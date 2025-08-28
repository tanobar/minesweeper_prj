from minesweeper_env import MinesweeperEnv
from agent import Agent
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
    # Cerca in ordine: 0, 1, qualsiasi non-mina
    for target_value in [0, 1, None]:  # None = qualsiasi non-mina
        for i in range(env.n_row):
            for j in range(env.n_col):
                cell_value = env.grid[i][j]
                if (target_value is None and cell_value != "M") or cell_value == target_value:
                    print(f"Prima mossa sicura: cella ({i}, {j}) con valore {cell_value}")
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
    
    while True:
        choice = input("Scegli configurazione (1-4): ").strip()
        if choice == "1":
            return Agent(n_row, n_col, strategy="random")
        elif choice == "2":
            return Agent(n_row, n_col, strategy="backtracking")
        elif choice == "3":
            return Agent(n_row, n_col, strategy="backtracking_advanced")
        elif choice == "4":
            return Agent(n_row, n_col, strategy="backtracking_gac3")
        else:
            print("Scelta non valida. Inserisci un numero da 1 a 4.")


n_row, n_col, m = 32, 32, 200  # Dimensione della griglia (r x c) e numero di mine m

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

print("Stato agente dopo prima mossa:")
agent.print_grid()
print()

move_count = 0
# ciclo di gioco
start = time.time()
while True:

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
                #agent.print_grid()
                print("\nGAME OVER.")
                game_over = True
                break
            
            if value is not None:
                agent.observe(x, y, value)
        
        if game_over:
            break

    elif move == "flag_all":
        mine_cells = action[1]
        for x, y in mine_cells:
            agent.mark_mine(x, y)

    #agent.print_grid()
    #print()

    # Controlla se l'agente ha vinto
    if agent.check_victory_status(env):
        # Se ha vinto, flagga automaticamente tutte le mine rimanenti
        for i in range(n_row):
            for j in range(n_col):
                if env.grid[i][j] == "M" and agent.knowledge[i][j] == "?":
                    agent.mark_mine(i, j)
        
        agent.print_grid()
        print(f"\n HAI VINTO IN {move_count} MOSSE!")
        break
    
    move_count += 1

end = time.time()
print("\n Tempo trascorso:", end - start, "secondi")
