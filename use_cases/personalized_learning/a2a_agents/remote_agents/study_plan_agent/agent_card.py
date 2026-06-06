from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)

build_study_plan_skill = AgentSkill(
    id='build_study_plan',
    name='Build Personalized Study Plan Skill',
    description='Builds a personalized learning plan based on topic, detected level, available time, and optional career skill gaps. Integrates job descriptions and resume profiles for career-focused plans.',
    tags=['study', 'plan', 'career', 'gap', 'schedule', 'learning', 'path', 'resume', 'job'],
    examples=[
        'Build me a 2-hour study plan for MCP.',
        'Create a beginner study plan for A2A.',
        'Build a plan based on my current MCP level.',
        'Prepare a learning plan for candidate_1 for the AI Engineer role.',
        'I have 30 minutes. What should I study for RAG?',
        'Give me a 1-day plan for prompt engineering.',
    ],
)

public_agent_card = AgentCard(
    name='Study Plan Agent',
    description='An agent that builds personalized learning plans. It uses the user\'s current level, available time, and optional career goals (job description + resume skill gaps) to generate ordered study steps, objectives, and practice suggestions.',
    url='http://localhost:8093/',
    supported_interfaces=[AgentInterface(url='http://localhost:8093/', transport='JSONRPC')],
    version='1.0.0',
    capabilities=AgentCapabilities(streaming=True),
    skills=[build_study_plan_skill],
    default_input_modes=['text'],
    default_output_modes=['text'],
)
