"""
Script di assessment semplice per confrontare le 4 strategie di minesweeper.
Testa su griglia 10x10 con densità mine 15% (15 mine), 100 games per strategia.
"""

from minesweeper_env import MinesweeperEnv
from agent import Agent
import time
import statistics
import json
from datetime import datetime


def safe_first_move(env, agent):
    """Garantisce una prima mossa sicura per qualsiasi agente."""
    for target_value in [0, 1, None]:  # None = qualsiasi non-mina
        for i in range(env.n_row):
            for j in range(env.n_col):
                cell_value = env.grid[i][j]
                if (target_value is None and cell_value != "M") or cell_value == target_value:
                    value = env.reveal(i, j)
                    agent.observe(i, j, value)
                    return i, j, value
    raise Exception("Impossibile trovare una prima mossa sicura!")


def run_single_game(strategy, n_row, n_col, n_mines):
    """Esegue una singola partita e restituisce le metriche."""
    env = MinesweeperEnv(n_row, n_col, n_mines)
    agent = Agent(n_row, n_col, strategy=strategy, total_mines=n_mines)
    agent.total_mines = n_mines
    agent.to_flag = n_mines
    
    # Prima mossa sicura
    safe_first_move(env, agent)
    
    move_count = 0
    move_times = []
    cells_revealed = 1  # Prima mossa già fatta
    game_start = time.time()
    won = False
    
    while True:
        move_start = time.time()
        action = agent.choose_action()
        move_end = time.time()
        
        if action is None:
            break
            
        move_times.append(move_end - move_start)
        move = action[0]
        
        if move == "reveal":
            x, y = action[1], action[2]
            value = env.reveal(x, y)
            if value == "M":
                # Game over - mina colpita
                agent.observe(x, y, value)
                break
            if value is not None:
                agent.observe(x, y, value)
                cells_revealed += 1
                
        elif move == "reveal_all_safe":
            safe_cells = action[1]
            game_over = False
            for x, y in safe_cells:
                value = env.reveal(x, y)
                if value == "M":
                    agent.observe(x, y, value)
                    game_over = True
                    break
                if value is not None:
                    agent.observe(x, y, value)
                    cells_revealed += 1
            if game_over:
                break
                
        elif move == "flag_all":
            mine_cells = action[1]
            for x, y in mine_cells:
                agent.mark_mine(x, y)
        
        # Controlla vittoria
        if agent.check_victory_status(env):
            # Flagga automaticamente le mine rimanenti
            for i in range(n_row):
                for j in range(n_col):
                    if env.grid[i][j] == "M" and agent.knowledge[i][j] == "?":
                        agent.mark_mine(i, j)
            won = True
            break
            
        move_count += 1
    
    game_end = time.time()
    game_time = game_end - game_start
    avg_move_time = statistics.mean(move_times) if move_times else 0
    
    return {
        'won': won,
        'cells_revealed': cells_revealed,
        'game_time': game_time,
        'avg_move_time': avg_move_time,
        'total_moves': move_count + 1  # +1 per la prima mossa
    }


def run_assessment_mode(mode="mode1"):
    """Esegue l'assessment in base alla modalità scelta."""
    if mode == "mode1":
        # Modalità 1: 10x10 con 15% mine, tutte le 4 strategie
        n_row, n_col = 10, 10
        density = 0.15
        strategies = [
            "random",
            "backtracking", 
            "backtracking_advanced",
            "backtracking_gac3"
        ]
        n_games = 100
        mode_name = "MODALITÀ 1 - Griglia piccola, tutte le strategie"
    elif mode == "mode2":
        # Modalità 2: 16x16 con 20% mine, solo strategie avanzate
        n_row, n_col = 16, 16
        density = 0.20
        strategies = [
            "backtracking_advanced",
            "backtracking_gac3"
        ]
        n_games = 100
        mode_name = "MODALITÀ 2 - Griglia grande, strategie avanzate"
    else:
        # Modalità 3: 16x30 con 99 mine, solo strategia GAC3
        n_row, n_col = 16, 30
        n_mines = 99  # Numero fisso di mine invece di densità
        strategies = [
            "backtracking_gac3"
        ]
        n_games = 50
        density = n_mines / (n_row * n_col)  # Calcola densità per display
        mode_name = "MODALITÀ 3 - Griglia expert, solo GAC3"
    
    if mode != "mode3":
        n_mines = int(n_row * n_col * density)
    
    print(f"=== {mode_name} ===")
    print(f"Griglia: {n_row}x{n_col} con {n_mines} mine ({density*100:.1f}%)")
    print(f"Games per strategia: {n_games}")
    print(f"Strategie: {', '.join(strategies)}")
    print()
    
    results = {}
    
    for i, strategy in enumerate(strategies):
        print(f"[{i+1}/{len(strategies)}] Testando strategia: {strategy}")
        
        games_data = []
        wins = 0
        
        for game_num in range(n_games):
            if (game_num + 1) % 20 == 0:
                print(f"  Game {game_num + 1}/{n_games}")
                
            game_result = run_single_game(strategy, n_row, n_col, n_mines)
            games_data.append(game_result)
            
            if game_result['won']:
                wins += 1
        
        # Calcola metriche aggregate
        win_rate = wins / n_games
        avg_cells_revealed = statistics.mean([g['cells_revealed'] for g in games_data])
        avg_move_time = statistics.mean([g['avg_move_time'] for g in games_data])
        avg_game_time = statistics.mean([g['game_time'] for g in games_data])
        
        results[strategy] = {
            'win_rate': win_rate,
            'avg_cells_revealed': avg_cells_revealed,
            'avg_move_time': avg_move_time,
            'avg_game_time': avg_game_time,
            'total_games': n_games,
            'wins': wins
        }
        
        print(f"  Win rate: {wins}/{n_games} ({win_rate*100:.1f}%)")
        print()
    
    return results, n_row, n_col, n_mines, n_games





def print_results(results, n_row, n_col, n_mines, n_games):
    """Stampa i risultati in formato leggibile."""
    print("=" * 60)
    print("RISULTATI ASSESSMENT")
    print("=" * 60)
    print(f"Configurazione: {n_row}x{n_col}, {n_mines} mine, {n_games} games/strategia")
    print()
    
    # Ordina per win rate
    sorted_strategies = sorted(results.items(), key=lambda x: x[1]['win_rate'], reverse=True)
    
    for strategy, metrics in sorted_strategies:
        print(f"STRATEGIA: {strategy}")
        print(f"  Win Rate: {metrics['wins']}/{metrics['total_games']} ({metrics['win_rate']*100:.1f}%)")
        print(f"  Celle rivelate (media): {metrics['avg_cells_revealed']:.1f}")
        print(f"  Tempo per mossa (media): {metrics['avg_move_time']*1000:.2f}ms")
        print(f"  Tempo per partita (media): {metrics['avg_game_time']:.2f}s")
        print()


def save_results(results, n_row, n_col, n_mines, n_games):
    """Salva i risultati in un file JSON."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"simple_assessment_{timestamp}.json"
    
    data = {
        'timestamp': timestamp,
        'configuration': {
            'grid_size': f"{n_row}x{n_col}",
            'n_mines': n_mines,
            'density': n_mines / (n_row * n_col),
            'games_per_strategy': n_games
        },
        'results': results
    }
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Risultati salvati in: {filename}")


if __name__ == "__main__":
    start_time = time.time()
    
    # Chiedi all'utente quale modalità eseguire
    print("Scegli modalità di assessment:")
    print("1. Modalità 1: 10x10, 15% mine, tutte le strategie")
    print("2. Modalità 2: 16x16, 20% mine, solo strategie avanzate")
    print("3. Modalità 3: 16x30, 99 mine, solo GAC3 (expert)")
    
    while True:
        choice = input("Inserisci la tua scelta (1-3): ").strip()
        if choice in ["1", "2", "3"]:
            break
        print("Scelta non valida. Inserisci 1, 2 o 3.")
    
    print()
    
    if choice == "1":
        results, n_row, n_col, n_mines, n_games = run_assessment_mode("mode1")
    elif choice == "2":
        results, n_row, n_col, n_mines, n_games = run_assessment_mode("mode2")
    else:
        results, n_row, n_col, n_mines, n_games = run_assessment_mode("mode3")
    
    print_results(results, n_row, n_col, n_mines, n_games)
    save_results(results, n_row, n_col, n_mines, n_games)

    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\nAssessment completato in {total_time/60:.1f} minuti")
