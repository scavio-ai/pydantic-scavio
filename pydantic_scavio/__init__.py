"""Scavio search tool for Pydantic AI agents.

[Scavio](https://scavio.dev) is a real-time search API for AI agents. This
package exposes Scavio's Google web search (v2) as a Pydantic AI tool.
"""

from dataclasses import KW_ONLY, dataclass
from functools import partial
from inspect import signature
from typing import overload
from urllib.parse import urlparse

from pydantic import TypeAdapter
from typing_extensions import Any, NotRequired, TypedDict

from pydantic_ai.tools import Tool

try:
    from scavio import AsyncScavioClient
except ImportError as _import_error:
    raise ImportError(
        'Please install `scavio` to use the Scavio search tool — `pip install pydantic-scavio` '
        'installs it automatically, so a missing `scavio` usually means a broken environment.'
    ) from _import_error

__all__ = (
    'ScavioSearchResult',
    'ScavioSearchTool',
    'scavio_search_tool',
    'scavio_heb_search_tool',
    'scavio_heb_product_tool',
    'scavio_heb_stores_tool',
    'scavio_kroger_search_tool',
    'scavio_kroger_product_tool',
)

__version__ = '0.1.5'

_UNSET: Any = object()
"""Sentinel to distinguish "not provided" from None in factory kwargs."""


class ScavioSearchResult(TypedDict):
    """A Scavio Google search result.

    See [Scavio documentation](https://scavio.dev/docs/search-api) for more information.
    """

    position: int
    """The rank of the result on the page."""
    title: str
    """The title of the search result."""
    url: str
    """The URL of the search result."""
    domain: str
    """The domain of the search result."""
    content: str
    """A short description (snippet) of the search result."""
    date: NotRequired[str | None]
    """The publication date of the result, if available."""


scavio_search_ta = TypeAdapter(list[ScavioSearchResult])


def _normalize(organic_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map Google v2 organic results (link/snippet) to the normalized result shape."""
    normalized: list[dict[str, Any]] = []
    for item in organic_results:
        link = item.get('link') or ''
        normalized.append(
            {
                'position': item.get('position', len(normalized) + 1),
                'title': item.get('title', ''),
                'url': link,
                'domain': urlparse(link).netloc if link else '',
                'content': item.get('snippet', ''),
                'date': item.get('date'),
            }
        )
    return normalized


@dataclass
class ScavioSearchTool:
    """The Scavio search tool."""

    client: AsyncScavioClient
    """The Scavio search client."""

    _: KW_ONLY

    async def __call__(
        self,
        query: str,
        country_code: str | None = None,
        language: str | None = None,
    ) -> list[ScavioSearchResult]:
        """Searches Google through Scavio for the given query and returns the results.

        Args:
            query: The search query to execute with Scavio.
            country_code: Two-letter country code to localize results (for example `us`).
            language: Two-letter language code for results (for example `en`).

        Returns:
            A list of organic search results from Scavio.
        """
        results: dict[str, Any] = await self.client.google.search(
            query,
            gl=country_code,
            hl=language,
        )
        return scavio_search_ta.validate_python(_normalize(results.get('organic_results', [])))


@overload
def scavio_search_tool(
    api_key: str,
    *,
    country_code: str | None = _UNSET,
    language: str | None = _UNSET,
) -> Tool[Any]: ...


@overload
def scavio_search_tool(
    *,
    client: AsyncScavioClient,
    country_code: str | None = _UNSET,
    language: str | None = _UNSET,
) -> Tool[Any]: ...


def scavio_search_tool(
    api_key: str | None = None,
    *,
    client: AsyncScavioClient | None = None,
    country_code: str | None = _UNSET,
    language: str | None = _UNSET,
) -> Tool[Any]:
    """Creates a Scavio search tool.

    [Scavio](https://scavio.dev) is a real-time search API for AI agents. This tool runs a
    Google web search (v2, 1 credit per search) and returns the organic results.

    Parameters provided here are fixed for all searches and hidden from the LLM's tool
    schema. Parameters left unset remain available for the LLM to set per-call.

    Args:
        api_key: The Scavio API key. Required if `client` is not provided.

            You can get one by signing up at [https://dashboard.scavio.dev](https://dashboard.scavio.dev).
        client: An existing AsyncScavioClient. If provided, `api_key` is ignored.
            This is useful for sharing a client across multiple tool instances.
        country_code: Two-letter country code to localize results (for example `us`).
        language: Two-letter language code for results (for example `en`).
    """
    if client is None:
        if api_key is None:
            raise ValueError('Either api_key or client must be provided')
        client = AsyncScavioClient(api_key=api_key)
    func = ScavioSearchTool(client=client).__call__

    kwargs: dict[str, Any] = {}
    if country_code is not _UNSET:
        kwargs['country_code'] = country_code
    if language is not _UNSET:
        kwargs['language'] = language

    if kwargs:
        original = func
        func = partial(func, **kwargs)
        func.__name__ = original.__name__  # type: ignore[union-attr]
        func.__qualname__ = original.__qualname__
        # partial with keyword args only updates defaults, not removes params.
        # Set __signature__ explicitly to exclude bound params from the tool schema.
        orig_sig = signature(original)
        func.__signature__ = orig_sig.replace(  # type: ignore[attr-defined]
            parameters=[p for name, p in orig_sig.parameters.items() if name not in kwargs]
        )

    return Tool[Any](
        func,  # pyright: ignore[reportArgumentType]
        name='scavio_search',
        description='Searches Google through Scavio for the given query and returns the results.',
    )

# ---------------------------------------------------------------------------
# HEB tools
# ---------------------------------------------------------------------------


@dataclass
class _HebSearchTool:
    """Scavio HEB grocery product search tool."""

    client: AsyncScavioClient
    _: KW_ONLY

    async def __call__(
        self,
        query: str,
        page: int | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """Search HEB grocery products.

        Args:
            query: The search query for HEB products.
            page: Page number for pagination.
            page_size: Number of results per page (max 60, default 30).

        Returns:
            Search results from HEB.
        """
        kwargs: dict[str, Any] = {}
        if page is not None:
            kwargs['page'] = page
        if page_size is not None:
            kwargs['page_size'] = page_size
        return await self.client.heb.search(query, **kwargs)


@overload
def scavio_heb_search_tool(
    api_key: str,
    *,
    page: int | None = _UNSET,
    page_size: int | None = _UNSET,
) -> Tool[Any]: ...


@overload
def scavio_heb_search_tool(
    *,
    client: AsyncScavioClient,
    page: int | None = _UNSET,
    page_size: int | None = _UNSET,
) -> Tool[Any]: ...


def scavio_heb_search_tool(
    api_key: str | None = None,
    *,
    client: AsyncScavioClient | None = None,
    page: int | None = _UNSET,
    page_size: int | None = _UNSET,
) -> Tool[Any]:
    """Creates a Scavio HEB product search tool.

    Search HEB grocery products by keyword. Returns product listings with
    pricing, availability and product details.

    Args:
        api_key: The Scavio API key. Required if ``client`` is not provided.
        client: An existing AsyncScavioClient.
        page: Page number for pagination.
        page_size: Number of results per page (max 60, default 30).
    """
    if client is None:
        if api_key is None:
            raise ValueError('Either api_key or client must be provided')
        client = AsyncScavioClient(api_key=api_key)
    func = _HebSearchTool(client=client).__call__

    kwargs: dict[str, Any] = {}
    if page is not _UNSET:
        kwargs['page'] = page
    if page_size is not _UNSET:
        kwargs['page_size'] = page_size

    if kwargs:
        original = func
        func = partial(func, **kwargs)
        func.__name__ = original.__name__  # type: ignore[union-attr]
        func.__qualname__ = original.__qualname__
        orig_sig = signature(original)
        func.__signature__ = orig_sig.replace(  # type: ignore[attr-defined]
            parameters=[p for name, p in orig_sig.parameters.items() if name not in kwargs]
        )

    return Tool[Any](
        func,  # pyright: ignore[reportArgumentType]
        name='scavio_heb_search',
        description='Search HEB grocery products by keyword.',
    )


@dataclass
class _HebProductTool:
    """Scavio HEB product detail tool."""

    client: AsyncScavioClient
    _: KW_ONLY

    async def __call__(
        self,
        product_url: str | None = None,
        product_id: str | None = None,
        slug: str | None = None,
    ) -> dict[str, Any]:
        """Get detailed information about an HEB product.

        Provide at least one identifier: ``product_url``, ``product_id``, or ``slug``.

        Args:
            product_url: Full HEB product page URL.
            product_id: HEB product ID.
            slug: HEB product slug.

        Returns:
            Product details from HEB.
        """
        kwargs: dict[str, Any] = {}
        if product_url is not None:
            kwargs['product_url'] = product_url
        if product_id is not None:
            kwargs['product_id'] = product_id
        if slug is not None:
            kwargs['slug'] = slug
        return await self.client.heb.product(**kwargs)


@overload
def scavio_heb_product_tool(
    api_key: str,
) -> Tool[Any]: ...


@overload
def scavio_heb_product_tool(
    *,
    client: AsyncScavioClient,
) -> Tool[Any]: ...


def scavio_heb_product_tool(
    api_key: str | None = None,
    *,
    client: AsyncScavioClient | None = None,
) -> Tool[Any]:
    """Creates a Scavio HEB product detail tool.

    Look up detailed information for an HEB product by URL, product ID, or slug.

    Args:
        api_key: The Scavio API key. Required if ``client`` is not provided.
        client: An existing AsyncScavioClient.
    """
    if client is None:
        if api_key is None:
            raise ValueError('Either api_key or client must be provided')
        client = AsyncScavioClient(api_key=api_key)
    func = _HebProductTool(client=client).__call__

    return Tool[Any](
        func,  # pyright: ignore[reportArgumentType]
        name='scavio_heb_product',
        description='Get detailed information about an HEB grocery product.',
    )


@dataclass
class _HebStoresTool:
    """Scavio HEB store finder tool."""

    client: AsyncScavioClient
    _: KW_ONLY

    async def __call__(
        self,
        zip: str | None = None,
        city: str | None = None,
    ) -> dict[str, Any]:
        """Find HEB store locations.

        Provide at least one of ``zip`` or ``city``.

        Args:
            zip: ZIP code to search near.
            city: City name to search in.

        Returns:
            A list of HEB store locations.
        """
        kwargs: dict[str, Any] = {}
        if zip is not None:
            kwargs['zip'] = zip
        if city is not None:
            kwargs['city'] = city
        return await self.client.heb.stores(**kwargs)


@overload
def scavio_heb_stores_tool(
    api_key: str,
) -> Tool[Any]: ...


@overload
def scavio_heb_stores_tool(
    *,
    client: AsyncScavioClient,
) -> Tool[Any]: ...


def scavio_heb_stores_tool(
    api_key: str | None = None,
    *,
    client: AsyncScavioClient | None = None,
) -> Tool[Any]:
    """Creates a Scavio HEB store finder tool.

    Find HEB store locations by ZIP code or city.

    Args:
        api_key: The Scavio API key. Required if ``client`` is not provided.
        client: An existing AsyncScavioClient.
    """
    if client is None:
        if api_key is None:
            raise ValueError('Either api_key or client must be provided')
        client = AsyncScavioClient(api_key=api_key)
    func = _HebStoresTool(client=client).__call__

    return Tool[Any](
        func,  # pyright: ignore[reportArgumentType]
        name='scavio_heb_stores',
        description='Find HEB store locations by ZIP code or city.',
    )


# ---------------------------------------------------------------------------
# Kroger tools
# ---------------------------------------------------------------------------


@dataclass
class _KrogerSearchTool:
    """Scavio Kroger grocery product search tool."""

    client: AsyncScavioClient
    _: KW_ONLY

    async def __call__(
        self,
        query: str,
        page: int | None = None,
    ) -> dict[str, Any]:
        """Search Kroger grocery products.

        Kroger operates Kroger, Ralphs, Fred Meyer, Harris Teeter,
        King Soopers, Fry's and other banners.

        Args:
            query: The search query for Kroger products.
            page: Page number for pagination.

        Returns:
            Search results from Kroger.
        """
        kwargs: dict[str, Any] = {}
        if page is not None:
            kwargs['page'] = page
        return await self.client.kroger.search(query, **kwargs)


@overload
def scavio_kroger_search_tool(
    api_key: str,
    *,
    page: int | None = _UNSET,
) -> Tool[Any]: ...


@overload
def scavio_kroger_search_tool(
    *,
    client: AsyncScavioClient,
    page: int | None = _UNSET,
) -> Tool[Any]: ...


def scavio_kroger_search_tool(
    api_key: str | None = None,
    *,
    client: AsyncScavioClient | None = None,
    page: int | None = _UNSET,
) -> Tool[Any]:
    """Creates a Scavio Kroger product search tool.

    Search Kroger grocery products by keyword. Kroger operates Kroger, Ralphs,
    Fred Meyer, Harris Teeter, King Soopers, Fry's and other banners.

    Args:
        api_key: The Scavio API key. Required if ``client`` is not provided.
        client: An existing AsyncScavioClient.
        page: Page number for pagination.
    """
    if client is None:
        if api_key is None:
            raise ValueError('Either api_key or client must be provided')
        client = AsyncScavioClient(api_key=api_key)
    func = _KrogerSearchTool(client=client).__call__

    kwargs: dict[str, Any] = {}
    if page is not _UNSET:
        kwargs['page'] = page

    if kwargs:
        original = func
        func = partial(func, **kwargs)
        func.__name__ = original.__name__  # type: ignore[union-attr]
        func.__qualname__ = original.__qualname__
        orig_sig = signature(original)
        func.__signature__ = orig_sig.replace(  # type: ignore[attr-defined]
            parameters=[p for name, p in orig_sig.parameters.items() if name not in kwargs]
        )

    return Tool[Any](
        func,  # pyright: ignore[reportArgumentType]
        name='scavio_kroger_search',
        description=(
            'Search Kroger grocery products by keyword. Kroger operates Kroger, '
            "Ralphs, Fred Meyer, Harris Teeter, King Soopers, Fry's and other banners."
        ),
    )


@dataclass
class _KrogerProductTool:
    """Scavio Kroger product detail tool."""

    client: AsyncScavioClient
    _: KW_ONLY

    async def __call__(
        self,
        product_url: str | None = None,
        upc: str | None = None,
        slug: str | None = None,
    ) -> dict[str, Any]:
        """Get detailed information about a Kroger product.

        Provide at least one identifier: ``product_url``, ``upc``, or ``slug``.

        Args:
            product_url: Full Kroger product page URL.
            upc: Universal Product Code.
            slug: Kroger product slug.

        Returns:
            Product details from Kroger.
        """
        kwargs: dict[str, Any] = {}
        if product_url is not None:
            kwargs['product_url'] = product_url
        if upc is not None:
            kwargs['upc'] = upc
        if slug is not None:
            kwargs['slug'] = slug
        return await self.client.kroger.product(**kwargs)


@overload
def scavio_kroger_product_tool(
    api_key: str,
) -> Tool[Any]: ...


@overload
def scavio_kroger_product_tool(
    *,
    client: AsyncScavioClient,
) -> Tool[Any]: ...


def scavio_kroger_product_tool(
    api_key: str | None = None,
    *,
    client: AsyncScavioClient | None = None,
) -> Tool[Any]:
    """Creates a Scavio Kroger product detail tool.

    Look up detailed information for a Kroger product by URL, UPC, or slug.

    Args:
        api_key: The Scavio API key. Required if ``client`` is not provided.
        client: An existing AsyncScavioClient.
    """
    if client is None:
        if api_key is None:
            raise ValueError('Either api_key or client must be provided')
        client = AsyncScavioClient(api_key=api_key)
    func = _KrogerProductTool(client=client).__call__

    return Tool[Any](
        func,  # pyright: ignore[reportArgumentType]
        name='scavio_kroger_product',
        description='Get detailed information about a Kroger grocery product.',
    )

