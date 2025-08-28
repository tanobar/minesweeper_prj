import pstats
#RUNNARE PRIMA python -m cProfile -o profile.out minesweeper_prj/trial.py SULLA CONSOLE
p = pstats.Stats("profile.out")
p.sort_stats("tottime").print_stats(20)
