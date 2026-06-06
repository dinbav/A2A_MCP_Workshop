"""Example client demonstrating MCP tool usage."""
import asyncio
import json
from fastmcp import Client

MCP_URL = "http://127.0.0.1:8003/mcp"


async def main():
    async with Client(MCP_URL) as client:
        await client.ping()
        tools = await client.list_tools()

        print("--- Available Tools ---")
        for t in tools:
            tags = t.meta.get('fastmcp', {}).get('tags', []) if t.meta else []
            print(f"  {t.name}  tags={tags}")
        print()

        # Example 1: General activities (no params)
        print("=== Example 1: General activities ===")
        result = await client.call_tool('suggest_activities_for_location_and_date', {})
        print(result.content[0].text)

        # Example 2: Indoor preference
        print("\n=== Example 2: Indoor preference ===")
        result = await client.call_tool('suggest_activities_for_location_and_date',
                                        {'preference': 'indoor'})
        print(result.content[0].text)

        # Example 3: Weather-based activities for Tel Aviv
        print("\n=== Example 3: Weather-based activities (Tel Aviv, today) ===")
        weather_result = await client.call_tool('get_weather_for_location_and_date_string',
                                                {'location_str': 'Tel Aviv, Israel', 'date_str': 'today'})
        weather_data = json.loads(weather_result.content[0].text)

        activity_result = await client.call_tool('suggest_activities_for_location_and_date',
                                                 {'weather_data': weather_data})
        print(activity_result.content[0].text)

        # Example 4: Local tips
        print("\n=== Example 4: Local tips for Paris (cultural) ===")
        tips_result = await client.call_tool('get_local_tips_by_city',
                                             {'city': 'Paris', 'trip_type': 'cultural'})
        print(tips_result.content[0].text)


asyncio.run(main())
