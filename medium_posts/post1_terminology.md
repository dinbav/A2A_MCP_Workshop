# When Agents Talk: The Language of Multi-Agent AI

## A Practical Guide to the Terms Every Developer Needs Before Building with A2A and MCP

*From the **When Agents Talk** workshop · Part 1 of 5*

---

> *"By Author using DALL-E"*
> *(Hero image: minimalist flat illustration of small robots holding name tags and speech bubbles, each labeled with a different role — orchestrator, agent, tool — pastel colors, white background, friendly and approachable)*

---

You ask a travel assistant to plan your Paris trip.

It doesn't answer alone. It calls a weather agent, a packing agent, and a local tips agent. Each one speaks to the others using a shared protocol. Data flows back. A complete answer arrives.

You never saw the plumbing. But someone built it.

Before you can build something like this, you need a shared vocabulary. Because the problem isn't the technology — it's that different blogs, papers, and libraries use the same words to mean completely different things.

This post is the vocabulary we use across the entire **When Agents Talk** series. Read it once. Then every other post will feel immediately familiar.

*For the code: In [Part 2](post2_no_llm.md), we build a full multi-agent system with zero LLM tokens. In [Part 3](post3_patterns.md), we add LLM reasoning where it actually adds value. In [Part 4](post4_production.md), we take it to production. In [Part 5](post5_migration.md), we cover upgrading the SDK.*

· What is an Agent? · What is A2A? · What is MCP? · Agent Card · Skill · Orchestrator · Remote Agent · Tool · Agent Logic · Agent Executor · Context ID · Task Store · LLM — and When You Don't Need One · Sources and Further Reading

---

<!-- DIAGRAM D1.1: post1_multiagent_landscape.excalidraw — The big picture: User → Orchestrator → Agents → MCP. Visual anchor before the glossary. -->

![The Multi-Agent Landscape — see post1_multiagent_landscape.excalidraw](diagrams/post1_multiagent_landscape.png)

*The full picture before we define any of the pieces.*

---

## The Glossary

Each entry follows the same pattern: **Technical Term** — what it is in plain language — an analogy to lock it in.

The technical term is the label you'll use in code, in documentation, and in conversation with other developers. The analogy is just the key that opens the door.

---

### **Agent**

An **agent** is a software process that receives a request and takes autonomous action to answer it. It doesn't just return a value — it *decides* what to do.

Analogy: A specialist at a help desk. You describe your problem. They figure out what steps to take, in what order, and come back with an answer.

> In this workshop, every agent is a self-contained Python process running on its own port. It receives a message, does its work, and streams back a response.

---

### **Multi-Agent System**

A **multi-agent system** is a collection of agents that collaborate to answer a single request. No single agent needs to know everything — each one handles the part it's good at.

Analogy: A hospital. The patient describes symptoms once. The system routes them to the right doctor, orders the right lab tests, coordinates the pharmacy. No one person does everything.

> In our workshop, one user message can trigger multiple specialized agents simultaneously — each doing its part, then returning results to be combined.

---

### **A2A (Agent-to-Agent protocol)**

**A2A** is an open protocol created by Google that defines how agents discover each other, call each other, and stream responses — all over standard HTTP.

Think of it as HTTP for agents. The same way a browser knows how to call any web server because they both speak HTTP, one A2A agent can call any other A2A agent because they share the protocol.

Key things A2A handles:
- **Discovery** — how does one agent know what another can do?
- **Transport** — how do messages travel between agents?
- **Streaming** — how does a long response arrive in chunks?
- **Multi-turn** — how does a conversation span multiple exchanges?

> The Python SDK is `a2a-sdk`. In our workshop we use version `0.3.22`. [Part 5](post5_migration.md) covers migrating to `1.x`.

---

### **MCP (Model Context Protocol)**

**MCP** is an open standard that defines how agents access tools and data sources. Where A2A is about agents talking to *each other*, MCP is about agents talking to *data and capabilities*.

Analogy: A USB standard. No matter what you plug in — keyboard, hard drive, camera — the protocol is the same. MCP is the USB standard for AI tools. Any agent that speaks MCP can plug into any MCP server.

Key things MCP handles:
- **Tool discovery** — an agent can ask "what tools do you have?"
- **Tool calling** — the agent calls a tool with arguments and gets back a result
- **Tagging** — tools can be tagged so agents filter only what they need

> In our workshop, MCP servers are built with `FastMCP`. Each tool is a plain Python function decorated with `@mcp.tool()`.

---

### **Agent Card**

An **Agent Card** is a JSON document that every A2A agent publishes at a well-known URL (`/.well-known/agent-card.json`). It describes what the agent can do — its name, skills, capabilities, and how to reach it.

Analogy: A business card with your job title, skills, and contact details. The orchestrator reads these cards to decide who to call.

An Agent Card contains:
- `name` — the agent's name
- `description` — what it does in plain English
- `skills` — a list of specific capabilities (each with tags and examples)
- `url` — where to send requests

> In our workshop, the card is defined in `agent_card.py` and served automatically by the A2A SDK. You never write the JSON by hand.

---

### **Skill**

A **Skill** is a named capability declared inside an Agent Card. Think of it as a line on a CV: not just "I can program" but "Python, 5 years, data pipelines."

Each skill has:
- `id` and `name` — what to call it
- `description` — what it does
- `tags` — short labels used for routing (e.g. `weather`, `assessment`, `packing`)
- `examples` — sample inputs that trigger this skill

The `tags` and `examples` are the key to routing. The orchestrator reads them and uses them to score which agent fits the user's request.

> **Word collision alert — "Skill" in AI tools vs. A2A**
> If you use Cursor, Claude, or similar AI tools you've probably seen the word "Skill" used for something else entirely: a Markdown (`.md`) file that gives the AI assistant step-by-step instructions for a specific task (e.g., *"how to review an agent card"* or *"how to create a PR"*). Those files are essentially *prompts-as-files* — they guide the assistant's behavior.
>
> An A2A **Skill**, by contrast, is a **metadata declaration** inside a JSON Agent Card. It doesn't contain instructions; it contains *routing labels* (id, description, tags, examples) that let an orchestrator decide which agent to call.
>
> Same word, completely different concept. In this series, "Skill" always means the A2A kind.

---

### **Orchestrator**

The **Orchestrator** is the agent that receives the user's message, reads the other agents' cards, decides who to call, and coordinates the response.

Analogy: An air traffic controller. They don't fly the planes. They know which planes are available, where they're going, and who should handle each incoming request.

What the orchestrator does, step by step:
1. Loads a registry of known agents
2. Fetches each agent's card from its live URL
3. Extracts keywords from the card's description, skills, tags, and examples
4. Scores the user's message against those keywords
5. Routes to the agent(s) with the highest match scores
6. Streams their responses back to the user

> The orchestrator is itself an agent — it follows the exact same 5-file structure as every other agent in the system.

---

### **Remote Agent**

A **Remote Agent** is a specialized agent that does one thing well. It is called by the orchestrator. It doesn't know anything about the user's original request — it only receives the routed message.

Analogy: The lab technician the air traffic controller sends you to. They run one specific test and return one specific result.

> "Remote" refers to the relationship with the orchestrator — these agents run as separate processes, often on separate ports. In a production system, they could run on separate machines.

---

### **Tool**

A **Tool** is a function exposed by an MCP server that an agent can call. The agent asks the MCP server "what tools do you have?", gets a list back, and calls the ones it needs.

Analogy: An API endpoint. Just as a frontend calls a backend REST endpoint to get data, an agent calls an MCP tool to get data or perform an action.

```python
# This is what a tool looks like in code — one decorated function
@mcp.tool(tags={"weather"})
def get_weather_for_location(location_str: str, date_str: str) -> dict:
    """Get weather for a location on a given date."""
    ...
```

The `tags` on the tool are how agents find the tools they need without loading all tools indiscriminately.

---

### **Agent Logic**

**Agent Logic** is the part of an agent that contains the actual business logic — the decisions, the LLM calls, the MCP calls, the output formatting. It lives in a file called `agent_logic.py`.

Analogy: The brain, as opposed to the skeleton. The skeleton (the infrastructure) is identical for every agent. The brain is what makes each agent unique.

> This is the most important concept in the series. In our workshop, every single agent shares identical infrastructure. The **only** file that differs between agents is `agent_logic.py`. This is the key to understanding how the system scales so gracefully.

---

### **Agent Executor**

The **Agent Executor** is the bridge between the A2A SDK's request lifecycle and the agent's business logic. It lives in `agent_executor.py`.

When the A2A SDK receives a message from the network, it hands it to the executor. The executor calls the agent logic, collects the responses, and hands them back to the SDK — which takes care of streaming them to the caller.

Analogy: A translator between two people who speak different languages. The SDK speaks "A2A protocol". The agent logic speaks "Python generator". The executor translates between them.

> In our workshop, every agent's `agent_executor.py` is **identical**. You never need to write it from scratch — just copy it and change the import.

---

### **Context ID**

A **Context ID** is a session token that links multiple messages together into a single conversation. Without it, every message would be treated as if it were the first one.

Analogy: A ticket number at a support desk. When you call back, you give your ticket number and the agent can see everything that was discussed before.

The orchestrator creates a Context ID on the first message and includes it in every subsequent message to the same conversation. The A2A SDK's task store uses it to retrieve conversation history.

---

### **Task Store**

The **Task Store** is where the A2A SDK stores the history of a conversation. Every message, every response, every status update — all stored by Context ID.

In our workshop we use `InMemoryTaskStore` — it's fast and simple. It lives inside the process. That means it resets on restart and cannot be shared across multiple server instances.

> For production, replace it with a persistent store (Redis, a database). [Part 4](post4_production.md) covers this.

---

### **LLM (Large Language Model)**

An **LLM** is the AI model that understands and generates text — GPT, Claude, Gemini, and so on. In our workshop, we use Azure OpenAI.

In a multi-agent system, an LLM is one possible component *inside* an agent — not the agent itself. An agent can use an LLM, a direct data lookup, or both.

---

## When Do You Actually Need an LLM?

This is the question most people don't ask — and they should.

An LLM is a powerful reasoning engine. It shines when:
- The output is **creative or generative** (e.g., write a packing list, draft an email)
- The input is **ambiguous** and needs understanding (e.g., "what should I pack for December in Paris?")
- The task requires **combining and reasoning** across multiple data sources

An LLM is *not* needed when:
- The output is always the **same for the same input** (e.g., "give me the study path for MCP at beginner level")
- You're doing a **structured lookup** in a database or JSON file
- You want **deterministic, testable, cost-free** behavior

> **Many useful agents don't need an LLM at all.** In [Part 2](post2_no_llm.md), we build a complete multi-agent system with four agents — and zero LLM tokens. This is a feature, not a limitation.

---

## Summary

Here is the full vocabulary we'll use across the series:

- **Agent** — a software process that receives a request and takes autonomous action
- **Multi-Agent System** — multiple agents collaborating to answer a single request
- **A2A** — the open protocol that lets agents discover and call each other over HTTP
- **MCP** — the open standard for exposing tools and data to agents
- **Agent Card** — the JSON document an agent publishes to describe what it can do
- **Skill** — a named capability inside an Agent Card, with tags and examples for routing *(not to be confused with Markdown instruction files by the same name in tools like Cursor or Claude)*
- **Orchestrator** — the agent that reads cards, scores requests, and delegates
- **Remote Agent** — a specialist agent called by the orchestrator
- **Tool** — a function exposed by an MCP server, callable by any agent
- **Agent Logic** — the only file that truly differs between agents; the business logic
- **Agent Executor** — the bridge between the A2A SDK and the agent logic; identical everywhere
- **Context ID** — the session token that links multiple messages into a conversation
- **Task Store** — where conversation history is stored, keyed by Context ID
- **LLM** — the AI reasoning engine inside an agent; required only when the task needs it

---

If this post helped you, please clap 👏 (you can clap up to 50 times!) — it's the main way Medium surfaces articles to new readers. The more people see this, the more developers can build without the gatekeeping. Thank you for helping spread it.

---

## Sources and Further Reading

**The A2A Protocol:**
- [A2A Protocol Specification](https://a2a-protocol.org/v1.0.0/specification/)
- [a2a-python SDK on GitHub](https://github.com/a2aproject/a2a-python)
- [a2a-sdk on PyPI](https://pypi.org/project/a2a-sdk/)

**Model Context Protocol:**
- [MCP Documentation](https://modelcontextprotocol.io/)
- [FastMCP on GitHub](https://github.com/jlowin/fastmcp)

**Related Posts in This Series:**
- **Part 2**: [Your First Multi-Agent System — No LLM Tokens Required](post2_no_llm.md)
- **Part 3**: [Three Patterns for Agent Intelligence](post3_patterns.md)
- **Part 4**: [When Agents Talk in Production: What No One Tells You](post4_production.md)
- **Part 5**: [When Agents Talk, But the Protocol Changed: Migrating a2a-sdk 0.3 to 1.0](post5_migration.md)

---

*Written by Dina Bavli · Data Scientist | NLP | AI Systems · ❤ sharing knowledge and contributing to the community*
