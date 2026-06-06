from a2a_agents.base_executor import BaseAgentExecutor
from .agent_logic import AgentLogic


class AgentExecutor(BaseAgentExecutor):
    def _make_logic(self):
        return AgentLogic()
