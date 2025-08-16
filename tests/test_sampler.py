from prob.approximate import RandomizedSampler
from prob.frontier import frontier_components
from prob.exact import ExactEnumeration

knowledge = [
    [2, "?", "?", "?" ],
    ["?","?","?","?"],
    ["?","?","?","?"],
    ["?","?","?", 2 ],
]

comps = frontier_components(knowledge, set())
print("num components:", len(comps), "sizes:", [len(vs) for vs,_ in comps])
vars_set, cons = comps[0]
print("first component size:", len(vars_set), "constraints:", len(cons))

res_ex = ExactEnumeration(vars_set, cons, max_solutions=100000).run()
print("solutions via exact:", res_ex["solutions"])
print("marginals (exact):", {k: round(v,3) for k,v in res_ex["marginals"].items()})

for c in cons:
    print("req:", c["count"], "vars:", sorted(c["vars"]))

sampler = RandomizedSampler(
    vars_set, cons,
    max_samples=5000,     # ↑ più soluzioni raccolte
    max_nodes=200000,     # ↑ un po’ di spazio di esplorazione
    max_time_sec=3.5,     # ↑ limite tempo (uscita garantita)
    seed=42
)
res = sampler.run()
print("solutions via sampler:", None if res is None else res["solutions"])
if res:
    items = list(res["marginals"].items())[:6]
    print("marginals (sample):", {k: round(v,3) for k,v in items})
