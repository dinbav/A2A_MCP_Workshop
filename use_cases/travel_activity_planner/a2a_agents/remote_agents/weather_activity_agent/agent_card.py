from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)


weather_skill = AgentSkill(
    id='weather',
    name='Weather Forecast',
    description='Get weather forecast for a specific location and date range',
    tags=['weather', 'forecast', 'temperature'],
    examples=['What is the weather like in New York this weekend?', 'Get weather forecast for San Francisco next week'],
)

activity_skill = AgentSkill(
    id='activities',
    name='Activity Suggestions',
    description='Suggest indoor or outdoor activities based on weather conditions',
    tags=['activities', 'outdoor', 'indoor', 'suggestions'],
    examples=['Suggest activities for 40°C weather', 'What outdoor activities can I do in sunny weather?'],
)

public_agent_card = AgentCard(
    name='Activity & Weather Agent',
    description='An agent that provides weather forecasts and suggests activities based on weather conditions. It can get weather data for any location and recommend suitable indoor or outdoor activities.',
    url='http://localhost:8082/',
    supported_interfaces=[AgentInterface(url='http://localhost:8082/', transport='JSONRPC')],
    version='1.0.0',
    capabilities=AgentCapabilities(streaming=True),
    skills=[weather_skill, activity_skill],
    default_input_modes=['text'],
    default_output_modes=['text'],
)
