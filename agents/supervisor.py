import asyncio
from typing import Literal
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from agents.graph import build_agents


class Route(BaseModel):
    """Which specialist agent should handle the user's query."""
    destination: Literal["weather", "country"] = Field(
        description="'weather' for weather/forecast/temperature questions; "
                    "'country' for questions about countries, capitals, population, currency, languages."
    )


async def build_supervisor():
    agent1, agent2, _, _ = await build_agents()
    router_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(Route)

    async def route_and_run(user_query: str) -> str:
        decision = await router_llm.ainvoke(
            f"Route this user query to the correct specialist:\n\n{user_query}"
        )
        if decision.destination == "weather":
            agent, label = agent1, "Agent 1 (weather)"
        else:
            agent, label = agent2, "Agent 2 (country)"

        result = await agent.ainvoke({"messages": [("user", user_query)]})
        answer = result["messages"][-1].content
        return f"[routed to {label}]\n{answer}"

    return route_and_run


async def main():
    supervisor = await build_supervisor()
    for q in [
        "What's the weather in Tokyo?",
        "What currency does Brazil use?",
        "How hot is it in Dubai right now?",
        "What's the dialing code for India?",
    ]:
        print("\nUSER:", q)
        print(await supervisor(q))


if __name__ == "__main__":
    asyncio.run(main())
