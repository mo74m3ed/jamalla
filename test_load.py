import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient


async def main():
    client_config = {
        "multi_source": {
            "transport": "streamable_http",
            "url": "http://localhost:8000/mcp",
        }
    }

    async with MultiServerMCPClient(client_config) as client:
        all_tools = await client.get_tools()
        print(f"Loaded {len(all_tools)} tools:")
        for t in all_tools:
            print(f"  - {t.name}: {t.description}")


if __name__ == "__main__":
    asyncio.run(main())
