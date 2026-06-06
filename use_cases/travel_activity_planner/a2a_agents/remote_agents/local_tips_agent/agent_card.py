from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)

local_tips_skill = AgentSkill(
    id='local_tips',
    name='Local Tips',
    description='Get local travel tips for transportation, food, safety, and recommended hours by city and trip type',
    tags=['local', 'tips', 'city guide', 'travel tips', 'local tips'],
    examples=[
        'Local tips for Tel Aviv family trip',
        'City guide for Paris cultural visit',
        'What are the local tips for Barcelona beach trip?',
    ],
)

public_agent_card = AgentCard(
    name='Local Tips Agent',
    description='An agent that provides local travel tips for cities. Given a city and trip type, it returns practical advice on transportation, food, safety, recommended hours, and local highlights.',
    url='http://localhost:8083/',
    supported_interfaces=[AgentInterface(url='http://localhost:8083/', transport='JSONRPC')],
    version='1.0.0',
    capabilities=AgentCapabilities(streaming=True),
    skills=[local_tips_skill],
    default_input_modes=['text'],
    default_output_modes=['text'],
)
