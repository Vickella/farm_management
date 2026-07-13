import json
from collections import defaultdict

import frappe
from frappe import _
import requests

CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
DEFAULT_COUNTRY_CODES = ("ZW", "Zimbabwe")


@frappe.whitelist()
def get_farm_weather(farm_name):
    """
    Fetch current weather and daily forecast for a farm using its GPS coordinates
    or by geocoding its location string.
    Returns current conditions and a 5-day forecast.
    """
    farm = frappe.get_doc("Farm", farm_name)
    farm.check_permission("read")

    lat, lon = _resolve_coordinates(farm)
    if not lat or not lon:
        frappe.throw(
            _(
                f"Could not resolve a weather location for Farm '{farm_name}'. "
                "Set the Farm Location to a recognizable place such as 'Rusape, Zimbabwe' "
                "or add GPS coordinates to the Farm record."
            )
        )

    api_key = _get_api_key()
    units = _get_weather_units()

    current = _fetch_current(lat, lon, api_key, units)
    forecast = _fetch_daily_forecast(lat, lon, api_key, units)

    if not current:
        frappe.throw(
            _(
                "Could not fetch current weather from OpenWeather. Confirm the server can "
                "reach api.openweathermap.org and that the API key in Farm Management "
                "Settings is valid."
            )
        )

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
    for query in _get_location_queries(location_string):
        try:
            response = requests.get(
                GEOCODING_URL,
                params={"q": query, "limit": 1, "appid": api_key},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0].get("lat"), data[0].get("lon")
        except Exception as e:
            _log_weather_error(f"Weather Geocoding Error: {query}", e)
    return None, None


def _get_location_queries(location_string):
    location = (location_string or "").strip()
    if not location:
        return []

    queries = [location]
    has_country_hint = "," in location or any(
        country.lower() in location.lower() for country in DEFAULT_COUNTRY_CODES
    )
    if not has_country_hint:
        queries.extend(f"{location},{country}" for country in DEFAULT_COUNTRY_CODES)
    return list(dict.fromkeys(queries))


def _get_api_key():
    api_key = frappe.conf.get("openweather_api_key")
    if api_key:
        return api_key

    try:
        settings = frappe.get_single("Farm Management Settings")
        if getattr(settings, "weather_api_key", None):
            api_key = settings.get_password("weather_api_key")
    except Exception as e:
        _log_weather_error("Weather Settings Error", e)

    if not api_key:
        frappe.throw(
            _(
                "OpenWeather API key is not configured. Set weather_api_key in site_config.json "
                "or Farm Management Settings."
            )
        )
    return api_key


def _get_weather_units():
    units = frappe.db.get_single_value("Farm Management Settings", "weather_units") or "metric"
    units = units.lower()
    return units if units in {"metric", "imperial"} else "metric"


def _get_units(units):
    unit_symbol = "C" if units == "metric" else ("F" if units == "imperial" else "K")
    wind_unit = "m/s" if units != "imperial" else "mph"
    return unit_symbol, wind_unit


def _log_weather_error(title, exc):
    message = frappe.get_traceback() or str(exc)
    frappe.log_error(title=title[:140], message=message)


def _fetch_current(lat, lon, api_key, units):
    try:
        response = requests.get(
            CURRENT_WEATHER_URL,
            params={"lat": lat, "lon": lon, "appid": api_key, "units": units},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        weather = (data.get("weather") or [{}])[0]
        main = data.get("main") or {}
        wind = data.get("wind") or {}
        clouds = data.get("clouds") or {}
        sys = data.get("sys") or {}
        unit_symbol, wind_unit = _get_units(units)
        return {
            "temperature": main.get("temp"),
            "feels_like": main.get("feels_like"),
            "humidity": main.get("humidity"),
            "pressure": main.get("pressure"),
            "wind_speed": wind.get("speed"),
            "wind_deg": wind.get("deg"),
            "clouds": clouds.get("all"),
            "visibility": data.get("visibility"),
            "uvi": None,
            "dew_point": None,
            "description": weather.get("description", "").title(),
            "icon": weather.get("icon"),
            "icon_url": f"https://openweathermap.org/img/wn/{weather.get('icon', '01d')}@2x.png",
            "sunrise": sys.get("sunrise"),
            "sunset": sys.get("sunset"),
            "unit_symbol": unit_symbol,
            "wind_unit": wind_unit,
        }
    except Exception as e:
        _log_weather_error("Weather Current Fetch Error", e)
        return {}


def _fetch_daily_forecast(lat, lon, api_key, units):
    try:
        response = requests.get(
            FORECAST_URL,
            params={"lat": lat, "lon": lon, "appid": api_key, "units": units},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        grouped = defaultdict(list)
        for record in data.get("list", []):
            dt_txt = record.get("dt_txt") or ""
            if dt_txt:
                grouped[dt_txt.split(" ")[0]].append(record)

        days = []
        unit_symbol, _wind_unit = _get_units(units)
        for _date_key in sorted(grouped)[:5]:
            records = grouped[_date_key]
            representative = records[len(records) // 2]
            weather = (representative.get("weather") or [{}])[0]
            temps = [
                record.get("main", {}).get("temp")
                for record in records
                if record.get("main", {}).get("temp") is not None
            ]
            pops = [record.get("pop", 0) for record in records]
            main = representative.get("main") or {}
            wind = representative.get("wind") or {}
            clouds = representative.get("clouds") or {}
            days.append(
                {
                    "dt": representative.get("dt"),
                    "temp_day": main.get("temp"),
                    "temp_min": min(temps) if temps else None,
                    "temp_max": max(temps) if temps else None,
                    "temp_night": records[-1].get("main", {}).get("temp"),
                    "humidity": main.get("humidity"),
                    "wind_speed": wind.get("speed"),
                    "pop": round(max(pops or [0]) * 100),
                    "clouds": clouds.get("all"),
                    "uvi": None,
                    "description": weather.get("description", "").title(),
                    "icon": weather.get("icon"),
                    "icon_url": f"https://openweathermap.org/img/wn/{weather.get('icon', '01d')}@2x.png",
                    "unit_symbol": unit_symbol,
                }
            )
        return days
    except Exception as e:
        _log_weather_error("Weather Forecast Fetch Error", e)
        return []


@frappe.whitelist()
def test_weather_location(location="Rusape, Zimbabwe"):
    """Test OpenWeather lookup without needing a Farm document."""
    frappe.only_for(("System Manager", "Farm Manager"))
    lat, lon = _geocode_location(location)
    if not lat or not lon:
        frappe.throw(_(f"Could not geocode location '{location}'."))

    api_key = _get_api_key()
    units = _get_weather_units()
    current = _fetch_current(lat, lon, api_key, units)
    forecast = _fetch_daily_forecast(lat, lon, api_key, units)
    if not current:
        frappe.throw(_(f"OpenWeather did not return current weather for '{location}'."))

    return {
        "location": location,
        "lat": lat,
        "lon": lon,
        "units": units,
        "current": current,
        "forecast_count": len(forecast),
        "forecast": forecast,
    }


@frappe.whitelist()
def get_farm_list_for_weather():
    """Return list of farms with location data for weather dashboard."""
    farms = frappe.get_list(
        "Farm",
        filters={"operational_status": "Active"},
        fields=["name", "farm_name", "location", "gps_coordinates"],
    )
    return farms
