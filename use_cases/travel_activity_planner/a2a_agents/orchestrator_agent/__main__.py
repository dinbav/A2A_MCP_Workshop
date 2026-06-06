from a2a_agents.server_factory import run
from a2a_agents.orchestrator_agent.agent_card import public_agent_card
from a2a_agents.orchestrator_agent.agent_executor import AgentExecutor

if __name__ == '__main__':
    run(public_agent_card, AgentExecutor, port=8080)
