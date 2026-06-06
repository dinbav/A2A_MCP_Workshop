# Post 3 Assets Guide — Three Patterns for Agent Intelligence

## Diagrams to Include

### D3.1 — Travel Planner Architecture
- **File:** `../diagrams/post3_architecture.excalidraw`
- **Placement:** After "What We're Building" section, before the component table
- **Caption:** *Three agents, three patterns — same framework, completely different intelligence strategies.*
- **What it shows:** Full system with LLM box, MCP server, 3 agents, color-coded by pattern; also shows external APIs

### D3.2 — Three Patterns Comparison
- **File:** `../diagrams/post3_patterns_comparison.excalidraw`
- **Placement:** Just before the "The Three Patterns" section begins (as a visual summary before the deep dives)
- **Caption:** *Inside each agent's agent_logic.py — three completely different approaches to the same framework.*
- **What it shows:** Side-by-side 3-column view of what each pattern's stream() method does

### D3.3 — LLM Tool Loop
- **File:** `../diagrams/post3_tool_loop.excalidraw`
- **Placement:** At the start of "Pattern 2 — LLM + Agentic Tool Loop" section
- **Caption:** *The agentic loop: the LLM decides what to call, calls the MCP tool, then decides again — up to 5 times.*
- **What it shows:** Flowchart of the Pattern 2 loop with decision diamond and MCP call step

### D3.4 — Pattern Decision Flowchart
- **File:** `../diagrams/post3_decision_flowchart.excalidraw`
- **Placement:** At the start of "Which Pattern Should You Use?" section
- **Caption:** *Start with Pattern 3. Upgrade only when the task genuinely demands it.*
- **What it shows:** Decision tree guiding the reader to the right pattern

---

## Hero Image

### Option A — Freepik Search Terms

Search on [freepik.com](https://freepik.com):

- `"three robots different methods problem solving flat"`
- `"AI agents tools brain comparison flat illustration"`
- `"machine learning approaches comparison infographic"`
- `"robot with book robot with tools robot thinking flat"`
- `"software design patterns comparison flat illustration"`

**Style to select:** Three distinct characters/robots side by side, each using a different method (thinking, using tools, looking up a book/database). Flat illustration, pastel colors.

### Option B — DALL-E / Midjourney Generation Prompt

```
Flat digital illustration of three friendly robots standing side by side, each solving a problem differently. Left robot: surrounded by thought bubbles and text (labeled "LLM Only"). Center robot: using a wrench to plug into a wall socket with data flowing in (labeled "LLM + Tools"). Right robot: reading a structured data book (labeled "MCP Direct"). Pastel color palette: lavender, peach, mint green. White background. Clean, modern, no photorealism.
```

**Aspect ratio:** 16:9

---

## Tags for Medium

`#LLM` `#MultiAgent` `#A2A` `#MCP` `#AIEngineering` `#Python` `#PromptEngineering` `#AgentDesign` `#AzureOpenAI` `#OpenSource`

## Subtitle for Medium

> A Deep Dive into When to Use LLM-Only, LLM + Tool Loop, or MCP Direct — with Real Code from a Multi-Agent Travel Planner

## Series Header

> *This is Part 3 of the **When Agents Talk** series. [Part 1](../post1_terminology.md) = vocabulary. [Part 2](../post2_no_llm.md) = first system with no LLM. This post = three patterns, LLM added where it counts.*

---

## Estimated Read Time
**14–18 minutes** (code-heavy with 4 major code blocks, plus 4 diagrams)
