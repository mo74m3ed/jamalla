import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient


async def main():
    client = MultiServerMCPClient({
        "multi_source": {
            "transport": "streamable_http",
            "url": "http://localhost:8000/mcp",
        }
    })
    all_tools = await client.get_tools()
    print(f"Loaded {len(all_tools)} tools:")
    for t in all_tools:
        print(f"  - {t.name}: {t.description}")


asyncio.run(main())
