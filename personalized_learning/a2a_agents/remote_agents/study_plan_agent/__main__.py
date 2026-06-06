from a2a_agents.server_factory import run
from .agent_card import public_agent_card
from .agent_executor import AgentExecutor

if __name__ == "__main__":
    run(public_agent_card, AgentExecutor, port=8093)
