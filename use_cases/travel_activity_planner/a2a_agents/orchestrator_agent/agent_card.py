from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)


routing_skill = AgentSkill(
    id='routing',
    name='Agent Routing',
    description='Analyzes user requests and routes them to the appropriate agent (Weather & Activity Agent or Packing List Agent)',
    tags=['routing', 'orchestration', 'manager'],
    examples=[
        'Route weather questions to Weather Agent',
        'Route packing requests to Packing List Agent',
    ],
)

public_agent_card = AgentCard(
    name='Orchestrator Agent',
    description='A manager agent that receives user requests and decides which agent to activate. Routes requests to the Weather & Activity Agent or the Packing List Agent based on the user\'s needs.',
    url='http://localhost:8080/',
    supported_interfaces=[AgentInterface(url='http://localhost:8080/', transport='JSONRPC')],
    version='1.0.0',
    capabilities=AgentCapabilities(streaming=True),
    skills=[routing_skill],
    default_input_modes=['text'],
    default_output_modes=['text'],
)





