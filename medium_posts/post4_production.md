# When Agents Talk in Production: What No One Tells You

## A Practical Guide to Guardrails, Observability, Error Handling, Auth, Cost, Scaling, Testing, and Human-in-the-Loop Design

*From the **When Agents Talk** workshop · Part 4 of 5*

---

> *"By Author using DALL-E"*
> *(Hero image: control room with multiple AI agents on screens, operators monitoring metrics and dashboards, calm but professional atmosphere, flat illustration, deep blue and amber color palette)*

---

Building a multi-agent system locally is surprisingly fun.

Deploying it to real users is where the surprises begin — and they are not always fun.

What happens when two agents return conflicting answers? What happens when an LLM decides to call a tool 40 times? What happens when a conversation history from a year ago takes 5 seconds to load? What happens when a user asks "delete my account" in the middle of a travel planning conversation?

In Posts 2 and 3 of this series, we built the system. In this post, we harden it.

This is Part 4 of the **When Agents Talk** series. The architecture concepts from [Part 1](post1_terminology.md) and the code patterns from [Parts 2](post2_no_llm.md) and [3](post3_patterns.md) are assumed.

*[Part 5](post5_migration.md) covers upgrading the SDK itself.*

· Guardrails · Observability · Error Handling · Auth & Security · Cost Control · Scaling · Testing in Production · Human-in-the-Loop · The Production Checklist · Sources and Further Reading

---

## 1. Guardrails: What Are They, and Where Do They Go?

A **guardrail** is a constraint that prevents an agent from doing something harmful, expensive, or embarrassing. The word sounds heavy; the implementation is usually just a function.

Guardrails come in two flavors:

**Input guardrails** — check the user's message *before* it reaches any agent:
- Block toxic or abusive content
- Reject requests that contain PII (personal identifiable information) that shouldn't be processed
- Block off-topic requests ("plan my dinner" in a travel assistant shouldn't go to the weather agent)

**Output guardrails** — check the agent's response *before* it's returned to the user:
- Block hallucinated URLs or phone numbers (verify they exist)
- Enforce response length limits
- Detect responses that contradict factual constraints (e.g., "Tel Aviv has no beaches")

### Where to implement them

The **orchestrator** is the right place for input guardrails — it sees every message before any agent does:

```python
# Pseudocode — add to orchestrator's stream() before _select_agents()

async def stream(self, user_input: str, ...):
    # Input guardrail — before routing
    if is_toxic(user_input):
        yield {"completed": True, ..., "content": "I can't help with that."}
        return
    if is_off_topic(user_input, allowed_domains=["travel", "packing"]):
        yield {"completed": True, ..., "content": "This assistant is for travel planning."}
        return

    agents, scored = await self._select_agents(user_input)
    ...
```

For output guardrails, add a post-processing step in `agent_logic.py` before each `yield`:

```python
# Pseudocode — in any agent_logic.py stream() method

response = await self.llm.ainvoke(messages)
content = response.content

# Output guardrail
content = remove_hallucinated_links(content)
content = enforce_max_length(content, max_chars=3000)

yield {"completed": True, ..., "content": content}
```

**Libraries to consider:**
- [Guardrails AI](https://github.com/guardrails-ai/guardrails) — structured validators for LLM outputs
- [LlamaGuard](https://ai.meta.com/research/publications/llama-guard-llm-based-input-output-safeguard-for-human-ai-conversations/) — Meta's input/output safety classifier
- A simple custom keyword blocklist — often enough for production v1

---

## 2. Observability: You Can't Fix What You Can't See

**Observability** in multi-agent systems means being able to answer: "What exactly happened during this conversation, and why did it produce this result?"

This is harder than observability in a regular API because:
- The same user message can trigger 3 agents in parallel
- Each agent may call the LLM multiple times
- An error on iteration 3 of 5 in agent B may or may not affect the user's final response

### What to trace

Every agent should emit structured traces for:
- Received message (user input, context_id, turn number)
- Routing decisions (which agents were selected and why — the score table is gold)
- Tool calls (name, arguments, latency, result summary)
- LLM calls (model, token count, latency)
- Final response (content length, which agent produced it)

### Implementation

Add spans to the orchestrator and each agent. The A2A SDK's `execute()` hook is the natural place:

```python
# Pseudocode — instrumented base_executor.py

async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
    with tracer.start_as_current_span("agent.execute") as span:
        span.set_attribute("agent.name", self.__class__.__name__)
        span.set_attribute("context_id", context.context_id)
        span.set_attribute("user_input", context.get_user_input()[:200])

        history = context.current_task.history if context.current_task else []
        async for response in self.agent.stream(context.get_user_input(), history=history):
            span.add_event("stream_chunk", {"completed": response.get("completed")})
            ...
```

**Tools and platforms:**
- [OpenTelemetry](https://opentelemetry.io/) — vendor-neutral traces (recommended starting point)
- [Langfuse](https://langfuse.com/) — purpose-built for LLM observability, free tier available
- [Arize Phoenix](https://phoenix.arize.com/) — another strong option, especially for LangChain traces
- [Datadog](https://www.datadoghq.com/) — if you're already using it for infrastructure

**Key metrics to alert on:**
- `p95 agent_latency > 10s` — something is slow or hung
- `tool_call_count > 8 per request` — Pattern 2 is looping unexpectedly
- `error_rate > 1%` — something is systematically failing
- `llm_cost_per_hour > threshold` — cost spike detection

---

## 3. Error Handling: Fail Gracefully, Not Silently

The most dangerous failure mode in a multi-agent system is **silent success** — the orchestrator returns a response, but one of the agents failed and the failure was swallowed.

### The current error contract

Every agent in our workshop returns a dict with `"failed": True` when something goes wrong:

```python
# Pattern — used in all three agent patterns

except Exception as e:
    yield {
        "completed": False,
        "failed": True,
        "input_required": False,
        "content": f"Error in weather_activity_agent: {e}",
    }
```

The base executor catches `failed: True` and calls `updater.failed()`. The orchestrator receives this event and includes the failure message in its output.

### What to add for production

**1. Retry with backoff for transient errors** (network timeouts, MCP server temporarily unavailable):

```python
# Add to _send_to_agent() in orchestrator_agent/agent_logic.py

import asyncio

async def _send_to_agent_with_retry(self, agent, user_input, context_id, max_retries=2):
    for attempt in range(max_retries + 1):
        try:
            async for event in self._send_to_agent(agent, user_input, context_id):
                yield event
            return
        except Exception as e:
            if attempt == max_retries:
                yield {"completed": False, "failed": True, ...,
                       "content": f"{agent.name} failed after {max_retries} retries: {e}"}
            else:
                await asyncio.sleep(2 ** attempt)   # 1s, 2s, 4s...
```

**2. Circuit breaker** — if an agent fails 5 times in a row, stop routing to it and alert:

```python
# Pseudocode — add to orchestrator

if self._consecutive_failures[agent.name] >= 5:
    logger.error(f"Circuit open for {agent.name} — skipping")
    continue
```

**3. Fallback response** — when an agent fails, return a partial response with a clear message:

```
I got responses from 2 of 3 agents. The packing list is below.
The weather agent is temporarily unavailable — please check back shortly.
[Packing list follows...]
```

Partial is better than nothing. Explicit is better than silent.

---

## 4. Auth & Security: Who Should Be Allowed to Talk?

In our workshop, every agent is open on localhost. In production, they must not be.

### Four layers to secure

**Layer 1 — Transport (HTTPS):** Every agent port must be behind HTTPS. In Kubernetes, this is handled by the Ingress. On a VM, use nginx as a reverse proxy with Let's Encrypt.

**Layer 2 — Agent-to-Agent Auth:** The orchestrator talks to remote agents over HTTP. Those calls should carry a signed token (JWT or HMAC) so a remote agent can verify the caller is your orchestrator, not an arbitrary client:

```python
# Add to orchestrator's _send_to_agent()

headers = {"Authorization": f"Bearer {self._get_agent_token()}"}
msg = Message(..., metadata={"auth_token": headers["Authorization"]})
```

```python
# Add to each remote agent's execute() — verify the token before processing

if not verify_token(context.request_metadata.get("auth_token")):
    yield {"completed": False, "failed": True, ..., "content": "Unauthorized"}
    return
```

**Layer 3 — User Auth (Orchestrator entry point):** The orchestrator's public port should require authentication from the user — API key, OAuth token, or session cookie.

**Layer 4 — MCP Server:** The MCP server should only accept connections from known agent IPs, not from the public internet. In a cloud deployment, put it in a private subnet.

**Sensitivity principles:**
- Never log the full user message — log a hash or a trimmed version
- Never store user messages longer than your privacy policy says you do
- If agents call external APIs with user data (e.g., a real weather API with location), be explicit in your terms about what data leaves your system

---

## 5. Cost Control: LLMs at Scale Are Expensive

In our workshop, we run two LLM agents. In production, you might have dozens. The cost math changes fast.

<!-- DIAGRAM D4.1: post4_cost_comparison.excalidraw — Bar chart: Pattern 1 vs 2 vs 3 cost per 1000 requests -->

![Cost per Request by Pattern — see post4_cost_comparison.excalidraw](diagrams/post4_cost_comparison.png)

### Strategies

**1. Prefer Pattern 3 (MCP Direct) wherever possible.** You already know this from Post 3. Every deterministic lookup that can be served from a JSON file or a database costs zero tokens.

**2. Cache LLM responses** for inputs that recur frequently:

```python
# Add to any LLM agent's stream() — before the LLM call

cache_key = hashlib.sha256(user_input.encode()).hexdigest()
if cached := self.response_cache.get(cache_key):
    yield {"completed": True, ..., "content": cached}
    return

response = await self.llm.ainvoke(messages)
self.response_cache.set(cache_key, response.content, ttl=3600)
yield {"completed": True, ..., "content": response.content}
```

This works well for Pattern 1 (LLM Only) because the same packing list for "Paris, December, 4 days" is always approximately the same.

**3. Cap iteration counts** in Pattern 2's tool loop. The current cap is 5. Tune it based on your actual traces. Most requests resolve in 2–3 iterations. A cap of 4 would cover 99% of real traffic with less cost.

**4. Set token limits** at the LLM call level:

```python
self.llm = AzureChatOpenAI(
    azure_deployment=...,
    max_tokens=800,     # response cap
    temperature=0.3,    # lower = cheaper (fewer retries needed)
)
```

**5. Track cost per context_id.** If a single conversation is costing more than X, surface it in your dashboard. This catches prompt injection and runaway conversations.

---

## 6. Scaling: From One Process to Many

The workshop runs 5 processes locally. Production may need hundreds.

### The statefulness problem

The current workshop uses `InMemoryTaskStore`. This works for one process. It does not work for multiple:
- Two requests in the same `context_id` might hit different server instances
- The second request won't have the history from the first

**Fix: Replace `InMemoryTaskStore` with a distributed store.** The A2A SDK is designed for this:

```python
# Replace in server_factory.py

# Workshop (in-memory):
task_store = InMemoryTaskStore()

# Production (Redis — example):
from my_redis_task_store import RedisTaskStore
task_store = RedisTaskStore(url=os.getenv("REDIS_URL"))
```

`RedisTaskStore` is not in the SDK — you implement it by subclassing `TaskStore` and storing/fetching from Redis by `task_id` and `context_id`.

### The stateless agent advantage

Each remote agent (Topic Explainer, Packing List, etc.) is stateless — all conversation state lives in the task store, not in the agent process. This means:
- **Horizontal scaling**: spin up 10 Packing List agents, put a load balancer in front
- **Zero-downtime deploys**: old and new versions can run side by side
- **Cost elasticity**: scale down during off-hours

The only component that has state is the **task store**. Make it external, and the rest scales freely.

### Kubernetes sketch

```yaml
# Kubernetes deployment sketch (not production-ready — illustrative only)

apiVersion: apps/v1
kind: Deployment
metadata:
  name: packing-list-agent
spec:
  replicas: 3          # horizontal scale
  template:
    spec:
      containers:
      - name: agent
        image: my-registry/packing-list-agent:v1
        env:
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
```

---

## 7. Testing in Production

Testing locally is different from testing in production. Here's how to bridge the gap.

### Canary deployments

Don't deploy new agent versions to 100% of traffic. Deploy to 10% first. Compare:
- Error rate: new vs. old
- P95 latency: new vs. old
- LLM cost per request: new vs. old

If the new version is better on all three, gradually increase to 100%.

### Synthetic traffic

Run a synthetic test suite against production on a schedule:

```python
# tests/synthetic_prod_test.py — run daily against production URL

TEST_CASES = [
    {"input": "explain MCP", "expected_agent": "Topic Explainer Agent"},
    {"input": "packing list for Paris December", "expected_agent": "Packing List Agent"},
    {"input": "weather in Tel Aviv this week", "expected_agent": "Activity & Weather Agent"},
]

for case in TEST_CASES:
    response = call_orchestrator(case["input"])
    assert case["expected_agent"] in response.routing_log, f"Routing failed for: {case['input']}"
```

This catches regressions — a change to an agent card's tags that breaks routing, for example.

### Shadow mode

When testing a new agent version, run it in shadow mode: the old agent responds to the user, but the new agent also processes the same request. Compare outputs offline. No user impact.

---

## 8. Human-in-the-Loop: When AI Shouldn't Decide Alone

**Human-in-the-loop (HITL)** means pausing the agent's response and waiting for a human to review or approve before proceeding. The A2A protocol has first-class support for this through the `input_required` state.

### When to use it

- The agent is about to **perform an irreversible action** (book a flight, send an email, delete data)
- The agent's **confidence is low** (the routing score is ambiguous, the LLM response quality score is below threshold)
- A **guardrail triggered** and a human supervisor should review before retrying
- The task is **sensitive** (health, legal, financial) and policy requires human sign-off

### How it works in our framework

```python
# Any agent_logic.py — when confirmation is needed

yield {
    "completed": False,
    "failed": False,
    "input_required": True,    # ← this is the key
    "content": "I found 3 flights matching your criteria. "
               "Shall I proceed to book the cheapest one at €280?",
}
```

The A2A SDK sets the task status to `input_required`. The client is notified. The conversation pauses. When the user replies "yes" or "no", the agent resumes with the confirmed answer and the conversation history intact.

In the base executor:

```python
elif input_required:
    message = new_agent_text_message(text=safe_content, ...)
    await updater.requires_input(message)   # A2A SDK state
```

This state is preserved in the task store. The conversation can be picked up hours later — even by a different server instance.

---

## The Production Checklist

Before going live:

**Guardrails**
- [ ] Input guardrail in the orchestrator (toxic content, off-topic detection)
- [ ] Output guardrail in LLM agents (length, hallucination checks)

**Observability**
- [ ] Distributed tracing across all agents (OpenTelemetry or equivalent)
- [ ] LLM cost tracking per `context_id`
- [ ] Alerts for: error rate, latency, tool loop count, cost spike

**Error Handling**
- [ ] Retry with backoff in the orchestrator's agent calls
- [ ] Circuit breaker per remote agent
- [ ] Partial response fallback when one agent fails

**Auth & Security**
- [ ] HTTPS on all public ports
- [ ] Agent-to-agent authentication (JWT or HMAC)
- [ ] MCP server in private subnet
- [ ] User auth at the orchestrator entry point

**Cost Control**
- [ ] Pattern 3 used for all deterministic lookups
- [ ] LLM response caching where inputs repeat
- [ ] Tool loop iteration cap tuned from real traces
- [ ] Token limits set on all LLM clients

**Scaling**
- [ ] `InMemoryTaskStore` replaced with Redis or equivalent
- [ ] Agents containerized and horizontally scalable
- [ ] Load balancer in front of each agent type

**Testing**
- [ ] Canary deployment pipeline
- [ ] Synthetic test suite running daily against production
- [ ] Shadow mode for new agent versions

**Human-in-the-Loop**
- [ ] `input_required` used for irreversible actions
- [ ] Sensitive domain actions flagged for supervisor review

---

If this post helped you, please clap 👏 (you can clap up to 50 times!) — it's the main way Medium surfaces articles to new readers. The more people see this, the more developers can build without the gatekeeping. Thank you for helping spread it.

---

## Sources and Further Reading

**Guardrails:**
- [Guardrails AI](https://github.com/guardrails-ai/guardrails)
- [LlamaGuard](https://ai.meta.com/research/publications/llama-guard-llm-based-input-output-safeguard-for-human-ai-conversations/)

**Observability:**
- [OpenTelemetry for Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Langfuse](https://langfuse.com/)
- [Arize Phoenix](https://phoenix.arize.com/)

**A2A Protocol — Task States:**
- [A2A Task Lifecycle](https://a2a-protocol.org/v1.0.0/specification/#task-lifecycle)

**Related Posts in This Series:**
- **Part 1**: [The Language of Multi-Agent AI](post1_terminology.md)
- **Part 2**: [Your First Multi-Agent System — No LLM Tokens Required](post2_no_llm.md)
- **Part 3**: [Three Patterns for Agent Intelligence](post3_patterns.md)
- **Part 5**: [Migrating a2a-sdk 0.3 to 1.0](post5_migration.md)

---

*Written by Dina Bavli · Data Scientist | NLP | AI Systems · ❤ sharing knowledge and contributing to the community*
