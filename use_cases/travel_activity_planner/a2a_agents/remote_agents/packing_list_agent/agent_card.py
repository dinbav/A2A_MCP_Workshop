from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)

packing_skill = AgentSkill(
    id='packing_list',
    name='Packing List Creator',
    description='Create a comprehensive packing list based on activities, weather, number of people, and whether kids are included. Items are organized by categories (clothes, toiletries, gadgets, etc.) with a checklist format per person.',
    tags=['packing', 'list', 'travel', 'checklist', 'categories'],
    examples=['Create a packing list for a beach trip', 'What should I pack for a hiking trip with 4 people and 2 kids?'],
)

invitation_skill = AgentSkill(
    id='invitation',
    name='Invitation Creator',
    description='Create a custom invitation to share with friends based on the planned activities',
    tags=['invitation', 'share', 'friends', 'event'],
    examples=['Create an invitation for a beach weekend', 'Generate an invitation for our hiking trip'],
)

public_agent_card = AgentCard(
    name='Packing List Agent',
    description='An agent that creates packing lists based on weather forecasts and planned activities. It considers the number of travelers, whether kids are included, and organizes items by categories. It can also create custom invitations to share with friends.',
    url='http://localhost:8081/',
    supported_interfaces=[AgentInterface(url='http://localhost:8081/', transport='JSONRPC')],
    version='1.0.0',
    capabilities=AgentCapabilities(streaming=True),
    skills=[packing_skill, invitation_skill],
    default_input_modes=['text'],
    default_output_modes=['text'],
)





