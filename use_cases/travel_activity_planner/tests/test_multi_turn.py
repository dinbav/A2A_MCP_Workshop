# MULTI-TURN CONVERSATION TEST
# Run with: python -m tests.test_multi_turn
# Requires all agents running (start_all.ps1)
#
# See MULTI_TURN_GUIDE.md for the full step-by-step guide.

import asyncio
from uuid import uuid4
from helpers import call_agent_with_context

ORCHESTRATOR_URL = "http://localhost:8080"

CONVERSATION = [
    "what is the weather in tel aviv?",
    "yes",
    "3 adults and 2 kids",
    "tel aviv one day beach",
]


async def main():
    ctx_id = str(uuid4())
    print("Main Agent: Enter text or 'exit' to quit\n")
    for user_input in CONVERSATION:
        print(f"User: {user_input}")
        response = await call_agent_with_context(
            ORCHESTRATOR_URL, user_input, context_id=ctx_id
        )
        print(f"Main Agent: {response}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
