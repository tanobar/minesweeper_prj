# tests/test_sampler_vs_exact.py
import random, sys
sys.path.append(".")
from prob.frontier import frontier_components
from prob.exact import ExactEnumeration
from prob.approximate import RandomizedSampler

def run_once():
    # costruiamo un micro-caso: un solo vincolo su k celle
    k = 6
    req = 2
    # knowledge fittizia: un numero 'req' con k ignote attorno
    knowledge = [[0]*(k+2) for _ in range(1)]
    # useremo direttamente la costruzione a mano di una componente:
    vars_set = {(0,i+1) for i in range(k)}
    cons = [{"vars": set(vars_set), "count": req}]

    ex = ExactEnumeration(vars_set, cons).run()
    sa = RandomizedSampler(vars_set, cons, max_samples=4000, max_time_sec=2.0, seed=0).run()
    assert ex and sa
    # confronta le marginali (errore assoluto < 0.05)
    for v in vars_set:
        assert abs(ex["marginals"][v] - sa["marginals"][v]) < 0.05

if __name__ == "__main__":
    for _ in range(5):
        run_once()
    print("Sampler ≈ Esatto su componenti piccole: OK")
