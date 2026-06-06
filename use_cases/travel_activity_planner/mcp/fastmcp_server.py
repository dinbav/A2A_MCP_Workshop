import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP
from mcp_utils import parse_date_range, get_weather_by_location, get_temperature_range
from datetime import datetime

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

if not os.getenv("NO_PROXY"):
    logging.warning("NO_PROXY not set")

logger = logging.getLogger("mcp.tools")

mcp = FastMCP()

# ---------------------------------------------------------------------------
# Static local-tips data loaded from JSON
# ---------------------------------------------------------------------------
_DATA_FILE = Path(__file__).parent / "data" / "local_tips.json"
with open(_DATA_FILE, encoding="utf-8") as _f:
    LOCAL_TIPS: dict = json.load(_f)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool
async def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}!"


@mcp.tool(tags={"weather"})
def get_weather_for_location_and_date_string(
        location_str: str,
        date_str: str = "today",
) -> dict:
    """
    Get weather for a location using a natural-language date string.

    Args:
        location_str: e.g. "Tel Aviv, Israel" or "Paris"
        date_str: e.g. "today", "this week", "6-9 december"

    Returns:
        Dict with location info, date range, weather data, and temperature range.
    """
    date_range = parse_date_range(date_str)
    start = datetime.strptime(date_range["start_date"], "%d-%m-%Y").strftime("%Y-%m-%d")
    end   = datetime.strptime(date_range["end_date"],   "%d-%m-%Y").strftime("%Y-%m-%d")

    result = get_weather_by_location(location_str, start, end)
    min_t, max_t = get_temperature_range(result["weather"])
    result["temperature_range"] = {"min_celsius": min_t, "max_celsius": max_t}
    return result


@mcp.tool(tags={"weather", "activities"})
def suggest_activities_for_location_and_date(
        weather_data: dict = None,
        preference: str = None,
) -> dict:
    """
    Suggest activities based on weather conditions or user preference.

    Args:
        weather_data: Pre-computed weather dict from get_weather_for_location_and_date_string (optional)
        preference: "indoor", "outdoor", or None for both

    Returns:
        Dict with suggested activities and optional weather context.
    """
    # No weather data — return general or preference-based suggestions
    if weather_data is None:
        if preference is None:
            return {
                "message": "General activity suggestions for any weather",
                "suggested_activities": [
                    "Visit a cafe or restaurant",
                    "Go to a museum or art gallery",
                    "Shopping (malls or local stores)",
                    "Watch a movie at cinema or home",
                    "Try a new hobby or workshop",
                    "Meet friends for coffee or meal",
                    "Read a book at a library or bookstore",
                    "Indoor sports (bowling, climbing, swimming)",
                ],
                "note": "Provide weather data or specify indoor/outdoor for personalised suggestions.",
            }
        preference = preference.lower()
        if preference == "indoor":
            return {
                "message": "Indoor activity suggestions",
                "suggested_activities": [
                    "Visit museums or art galleries",
                    "Go to the cinema",
                    "Indoor shopping or mall visit",
                    "Try a new restaurant or cafe",
                    "Bowling or indoor sports",
                    "Spa or wellness center",
                    "Indoor climbing or fitness",
                    "Board game cafe or arcade",
                ],
            }
        if preference == "outdoor":
            return {
                "message": "Outdoor activity suggestions",
                "suggested_activities": [
                    "Hiking or nature walks",
                    "Cycling tour",
                    "Outdoor sports",
                    "Picnic in the park",
                    "Photography expedition",
                    "Visit botanical gardens or parks",
                    "Outdoor dining",
                    "Beach or water activities",
                ],
                "note": "Provide weather data for weather-specific recommendations.",
            }
        raise ValueError(f"Invalid preference '{preference}'. Use 'indoor' or 'outdoor'.")

    # Weather data provided — generate weather-aware suggestions
    min_temp = weather_data["temperature_range"]["min_celsius"]
    max_temp = weather_data["temperature_range"]["max_celsius"]
    avg_temp = (min_temp + max_temp) / 2
    conditions = weather_data["conditions_summary"]["unique_weather_descriptions"]

    has_rain        = any("rain" in d.lower() or "drizzle" in d.lower() for d in conditions)
    has_snow        = any("snow" in d.lower() for d in conditions)
    has_thunderstorm = any("thunderstorm" in d.lower() for d in conditions)

    indoor, outdoor = [], []

    if has_thunderstorm:
        indoor += ["Stay indoors - thunderstorm expected", "Watch movies at home",
                   "Read a book with a hot beverage", "Work on indoor hobbies"]
    elif avg_temp >= 35:
        indoor  += ["Air-conditioned museum visit", "Shopping mall", "Cinema", "Indoor pool"]
        outdoor += ["Early morning walk (before 9 AM)", "Evening stroll (after 7 PM)"]
    elif avg_temp >= 30:
        indoor  += ["Art gallery", "Indoor climbing", "Spa or wellness center"]
        outdoor += ["Beach or pool swimming", "Water sports", "Early morning or evening activities"]
    elif has_rain:
        indoor += ["Museums or art galleries", "Cinema", "Indoor shopping",
                   "New restaurant or cafe", "Bowling or indoor sports"]
    elif has_snow:
        if avg_temp < -5:
            indoor  += ["Indoor ice skating", "Cozy cafe with hot chocolate", "Winter market"]
            outdoor += ["Build a snowman", "Winter photography"]
        else:
            outdoor += ["Skiing or snowboarding", "Winter hiking", "Snow photography", "Sledding"]
    elif avg_temp < 5:
        indoor  += ["Cozy bookstore", "Bowling or climbing", "Hot springs or spa", "Museum tour"]
        outdoor += ["Brisk walk with warm clothing", "Short winter hike"]
    elif avg_temp < 15:
        outdoor += ["Hiking", "Cycling", "Outdoor photography", "Botanical gardens"]
    elif avg_temp < 25:
        outdoor += ["Picnic in the park", "Outdoor sports", "City walking tour",
                    "Outdoor dining", "Jogging"]
    else:
        outdoor += ["Beach day or swimming", "Water sports", "Early morning or evening activities",
                    "Water parks or pools"]

    if preference and preference.lower() == "indoor":
        suggested = indoor
    elif preference and preference.lower() == "outdoor":
        suggested = outdoor
    else:
        suggested = outdoor + indoor

    heat_warning = None
    if max_temp >= 35:
        heat_warning = "Extreme heat warning! Limit outdoor exposure and stay hydrated."
    elif max_temp >= 30:
        heat_warning = "High temperature alert. Take precautions and drink plenty of water."

    return {
        "location": weather_data["location"]["resolved_name"],
        "date_range": weather_data["date_range"],
        "temperature_range": {"min": min_temp, "max": max_temp, "average": round(avg_temp, 1)},
        "weather_conditions": conditions,
        "suggested_activities": suggested,
        "activity_breakdown": {"indoor_options": len(indoor), "outdoor_options": len(outdoor)},
        "heat_warning": heat_warning,
        "weather_summary": f"Temperature {min_temp}–{max_temp}°C with {', '.join(conditions).lower()}",
    }


@mcp.tool(tags={"local_tips"})
def get_local_tips_by_city(city: str, trip_type: str = "general") -> dict:
    """
    Get local travel tips for a city and trip type.

    Args:
        city: e.g. "Tel Aviv", "Paris", "Barcelona", "Rome", "London"
        trip_type: "general", "family", "beach", "cultural", "adventure", or "romantic"

    Returns:
        Dict with transportation, food, safety, recommended hours, local highlights,
        and trip-type-specific tips.
    """
    city_key = city.lower().strip()
    trip_type_key = trip_type.lower().strip()

    if city_key not in LOCAL_TIPS:
        return {
            "city": city,
            "trip_type": trip_type,
            "found": False,
            "message": f"No tips found for '{city}'. Available cities: {', '.join(LOCAL_TIPS)}.",
        }

    tips = LOCAL_TIPS[city_key]
    valid_types = {"general", "family", "beach", "cultural", "adventure", "romantic"}
    if trip_type_key not in valid_types:
        trip_type_key = "general"

    result = {
        "city": city.title(),
        "trip_type": trip_type_key,
        "found": True,
        "transportation":     tips["transportation"],
        "food":               tips["food"],
        "safety":             tips["safety"],
        "recommended_hours":  tips["recommended_hours"],
        "local_highlights":   tips["local_highlights"],
        "trip_type_tips":     tips.get(trip_type_key) if trip_type_key != "general" else None,
    }
    return result


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8003, path="/mcp", log_level="info")
