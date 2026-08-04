"""Tests for the Scavio search tool."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from scavio import AsyncScavioClient

from pydantic_scavio import ScavioSearchTool, scavio_search_tool

V2_RESPONSE = {
    "search_information": {"total_results": 1000},
    "organic_results": [
        {
            "position": 1,
            "title": "Pydantic AI",
            "link": "https://pydantic.dev/docs/ai/overview/",
            "snippet": "Pydantic AI is a Python agent framework.",
        },
        {
            "position": 2,
            "title": "GitHub - pydantic/pydantic-ai",
            "link": "https://github.com/pydantic/pydantic-ai",
            "snippet": "Agent framework, the Pydantic way.",
            "date": "Jan 1, 2026",
        },
    ],
    "credits_used": 1,
    "credits_remaining": 999,
}


def make_mock_client() -> MagicMock:
    client = MagicMock(spec=AsyncScavioClient)
    client.google = MagicMock()
    client.google.search = AsyncMock(return_value=V2_RESPONSE)
    return client


async def test_basic_search():
    """v2 organic_results are normalized to position/title/url/domain/content."""
    client = make_mock_client()
    tool = ScavioSearchTool(client=client)
    results = await tool("What is Pydantic AI?")
    assert results == [
        {
            "position": 1,
            "title": "Pydantic AI",
            "url": "https://pydantic.dev/docs/ai/overview/",
            "domain": "pydantic.dev",
            "content": "Pydantic AI is a Python agent framework.",
            "date": None,
        },
        {
            "position": 2,
            "title": "GitHub - pydantic/pydantic-ai",
            "url": "https://github.com/pydantic/pydantic-ai",
            "domain": "github.com",
            "content": "Agent framework, the Pydantic way.",
            "date": "Jan 1, 2026",
        },
    ]
    client.google.search.assert_awaited_once_with("What is Pydantic AI?", gl=None, hl=None)


async def test_country_and_language_translated():
    """country_code/language map to the v2 gl/hl wire params."""
    client = make_mock_client()
    tool = ScavioSearchTool(client=client)
    await tool("restaurants", country_code="fr", language="fr")
    client.google.search.assert_awaited_once_with("restaurants", gl="fr", hl="fr")


async def test_factory_with_bound_params():
    """Factory-bound params are hidden from the LLM tool schema and forwarded on call."""
    client = make_mock_client()
    tool = scavio_search_tool(client=client, country_code="us", language="en")
    schema = tool.function_schema.json_schema
    assert "query" in schema["properties"]
    assert "country_code" not in schema["properties"]
    assert "language" not in schema["properties"]


def test_factory_requires_api_key_or_client():
    with pytest.raises(ValueError, match="Either api_key or client must be provided"):
        scavio_search_tool()  # pyright: ignore[reportCallIssue]


def test_factory_with_client():
    client = AsyncScavioClient(api_key="test-key")
    tool = scavio_search_tool(client=client)
    assert tool.name == "scavio_search"


def test_surface_is_exactly_one_tool():
    """This package is curated: one tool, one endpoint (POST /api/v2/google).

    Guards the README's "1 endpoint, flat 1 credit" claim against silent growth.
    """
    from pydantic_scavio import __all__ as exported

    assert set(exported) == {'ScavioSearchResult', 'ScavioSearchTool', 'scavio_search_tool'}
    tool = scavio_search_tool(client=make_mock_client())
    assert tool.name == 'scavio_search'


async def test_only_google_search_is_ever_called():
    """A client that raises on any other namespace proves nothing else is reachable."""

    class _StrictClient:
        def __init__(self):
            self.google = MagicMock()
            self.google.search = AsyncMock(return_value=V2_RESPONSE)

        def __getattr__(self, name):
            raise AssertionError(f'curated surface: {name} is not exposed by pydantic-scavio')

    results = await ScavioSearchTool(client=_StrictClient())('anything')
    assert len(results) == 2


async def test_uses_google_v2_vocabulary_only():
    """/api/v1/google is retired (410). Only the v2 params gl/hl reach the SDK."""
    client = make_mock_client()
    await ScavioSearchTool(client=client)('x', country_code='us', language='en')
    _, kwargs = client.google.search.call_args
    assert kwargs == {'gl': 'us', 'hl': 'en'}
    assert not {'country_code', 'language', 'light_request', 'search_type', 'page'} & set(kwargs)


@pytest.mark.skipif("SCAVIO_API_KEY" not in os.environ, reason="requires live API key")
async def test_live_search():
    """One live call against api.scavio.dev (set SCAVIO_API_KEY to run)."""
    tool = ScavioSearchTool(client=AsyncScavioClient(api_key=os.environ["SCAVIO_API_KEY"]))
    results = await tool("pydantic ai agent framework")
    assert len(results) > 0
    first = results[0]
    assert first["url"].startswith("http")
    assert first["title"]
    assert first["domain"]
