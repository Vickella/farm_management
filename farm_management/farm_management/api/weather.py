import json

import frappe
from frappe import _
import requests


@frappe.whitelist()
def get_farm_weather(farm_name):
    """
    Fetch current weather and daily forecast for a farm using its GPS coordinates
    or by geocoding its location string.
    Returns current conditions and 7-day daily forecast.
    """
    farm = frappe.get_doc("Farm", farm_name)

    lat, lon = _resolve_coordinates(farm)
    if not lat or not lon:
        frappe.throw(
            _(
                f"Farm '{farm_name}' has no GPS coordinates or location set. "
                "Please add GPS coordinates or a location name to the Farm record."
            )
        )

    api_key = _get_api_key()
    units = frappe.db.get_single_value("Farm Management Settings", "weather_units") or "metric"

    current = _fetch_current(lat, lon, api_key, units)
    forecast = _fetch_daily_forecast(lat, lon, api_key, units)

    return {
        "farm": farm_name,
        "location": farm.location or f"{lat}, {lon}",
        "lat": lat,
        "lon": lon,
        "units": units,
        "current": current,
        "forecast": forecast,
    }


def _resolve_coordinates(farm):
    """Extract lat/lon from farm GPS field or geocode the location string."""
    if farm.gps_coordinates:
        try:
            geo = json.loads(farm.gps_coordinates)
            features = geo.get("features", [])
            if features:
                coords = features[0].get("geometry", {}).get("coordinates", [])
                if len(coords) >= 2:
                    return coords[1], coords[0]
        except Exception:
            pass

    if farm.location:
        return _geocode_location(farm.location)

    return None, None


def _geocode_location(location_string):
    """Use OpenWeather Geocoding API to resolve location string to coordinates."""
    api_key = _get_api_key()
    try:
        response = requests.get(
            "https://api.openweathermap.org/geo/1.0/direct",
            params={"q": location_string, "limit": 1, "appid": api_key},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0].get("lat"), data[0].get("lon")
    except Exception as e:
        frappe.log_error(str(e), "Weather Geocoding Error")
    return None, None


def _get_api_key():
    api_key = frappe.db.get_single_value("Farm Management Settings", "weather_api_key")
    if not api_key:
        api_key = "bfd7d15e4d142c6c9e49e6d317bbca00"
    return api_key


def _get_units(units):
    unit_symbol = "C" if units == "metric" else ("F" if units == "imperial" else "K")
    wind_unit = "m/s" if units != "imperial" else "mph"
    return unit_symbol, wind_unit


def _fetch_current(lat, lon, api_key, units):
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/4.0/onecall/current",
            params={"lat": lat, "lon": lon, "appid": api_key, "units": units},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        record = data.get("data", [{}])[0]
        weather = record.get("weather", [{}])[0]
        unit_symbol, wind_unit = _get_units(units)
        return {
            "temperature": record.get("temp"),
            "feels_like": record.get("feels_like"),
            "humidity": record.get("humidity"),
            "pressure": record.get("pressure"),
            "wind_speed": record.get("wind_speed"),
            "wind_deg": record.get("wind_deg"),
            "clouds": record.get("clouds"),
            "visibility": record.get("visibility"),
            "uvi": record.get("uvi"),
            "dew_point": record.get("dew_point"),
            "description": weather.get("description", "").title(),
            "icon": weather.get("icon"),
            "icon_url": f"https://openweathermap.org/img/wn/{weather.get('icon', '01d')}@2x.png",
            "sunrise": record.get("sunrise"),
            "sunset": record.get("sunset"),
            "unit_symbol": unit_symbol,
            "wind_unit": wind_unit,
        }
    except Exception as e:
        frappe.log_error(str(e), "Weather Current Fetch Error")
        return {}


def _fetch_daily_forecast(lat, lon, api_key, units):
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/4.0/onecall/timeline/1day",
            params={"lat": lat, "lon": lon, "appid": api_key, "units": units, "cnt": 7},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        days = []
        unit_symbol, _wind_unit = _get_units(units)
        for record in data.get("data", []):
            weather = record.get("weather", [{}])[0]
            temp = record.get("temp", {})
            days.append(
                {
                    "dt": record.get("dt"),
                    "temp_day": temp.get("day"),
                    "temp_min": temp.get("min"),
                    "temp_max": temp.get("max"),
                    "temp_night": temp.get("night"),
                    "humidity": record.get("humidity"),
                    "wind_speed": record.get("wind_speed"),
                    "pop": round(record.get("pop", 0) * 100),
                    "clouds": record.get("clouds"),
                    "uvi": record.get("uvi"),
                    "description": weather.get("description", "").title(),
                    "icon": weather.get("icon"),
                    "icon_url": f"https://openweathermap.org/img/wn/{weather.get('icon', '01d')}@2x.png",
                    "unit_symbol": unit_symbol,
                }
            )
        return days
    except Exception as e:
        frappe.log_error(str(e), "Weather Forecast Fetch Error")
        return []


@frappe.whitelist()
def get_farm_list_for_weather():
    """Return list of farms with location data for weather dashboard."""
    farms = frappe.get_all(
        "Farm",
        filters={"operational_status": "Active"},
        fields=["name", "farm_name", "location", "gps_coordinates"],
    )
    return farms

