import asyncio
from builtins import ExceptionGroup
from collections.abc import AsyncIterator, Sequence
from typing import Literal

import httpx
from dagster import (
    ConfigurableResource,
    __version__ as dagster_version,
)
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import TextContent
from pydantic import BaseModel, Field

_MAX_RESPONSE_BYTES = 1024 * 1024


class ParallelSearchResult(BaseModel):
    """A source URL and the passages returned by Parallel Search."""

    url: str
    title: str
    excerpts: list[str]


class _SearchResponse(BaseModel):
    results: list[ParallelSearchResult]


class _BoundedStream(httpx.AsyncByteStream):
    def __init__(self, stream: httpx.AsyncByteStream):
        self._stream = stream

    async def __aiter__(self) -> AsyncIterator[bytes]:
        remaining = _MAX_RESPONSE_BYTES
        async for chunk in self._stream:
            remaining -= len(chunk)
            if remaining < 0:
                raise RuntimeError("Parallel Search returned an oversized response.")
            yield chunk

    async def aclose(self) -> None:
        await self._stream.aclose()


async def _check_response(response: httpx.Response) -> None:
    # The MCP SDK can follow same-origin redirects itself, so reject them before
    # the SDK receives the response and can send the query to another URL.
    if response.is_redirect:
        raise RuntimeError("Parallel Search returned an unexpected redirect.")
    if response.headers.get("Content-Encoding", "identity").lower() != "identity":
        raise RuntimeError("Parallel Search returned an unsupported content encoding.")
    if not isinstance(response.stream, httpx.AsyncByteStream):
        raise RuntimeError("Parallel Search returned an invalid response stream.")
    response.stream = _BoundedStream(response.stream)
    if response.headers.get("Content-Type", "").lower().startswith("application/json"):
        # Fail here on a truncated or oversized JSON body. The SDK treats
        # exceptions during JSON parsing as stream events and may wait for a reply.
        await response.aread()


class ParallelSearchResource(ConfigurableResource):
    """Use keyless Parallel Search from an asset.

    Register this resource with the official endpoint to opt in. Calling
    :py:meth:`search` sends the supplied objective and queries to Parallel.
    Use public search terms and keep secrets and private asset data out of them.
    """

    endpoint: Literal["https://mcp.parallel.ai/mcp"] = Field(
        description="The official keyless Parallel MCP endpoint."
    )

    async def search(
        self, *, objective: str, search_queries: Sequence[str]
    ) -> list[ParallelSearchResult]:
        """Find sources for a public search objective using one or more keyword queries."""
        if (
            not objective.strip()
            or not search_queries
            or any(not query.strip() for query in search_queries)
        ):
            raise ValueError("Provide a search objective and at least one nonempty keyword query.")

        try:
            async with (
                asyncio.timeout(30),
                httpx.AsyncClient(
                    headers={
                        "User-Agent": f"Dagster/{dagster_version}",
                        "Accept-Encoding": "identity",
                    },
                    timeout=15,
                    follow_redirects=False,
                    trust_env=False,
                    event_hooks={"response": [_check_response]},
                ) as client,
            ):
                async with streamable_http_client(self.endpoint, http_client=client) as (
                    read,
                    write,
                    _,
                ):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(
                            "web_search",
                            {"objective": objective, "search_queries": list(search_queries)},
                        )
        except TimeoutError:
            raise RuntimeError("Parallel Search timed out.") from None
        except (ExceptionGroup, httpx.HTTPError):
            raise RuntimeError("Could not complete a request to Parallel Search.") from None

        if result.isError:
            raise RuntimeError("Parallel Search rejected the search request.")

        try:
            if result.structuredContent is not None:
                return _SearchResponse.model_validate(result.structuredContent).results
            if len(result.content) == 1 and isinstance(result.content[0], TextContent):
                return _SearchResponse.model_validate_json(result.content[0].text).results
        except ValueError:
            pass
        raise RuntimeError("Parallel Search returned an invalid search result.")
