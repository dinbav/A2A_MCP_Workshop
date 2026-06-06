# Multi-Turn Conversation Guide

This guide explains how conversation memory (multi-turn) works in the Personalized Learning use case and how to verify it end-to-end.

## How It Works

Every agent in this system supports multi-turn conversation:

1. **`base_executor.py`** reads `context.current_task.history` from the A2A SDK and passes it to `agent.stream(user_input, history=history)`.
2. **Each agent logic** iterates the `history` list, extracts plain text from each part, and concatenates it with the current user input to form `full_context`. Topic and intent are parsed from this combined context.
3. **The orchestrator** forwards `context_id` to each remote agent it calls, so the remote agent can also access the full history.
4. **The client** reuses the same `context_id` for every turn in a conversation.

This means: if you tell the system "I want to learn MCP" and then say "Assess me", the Assessment Agent knows the topic is MCP from the history.

## Running the Memory Test

```powershell
# Requires all services running (start_all.ps1)
python -m tests.test_memory
```

This runs a 4-turn conversation:

| Turn | User input | What the agent must know |
|------|-----------|--------------------------|
| 1 | "I want to learn MCP. I am a complete beginner." | Establishes: topic=MCP, level=beginner |
| 2 | "Assess me on MCP." | Assessment Agent reads state, gives quiz |
| 3 | "I got 3 out of 4 correct." | History → topic=MCP → updates level |
| 4 | "Build me a 2-hour study plan based on my current level." | Study Plan Agent uses updated MCP level |

## Step-by-Step: How to Verify Memory Is Working

### Step 1: Start all services

```powershell
.\start_all.ps1
```

### Step 2: Run the multi-turn test

```powershell
python -m tests.test_memory
```

Watch that:
- Turn 2 response mentions MCP questions (not a random topic).
- Turn 3 response mentions updating the MCP level.
- Turn 4 response builds a plan for MCP (not a default topic).

### Step 3: Run the interactive client

```powershell
python a2a_agents/client.py
```

Type the same 4-turn conversation manually. The `context_id` is printed at startup and reused for every turn.

## How context_id Flows Through the System

```
User Client
    │  context_id = "abc123"
    ▼
Orchestrator (port 8090)
    │  context.context_id = "abc123"
    │  history = [Turn 1, Turn 2, Turn 3]
    │
    ├──► Topic Explainer (8091)  ← context_id forwarded, sees full history
    ├──► Assessment Agent (8092) ← context_id forwarded, sees full history
    └──► Study Plan Agent (8093) ← context_id forwarded, sees full history
```

## How the History Forwarding Works in Code

### `base_executor.py`

```python
history = context.current_task.history if context.current_task else []
async for response in self.agent.stream(context.get_user_input(), history=history):
    ...
```

### Each `agent_logic.py`

```python
async def stream(self, user_input: str, history=None) -> AsyncGenerator:
    # Concatenate all prior message texts with the current input
    history_texts = []
    for msg in (history or []):
        for part in msg.parts:
            text = getattr(part, 'text', None) or ''
            if text:
                history_texts.append(text)
    full_context = ' '.join(history_texts + [user_input])

    # Parse topic/intent from the combined context
    topic = _parse_topic(full_context)
    # ... rule-based MCP calls using topic
```

### `orchestrator_agent/agent_logic.py`

```python
# context_id is forwarded to each remote agent:
msg.context_id = context_id
```

## What Breaks Without Memory

Without history forwarding:
- Turn 2 "Assess me" → Agent has no idea what topic to assess.
- Turn 3 "I got 3 out of 4 correct" → Agent cannot update any level.
- Turn 4 "Build me a plan" → Agent defaults to some random topic.

This is why memory is fundamental to the workshop use case.

## Workshop Exercise: Break and Fix Memory

1. Comment out the history loop in `topic_explainer_agent/agent_logic.py`.
2. Run the memory test — observe Turn 2 fails to reference MCP.
3. Restore the history loop.
4. Run the test again — observe it passes.

This exercise demonstrates exactly why history forwarding matters.
