import sys
sys.path.append(".")

from agent import RandomAgent

def test_random_agent_prob_fallback():
    n = 3
    ag = RandomAgent(n)
    ag.knowledge = [
        [1, "?", "?" ],
        ["?","?","?"],
        ["?","?",  1 ],
    ]
    ag.mine_cells = set()
    ag.moves_made = set()

    action = ag.choose_action()
    print("Azione:", action)
    assert action is not None and action[0] == "reveal"
    # in questo setup, il min-risk dovrebbe preferire il centro (1,1)
    # (se non ci sono celle sicure già note)
    # assert action[1:] == (1,1)

if __name__ == "__main__":
    test_random_agent_prob_fallback()
    print("OK")
