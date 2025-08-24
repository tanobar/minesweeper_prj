import sys
import time

sys.path.append(".")

def test_assessment():
    """Testa il sistema di assessment."""
    print("Test Assessment Semplificato")
    print("=" * 40)
    
    try:
        from assessment import Assessment, GameRunner, get_strategies
        print("Import successful")
        
        # Test singola partita per ogni strategia
        runner = GameRunner()
        strategies = get_strategies()
        
        print(f"\n Test single games per {len(strategies)} strategie:")
        
        for strategy in strategies:
            print(f"  Testing {strategy}...", end=" ")
            
            start_time = time.time()
            result = runner.play_game(strategy, grid_size=6, mine_count=5, seed=42)
            execution_time = time.time() - start_time
            
            print(f"Result: {result.result}, Steps: {result.steps}, Time: {execution_time:.3f}s")
        
        print("\n Mini assessment (3 games per strategia)...")
        
        # Mini assessment senza salvataggio file e senza creare cartelle
        assessment = Assessment(output_dir=None)
        grid_configs = [{"grid_size": 6, "mine_count": 5}]
        
        start_time = time.time()
        metrics = assessment.run_assessment(strategies, grid_configs, games_per_config=3)
        total_time = time.time() - start_time
        
        print(f"\n Mini assessment completato in {total_time:.2f}s")
        print("Risultati:")
        
        for strategy, metric in sorted(metrics.items(), key=lambda x: x[1].win_rate, reverse=True):
            print(f"  {strategy}: {metric.win_rate*100:.1f}% win rate, {metric.avg_time_per_move*1000:.1f}ms/move")
        
        print("\n Tutti i test passed!")
        return True
        
    except Exception as e:
        print(f"\n Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print(" TEST SISTEMA ASSESSMENT MINESWEEPER")
    print("=" * 50)
    print("Questo test verifica che tutte le 5 strategie funzionino.")
    print()
    
    success = test_assessment()
    
    print("\n" + "=" * 50)
    if success:
        print(" SISTEMA PRONTO!")
        print()
        print(" Per lanciare l'assessment:")
        print("   python assessment.py --mode quick")
        print("   python assessment.py --mode medium") 
        print("   python assessment.py --mode full")
    else:
        print(" SISTEMA NON FUNZIONANTE!")
        print("Controllare errori sopra.")


if __name__ == "__main__":
    main()
