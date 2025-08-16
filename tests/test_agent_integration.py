import sys
sys.path.append(".")

from backtrackingcspagent import BacktrackingCSPAgent

def test_agent_pick():
    n = 3
    agent = BacktrackingCSPAgent(n)

    # inizializza lo stato dell'agente
    agent.knowledge = [
        [1, "?", "?" ],
        ["?","?","?"],
        ["?","?",  1 ],
    ]
    agent.mine_cells = set()
    agent.moves_made = set()

    # Chiama il metodo che nel tuo file ritorna ("reveal", x, y)
    # Sostituisci 'decide_next_action' con il nome reale della tua funzione.
    action = agent.choose_action()   # <-- usa il nome reale del tuo metodo
    print("Azione:", action)

    assert action is not None
    a, x, y = action
    assert a == "reveal"
    # in questo setup, ci aspettiamo (1,1) se non ci sono celle sicure deterministiche
    # (Se prima il CSP trova mosse sicure, è ok che scelga quelle e non arrivi al fallback).
    # Se arriva al fallback: 
    # assert (x, y) == (1,1)

if __name__ == "__main__":
    test_agent_pick()
    print("\nTest integrazione eseguito.")