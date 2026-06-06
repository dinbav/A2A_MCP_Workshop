from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)

explain_topic_skill = AgentSkill(
    id='explain_topic',
    name='Explain Topic Skill',
    description='Explains a learning topic (MCP, A2A, RAG, prompt engineering, Python async) at the requested level. Returns a structured explanation with key concepts, common misconceptions, and a next step suggestion.',
    tags=['explanation', 'topic', 'concepts', 'beginner', 'intermediate', 'advanced', 'learn', 'explain'],
    examples=[
        'Explain MCP for a beginner.',
        'Explain A2A for an intermediate developer.',
        'What are the key concepts in RAG?',
        'Give me an overview of prompt engineering at an advanced level.',
        'What is Python async programming?',
    ],
)

public_agent_card = AgentCard(
    name='Topic Explainer Agent',
    description='An agent that explains learning topics (MCP, A2A, RAG, prompt engineering, Python async) at the requested level. Provides structured explanations with key concepts, common misconceptions, and next step suggestions.',
    url='http://localhost:8091/',
    supported_interfaces=[AgentInterface(url='http://localhost:8091/', transport='JSONRPC')],
    version='1.0.0',
    capabilities=AgentCapabilities(streaming=True),
    skills=[explain_topic_skill],
    default_input_modes=['text'],
    default_output_modes=['text'],
)
