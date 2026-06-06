import os
import traceback
from typing import AsyncGenerator

import dotenv
dotenv.load_dotenv()

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import ToolMessage, HumanMessage, SystemMessage, AIMessage
from a2a.types import Role
from fastmcp import Client

SYSTEM_PROMPT = """You are a weather and activity assistant.

Available tools:
- get_weather_for_location_and_date_string – fetch weather for a location and date
- suggest_activities_for_location_and_date – recommend activities based on weather

Rules:
- When a city or location is mentioned, ALWAYS call get_weather_for_location_and_date_string first.
- Then pass the weather result to suggest_activities_for_location_and_date.
- Only call suggest_activities_for_location_and_date without weather data when NO location is given.
- location_str format: "City, Country" (e.g. "Tel Aviv, Israel").
- Set preference to "indoor" or "outdoor" when the user specifies.
- Always state the city name and use the word "activities" in your final response."""


class AgentLogic:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_api_type="azure",
        )
        self.mcp_url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8003/mcp")
        self.mcp_client = Client(self.mcp_url)

    async def _get_mcp_tools_by_tags(self, include_tags: set) -> list:
        """Return LLM-ready tool definitions for MCP tools that match any of the given tags."""
        try:
            async with self.mcp_client:
                await self.mcp_client.ping()
                tools = []
                for t in await self.mcp_client.list_tools():
                    tags = set()
                    if t.meta and isinstance(t.meta, dict):
                        fm = t.meta.get('fastmcp', {})
                        if isinstance(fm, dict):
                            tags.update(fm.get('tags', []))
                    if not tags.isdisjoint(include_tags):
                        tools.append({
                            "type": "function",
                            "function": {
                                "name": t.name,
                                "description": t.description or t.name,
                                "parameters": t.inputSchema or {"type": "object", "properties": {}},
                            },
                        })
                return tools
        except Exception as e:
            print(f"[WeatherActivityAgent] Error fetching MCP tools: {e}")
            return []

    async def stream(self, user_input: str, history=None) -> AsyncGenerator:
        try:
            tool_definitions = await self._get_mcp_tools_by_tags({"weather", "activities"})

            if not tool_definitions:
                yield {"completed": False, "failed": True, "input_required": False,
                       "content": "No MCP tools available. Ensure the MCP server is running."}
                return

            llm_with_tools = self.llm.bind_tools(tool_definitions)
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

            for _ in range(5):
                response = await llm_with_tools.ainvoke(messages)
                tool_calls = response.tool_calls if hasattr(response, 'tool_calls') else []

                if not tool_calls:
                    yield {"completed": True, "failed": False, "input_required": False,
                           "content": response.content if hasattr(response, 'content') else ""}
                    return

                messages.append(response)

                for call in tool_calls:
                    tool_name = call["name"]
                    arguments  = call["args"]
                    call_id    = call["id"]

                    yield {"completed": False, "failed": False, "input_required": False,
                           "content": f"\n[Tool] {tool_name}\n"}

                    async with self.mcp_client:
                        result = await self.mcp_client.call_tool(tool_name, arguments)
                        result_text = result.content[0].text if result.content else "{}"

                    yield {"completed": False, "failed": False, "input_required": False,
                           "content": f"[Result]\n{result_text}\n\n"}

                    messages.append(ToolMessage(tool_call_id=call_id, content=str(result_text)))

                yield {"completed": False, "failed": False, "input_required": False,
                       "content": "Processing results...\n\n"}

            yield {"completed": True, "failed": False, "input_required": False,
                   "content": "Reached maximum number of reasoning steps."}

        except Exception as e:
            traceback.print_exc()
            yield {"completed": False, "failed": True, "input_required": False,
                   "content": f"Error in weather_activity_agent: {e}"}
