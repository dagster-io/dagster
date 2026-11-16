import asyncio
from builtins import ExceptionGroup
from collections.abc import AsyncIterator, Callable, Sequence
from functools import partial
from typing import Literal
from urllib.parse import urlsplit

import httpx2
from dagster import (
    ConfigurableResource,
    __version__ as dagster_version,
)
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import TextContent
from pydantic import AnyHttpUrl, BaseModel, Field, TypeAdapter, field_validator

_MAX_RESPONSE_BYTES = 1024 * 1024
_SOURCE_URL = TypeAdapter(AnyHttpUrl)


class ParallelSearchResult(BaseModel):
    """A source URL and the passages returned by Parallel Search."""

    url: str
    title: str
    excerpts: list[str]

    @field_validator("url")
    @classmethod
    def _validate_source_url(cls, url: str) -> str:
        # Validate the original string that downstream assets will receive.
        if (
            not urlsplit(url).hostname
            or "\\" in url
            or any(
                character.isspace() or ord(character) < 32 or ord(character) == 127
                for character in url
            )
        ):
            raise ValueError("Expected an absolute HTTP or HTTPS source URL.")
        _SOURCE_URL.validate_python(url)
        return url


class _SearchResponse(BaseModel):
    results: list[ParallelSearchResult]


class _BoundedStream(httpx2.AsyncByteStream):
    def __init__(self, stream: httpx2.AsyncByteStream, on_oversized: Callable[[], None]):
        self._stream = stream
        self._on_oversized = on_oversized

    async def __aiter__(self) -> AsyncIterator[bytes]:
        remaining = _MAX_RESPONSE_BYTES
        async for chunk in self._stream:
            remaining -= len(chunk)
            if remaining < 0:
                self._on_oversized()
                raise RuntimeError("Parallel Search returned an oversized response.")
            yield chunk

    async def aclose(self) -> None:
        await self._stream.aclose()


async def _check_response(response: httpx2.Response, *, on_oversized: Callable[[], None]) -> None:
    # The MCP SDK can follow same-origin redirects itself, so reject them before
    # the SDK receives the response and can send the query to another URL.
    if response.is_redirect:
        raise RuntimeError("Parallel Search returned an unexpected redirect.")
    if response.headers.get("Content-Encoding", "identity").lower() != "identity":
        raise RuntimeError("Parallel Search returned an unsupported content encoding.")
    if not isinstance(response.stream, httpx2.AsyncByteStream):
        raise RuntimeError("Parallel Search returned an invalid response stream.")
    response.stream = _BoundedStream(response.stream, on_oversized)
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
        if not isinstance(objective, str) or not objective.strip():
            raise ValueError("Provide a nonempty search objective string.")
        if not isinstance(search_queries, Sequence) or isinstance(search_queries, (str, bytes)):
            raise ValueError("Pass search_queries as a sequence of strings, such as ['my query'].")

        queries = list(search_queries)
        if not queries or any(not isinstance(query, str) or not query.strip() for query in queries):
            raise ValueError("Provide at least one nonempty keyword string in search_queries.")

        deadline = asyncio.timeout(30)
        response_too_large = False

        def stop_oversized_response() -> None:
            nonlocal response_too_large
            response_too_large = True
            # The SDK catches read errors in SSE streams while the call keeps waiting.
            if not deadline.expired():
                deadline.reschedule(asyncio.get_running_loop().time())

        try:
            async with (
                deadline,
                httpx2.AsyncClient(
                    headers={
                        "User-Agent": f"Dagster/{dagster_version}",
                        "Accept-Encoding": "identity",
                    },
                    timeout=15,
                    follow_redirects=False,
                    trust_env=False,
                    event_hooks={
                        "response": [partial(_check_response, on_oversized=stop_oversized_response)]
                    },
                ) as client,
            ):
                async with streamable_http_client(self.endpoint, http_client=client) as (
                    read,
                    write,
                ):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(
                            "web_search",
                            {"objective": objective, "search_queries": queries},
                        )
        except (TimeoutError, ExceptionGroup, httpx2.HTTPError) as error:
            if response_too_large:
                raise RuntimeError("Parallel Search returned an oversized response.") from None
            if isinstance(error, TimeoutError):
                raise RuntimeError("Parallel Search timed out.") from None
            raise RuntimeError("Could not complete a request to Parallel Search.") from None

        if result.is_error:
            raise RuntimeError("Parallel Search rejected the search request.")

        try:
            if result.structured_content is not None:
                return _SearchResponse.model_validate(result.structured_content).results
            if len(result.content) == 1 and isinstance(result.content[0], TextContent):
                return _SearchResponse.model_validate_json(result.content[0].text).results
        except ValueError:
            pass
        raise RuntimeError("Parallel Search returned an invalid search result.")
