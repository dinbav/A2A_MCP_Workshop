# When Agents Talk: Three Patterns for Agent Intelligence

## A Deep Dive into When to Use LLM-Only, LLM + Tool Loop, or MCP Direct — with Real Code from a Multi-Agent Travel Planner

*From the **When Agents Talk** workshop · Part 3 of 5*

---

> *"By Author using DALL-E"*
> *(Hero image: three distinct AI robots each solving a problem in a different way — one thinking (LLM), one using tools (wrench), one looking up a book (direct lookup) — flat illustration, pastel colors, side by side)*

---

You're planning a trip to Paris in December.

You ask one assistant. Behind the scenes, three different agents spring into action.

One **looks up local tips** without touching an AI model at all. It parses your message, queries a data file, and returns a formatted result. Fast. Free. Deterministic.

One **generates a packing list** using an LLM. It doesn't need any external data — it reasons from its training, guided by a system prompt. Creative. Flexible. Costs tokens.

One **checks the weather and suggests activities** by calling a live weather API, then letting an LLM reason over the results. It uses real data. It uses AI to combine and explain. The most powerful of the three — and the most expensive.

Three agents. Three completely different approaches. Same user request.

This is Part 3 of the **When Agents Talk** series. In [Part 2](post2_no_llm.md), we built a full multi-agent system with zero LLM calls. That established the foundation. Now we add the LLM — and show exactly where it earns its place.

*[Part 4](post4_production.md) covers taking this to production. [Part 5](post5_migration.md) covers upgrading the SDK.*

· What We're Building · The MCP Server — Now with Live Data · Pattern 1: LLM Only · Pattern 2: LLM + Agentic Tool Loop · Pattern 3: MCP Direct · Which Pattern Should You Use? · Multi-Turn Memory · The Orchestrator · Testing Strategy · Sources and Further Reading

---

## What We're Building

The **Travel Activity Planner**. A complete multi-agent system where a single request — "I'm traveling to Paris in December" — can trigger multiple specialized agents in parallel.

<!-- DIAGRAM D3.1: post3_architecture.excalidraw — Travel Planner architecture with external APIs -->

![Travel Planner Architecture — see post3_architecture.excalidraw](diagrams/post3_architecture.png)

| Component | Port | Pattern | LLM? | MCP? |
|-----------|------|---------|------|------|
| **MCP Server** | 8003 | — | No | — |
| **Packing List Agent** | 8081 | Pattern 1: LLM Only | ✅ Yes | ❌ No |
| **Weather & Activity Agent** | 8082 | Pattern 2: LLM + Tool Loop | ✅ Yes | ✅ Yes |
| **Local Tips Agent** | 8083 | Pattern 3: MCP Direct | ❌ No | ✅ Yes |
| **Orchestrator** | 8080 | Keyword routing | ❌ No | ❌ No |

Note what's different from [Part 2](post2_no_llm.md): the MCP server here calls **live external APIs** — real weather data from Open-Meteo, real geocoding from Nominatim. And two of the three agents use an LLM.

The five-file agent structure is identical to Part 2. The `agent_executor.py`, `server_factory.py`, `__main__.py` — all the same. We won't repeat them. Only `agent_logic.py` changes. That's the whole point.

---

## The MCP Server: Now with Live External Data

The travel MCP server follows the same `@mcp.tool()` pattern from Part 2. What's new: the tools call **real external APIs**.

```python
# use_cases/travel_activity_planner/mcp/fastmcp_server.py  (lines 46–68)

@mcp.tool(tags={"weather"})
def get_weather_for_location_and_date_string(
        location_str: str,
        date_str: str = "today",
) -> dict:
    """
    Get weather for a location using a natural-language date string.

    Args:
        location_str: e.g. "Tel Aviv, Israel" or "Paris"
        date_str: e.g. "today", "this week", "6-9 december"
    """
    date_range = parse_date_range(date_str)         # custom date parser
    start = datetime.strptime(date_range["start_date"], "%d-%m-%Y").strftime("%Y-%m-%d")
    end   = datetime.strptime(date_range["end_date"],   "%d-%m-%Y").strftime("%Y-%m-%d")

    result = get_weather_by_location(location_str, start, end)   # Open-Meteo API
    min_t, max_t = get_temperature_range(result["weather"])
    result["temperature_range"] = {"min_celsius": min_t, "max_celsius": max_t}
    return result
```

Under the hood, `get_weather_by_location` calls the **Open-Meteo API** (free, no key required), and `parse_date_range` handles natural-language dates like "this week" or "6-9 december". These are in `mcp/mcp_utils.py`.

The decorator `@mcp.tool(tags={"weather"})` is identical to Part 2. The business logic inside the function is what changed — from a JSON lookup to a real API call. The MCP pattern is the same.

---

## The Three Patterns

Before we dive in, here is the key visual: what's actually happening inside each agent's `agent_logic.py`.

<!-- DIAGRAM D3.2: post3_patterns_comparison.excalidraw — 3 columns: what's inside each agent_logic.py -->

![Three Patterns Comparison — see post3_patterns_comparison.excalidraw](diagrams/post3_patterns_comparison.png)

---

## Pattern 1 — LLM Only: Packing List Agent (:8081)

**When to use it:** The task is creative or generative. You don't need live data. You need language understanding and natural output.

**Trade-off:** Non-deterministic (different runs = different outputs). Costs tokens. Fast for the user, because there's no data lookup delay.

```python
# use_cases/travel_activity_planner/a2a_agents/remote_agents/packing_list_agent/agent_logic.py

SYSTEM_PROMPT = """You are a packing list and trip invitation specialist.

Skills:
- Create categorised packing lists (clothes, toiletries, gadgets, gear, food)
- Write engaging group-trip invitations
- Adapt recommendations to weather, activities, duration, group size, and children

Packing list format:
- Use these exact category headers: 👕 Clothes, 🧴 Toiletries, 📱 Gadgets & Electronics,
  🎒 Gear & Equipment, 🍽️ Food & Snacks
- Use [ ] checkboxes for each item"""


async def stream(self, user_input: str, history=None) -> AsyncGenerator:
    # Build message list: system prompt + conversation history + new message
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in (history or []):
        for part in msg.parts:
            if hasattr(part, 'text') and part.text:
                role = HumanMessage if msg.role == Role.ROLE_USER else AIMessage
                messages.append(role(content=part.text))
    messages.append(HumanMessage(content=user_input))

    # Single LLM call — no tools, no loop
    response = await self.llm.ainvoke(messages)
    yield {
        "completed": True,
        "failed": False,
        "input_required": False,
        "content": response.content,
    }
```

What's happening:

1. **System prompt** — defines personality and output format
2. **History** — previous turns are prepended, so the LLM has context for follow-ups ("make the list shorter" on a second message works correctly)
3. **Single `ainvoke`** — one LLM call, one response
4. **One `yield`** — the response is complete

No MCP calls. No tool definitions. No loop. Just a prompt, history, and one model call.

---

## Pattern 2 — LLM + Agentic Tool Loop: Weather & Activity Agent (:8082)

**When to use it:** The task needs live or external data, AND the LLM needs to reason about that data before responding. Not just look it up — *combine and explain* it.

**Trade-off:** Most powerful. Most expensive (multiple LLM calls per request). Least predictable (the LLM decides which tools to call and in what order).

<!-- DIAGRAM D3.3: post3_tool_loop.excalidraw — The agentic loop: LLM → tool_calls? → MCP → back to LLM (max 5) -->

![LLM Tool Loop — see post3_tool_loop.excalidraw](diagrams/post3_tool_loop.png)

```python
# use_cases/travel_activity_planner/a2a_agents/remote_agents/weather_activity_agent/agent_logic.py

async def stream(self, user_input: str, history=None) -> AsyncGenerator:
    # Step 1: fetch only the tools this agent needs (tagged "weather" or "activities")
    tool_definitions = await self._get_mcp_tools_by_tags({"weather", "activities"})
    llm_with_tools = self.llm.bind_tools(tool_definitions)

    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    # ... (history injection, same as Pattern 1) ...
    messages.append(HumanMessage(content=user_input))

    # Step 2: agentic loop — up to 5 iterations
    for _ in range(5):
        response = await llm_with_tools.ainvoke(messages)
        tool_calls = response.tool_calls if hasattr(response, 'tool_calls') else []

        if not tool_calls:
            # LLM decided it has enough information — done
            yield {"completed": True, ..., "content": response.content}
            return

        messages.append(response)  # keep the LLM's decision in context

        # Step 3: execute each tool call against the MCP server
        for call in tool_calls:
            async with self.mcp_client:
                result = await self.mcp_client.call_tool(call["name"], call["args"])
                result_text = result.content[0].text

            yield {"completed": False, ..., "content": f"\n[Tool] {call['name']}\n"}

            # Step 4: add tool result back into the message chain
            messages.append(ToolMessage(tool_call_id=call["id"], content=result_text))

    # Safety net: 5 iterations reached
    yield {"completed": True, ..., "content": "Reached maximum reasoning steps."}
```

The loop step by step:

1. **Tag-filtered tool discovery** — `_get_mcp_tools_by_tags({"weather", "activities"})` fetches only the relevant tools from the MCP server. The agent never sees the career tools, the assessment tools, etc.
2. **`llm.bind_tools()`** — LangChain attaches the tool definitions to the model, so it knows what's available and can decide to call them.
3. **LLM decides** — on each iteration, the model either returns tool_calls or a final answer.
4. **MCP call** — for each tool_call, the agent calls the MCP server directly.
5. **`ToolMessage` injected** — the tool's result goes back into the message chain, so the LLM has it for the next iteration.
6. **Repeat** — the LLM sees the tool results and either calls more tools or generates the final answer.

The 5-iteration cap is a production guardrail. In practice, weather + activities typically resolves in 2 iterations.

---

## Pattern 3 — MCP Direct: Local Tips Agent (:8083)

You've already seen this pattern in [Part 2](post2_no_llm.md). This is the same approach — parse input, call MCP tool, format result. No LLM.

```python
# use_cases/travel_activity_planner/a2a_agents/remote_agents/local_tips_agent/agent_logic.py

async def stream(self, user_input: str, history=None) -> AsyncGenerator:
    city, trip_type = self._parse_input(user_input)  # keyword matching

    async with Client(self.mcp_url) as client:
        result = await client.call_tool(
            "get_local_tips_by_city",
            {"city": city, "trip_type": trip_type},
        )

    data = json.loads(result.content[0].text)
    formatted = self._format_tips(data)
    yield {"completed": True, ..., "content": formatted}
```

**When to use it:** The task has a known structure. "Give me local tips for Paris" always maps to the same tool call with the same parameter structure. No reasoning needed. No ambiguity.

**Trade-off:** Zero cost. Milliseconds. Fully testable without any model.

---

## Which Pattern Should You Use?

<!-- DIAGRAM D3.4: post3_decision_flowchart.excalidraw — Decision tree: which pattern fits your task? -->

![Pattern Decision Guide — see post3_decision_flowchart.excalidraw](diagrams/post3_decision_flowchart.png)

| Ask yourself | Answer | Pattern |
|---|---|---|
| Is the output always the same for the same input? | Yes | **Pattern 3 — MCP Direct** |
| Does it need live/external data AND creative synthesis? | Yes | **Pattern 2 — LLM + Tool Loop** |
| Is it creative or generative, with no external data needed? | Yes | **Pattern 1 — LLM Only** |

A simpler rule: **start with Pattern 3**. If deterministic lookup can answer the question — use it. Only reach for an LLM when the task genuinely needs language reasoning.

---

## Multi-Turn Memory: One Addition, Works for All LLM Agents

**Multi-turn memory** means the agent remembers what was said earlier in the conversation. "Make the list shorter" on a follow-up message works because the LLM sees the original exchange.

This is handled automatically by the base executor — you've already seen it:

```python
# use_cases/travel_activity_planner/a2a_agents/base_executor.py  (line 29)

history = context.current_task.history if context.current_task else []
async for response in self.agent.stream(context.get_user_input(), history=history):
    ...
```

The **Task Store** (managed by the A2A SDK) stores the full history keyed by **Context ID**. The base executor retrieves it and passes it to `stream()`. Each LLM agent prepends it to the message list.

No per-agent changes are needed. Pattern 1 and Pattern 2 agents both receive `history` and use it. Pattern 3 agents receive it too — they can use it for context extraction across turns.

---

## The Orchestrator: Same Pattern, Different Registry

The travel orchestrator works exactly like the learning orchestrator from [Part 2](post2_no_llm.md) — keyword scoring against live agent cards, 50% threshold, multi-agent fan-out.

Only the registry is different:

```json
// use_cases/travel_activity_planner/a2a_agents/orchestrator_agent/agents_registry.json
{
  "agents": [
    { "name": "Packing List Agent",       "url": "http://localhost:8081" },
    { "name": "Activity & Weather Agent", "url": "http://localhost:8082" },
    { "name": "Local Tips Agent",         "url": "http://localhost:8083" }
  ]
}
```

The orchestrator logic file (`agent_logic.py`) is not modified. You point it at a new registry, and it automatically discovers the new agents' cards, builds a new keyword index, and routes correctly.

This is the proof that the architecture generalizes. Two completely different domains — learning and travel — running on the same orchestrator code.

---

## Testing Strategy

The three patterns have different testing costs:

| Pattern | How to test | LLM needed? | Speed |
|---------|------------|-------------|-------|
| Pattern 3 — MCP Direct | Call the MCP tool directly, check JSON output | No | Fast (< 1s) |
| Pattern 1 — LLM Only | Full agent conversation test | Yes | Slow (LLM latency) |
| Pattern 2 — LLM + Tool Loop | Split: MCP tools tested separately, LLM behavior tested together | Partial | Mixed |

```bash
# Test MCP tools only — fast, no LLM
python tests/run_all_tests.py --only mcp

# Test all including LLM agents — requires AZURE_OPENAI_* env vars
python tests/run_all_tests.py

# Skip agent conversation tests
python tests/run_all_tests.py --skip-agents
```

The MCP test suite is your regression suite. Run it on every code change. It tests all 8 tools without touching the LLM — fast, free, and deterministic.

---

## Summary

We've now seen all three agent patterns with real, working code:

- **Pattern 1 — LLM Only**: system prompt + single `llm.ainvoke()`. Use for creative, generative tasks with no external data.
- **Pattern 2 — LLM + Agentic Tool Loop**: tag-filtered MCP discovery + `llm.bind_tools()` + up-to-5 iteration loop. Use when you need live data AND LLM reasoning over it.
- **Pattern 3 — MCP Direct**: parse → `client.call_tool()` → format. Use for deterministic lookups. No LLM. No cost. Already seen in Part 2.

The key takeaway: **the framework never changed**. `server_factory.py`, `base_executor.py`, `agent_executor.py`, `__main__.py` — all identical across all 6 agents in both use cases. Only `agent_logic.py` and the MCP tools changed.

This is post 3 of 5.

[Part 4](post4_production.md) covers what happens when you deploy this to real users — guardrails, observability, cost control, scaling, and human-in-the-loop design.

[Part 5](post5_migration.md) covers upgrading from `a2a-sdk==0.3.22` (what this workshop uses) to `1.x` — with before/after code for every breaking change.

The repo with all the working code is linked in Sources below.

---

If this post helped you, please clap 👏 (you can clap up to 50 times!) — it's the main way Medium surfaces articles to new readers. The more people see this, the more developers can build without the gatekeeping. Thank you for helping spread it.

---

## Sources and Further Reading

**Workshop Repository:**
- [When Agents Talk — Workshop Code](https://github.com/dinabavli/a2a_mcp_workshop) *(link to repo)*

**LangChain — LLM + Tool Integration:**
- [LangChain Tool Calling Guide](https://python.langchain.com/docs/how_to/tool_calling/)
- [AzureChatOpenAI docs](https://python.langchain.com/docs/integrations/chat/azure_chat_openai/)

**Open-Meteo (free weather API):**
- [Open-Meteo API](https://open-meteo.com/)

**FastMCP:**
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)

**Related Posts in This Series:**
- **Part 1**: [The Language of Multi-Agent AI](post1_terminology.md)
- **Part 2**: [Your First Multi-Agent System — No LLM Tokens Required](post2_no_llm.md)
- **Part 4**: [When Agents Talk in Production](post4_production.md)
- **Part 5**: [Migrating a2a-sdk 0.3 to 1.0](post5_migration.md)

---

*Written by Dina Bavli · Data Scientist | NLP | AI Systems · ❤ sharing knowledge and contributing to the community*
