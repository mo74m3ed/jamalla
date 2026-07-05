import asyncio
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from agents.agent_config import get_mcp_client, AGENT_PREFIXES


def filter_tools(all_tools, prefix):
    """The whole mechanism: keep only tools whose name starts with prefix."""
    return [t for t in all_tools if t.name.startswith(prefix)]


async def build_agents():
    client = get_mcp_client()
    all_tools = await client.get_tools()          # full catalog — all 7

    agent1_tools = filter_tools(all_tools, AGENT_PREFIXES["agent1"])   # weather
    agent2_tools = filter_tools(all_tools, AGENT_PREFIXES["agent2"])   # country

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    agent1 = create_agent(llm, agent1_tools)   # bound to weather only
    agent2 = create_agent(llm, agent2_tools)   # bound to country only

    return agent1, agent2, agent1_tools, agent2_tools


async def main():
    a1, a2, t1, t2 = await build_agents()

    # PROOF: each agent sees only its subset
    print("Agent 1 tools:", [t.name for t in t1])
    print("Agent 2 tools:", [t.name for t in t2])

    # Ask agent 1 something it CAN do
    r = await a1.ainvoke({"messages": [("user", "What's the weather in Kuala Lumpur?")]})
    print("\nAgent 1 weather answer:\n", r["messages"][-1].content)

    # Ask agent 1 something only agent 2 has tools for
    r = await a1.ainvoke({"messages": [("user", "What's the capital of Japan?")]})
    print("\nAgent 1 asked a country question (no country tools):\n", r["messages"][-1].content)

    r = await a1.ainvoke({"messages": [("user", "What is the exact current population of Japan?")]})
    print("\nAgent 1 asked a country question (no country tools):\n", r["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
