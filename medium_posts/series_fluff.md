# When Agents Talk — Series Fluff & Social Copy

## Series Details

**Series Title:** When Agents Talk
**Series Subtitle:** A 5-Part Developer Guide to Building Multi-Agent AI Systems with A2A and MCP
**Author:** Dina Bavli

---

## LinkedIn Posts

### Post 1 — Terminology (The Language of Multi-Agent AI)

---

🤖 I've been building multi-agent AI systems, and the number one problem people run into isn't the code.

It's the vocabulary.

"Agent" means something different in every blog post. "Tool" means something different in every library. "Orchestrator" is used for five completely different things.

So I wrote the glossary I wish had existed when I started.

**When Agents Talk: Part 1 — The Language of Multi-Agent AI**

13 terms. Clear definitions. Real analogies. The exact words we use in all the code across this series.

Including the answer to: **do you even need an LLM at all?**

(Spoiler: often, no.)

→ [Link to Medium post]

This is Part 1 of a 5-part series where I open up the full workshop code — agents, tools, patterns, production, and migration — for everyone. No gatekeeping.

If it helps, please clap and share. 🙏 The more people see it, the more developers can build with confidence.

#AI #MultiAgent #Python #MCP #A2A #AIEngineering #MachineLearning

---

### Post 2 — No LLM System

---

What if I told you that you can build a complete, working multi-agent AI system — 4 agents collaborating in real time — with zero LLM API calls?

No OpenAI. No Anthropic. No token cost. No latency from a model.

I built it. Here's how.

**When Agents Talk: Part 2 — Your First Multi-Agent System, No LLM Tokens Required**

In this post, I walk through:
✅ An MCP server with 8 tools (learning topics, assessments, study paths)
✅ 3 specialized agents + 1 orchestrator
✅ The 5-file blueprint that every agent in the system shares (4 of 5 files are identical)
✅ Keyword-based routing without any AI

The framework is the same as what you'll use when you *do* add an LLM.

→ [Link to Medium post]

Part 3 adds LLM reasoning. But you need this foundation first.

If this kind of no-nonsense breakdown is useful to you — clap, share, or drop a comment. It helps more people find it. 🙏

#Python #AIEngineering #MultiAgent #A2A #MCP #OpenSource #NoCode

---

### Post 3 — Three Patterns

---

One user message. Three different agents spring into action.

One uses **no AI at all** — just a data lookup.
One uses an **LLM for creative generation** — no external data needed.
One uses an **LLM + live tool calls** — real weather data, real reasoning, real cost.

Three completely different approaches. Same framework. Same 5 files. Same orchestrator.

**When Agents Talk: Part 3 — Three Patterns for Agent Intelligence**

This is the post that makes the whole series click.

→ [Link to Medium post]

I show you the code, the decision logic, and — critically — **when NOT to use an LLM**.

The decision chart alone is worth the read.

If this is useful, please share it. The more people see this, the more devs can build multi-agent systems without spending weeks figuring out the patterns. 🙏

#LLM #MultiAgent #AI #Python #A2A #MCP #AIEngineering #AzureOpenAI

---

### Post 4 — Production

---

Building a multi-agent system locally is surprisingly fun.

Deploying it to real users is where the surprises begin.

What happens when:
→ Two agents return conflicting answers?
→ An LLM decides to call a tool 40 times?
→ A conversation from 6 months ago takes 5 seconds to load?
→ A user types "delete my account" in the middle of a travel planning session?

**When Agents Talk: Part 4 — What No One Tells You About Production**

This post covers:
🔒 Guardrails (input + output)
📊 Observability (what to trace, what to alert on)
💥 Error handling (fail gracefully, never silently)
🔑 Auth & security (4 layers)
💰 Cost control (LLMs at scale are expensive — here's what to do)
📈 Scaling (replace InMemoryTaskStore, go horizontal)
🧪 Testing in production (canary, synthetic, shadow mode)
🧑‍💼 Human-in-the-loop (the A2A SDK supports it natively)

→ [Link to Medium post]

No fluff. All actionable. With a checklist at the end.

If it helps, please clap and share. This kind of information shouldn't be gatekept. 🙏

#MLOps #LLMOps #AIEngineering #Production #MultiAgent #Python #A2A

---

### Post 5 — Migration Guide

---

The workshop code runs on `a2a-sdk==0.3.22`.

The protocol hit v1.0. The SDK followed. There are breaking changes.

**When Agents Talk: Part 5 — When the Protocol Changed: Migrating a2a-sdk 0.3 to 1.0**

Every breaking change. Before and after code. Side by side.

Including:
→ TextPart → Part (unified type)
→ Role.user → Role.USER (enum casing)
→ A2AStarletteApplication → route factory functions
→ a2a.utils.* → a2a.helpers
→ How to use compatibility mode to migrate gradually

Total effort for the workshop codebase: **2–4 hours**. Most of it is grep-and-replace.

→ [Link to Medium post]

This is the last post in the series. 5 posts, full workshop code, no gatekeeping.

If the series has been useful to you — please share it. Every clap helps more developers find it. Thank you so much. 🙏❤

#Python #A2A #MigrationGuide #APIUpgrade #MultiAgent #AIEngineering #OpenSource

---

## Tweet / X Thread Starters

### Series announcement tweet

```
🤖 New series: "When Agents Talk" — 5 posts on building multi-agent AI systems with A2A + MCP

Part 1: The vocabulary (no code)
Part 2: Full system, zero LLM calls
Part 3: 3 patterns — when to use LLM
Part 4: Production hardening
Part 5: SDK migration guide

All workshop code is open. No gatekeeping. 🧵
```

### Post 2 tweet

```
You can build a 4-agent multi-agent system with:
- Zero LLM API calls
- Zero cost per request
- 100% deterministic behavior

Here's the full code breakdown:
[link]

The same framework works when you DO add an LLM later. Start here.
```

### Post 3 tweet

```
3 agents. 3 completely different strategies.

Pattern 1: LLM generates the answer (creative task)
Pattern 2: LLM calls live tools in a loop (reasoning + data)
Pattern 3: No LLM — just a direct tool call (free, fast, deterministic)

Same framework. Same 5 files. Same orchestrator.

Full code: [link]
```

### Post 4 tweet

```
"The most dangerous failure mode in a multi-agent system is **silent success**."

Thread on what happens when you deploy to real users:
- Guardrails
- Observability
- Cost control (LLMs are expensive at scale)
- Scaling (InMemoryTaskStore won't cut it)
- Human-in-the-loop

Full post: [link]
```

### Post 5 tweet

```
a2a-sdk 0.3.22 → 1.0: the migration guide

7 breaking changes. Before/after code for each.

- TextPart → Part(text=x)
- Role.user → Role.USER
- A2AStarletteApplication → route factory functions
- a2a.utils.* → a2a.helpers

2–4 hours total. Most is grep-and-replace.

Full guide: [link]
```

---

## Medium Tags by Post

| Post | Tags |
|------|------|
| Post 1 | Artificial Intelligence, Python, Machine Learning, Programming, Software Engineering |
| Post 2 | Python, Artificial Intelligence, Software Engineering, Open Source, Programming |
| Post 3 | Artificial Intelligence, Machine Learning, Python, Software Architecture, LLM |
| Post 4 | Machine Learning, Software Engineering, DevOps, Artificial Intelligence, Python |
| Post 5 | Python, Software Engineering, Programming, Open Source, Artificial Intelligence |

---

## Series CTA (call-to-action) — Use at the End of Every Post

> If this post helped you, please clap 👏 (you can clap up to 50 times!) — it's the main way Medium surfaces articles to new readers. The more people see this, the more developers can build without the gatekeeping. Thank you for helping spread it.

---

## Author Bio for Medium

> **Dina Bavli** — Data Scientist | NLP | AI Systems
>
> ❤ Sharing knowledge and contributing to the community. I write about the things I had to figure out the hard way — so you don't have to.
>
> [Follow on Medium] | [LinkedIn] | [GitHub]
