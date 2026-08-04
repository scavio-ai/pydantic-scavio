# pydantic-scavio

Real-time Google search for [Pydantic AI](https://ai.pydantic.dev) agents, powered by [Scavio](https://scavio.dev) — a unified search API for AI agents (Google, YouTube, Amazon, Walmart, Reddit, TikTok, TikTok Shop, Instagram, X, LinkedIn).

## Scope: 1 endpoint, by design

This package is a **curated subset** of the Scavio API, not a wrapper around all of it. It ships exactly **1** of Scavio's 98 endpoints:

| Tool | Endpoint | Platform | Credits |
|---|---|---|---|
| `scavio_search` | `POST /api/v2/google` | Google (web search) | 1 |

That is the whole surface, and it stays that way on purpose: one small, well-described tool an agent picks correctly every time beats a hundred it has to disambiguate between.

**Credits:** 1 credit per search, flat. Nothing here reaches the endpoints that cost more (YouTube transcripts are 8, Instagram is 2-10, a LinkedIn job is 30).

### Reaching the rest of the API

Scavio covers 98 live endpoints across ten platforms: **Google, YouTube, Amazon, Walmart, Reddit, TikTok, TikTok Shop, Instagram, X, and LinkedIn.** Point a Pydantic AI agent at the hosted MCP server for all of them:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

scavio = MCPServerStreamableHTTP(
    'https://mcp.scavio.dev/mcp',
    headers={'x-api-key': 'sk_live_...'},
)

agent = Agent('openai:gpt-5.5', toolsets=[scavio])
```

That server exposes 100 tools, one per endpoint. See the [MCP docs](https://scavio.dev/docs/mcp). Alternatively, call the `scavio` SDK directly — it is already a dependency here — and wrap whichever endpoints you need as your own tools.

## Install

```bash
pip install pydantic-scavio
```

Get a free API key (50 one-time signup credits, no monthly refill, no credit card) at [dashboard.scavio.dev](https://dashboard.scavio.dev).

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

## License

MIT
