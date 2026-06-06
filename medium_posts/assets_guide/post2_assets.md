# Post 2 Assets Guide — Your First Multi-Agent System, No LLM Tokens Required

## Diagrams to Include

### D2.1 — Full System Architecture
- **File:** `../diagrams/post2_architecture.excalidraw`
- **Placement:** After "What We're Building" intro, before the component table
- **Caption:** *Personalized Learning: 4 agents + 1 MCP server, all on distinct ports, no LLM.*
- **What it shows:** Port numbers for all 5 components, arrows showing A2A vs MCP flows

### D2.2 — Agent Anatomy (5 Files)
- **File:** `../diagrams/post2_agent_anatomy.excalidraw`
- **Placement:** At the start of "The Agent Anatomy: Five Files, One Blueprint" section
- **Caption:** *Green = identical across every agent. Orange = same structure, different content. Red = the only file that truly changes.*
- **What it shows:** Stack of 5 files, color-coded by how much they differ

### D2.3 — End-to-End Request Flow
- **File:** `../diagrams/post2_request_flow.excalidraw`
- **Placement:** At the start of "The Orchestrator: Routing Without AI" section
- **Caption:** *"explain mcp" from message to formatted response — no LLM was called at any point.*
- **What it shows:** 7-step numbered flow from user input to returned answer, with clear color-coding for A2A vs MCP calls

---

## Hero Image

### Option A — Freepik Search Terms

Search on [freepik.com](https://freepik.com):

- `"construction workers building pipeline AI flat"`
- `"robot assembly line teamwork flat illustration"`
- `"AI agents collaboration no brain flat design"`
- `"software architecture workflow flat icons pastel"`
- `"modular system building blocks flat illustration"`

**Style to select:** Flat illustration. No brain icon, no lightbulb, no "AI magic" imagery — the point is engineering, structure, teamwork without AI. Pastel, white background preferred.

### Option B — DALL-E / Midjourney Generation Prompt

```
Flat digital illustration of four small construction-worker robots building a data pipeline together. One robot lays cable (labeled "MCP"), one routes traffic at a junction (labeled "Orchestrator"), and two others carry data packages (labeled "Agent"). No brain symbols, no AI lightning bolts — emphasize physical teamwork and structure. Pastel color palette: warm orange, mint green, soft blue. White background. Clean, professional, friendly, no photorealism.
```

**Aspect ratio:** 16:9

---

## Tags for Medium

`#Python` `#MultiAgent` `#A2A` `#MCP` `#AIEngineering` `#OpenSource` `#AgentDesign` `#SoftwareArchitecture` `#NoLLM` `#FastMCP`

## Subtitle for Medium

> A Detailed Exploration of Building a Complete Orchestrator, 3 Agents, and an MCP Tool Server — Without a Single AI API Call

## Series Header

> *This is Part 2 of the **When Agents Talk** series. [Part 1](../post1_terminology.md) covers the vocabulary. This post builds the first complete system.*

---

## Estimated Read Time
**12–15 minutes** (code-heavy, readers will pause to study snippets)
