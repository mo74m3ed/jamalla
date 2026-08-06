import asyncio, httpx

BASE = "https://countriesnow.space/api/v0.1"

async def main():
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as c:
        # capital
        r = await c.post(f"{BASE}/countries/info", json={"returns": "capital"})
        r.raise_for_status()
        data = r.json().get("data", [])
        japan = next((x for x in data if x.get("name", "").lower() == "japan"), None)
        print("capital:", japan)

        # currency
        r = await c.post(f"{BASE}/countries/info", json={"returns": "currency"})
        r.raise_for_status()
        data = r.json().get("data", [])
        japan = next((x for x in data if x.get("name", "").lower() == "japan"), None)
        print("currency:", japan)

        # population
        r = await c.post(f"{BASE}/countries/population/q", json={"country": "Japan"})
        r.raise_for_status()
        counts = r.json().get("data", {}).get("populationCounts", [])
        latest = max(counts, key=lambda x: x["year"]) if counts else None
        print("population:", latest)

if __name__ == "__main__":
    asyncio.run(main())
