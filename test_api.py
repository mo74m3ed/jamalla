import asyncio, httpx

BASE = "https://countriesnow.space/api/v0.1"

async def main():
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as c:
        # capital
        r = await c.get(f"{BASE}/countries/info", params={"returns": "capital"})
        data = r.json().get("data", [])
        japan = next((x for x in data if x.get("name", "").lower() == "japan"), None)
        print("capital:", japan)

        # currency
        r = await c.get(f"{BASE}/countries/info", params={"returns": "currency"})
        data = r.json().get("data", [])
        japan = next((x for x in data if x.get("name", "").lower() == "japan"), None)
        print("currency:", japan)

        # population
        r = await c.get(f"{BASE}/countries/population/q", params={"country": "Japan"})
        counts = r.json().get("data", {}).get("populationCounts", [])
        latest = max(counts, key=lambda x: x["year"]) if counts else None
        print("population:", latest)

asyncio.run(main())
