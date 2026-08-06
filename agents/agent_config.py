import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

MCP_URL = os.getenv("MCP_URL", "http://localhost:8000/mcp")

def get_mcp_client():
    return MultiServerMCPClient({
        "multi_source": {
            "transport": "streamable_http",
            "url": MCP_URL,
        }
    })

AGENT_PREFIXES = {
    "agent1": "weather_",
    "agent2": "country_",
}
