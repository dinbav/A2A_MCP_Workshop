import json
import os
from typing import AsyncGenerator
from fastmcp import Client
import dotenv
dotenv.load_dotenv()


class AgentLogic:
    KNOWN_CITIES = ["tel aviv", "paris", "barcelona", "rome", "london"]
    TRIP_TYPES   = ["family", "beach", "cultural", "adventure", "romantic"]

    def __init__(self):
        self.mcp_url = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8003/mcp")

    def _parse_input(self, user_input: str) -> tuple[str, str]:
        lower = user_input.lower()
        city      = next((c for c in self.KNOWN_CITIES if c in lower), "tel aviv")
        trip_type = next((t for t in self.TRIP_TYPES   if t in lower), "general")
        return city, trip_type

    def _format_tips(self, data: dict) -> str:
        if not data.get("found", True):
            return data.get("message", "City not found.")

        lines = [
            f"Local Tips for {data['city']} ({data['trip_type'].capitalize()} trip)",
            "=" * 50,
            f"Transportation:     {data['transportation']}",
            f"Food:               {data['food']}",
            f"Safety:             {data['safety']}",
            f"Recommended Hours:  {data['recommended_hours']}",
            f"Local Highlights:   {data['local_highlights']}",
        ]
        if data.get("trip_type_tips"):
            lines.append(f"Trip Tips:          {data['trip_type_tips']}")
        return "\n".join(lines)

    async def stream(self, user_input: str, history=None) -> AsyncGenerator:
        city, trip_type = self._parse_input(user_input)

        try:
            async with Client(self.mcp_url) as client:
                result = await client.call_tool(
                    "get_local_tips_by_city",
                    {"city": city, "trip_type": trip_type},
                )
            raw = result.content[0].text if result.content else "{}"
            data = json.loads(raw)
            formatted = self._format_tips(data)
            yield {"completed": True, "failed": False, "input_required": False, "content": formatted}

        except Exception as e:
            yield {"completed": False, "failed": True, "input_required": False,
                   "content": f"Error fetching local tips: {e}"}
