# Multi-Agent MCP Demo

A working demonstration of **one MCP server exposing many tools**, with **multiple LangGraph agents each bound to a filtered subset** of those tools, and a **supervisor** that routes each user question to the right agent, all deployed to the cloud with a browser chat UI.

> **The core idea:** a single MCP server hands over its *entire* tool catalog to any client. Filtering, deciding *which* agent sees *which* tools, happens on the client side, in one line:
> ```python
> agent_tools = [t for t in all_tools if t.name.startswith(prefix)]
> ```

## 🔗 Live URLs

| Service | URL |
|---|---|
| 💬 **Chat UI (agents)** | https://multi-agent-mcp-agents.onrender.com |
| 🛠️ **MCP server** | https://multi-agent-mcp.onrender.com/mcp |
| ❤️ MCP health check | https://multi-agent-mcp.onrender.com/health |
| 📦 Source | https://github.com/jamalla/multi-agent-mcp |

> ⏳ **Cold start:** both services run on Render's free tier and sleep after ~15 min idle. The first request after a nap can take 30 to 50s to wake the container, then the second is fast. The chat UI shows a "may take ~40s" hint while waiting.

## Architecture

```
                        Browser (chat UI)
                                │
                                ▼
        ┌───────────────────────────────────────────────┐
        │   FastAPI agent service  (Render service #2)    │
        │   ┌─────────────────────────────────────────┐  │
        │   │           LangGraph Supervisor          │  │
        │   │  (LLM router → picks the right agent)    │  │
        │   └──────────┬──────────┬──────────┬────────┘  │
        │       ┌──────▼─────┐ ┌──▼───────┐ ┌▼─────────┐ │
        │       │  Agent 1    │ │ Agent 2   │ │ Agent 3  │ │
        │       │ weather_*   │ │ country_* │ │worldcup_*│ │
        │       │ (2 tools)   │ │ (5 tools) │ │(5 tools) │ │
        │       └──────┬─────┘ └──┬───────┘ └┬─────────┘ │
        └──────────────┼──────────┼──────────┼───────────┘
                       └──────────┼──────────┘
                     filtered subsets of one catalog
                                  │  (streamable-HTTP / MCP)
                     ┌────────────▼────────────┐
                     │      MCP Server         │  (Render service #1)
                     │   12 tools, unfiltered  │
                     └────┬──────────┬─────────┬┘
                          │          │         │
                 ┌────────▼─┐ ┌──────▼────┐ ┌──▼──────────────┐
                 │Open-Meteo│ │CountriesNow│ │football-data.org│
                 │(weather) │ │ (country)  │ │  (World Cup)    │
                 └──────────┘ └────────────┘ └─────────────────┘
```

**Two clean separations:**
- The **supervisor** decides *who* handles a query (routing).
- The **prefix filter** decides *what* each agent can do (tool scoping).

## The tools (12 total)

The naming convention (`weather_` / `country_` / `worldcup_` prefixes) is what makes per-agent filtering a one-liner.

| Prefix | Tool | Source API |
|---|---|---|
| `weather_` | `weather_geocode` | Open-Meteo (geocoding) |
| `weather_` | `weather_current` | Open-Meteo (forecast) |
| `country_` | `country_capital` | CountriesNow |
| `country_` | `country_currency` | CountriesNow |
| `country_` | `country_population` | CountriesNow |
| `country_` | `country_dial_code` | CountriesNow |
| `country_` | `country_flag` | CountriesNow |
| `worldcup_` | `worldcup_matches_upcoming` | football-data.org |
| `worldcup_` | `worldcup_match_results` | football-data.org |
| `worldcup_` | `worldcup_group_standings` | football-data.org |
| `worldcup_` | `worldcup_teams` | football-data.org |
| `worldcup_` | `worldcup_team_form` | football-data.org |

Open-Meteo and CountriesNow are free and need **no key**. football-data.org needs a free API key (`FOOTBALL_API_KEY`). "Predictions" are the World Cup agent reasoning over standings and recent form it fetches with these tools, not a separate prediction API.

## Observability: see the route & tool steps

Every answer returns a structured trace, rendered under each message in the UI (expandable):

```
🌤️ routed to Agent 1 (weather)   ▸ Show reasoning (4 steps)
   🔧 weather_geocode({"city":"Tokyo"})
   📥 weather_geocode → {"name":"Tokyo","country":"Japan","latitude":35.6895,...}
   🔧 weather_current({"latitude":35.6895,"longitude":139.69171})
   📥 weather_current → {"temperature_2m":27.0,"wind_speed_10m":4.5,...}
```

The `/ask` endpoint returns:
```json
{
  "answer": "…",
  "route":  { "destination": "weather", "agent": "Agent 1 (weather)" },
  "steps":  [ { "kind": "tool_call", "tool": "...", "args": {...} },
              { "kind": "tool_result", "tool": "...", "output": "..." } ]
}
```

For deeper tracing (timings, tokens, nested spans), set `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` to enable **LangSmith**, no code changes required.

## Tech stack

- **MCP server:** [FastMCP](https://gofastmcp.com) over streamable-HTTP
- **Agents / routing:** LangGraph (`create_react_agent`) + LangChain
- **MCP ↔ LangGraph bridge:** `langchain-mcp-adapters`
- **LLM:** OpenAI `gpt-4o-mini` (routing + agents)
- **API / UI:** FastAPI (serves both `/ask` and the chat page)
- **Hosting:** Render (two Docker web services, free tier)

## Project structure

```
multi-agent-mcp/
├── mcp_server/
│   └── server.py          # FastMCP server: 7 tools + /health, reads $PORT
├── agents/
│   ├── agent_config.py    # MCP client + prefix map (reads MCP_URL from env)
│   ├── graph.py           # build_agents(): filter tools → create_react_agent
│   ├── supervisor.py      # LLM router + trace extraction
│   └── api.py             # FastAPI: /ask + chat UI
├── Dockerfile.server      # image for the MCP server
├── Dockerfile.agents      # image for the FastAPI agent service
├── docker-compose.yml     # local parity for the MCP server
├── render.yaml            # Render blueprint (MCP server)
├── requirements.txt
└── .env                   # OPENAI_API_KEY (gitignored, never committed)
```

## Run locally

```bash
# 1. Install
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt fastapi uvicorn

# 2. Configure
#   .env → OPENAI_API_KEY=sk-...

# 3a. Start the MCP server (terminal 1)
python -m mcp_server.server                     # serves http://localhost:8000/mcp

# 3b. Start the agent API + chat UI (terminal 2)
#   defaults MCP_URL to http://localhost:8000/mcp
uvicorn agents.api:app --reload --port 8080     # open http://localhost:8080
```

Point the agents at a **remote** MCP server without any code change:
```bash
export MCP_URL="https://multi-agent-mcp.onrender.com/mcp"
uvicorn agents.api:app --port 8080
```

## Deploy (Render)

Two Docker web services from this repo.

**Service 1: MCP server**
- Dockerfile: `Dockerfile.server`
- Health check path: `/health`
- Env vars:
  - `FOOTBALL_API_KEY` = your football-data.org key (needed by the World Cup tools)

**Service 2: Agent API + UI**
- Dockerfile: `Dockerfile.agents`
- Env vars:
  - `OPENAI_API_KEY` = your OpenAI key
  - `MCP_URL` = `https://multi-agent-mcp.onrender.com/mcp`

Both read `$PORT` (injected by Render) and bind `0.0.0.0`, so no port config is needed. `render.yaml` describes the MCP server as a blueprint.

## Author

**Jamalla Zawia** - jamala.zawia@gmail.com
