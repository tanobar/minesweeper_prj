"""
assessment.py - Assessment semplificato per confrontare le 5 strategie minesweeper.

Sistema focalizzato che raccoglie solo le metriche essenziali:
- Win rate
- Numero medio di celle rivelate
- Tempo medio per mossa/partita

Confronta le 5 strategie: random, backtracking, backtracking_advanced, backtracking_gac3, backtracking_pb
"""

import sys
import time
import random
import json
import argparse
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, asdict
import statistics
from pathlib import Path

sys.path.append(".")

from agent import Agent
from minesweeper_env import MinesweeperEnv


@dataclass
class GameResult:
    """Risultato di una singola partita."""
    strategy: str
    result: str  # "win", "mine", "stuck"
    steps: int
    revealed_cells: int
    time_total: float
    time_per_move: float
    grid_size_h: int
    grid_size_w: int
    mine_count: int
    seed: int


@dataclass
class StrategyMetrics:
    """Metriche aggregate per una strategia."""
    strategy: str
    games_played: int
    win_rate: float
    avg_revealed_cells: float
    avg_steps: float
    avg_time_total: float
    avg_time_per_move: float


class GameRunner:
    """Esegue singole partite con focus sulle metriche essenziali."""
    
    def safe_first_move(self, env, agent):
        """Prima mossa sicura garantita."""
        for i in range(env.n_row):
            for j in range(env.n_col):
                if env.grid[i][j] == 0:
                    value = env.reveal(i, j)
                    agent.observe(i, j, value)
                    return i, j, value
        
        for i in range(env.n_row):
            for j in range(env.n_col):
                if env.grid[i][j] == 1:
                    value = env.reveal(i, j)
                    agent.observe(i, j, value)
                    return i, j, value
        
        for i in range(env.n_row):
            for j in range(env.n_col):
                if env.grid[i][j] != "M":
                    value = env.reveal(i, j)
                    agent.observe(i, j, value)
                    return i, j, value
        
        raise Exception("Impossibile trovare una prima mossa sicura!")
    
    def count_revealed_cells(self, knowledge):
        """Conta celle rivelate."""
        revealed = 0
        n_row = len(knowledge)
        n_col = len(knowledge[0])
        for i in range(n_row):
            for j in range(n_col):
                if knowledge[i][j] != "?" and knowledge[i][j] != "X":
                    revealed += 1
        return revealed
    
    def play_game(self, strategy: str, grid_size_h: int, grid_size_w: int, mine_count: int, seed: int) -> GameResult:
        """Esegue una singola partita."""
        
        random.seed(seed)
        env = MinesweeperEnv(grid_size_h, grid_size_w, mine_count)
        agent = Agent(grid_size_h, grid_size_w, strategy=strategy, total_mines=mine_count)
        
        start_time = time.time()
        move_times = []
        steps = 0
        
        try:
            # Prima mossa sicura
            move_start = time.time()
            self.safe_first_move(env, agent)
            move_times.append(time.time() - move_start)
            
            # Game loop
            while True:
                move_start = time.time()
                action = agent.choose_action()
                
                if action is None:
                    result = "stuck"
                    break
                
                move_type = action[0]
                
                if move_type == "reveal":
                    x, y = action[1], action[2]
                    value = env.reveal(x, y)
                    move_times.append(time.time() - move_start)
                    steps += 1
                    
                    if value == "M":
                        agent.observe(x, y, value)
                        result = "mine"
                        break
                    
                    agent.observe(x, y, value)
                
                elif move_type == "reveal_all_safe":
                    safe_cells = action[1]
                    move_times.append(time.time() - move_start)
                    
                    game_over = False
                    for x, y in safe_cells:
                        value = env.reveal(x, y)
                        steps += 1
                        
                        if value == "M":
                            agent.observe(x, y, value)
                            result = "mine"
                            game_over = True
                            break
                        
                        agent.observe(x, y, value)
                    
                    if game_over:
                        break
                
                elif move_type == "flag":
                    x, y = action[1], action[2]
                    move_times.append(time.time() - move_start)
                    env.flag(x, y)
                    agent.mark_mine(x, y)
                
                # Check victory
                if agent.check_victory_status(env):
                    result = "win"
                    break
            
            total_time = time.time() - start_time
            revealed = self.count_revealed_cells(agent.knowledge)
            avg_move_time = statistics.mean(move_times) if move_times else 0
            
            return GameResult(
                strategy=strategy,
                result=result,
                steps=steps,
                revealed_cells=revealed,
                time_total=total_time,
                time_per_move=avg_move_time,
                grid_size_h=grid_size_h,
                grid_size_w=grid_size_w,
                mine_count=mine_count,
                seed=seed
            )
        
        except Exception as e:
            total_time = time.time() - start_time
            revealed = self.count_revealed_cells(agent.knowledge)
            avg_move_time = statistics.mean(move_times) if move_times else 0
            
            return GameResult(
                strategy=strategy,
                result="error",
                steps=steps,
                revealed_cells=revealed,
                time_total=total_time,
                time_per_move=avg_move_time,
                grid_size_h=grid_size_h,
                grid_size_w=grid_size_w,
                mine_count=mine_count,
                seed=seed
            )


class Assessment:
    """Assessment semplificato per confrontare le 5 strategie."""
    
    def __init__(self, output_dir="results"):
        self.runner = GameRunner()
        self.results = []
        
        # Configura cartella risultati
        if output_dir is not None:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(exist_ok=True)
            print(f"Risultati verranno salvati in: {self.output_dir.absolute()}")
        else:
            self.output_dir = None
    
    def run_assessment(self, strategies, grid_configs, games_per_config=50):
        """
        Esegue l'assessment per tutte le strategie e configurazioni.
        
        Args:
            strategies: Lista delle strategie da testare
            grid_configs: Lista di dict con 'grid_size_h', 'grid_size_w' e 'mine_count'
            games_per_config: Numero di partite per configurazione
        """
        total_configs = len(strategies) * len(grid_configs)
        total_games = total_configs * games_per_config
        
        print(f"Assessment")
        print(f"Strategie: {len(strategies)}")
        print(f"Configurazioni griglia: {len(grid_configs)}")
        print(f"Games per configurazione: {games_per_config}")
        print(f"Total games: {total_games}")
        print()
        
        config_count = 0
        for grid_config in grid_configs:
            grid_size_h = grid_config['grid_size_h']
            grid_size_w = grid_config['grid_size_w']
            mine_count = grid_config['mine_count']
            
            print(f"Griglia {grid_size_h}x{grid_size_w} con {mine_count} mine")
            
            for strategy_idx, strategy in enumerate(strategies):
                config_count += 1
                print(f"  [{strategy_idx+1}/{len(strategies)}] Strategia: {strategy}")
                
                strategy_results = []
                for game_num in range(games_per_config):
                    if game_num % 10 == 0 and game_num > 0:
                        print(f"    Game {game_num}/{games_per_config}")
                    
                    seed = random.randint(0, 10**9)
                    result = self.runner.play_game(strategy, grid_size_h, grid_size_w, mine_count, seed)
                    strategy_results.append(result)
                    self.results.append(result)
                
                # Quick summary per strategia
                wins = sum(1 for r in strategy_results if r.result == "win")
                print(f"    Win rate: {wins}/{games_per_config} ({wins/games_per_config*100:.1f}%)")
            
            print()
        
        return self._compute_metrics()
    
    def _compute_metrics(self):
        """Calcola metriche aggregate per strategia."""
        strategy_results = defaultdict(list)
        
        for result in self.results:
            strategy_results[result.strategy].append(result)
        
        metrics = {}
        for strategy, results in strategy_results.items():
            if not results:
                continue
            
            total_games = len(results)
            wins = sum(1 for r in results if r.result == "win")
            
            win_rate = wins / total_games if total_games > 0 else 0
            avg_revealed = statistics.mean([r.revealed_cells for r in results])
            avg_steps = statistics.mean([r.steps for r in results])
            avg_time_total = statistics.mean([r.time_total for r in results])
            avg_time_per_move = statistics.mean([r.time_per_move for r in results])
            
            metrics[strategy] = StrategyMetrics(
                strategy=strategy,
                games_played=total_games,
                win_rate=win_rate,
                avg_revealed_cells=avg_revealed,
                avg_steps=avg_steps,
                avg_time_total=avg_time_total,
                avg_time_per_move=avg_time_per_move
            )
        
        return metrics
    
    def generate_report(self, metrics, filename=None):
        """Genera report semplificato."""
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("MINESWEEPER - CONFRONTO STRATEGIE")
        report_lines.append("=" * 80)
        report_lines.append(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Total games: {len(self.results)}")
        report_lines.append("")
        
        # Tabella riassuntiva
        report_lines.append("RISULTATI CONFRONTO")
        report_lines.append("-" * 60)
        report_lines.append(f"{'Strategia':<20} {'Win Rate':<10} {'Celle Avg':<10} {'Tempo/Mossa':<12}")
        report_lines.append("-" * 60)
        
        sorted_strategies = sorted(metrics.items(), key=lambda x: x[1].win_rate, reverse=True)
        
        for strategy, metric in sorted_strategies:
            report_lines.append(
                f"{strategy:<20} {metric.win_rate*100:>7.1f}% "
                f"{metric.avg_revealed_cells:>8.1f} "
                f"{metric.avg_time_per_move*1000:>9.1f}ms"
            )
        
        report_lines.append("")
        
        # Analisi dettagliata
        report_lines.append("ANALISI DETTAGLIATA")
        report_lines.append("-" * 30)
        
        for strategy, metric in sorted_strategies:
            report_lines.append(f"{strategy.upper()}:")
            report_lines.append(f"  Win rate: {metric.win_rate*100:.1f}%")
            report_lines.append(f"  Celle rivelate (media): {metric.avg_revealed_cells:.1f}")
            report_lines.append(f"  Steps per game: {metric.avg_steps:.1f}")
            report_lines.append(f"  Tempo per game: {metric.avg_time_total:.3f}s")
            report_lines.append(f"  Tempo per mossa: {metric.avg_time_per_move*1000:.1f}ms")
            report_lines.append("")
        
        # Conclusioni
        if sorted_strategies:
            best = sorted_strategies[0]
            report_lines.append("CONCLUSIONI")
            report_lines.append("-" * 20)
            report_lines.append(f"Migliore strategia: {best[0]}")
            report_lines.append(f"  - Win rate: {best[1].win_rate*100:.1f}%")
            report_lines.append(f"  - Velocità: {best[1].avg_time_per_move*1000:.1f}ms/mossa")
            
            # Confronto con/senza PB
            pb_strategy = None
            no_pb_strategies = []
            
            for strategy, metric in metrics.items():
                if strategy == "backtracking_pb":
                    pb_strategy = (strategy, metric)
                elif strategy != "random":
                    no_pb_strategies.append((strategy, metric))
            
            if pb_strategy and no_pb_strategies:
                report_lines.append("")
                report_lines.append("IMPATTO PROBABILISTIC REASONING (PB)")
                report_lines.append("-" * 45)
                
                avg_no_pb_win_rate = statistics.mean([m[1].win_rate for m in no_pb_strategies])
                pb_win_rate = pb_strategy[1].win_rate
                
                report_lines.append(f"Win rate con PB: {pb_win_rate*100:.1f}%")
                report_lines.append(f"Win rate senza PB (media): {avg_no_pb_win_rate*100:.1f}%")
                report_lines.append(f"Miglioramento: {(pb_win_rate - avg_no_pb_win_rate)*100:+.1f}%")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        report_text = "\n".join(report_lines)
        print(report_text)
        
        if filename:
            # Se filename non ha path, salvalo nella cartella output_dir (se esiste)
            file_path = Path(filename)
            if not file_path.is_absolute() and file_path.parent == Path('.') and self.output_dir is not None:
                file_path = self.output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"\nReport salvato in: {file_path.absolute()}")
        
        return report_text
    
    def save_data(self, filename):
        """Salva dati grezzi in JSON."""
        if self.output_dir is None:
            print("Salvataggio dati disabilitato (modalità test)")
            return
            
        # Se filename non ha path, salvalo nella cartella output_dir
        file_path = Path(filename)
        if not file_path.is_absolute() and file_path.parent == Path('.'):
            file_path = self.output_dir / filename
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_games": len(self.results),
            "results": [asdict(r) for r in self.results]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Dati salvati in: {file_path.absolute()}")


def get_strategies():
    """Ritorna le 5 strategie da confrontare."""
    return [
        "random",
        "backtracking", 
        "backtracking_advanced",
        "backtracking_gac3",
        "backtracking_pb"
    ]


def get_grid_configs(mode="quick"):
    """Ritorna configurazioni griglia per il test."""
    if mode == "quick":
        return [
            {"grid_size_h": 8, "grid_size_w": 8, "mine_count": 10}
        ]
    elif mode == "medium":
        return [
            {"grid_size_h": 8, "grid_size_w": 8, "mine_count": 10},
            {"grid_size_h": 10, "grid_size_w": 10, "mine_count": 15}
        ]
    else:  # full
        return [
            {"grid_size_h": 8, "grid_size_w": 8, "mine_count": 10},
            {"grid_size_h": 10, "grid_size_w": 10, "mine_count": 15},
            {"grid_size_h": 12, "grid_size_w": 12, "mine_count": 20}
        ]


def main():
    parser = argparse.ArgumentParser(description="Assessment Semplificato Strategie Minesweeper")
    parser.add_argument("--mode", choices=["quick", "medium", "full"], default="quick",
                       help="Modalità assessment (default: quick)")
    parser.add_argument("--games", type=int, default=50, 
                       help="Numero di games per configurazione (default: 50)")
    parser.add_argument("--output", type=str, help="Nome file output per report")
    parser.add_argument("--data", type=str, help="Nome file per dati JSON")
    parser.add_argument("--results-dir", type=str, default="results",
                       help="Cartella per salvare risultati (default: results)")
    
    args = parser.parse_args()
    
    # Configurazione
    strategies = get_strategies()
    grid_configs = get_grid_configs(args.mode)
    
    print(f"Modalità: {args.mode}")
    print(f"Strategie: {', '.join(strategies)}")
    print(f"Configurazioni: {len(grid_configs)}")
    print()
    
    # Esegui assessment
    assessment = Assessment(output_dir=args.results_dir)
    
    start_time = time.time()
    metrics = assessment.run_assessment(strategies, grid_configs, args.games)
    total_time = time.time() - start_time
    
    print(f"Assessment completato in {total_time/60:.1f} minuti")
    print()
    
    # Genera report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = args.output or f"strategy_comparison_{timestamp}.txt"
    data_file = args.data or f"strategy_data_{timestamp}.json"
    
    assessment.generate_report(metrics, report_file)
    assessment.save_data(data_file)
    
    print(f"Risultati salvati in: {assessment.output_dir}")
    print(f"Report: {report_file}")
    print(f"Dati: {data_file}")
    
    print("\nAssessment completato!")


if __name__ == "__main__":
    main()
