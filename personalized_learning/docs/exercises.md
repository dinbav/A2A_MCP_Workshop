# Workshop Exercises

This document contains guided exercises for the Personalized Learning workshop. Participants complete them after the full solution has been presented.

## Prerequisites

- All services running (`.\start_all.ps1`)
- Passing MCP tests: `python tests/run_all_tests.py --skip-agents`
- Familiarity with the travel use case architecture

---

## Exercise 1: Explore the MCP Server

**Goal:** Get comfortable calling MCP tools directly.

### 1a. Use the MCP Playground

Start the Streamlit UI:
```powershell
.\start_all.ps1 -UI
```
Open http://localhost:8504 and:
1. Call `get_topic_summary` for `mcp` at `beginner` level.
2. Call `get_topic_summary` for `a2a` at `intermediate` level.
3. Call `get_assessment_questions_by_topic` for `rag` at `beginner`, limit=4.
4. Call `get_skill_gap_analysis` for `candidate_1` and `ai_engineer`.

### 1b. Call tools from Python

```python
import asyncio, json
from fastmcp import Client

async def main():
    async with Client("http://127.0.0.1:8004/mcp") as client:
        r = await client.call_tool("get_topic_summary", {"topic": "mcp", "level": "beginner"})
        print(json.loads(r.content[0].text))

asyncio.run(main())
```

### 1c. Observe the data_source field

Every tool response includes `"data_source": "local_json"`. This confirms no external APIs are used.

**Question:** What happens if you call `get_topic_summary` with `topic="blockchain"`? Why?

---

## Exercise 2: Understand the Agent Cards

**Goal:** See how agent skills drive orchestrator routing.

### 2a. Fetch an Agent Card

```python
import asyncio, httpx

async def main():
    async with httpx.AsyncClient() as http:
        r = await http.get("http://localhost:8091/.well-known/agent-card.json")
        print(r.json())

asyncio.run(main())
```

Fetch cards for all 3 agents (ports 8091, 8092, 8093).

**Question:** What tags does the Assessment Agent advertise? How do these affect routing?

### 2b. Trace a routing decision

Send this message to the orchestrator via the interactive client:
```
python a2a_agents/client.py
> Quiz me on A2A.
```

The response will start with `Running agents: ...` — note which agent was selected.

Now try: `Explain A2A for a beginner.` — different agent?

**Question:** Why does "quiz" route to Assessment but "explain" routes to Topic Explainer?

---

## Exercise 3: Multi-Turn Conversation

**Goal:** Verify conversation memory works across turns.

Run the memory test:
```powershell
python -m tests.test_memory
```

Then run the interactive client and repeat the 4-turn scenario manually:
```
python a2a_agents/client.py
> I want to learn MCP. I am a complete beginner.
> Assess me on MCP.
> I got 3 out of 4 correct.
> Build me a 2-hour study plan based on my current level.
```

**Question:** What happens if you start a new session (new `context_id`) for Turn 3? Does the agent still know the topic?

### 3b. Break and fix memory (optional)

1. Open `a2a_agents/remote_agents/topic_explainer_agent/agent_logic.py`.
2. Comment out the history loop in the `stream()` method.
3. Restart the Topic Explainer Agent.
4. Run the memory test. Observe Turn 2 fails.
5. Restore the history loop and restart.

---

## Exercise 4: Career Learning Flow

**Goal:** Understand how the Study Plan Agent uses multiple MCP tools.

Send this to the orchestrator:
```
Prepare a learning plan for candidate_1 for the AI Engineer role.
```

Observe the verbose output — the agent should call:
1. `get_skill_gap_analysis(job_id="ai_engineer", candidate_id="candidate_1")`
2. `get_study_path(...)` for one or more missing skills

**Question:** What topics are recommended for `candidate_1`? Why?

Try `candidate_2` for `data_scientist`. Are the recommendations different?

---

## Exercise 5: Add a New Topic

**Goal:** Add a new learning topic end-to-end.

Adding a topic requires changes in **two places**: the JSON data files and the Python parsing constants.

### Step A — Add data files

1. Open `mcp/data/learning/topics.json` and add `"langchain"` with `beginner`, `intermediate`, `advanced` entries.
2. Open `mcp/data/learning/assessment_questions.json` and add 4 questions per level.
3. Open `mcp/data/learning/study_paths.json` and add study paths for all 3 levels × 3 time slots.

### Step B — Register the topic in each agent

Each remote agent has a hardcoded `KNOWN_TOPICS` list and `TOPIC_ALIASES` dict that controls whether the agent recognises a topic from user input. Add `"langchain"` to both in:

- `a2a_agents/remote_agents/topic_explainer_agent/agent_logic.py`
- `a2a_agents/remote_agents/assessment_agent/agent_logic.py`
- `a2a_agents/remote_agents/study_plan_agent/agent_logic.py`

### Step C — Restart all services and test

```
python a2a_agents/client.py
> Explain LangChain for a beginner.
```

**Question:** What happens if you skip Step B? Which part of the flow breaks first?

---

## Exercise 6: Observe the Level-Up Logic

**Goal:** Verify the 85% threshold logic in `update_learning_state`.

Run the MCP test directly:
```python
import asyncio, json
from fastmcp import Client

async def test_level_up():
    async with Client("http://127.0.0.1:8004/mcp") as c:
        # Perfect score — should advance
        r = await c.call_tool("update_learning_state",
            {"user_id": "exercise_user", "topic": "mcp", "correct_count": 4, "total_count": 4})
        print("4/4:", json.loads(r.content[0].text))

        # Low score — should stay
        r = await c.call_tool("update_learning_state",
            {"user_id": "exercise_user2", "topic": "mcp", "correct_count": 3, "total_count": 4})
        print("3/4:", json.loads(r.content[0].text))

asyncio.run(test_level_up())
```

**Question:** What is the `new_level` for 4/4? For 3/4? The level-up threshold is 75% — what score is the minimum to advance?

---

## Exercise 7: Run the Full Test Suite

```powershell
python tests/run_all_tests.py --verbose
```

Review every failing test. Fix the issue or explain why it would fail (e.g., LLM API not configured).

**Bonus:** Add one new MCP test to `tests/test_mcp.py` for a case not already covered.
