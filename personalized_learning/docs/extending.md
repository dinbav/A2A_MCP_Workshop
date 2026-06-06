# Extending the Use Case

## Adding a New Learning Topic

Adding a topic requires changes in **two places**: the JSON data files (MCP server) and the Python parsing constants (agent logic files).

### Step 1: Add the topic summary

Edit `mcp/data/learning/topics.json`:

```json
{
  "your_new_topic": {
    "beginner": {
      "summary": "...",
      "key_concepts": ["...", "..."],
      "common_misconceptions": ["...", "..."],
      "next_step": "..."
    },
    "intermediate": { ... },
    "advanced": { ... }
  }
}
```

### Step 2: Add assessment questions

Edit `mcp/data/learning/assessment_questions.json`:

```json
{
  "your_new_topic": {
    "beginner": [
      {
        "id": "nt_b_1",
        "question": "...",
        "expected_answer": "...",
        "explanation": "...",
        "level": "beginner",
        "score_weight": 1.0
      }
    ],
    "intermediate": [ ... ],
    "advanced": [ ... ]
  }
}
```

### Step 3: Add study paths

Edit `mcp/data/learning/study_paths.json`. Add your topic with all 3 levels × 3 time slots.

### Step 4: Update the skill map (optional)

If your topic maps to job skills, edit `mcp/data/career/skill_map.json`:

```json
{
  "your_skill": {
    "learning_topic": "your_new_topic",
    "description": "...",
    "related_skills": []
  }
}
```

### Step 5: Register the topic in each agent

Each remote agent has a hardcoded `KNOWN_TOPICS` list and `TOPIC_ALIASES` dict used to parse the topic from user input. Add your new topic to both in each of these files:

- `a2a_agents/remote_agents/topic_explainer_agent/agent_logic.py`
- `a2a_agents/remote_agents/assessment_agent/agent_logic.py`
- `a2a_agents/remote_agents/study_plan_agent/agent_logic.py`

### Step 6: Restart all services

```powershell
.\start_all.ps1 -Stop
.\start_all.ps1
```

The MCP server reloads all JSON on startup. The agents pick up the updated `KNOWN_TOPICS` on restart.

---

## Adding a New Agent

To add a 4th specialist agent:

1. Create `a2a_agents/remote_agents/your_agent/` with the standard 5 files.
2. Choose a port (e.g., 8094).
3. Add to `a2a_agents/orchestrator_agent/agents_registry.json`.
4. Add to `start_all.ps1`.
5. Add tests to `tests/test_agents.py`.

---

## Adding a New MCP Tool

1. Add the data file to `mcp/data/`.
2. Add the tool function to `mcp/fastmcp_server.py` with `@mcp.tool(tags={...})`.
3. Add tests to `tests/test_mcp.py`.
4. Update the tool list in `README.md`.

---

## Adding a New Job or Candidate

Edit `mcp/data/career/job_descriptions.json` or `mcp/data/career/sample_resumes.json`. The skill gap analysis will automatically include the new entries.

---

## Workshop-Starter Branch Strategy

The full solution is structured so that a future `workshop-starter` branch can be created by replacing selected components with TODO stubs for participants to implement.

### What participants would implement in workshop-starter

#### 1. `get_study_path` tool body (`mcp/fastmcp_server.py`)

Replace the implementation with:
```python
@mcp.tool(tags={"study", "plan"})
def get_study_path(topic: str, level: str = "beginner", available_time: str = "2_hours") -> dict:
    """..."""
    # TODO: Implement this tool.
    # 1. Validate topic (use VALID_TOPICS), level (use VALID_LEVELS), available_time (use VALID_TIMES).
    # 2. Look up STUDY_PATHS[topic_key][level_key][time_key].
    # 3. Return a dict with: topic, level, available_time, learning_objectives,
    #    ordered_steps, practice_suggestions, estimated_total_time, data_source.
    raise NotImplementedError("TODO: implement get_study_path")
```

#### 2. `study_plan_agent/agent_logic.py`

Replace with a stub showing the tag filter to use and the expected behavior.

#### 3. `agents_registry.json`

Remove the Study Plan Agent entry.

#### 4. Orchestrator agent card

Remove `study`, `plan`, `career`, `gap` from routing skill tags.

### How to create the workshop-starter branch

```bash
git checkout -b workshop-starter
# Edit the 4 files above
git add .
git commit -m "workshop-starter: remove Study Plan Agent for participant implementation"
git push origin workshop-starter
```

### What participants submit

After completing the workshop, participants submit a PR from `workshop-starter` back to `main` (or a personal fork) with their implementation of the Study Plan Agent.

---

## Persistent Learning State

The current implementation uses an in-memory dict seeded from `user_learning_state.json`. State resets on server restart.

To add persistence:
1. Replace `_LEARNING_STATE` dict with reads/writes to a SQLite or Redis store.
2. The tool interface stays the same — only the storage backend changes.
3. This is a natural extension exercise for advanced participants.
