# pydantic-scavio

Real-time Google search for [Pydantic AI](https://ai.pydantic.dev) agents, powered by [Scavio](https://scavio.dev) — a unified search API for AI agents covering 31 platforms (Google, YouTube, Amazon, Walmart, eBay, Target, Home Depot, Reddit, X, TikTok, TikTok Shop, Instagram, LinkedIn, Threads, Kuaishou, Zillow, Redfin, Booking.com, Tripadvisor, Airbnb, Yelp, Indeed, Glassdoor, the app stores, G2, Capterra, ad transparency, SEC EDGAR and Companies House) plus an Extract endpoint for any URL.

## Scope: 1 endpoint, by design

This package is a **curated subset** of the Scavio API, not a wrapper around all of it. It ships exactly **1** of Scavio's 195 endpoints:

| Tool | Endpoint | Platform | Credits |
|---|---|---|---|
| `scavio_search` | `POST /api/v2/google` | Google (web search) | 1 |

That is the whole surface, and it stays that way on purpose: one small, well-described tool an agent picks correctly every time beats a hundred it has to disambiguate between.

**Credits:** 1 credit per search, flat. Nothing here reaches the endpoints that cost more (YouTube transcripts are 5, Instagram is 2-10, a LinkedIn job is 30), nor the body-priced ones whose cost depends on the request rather than a flat number (Walmart, Threads, Kuaishou and `extract`).

### Reaching the rest of the API

Scavio covers **195 live endpoints**: 194 across 31 platforms, plus `extract`, which reads any URL. The platforms are **Google, YouTube, Amazon, Walmart, eBay, Target, Home Depot, Reddit, X, TikTok, TikTok Shop, Instagram, LinkedIn, Threads, Kuaishou, Zillow, Redfin, Booking.com, Tripadvisor, Airbnb, Yelp, Indeed, Glassdoor, the Apple App Store, Google Play, SEC EDGAR, Companies House, G2, Capterra, Google Ads Transparency and the Meta Ad Library.** The most recent batch added 93 endpoints across 22 platforms plus `extract` — 21 of those platforms are new to Scavio and Walmart was rebuilt. **None of them are reachable through this package**, which stays at Google web search. Point a Pydantic AI agent at the hosted MCP server for all of them:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

scavio = MCPServerStreamableHTTP(
    'https://mcp.scavio.dev/mcp',
    headers={'x-api-key': 'sk_live_...'},
)

agent = Agent('openai:gpt-5.5', toolsets=[scavio])
```

That server exposes 191 tools; a curated subset loads by default and the rest is one env var away. See the [MCP docs](https://scavio.dev/docs/mcp).

Alternatively, call the `scavio` SDK directly — it is already a dependency here — and wrap whichever endpoints you need as your own tools: `client.youtube.transcript(...)`, `client.ebay.search(...)`, `client.sec.filings(...)`, `client.meta_ads.search(...)`. Reading an arbitrary URL is a top-level method, not a namespace: `client.extract(url, format="markdown")`, never `client.extract.extract(...)`. See the [SDK reference](https://scavio.dev/docs/python-sdk-reference) and the [full endpoint list](https://scavio.dev/docs/api-reference).

The newer verticals each have their own page: [eBay](https://scavio.dev/docs/ebay-search), [Target](https://scavio.dev/docs/target-search) and [Home Depot](https://scavio.dev/docs/home-depot-search), [Zillow](https://scavio.dev/docs/zillow-search) and [Redfin](https://scavio.dev/docs/redfin-search), [Booking.com](https://scavio.dev/docs/booking-search), [Tripadvisor](https://scavio.dev/docs/tripadvisor-search) and [Airbnb](https://scavio.dev/docs/airbnb-search), [Yelp](https://scavio.dev/docs/yelp-search), [Indeed](https://scavio.dev/docs/indeed-search) and [Glassdoor](https://scavio.dev/docs/glassdoor-companies), the [Apple App Store](https://scavio.dev/docs/app-store-search) and [Google Play](https://scavio.dev/docs/google-play-search), [G2](https://scavio.dev/docs/g2-search) and [Capterra](https://scavio.dev/docs/capterra-search), [Google Ads Transparency](https://scavio.dev/docs/google-ads-search) and the [Meta Ad Library](https://scavio.dev/docs/meta-ads-search), [SEC EDGAR](https://scavio.dev/docs/sec-edgar-filings) and [Companies House](https://scavio.dev/docs/companies-house-search), [Threads](https://scavio.dev/docs/threads-profile) and [Kuaishou](https://scavio.dev/docs/kuaishou-profile), plus [Extract](https://scavio.dev/docs/extract).

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
