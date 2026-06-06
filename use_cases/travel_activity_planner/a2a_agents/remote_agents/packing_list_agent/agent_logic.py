import os
import traceback
from typing import AsyncGenerator

import dotenv
dotenv.load_dotenv()

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from a2a.types import Role

SYSTEM_PROMPT = """You are a packing list and trip invitation specialist.

Skills:
- Create categorised packing lists (clothes, toiletries, gadgets, gear, food)
- Write engaging group-trip invitations
- Adapt recommendations to weather, activities, duration, group size, and children

Packing list format:
- Use these exact category headers: 👕 Clothes, 🧴 Toiletries, 📱 Gadgets & Electronics, 🎒 Gear & Equipment, 🍽️ Food & Snacks
- Use [ ] checkboxes for each item
- Include quantities where useful (e.g. "[ ] 3 pairs of socks")
- Add a kids section when children are mentioned

For invitations: be warm, include trip details, mention what to bring, use emojis.

Ask for clarification if critical details are missing (destination, duration, group composition)."""


class AgentLogic:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_api_type="azure",
        )

    async def stream(self, user_input: str, history=None) -> AsyncGenerator:
        try:
            messages = [SystemMessage(content=SYSTEM_PROMPT)]
            for msg in (history or []):
                for part in msg.parts:
                    text = part.root.text if hasattr(part, 'root') and hasattr(part.root, 'text') else ""
                    if text:
                        if msg.role == Role.user:
                            messages.append(HumanMessage(content=text))
                        else:
                            messages.append(AIMessage(content=text))
            messages.append(HumanMessage(content=user_input))
            response = await self.llm.ainvoke(messages)
            yield {
                "completed": True,
                "failed": False,
                "input_required": False,
                "content": response.content if hasattr(response, 'content') else "",
            }
        except Exception as e:
            traceback.print_exc()
            yield {
                "completed": False,
                "failed": True,
                "input_required": False,
                "content": f"Error in packing_list_agent: {e}",
            }
