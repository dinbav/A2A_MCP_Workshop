from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)

routing_skill = AgentSkill(
    id='routing',
    name='Agent Routing',
    description='Analyzes user requests and routes them to the appropriate learning agent: Topic Explainer Agent, Assessment Agent, or Study Plan Agent.',
    tags=['routing', 'orchestration', 'manager', 'learning', 'study', 'assessment', 'explain'],
    examples=[
        'Route explanation questions to Topic Explainer Agent',
        'Route quiz requests to Assessment Agent',
        'Route study plan requests to Study Plan Agent',
    ],
)

public_agent_card = AgentCard(
    name='Learning Orchestrator Agent',
    description='A manager agent that receives user learning requests and routes them to the appropriate specialist agent: Topic Explainer, Assessment, or Study Plan. Supports multi-turn conversations and career-focused learning flows.',
    url='http://localhost:8090/',
    supported_interfaces=[AgentInterface(url='http://localhost:8090/', transport='JSONRPC')],
    version='1.0.0',
    capabilities=AgentCapabilities(streaming=True),
    skills=[routing_skill],
    default_input_modes=['text'],
    default_output_modes=['text'],
)
