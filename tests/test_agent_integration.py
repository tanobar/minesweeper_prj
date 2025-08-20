# tests/test_agent_integration.py
import sys
sys.path.append(".")

from agent import Agent

def test_agent_pick():
    n = 3
    agent = Agent(n, strategy="backtracking")

    # Riveliamo due celle numeriche per creare vincoli di frontiera
    agent.observe(0, 0, 1)
    agent.observe(2, 2, 1)

    action = agent.choose_action()
    print("Azione:", action)

    assert action is not None
    a, x, y = action
    assert a in ("reveal", "flag")

if __name__ == "__main__":
    test_agent_pick()
    print("\nTest integrazione eseguito.")
