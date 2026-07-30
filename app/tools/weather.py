"""Weather tool backed by the Open-Meteo API (geocoding + daily forecast)."""

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Open-Meteo returns numeric weather codes; map the common ones to words.
WEATHER_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "foggy", 51: "light drizzle", 61: "light rain",
    63: "rain", 65: "heavy rain", 71: "light snow", 73: "snow",
    75: "heavy snow", 80: "rain showers", 95: "thunderstorm",
}


def get_weather(city: str, days: int = 3) -> dict:
    """Return a daily forecast for the next few days in the given city."""
    geo = requests.get(
        GEOCODE_URL, params={"name": city, "count": 1}, timeout=15
    ).json()

    if not geo.get("results"):
        return {"error": f"Could not find a city named '{city}'."}

    place = geo["results"][0]
    forecast = requests.get(
        FORECAST_URL,
        params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "forecast_days": days,
            "timezone": "auto",
        },
        timeout=15,
    ).json()

    daily = forecast.get("daily", {})
    forecast_days = []
    for i, date in enumerate(daily.get("time", [])):
        code = daily["weather_code"][i]
        forecast_days.append({
            "date": date,
            "condition": WEATHER_CODES.get(code, "unknown"),
            "temp_max_c": daily["temperature_2m_max"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
        })

    return {
        "city": place["name"],
        "country": place.get("country", ""),
        "forecast": forecast_days,
    }
