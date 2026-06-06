from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)

assess_level_skill = AgentSkill(
    id='assess_level',
    name='Assess Topic Level Skill',
    description='Generates assessment questions for a topic, evaluates quiz answers, and updates the user learning level. Supports follow-up answers within the same conversation.',
    tags=['assessment', 'quiz', 'level', 'score', 'questions', 'evaluate', 'test'],
    examples=[
        'Give me a short quiz for MCP.',
        'Assess my level in A2A.',
        'I got 3 out of 4 correct.',
        'What is my current MCP level?',
        'Test my knowledge of RAG.',
        'Quiz me on prompt engineering at intermediate level.',
    ],
)

public_agent_card = AgentCard(
    name='Assessment Agent',
    description='An agent that assesses user knowledge on topics like MCP, A2A, RAG, prompt engineering, and Python async. It generates quiz questions, evaluates results, and updates the user level (beginner → intermediate → advanced).',
    url='http://localhost:8092/',
    supported_interfaces=[AgentInterface(url='http://localhost:8092/', transport='JSONRPC')],
    version='1.0.0',
    capabilities=AgentCapabilities(streaming=True),
    skills=[assess_level_skill],
    default_input_modes=['text'],
    default_output_modes=['text'],
)
