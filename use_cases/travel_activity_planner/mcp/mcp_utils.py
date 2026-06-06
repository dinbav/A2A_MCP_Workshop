from geopy.geocoders import Nominatim
from datetime import date, timedelta, datetime
from dateutil.parser import parse
import re
import requests

def parse_date_range(date_str: str) -> dict[str, str]:
    """
    Parses a string to determine a start and end date.

    Args:
        date_str: A string like "today", "this week", "next weekend",
                  "11 nov", or "6-9 december".

    Returns:
        A dictionary with "start_date" and "end_date" in "DD-MM-YYYY" format.
    """
    today = date.today()
    date_str = date_str.lower().strip()
    output_format = "%d-%m-%Y"

    start_date = None
    end_date = None

    if date_str == "today":
        start_date = end_date = today
    elif date_str == "this week":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif date_str == "next week":
        start_date = today + timedelta(days=(7 - today.weekday()))
        end_date = start_date + timedelta(days=6)
    elif date_str == "this weekend":
        # Saturday of the current week
        start_date = today - timedelta(days=today.weekday()) + timedelta(days=5)
        end_date = start_date + timedelta(days=1)
    elif date_str == "next weekend":
        # Saturday of the next week
        start_date = today + timedelta(days=(7 - today.weekday() + 5))
        end_date = start_date + timedelta(days=1)
    else:
        # Try to parse ranges like "6-9 december" or "6 to 9 dec"
        range_match = re.match(r"(\d{1,2})\s*(?:-|to)\s*(\d{1,2})\s+([a-z]+)", date_str)
        if range_match:
            day_start, day_end, month_str = range_match.groups()
            try:
                # Use dateutil.parser to handle month name
                start_dt = parse(f"{day_start} {month_str} {today.year}").date()
                end_dt = parse(f"{day_end} {month_str} {today.year}").date()

                # If the date has passed this year, use next year
                if end_dt < today:
                    start_date = start_dt.replace(year=today.year + 1)
                    end_date = end_dt.replace(year=today.year + 1)
                else:
                    start_date = start_dt
                    end_date = end_dt
            except ValueError:
                pass  # Fallback to single date parsing

        # Fallback for single dates like "11 nov"
        if not start_date:
            try:
                # parse can return a datetime or a date object
                parsed_val = parse(date_str, default=datetime(today.year, 1, 1))
                dt = parsed_val.date() if isinstance(parsed_val, datetime) else parsed_val

                # If no year was specified and the date is in the past, assume next year
                if dt < today and str(today.year) not in date_str:
                     start_date = end_date = dt.replace(year=today.year + 1)
                else:
                     start_date = end_date = dt
            except ValueError:
                raise ValueError(f"Could not parse the date string: {date_str}")

    if not start_date or not end_date:
        raise ValueError(f"Could not parse the date string: {date_str}")

    return {
        "start_date": start_date.strftime(output_format),
        "end_date": end_date.strftime(output_format)
    }

def parse_date(d):
    """
    Accepts:
      - datetime.date
      - datetime.datetime
      - "YYYY-MM-DD" string
    Returns a datetime.date
    """
    if isinstance(d, date) and not isinstance(d, datetime):
        return d
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, str):
        return datetime.strptime(d, "%Y-%m-%d").date()
    raise ValueError("Unsupported date format. Use date object or 'YYYY-MM-DD' string.")

def get_temperature_range(weather_json):
    """
    Receives the 'weather' dict from get_weather_by_city().
    Returns (min_temp, max_temp).
    """
    temps = weather_json.get("hourly", {}).get("temperature_2m", [])

    if not temps:
        return None, None

    return min(temps), max(temps)

WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog and depositing rime fog",
    48: "Fog and depositing rime fog",
    51: "Drizzle: Light intensity",
    53: "Drizzle: Moderate intensity",
    55: "Drizzle: Dense intensity",
    56: "Freezing Drizzle: Light intensity",
    57: "Freezing Drizzle: Dense intensity",
    61: "Rain: Slight intensity",
    63: "Rain: Moderate intensity",
    65: "Rain: Heavy intensity",
    66: "Freezing Rain: Light intensity",
    67: "Freezing Rain: Heavy intensity",
    71: "Snow fall: Slight intensity",
    73: "Snow fall: Moderate intensity",
    75: "Snow fall: Heavy intensity",
    77: "Snow grains",
    80: "Rain showers: Slight intensity",
    81: "Rain showers: Moderate intensity",
    82: "Rain showers: Violent intensity",
    85: "Snow showers: Slight intensity",
    86: "Snow showers: Heavy intensity",
    95: "Thunderstorm: Slight or moderate",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

def summarize_conditions(weather_json: dict) -> dict:
    """Return unique weather descriptions and per-hour conditions from an Open-Meteo response."""
    hourly = weather_json.get("hourly", {})
    times    = hourly.get("time", [])        or []
    precip   = hourly.get("precipitation", []) or []
    snowfall = hourly.get("snowfall", [])    or []
    codes    = hourly.get("weathercode", []) or []

    hourly_conditions = [
        {
            "time":        ts,
            "code":        codes[i] if i < len(codes) else None,
            "description": WEATHER_CODE_MAP.get(codes[i] if i < len(codes) else None, "Unknown"),
            "precip_mm":   precip[i]   if i < len(precip)   else 0,
            "snowfall_cm": snowfall[i] if i < len(snowfall) else 0,
        }
        for i, ts in enumerate(times)
    ]

    return {
        "unique_weather_descriptions": sorted({hc["description"] for hc in hourly_conditions}),
        "hourly_conditions": hourly_conditions,
    }

def get_weather_by_location(
    location_str: str,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
):
    geolocator = Nominatim(user_agent="weather_lookup_example")
    location = geolocator.geocode(location_str)
    if not location:
        raise ValueError(f"Could not find location for '{location_str}'")

    lat, lon = location.latitude, location.longitude

    today = date.today()
    if start_date is None:
        start_date = today
    if end_date is None:
        end_date = start_date

    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        f"&start_date={start_date.isoformat()}"
        f"&end_date={end_date.isoformat()}"
        "&hourly=temperature_2m,relativehumidity_2m,precipitation,snowfall,weathercode"
        "&timezone=auto"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    conditions = summarize_conditions(data)

    return {
        "location": {
            "input_location": location_str,
            "resolved_name": location.address,
            "latitude": lat,
            "longitude": lon,
        },
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "url": url,
        "weather": data,
        "conditions_summary": conditions,
    }