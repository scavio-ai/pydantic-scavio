# pydantic-scavio

Real-time Google search for [Pydantic AI](https://ai.pydantic.dev) agents, powered by [Scavio](https://scavio.dev) — a unified search API for AI agents (Google, YouTube, Amazon, Walmart, Reddit, TikTok, Instagram).

Every search costs 1 credit and returns Google's live results as clean, typed JSON.

## Install

```bash
pip install pydantic-scavio
```

Get a free API key (50 signup credits, no credit card) at [dashboard.scavio.dev](https://dashboard.scavio.dev).

## Usage

```python
from pydantic_ai import Agent
from pydantic_scavio import scavio_search_tool

agent = Agent(
    "openai:gpt-5.5",
    tools=[scavio_search_tool(api_key="sk_live_...")],
    system_prompt="Search the web when you need current information.",
)

result = agent.run_sync("What changed in the latest Pydantic AI release?")
print(result.output)
```

## Fixing parameters for the agent

Parameters you pass to the factory are fixed for all searches and hidden from the LLM's tool schema; parameters you leave unset stay available for the LLM to set per call.

```python
# Always search from the US in English; the LLM only controls the query.
tool = scavio_search_tool(api_key="sk_live_...", country_code="us", language="en")
```

## Sharing a client

```python
from scavio import AsyncScavioClient
from pydantic_scavio import scavio_search_tool

client = AsyncScavioClient(api_key="sk_live_...")
tool = scavio_search_tool(client=client)
```

## Result shape

The tool returns `list[ScavioSearchResult]`:

| Field | Type | Description |
|---|---|---|
| `position` | `int` | Rank of the result on the page |
| `title` | `str` | Result title |
| `url` | `str` | Result URL |
| `domain` | `str` | Result domain |
| `content` | `str` | Snippet |
| `date` | `str \| None` | Publication date when available |

## Beyond Google

The same `scavio` SDK covers YouTube, Amazon, Walmart, Reddit, TikTok, and Instagram, and Scavio also ships a hosted [MCP server](https://scavio.dev/docs/mcp) with 46 tools. See the [docs](https://scavio.dev/docs).

## License

MIT
