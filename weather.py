import requests
import json
import time
from datetime import datetime, timezone
import os


def update_weather():
    latitude = 40.69225
    longitude = -73.91458

    url = "https://api.open-meteo.com/v1/gfs"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "snowfall",
            "wind_speed_10m",
            "cloud_cover"
        ],

        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "snowfall_sum",
            "sunrise",
            "sunset",
            "moon_phase"
        ],

        "forecast_hours": 32,
        "forecast_days": 2,
        "timezone": "America/New_York",

        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    weather = response.json()
    weather["fetched_at"] = datetime.now(timezone.utc).isoformat()
    with open("weather.json", "w") as file:
        json.dump(weather, file)


REFRESH_SECONDS = 6 * 60 * 60


def get_cached_fetch_time():
    try:
        with open("weather.json", "r") as file:
            weather = json.load(file)

        return datetime.fromisoformat(weather["fetched_at"])

    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError):
        return None


def main():

    while True:
        fetched_at = get_cached_fetch_time()
        if fetched_at is not None:
            now = datetime.now(timezone.utc)
            age = (now - fetched_at).total_seconds()

            if age < REFRESH_SECONDS:
                time_remaining = REFRESH_SECONDS - age
                time.sleep(time_remaining)
                continue

        try:
            update_weather()
        except requests.RequestException as error:
            print(f"Weather update failed: {error}")
            time.sleep(60)