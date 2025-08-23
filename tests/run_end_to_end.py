# tests/run_end_to_end.py
import sys, argparse, random, collections
sys.path.append(".")

from agent import Agent  # <-- usa l'unica classe Agent

def neighbors(n, i, j):
    for di in (-1,0,1):
        for dj in (-1,0,1):
            if di==0 and dj==0: continue
            r, c = i+di, j+dj
            if 0 <= r < n and 0 <= c < n:
                yield r, c

class MiniEnv:
    """Mini environment per testare gli agenti senza dipendere dall'Env ufficiale."""
    def __init__(self, n, num_mines, seed=0):
        self.n = n
        self.num_mines = num_mines
        self.rng = random.Random(seed)
        # piazza mine
        all_cells = [(i,j) for i in range(n) for j in range(n)]
        self.mines = set(self.rng.sample(all_cells, num_mines))
        # precompute contatori adiacenze
        self.counts = [[0]*n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if (i,j) in self.mines: continue
                self.counts[i][j] = sum((r,c) in self.mines for (r,c) in neighbors(n,i,j))
        # revealed tracking (solo per la logica dell'env di test)
        self.revealed = set()

    def reveal(self, x, y):
        """Rivela la cella (x,y). Ritorna:
           - ('M', []) se è una mina
           - (k, revealed_list) se è safe, con k=count di (x,y) e revealed_list = [(i,j,val), ...]
             includendo flood-fill se k==0.
        """
        if (x,y) in self.mines:
            return 'M', []
        n = self.n
        q = collections.deque()
        out = []
        def do_reveal(i,j):
            if (i,j) in self.revealed: return
            self.revealed.add((i,j))
            out.append((i,j, self.counts[i][j]))
            if self.counts[i][j]==0:
                for r,c in neighbors(n,i,j):
                    if (r,c) not in self.revealed and (r,c) not in self.mines:
                        q.append((r,c))
        if self.counts[x][y]==0:
            q.append((x,y))
            while q:
                i,j = q.popleft()
                do_reveal(i,j)
        else:
            do_reveal(x,y)
        return self.counts[x][y], out

    def check_victory(self, agent_knowledge):
        safe_total = self.n*self.n - self.num_mines
        safe_revealed = 0
        for i in range(self.n):
            for j in range(self.n):
                if (i,j) not in self.mines and isinstance(agent_knowledge[i][j], int):
                    safe_revealed += 1
        return safe_revealed == safe_total

def make_agent(agent_kind, n):
    if agent_kind == "random":
        return Agent(n, strategy="random")        # random puro (no PB)
    elif agent_kind == "bt":
        return Agent(n, strategy="backtracking")  # backtracking + PB S1
    else:
        raise ValueError(f"Unknown agent_kind: {agent_kind}")

def play_one(agent_kind, n, mines, seed):
    env = MiniEnv(n, mines, seed)
    agent = make_agent(agent_kind, n)
    agent.total_mines = mines
    # Prima mossa: trova una safe per avviare il gioco
    start = None
    for i in range(n):
        for j in range(n):
            if (i,j) not in env.mines:
                start = (i,j); break
        if start: break

    k, revealed = env.reveal(*start)
    for (i,j,val) in revealed:
        agent.observe(i,j,val)

    steps = 0
    while True:
        # 1) Chiedo all'agente la prossima azione
        if hasattr(agent, "choose_action"):
            action = agent.choose_action()
        elif hasattr(agent, "decide_next_action"):
            action = agent.decide_next_action()
        else:
            raise RuntimeError("L'agente non espone choose_action/decide_next_action")

        if action is None:
            return {"result":"stuck", "steps":steps}

        # Normalizza e gestisci flag/mark
        a = None; x = y = None
        if isinstance(action, (list, tuple)):
            if len(action) == 2 and all(isinstance(v, int) for v in action):
                a, (x, y) = "reveal", action
            elif len(action) >= 3:
                a = str(action[0]).strip().lower()
                x, y = action[1], action[2]
            else:
                return {"result":"invalid_action", "steps":steps, "action":action}
        else:
            return {"result":"invalid_action", "steps":steps, "action":action}

        if a in ("flag","mark","mark_mine","mine"):
            agent.mark_mine(x, y)
            continue
        if a not in ("reveal","open","click"):
            return {"result":"invalid_action", "steps":steps, "action":action}

        # 3) Esegui reveal
        steps += 1  # conta solo i reveal come step
        val, revealed = env.reveal(x, y)
        if val == 'M':
            return {"result":"mine", "steps":steps, "pos":(x,y)}
        for (i,j,v) in revealed:
            agent.observe(i,j,v)

        # 4) Check vittoria
        if env.check_victory(agent.knowledge):
            return {"result":"win", "steps":steps}

def bench(agent_kind, n, mines, games, seed):
    rng = random.Random(seed)
    wins = 0; mines_hit = 0; stucks = 0
    steps_sum = 0
    for g in range(games):
        r = play_one(agent_kind, n, mines, seed=rng.randint(0,10**9))
        steps_sum += r.get("steps",0)
        if r["result"] == "win": wins += 1
        elif r["result"] == "mine": mines_hit += 1
        elif r["result"] == "stuck": stucks += 1
    return {"wins": wins, "mines": mines_hit, "stuck": stucks, "games": games, "avg_steps": steps_sum/max(1,games)}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", choices=["random","bt"], default="random")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--mines", type=int, default=10)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--games", type=int, default=1)
    args = ap.parse_args()

    if args.games == 1:
        out = play_one(args.agent, args.n, args.mines, args.seed)
        print(out)
    else:
        res = bench(args.agent, args.n, args.mines, args.games, args.seed)
        print(res)
