import os
import httpx
from fastmcp import FastMCP

mcp = FastMCP("multi-source-server")

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


# ---------- API 1: Open-Meteo (weather) ----------

@mcp.tool()
async def weather_geocode(city: str) -> dict:
    """Find latitude/longitude for a city name."""
    async with httpx.AsyncClient() as client:
        r = await client.get(GEOCODE_URL, params={"name": city, "count": 1})
        r.raise_for_status()
        data = r.json()
    if not data.get("results"):
        return {"error": f"No location found for '{city}'"}
    top = data["results"][0]
    return {
        "name": top["name"],
        "country": top.get("country"),
        "latitude": top["latitude"],
        "longitude": top["longitude"],
    }


@mcp.tool()
async def weather_current(latitude: float, longitude: float) -> dict:
    """Get current weather for a latitude/longitude."""
    async with httpx.AsyncClient() as client:
        r = await client.get(FORECAST_URL, params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,wind_speed_10m,relative_humidity_2m",
        })
        r.raise_for_status()
        return r.json().get("current", {})


# ---------- API 2: CountriesNow ----------
# restcountries.com/v3.1 is deprecated; countriesnow.space is the replacement.

COUNTRIES_URL = "https://countriesnow.space/api/v0.1"


async def _fetch_info_field(field: str) -> list[dict]:
    """Fetch all countries with one selected field from the info endpoint."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        r = await client.get(f"{COUNTRIES_URL}/countries/info", params={"returns": field})
        r.raise_for_status()
        return r.json().get("data", [])


def _find_country(records: list[dict], name: str) -> dict | None:
    name_lower = name.lower()
    return next((r for r in records if r.get("name", "").lower() == name_lower), None)


@mcp.tool()
async def country_capital(name: str) -> dict:
    """Get the capital city of a country."""
    records = await _fetch_info_field("capital")
    c = _find_country(records, name)
    if not c:
        return {"error": f"No country found for '{name}'"}
    return {"country": c["name"], "capital": c.get("capital")}


@mcp.tool()
async def country_currency(name: str) -> dict:
    """Get the currency code used in a country."""
    records = await _fetch_info_field("currency")
    c = _find_country(records, name)
    if not c:
        return {"error": f"No country found for '{name}'"}
    return {"country": c["name"], "currency": c.get("currency")}


@mcp.tool()
async def country_population(name: str) -> dict:
    """Get the most recent population figure for a country."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        r = await client.get(f"{COUNTRIES_URL}/countries/population/q", params={"country": name})
        if r.status_code == 404:
            return {"error": f"No country found for '{name}'"}
        r.raise_for_status()
        counts = r.json().get("data", {}).get("populationCounts", [])
    if not counts:
        return {"error": "No population data available"}
    latest = max(counts, key=lambda x: x["year"])
    return {"country": name, "year": latest["year"], "population": latest["value"]}


@mcp.tool()
async def country_dial_code(name: str) -> dict:
    """Get the international dialling code for a country."""
    records = await _fetch_info_field("dialCode")
    c = _find_country(records, name)
    if not c:
        return {"error": f"No country found for '{name}'"}
    return {"country": c["name"], "dial_code": c.get("dialCode")}


@mcp.tool()
async def country_flag(name: str) -> dict:
    """Get the Unicode flag emoji for a country."""
    records = await _fetch_info_field("unicodeFlag")
    c = _find_country(records, name)
    if not c:
        return {"error": f"No country found for '{name}'"}
    return {"country": c["name"], "flag": c.get("unicodeFlag")}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
