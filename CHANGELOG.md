# Changelog

The version is declared in `pyproject.toml` and mirrored in
`pydantic_scavio/__init__.py`. A push to `main` publishes to PyPI when the
`pyproject.toml` version is one PyPI does not already have.

## [0.1.2]

### Changed

- Raise the `scavio` floor to `>=0.15.0`. `scavio_search_tool` needs nothing
  beyond `google.search`, but a lower floor lets a resolver install an SDK
  without the namespaces every other Scavio package now assumes, so the floor
  moves with the ecosystem.
- README: correct the counts. Scavio is at 195 endpoints -- 194 across 31
  platforms, plus `extract` -- where the README said "98 endpoints across ten
  platforms", and the hosted MCP server exposes 191 tools where it said 100.
  The most recent batch added 93 endpoints across 22 platforms plus `extract`,
  21 of those platforms new; **none of them are reachable through this
  package**, whose surface is unchanged at 1 tool and 1 endpoint.
- README: name the body-priced surfaces (Walmart, Threads, Kuaishou, `extract`)
  in the credits note rather than implying every endpoint has a flat price, and
  document `extract` as the top-level `client.extract(url)` -- it is not a
  namespace.

### Added

- Tests pinning the two facts a version bump keeps getting wrong: that
  `pyproject.toml` and `pydantic_scavio.__version__` agree, and that the
  `scavio` floor has not fallen behind the ecosystem.

## [0.1.1]

### Changed

- README: state the curated scope explicitly (1 tool, 1 endpoint) and point at
  the hosted MCP server for the rest of the API.
- Raise the `scavio` floor to `>=0.14.0`.

## [0.1.0]

### Added

- `scavio_search_tool`, a Pydantic AI tool wrapping Scavio Google web search
  (v2), returning typed `ScavioSearchResult` rows. Factory-bound parameters are
  hidden from the LLM tool schema; unset ones stay available per call.
