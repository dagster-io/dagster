import asyncio
import json
from collections.abc import AsyncIterator
from functools import partial
from typing import Literal
from urllib.parse import urlsplit

import dagster as dg
import httpx2
import pytest
from dagster_parallel import ParallelSearchResource

ENDPOINT: Literal["https://mcp.parallel.ai/mcp"] = "https://mcp.parallel.ai/mcp"
SOURCE_URL = "https://github.com/dagster-io/dagster/releases/tag/1.13.0"
SOURCE = {
    "url": SOURCE_URL,
    "title": "Dagster 1.13.0",
    "excerpts": ["Partitioned asset checks can target specific partitions of an upstream asset."],
}
OBJECTIVE = "Find the official Dagster 1.13.0 release notes."
QUERIES = ["site:github.com Dagster 1.13.0 release notes"]


class _ResponseBody(httpx2.AsyncByteStream):
    def __init__(self, *chunks: bytes):
        self._chunks = chunks

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self._chunks:
            yield chunk


@pytest.fixture
def server(monkeypatch):
    client = httpx2.AsyncClient
    requests = []

    def install(response: str, *, source_url: str = SOURCE_URL):
        source = {**SOURCE, "url": source_url}

        def handle(request: httpx2.Request) -> httpx2.Response:
            assert str(request.url) == ENDPOINT
            assert request.headers["User-Agent"] == f"Dagster/{dg.__version__}"
            assert "Authorization" not in request.headers
            message = json.loads(request.content)
            requests.append(message)
            method = message["method"]
            if method == "notifications/initialized":
                return httpx2.Response(202)
            if method == "initialize":
                result = {
                    "protocolVersion": message["params"]["protocolVersion"],
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "Parallel", "version": "test"},
                }
            elif method == "tools/list":
                result = {"tools": [{"name": "web_search", "inputSchema": {"type": "object"}}]}
            else:
                assert method == "tools/call"
                assert message["params"] == {
                    "name": "web_search",
                    "arguments": {"objective": OBJECTIVE, "search_queries": QUERIES},
                }
                if response == "redirect":
                    return httpx2.Response(307, headers={"Location": f"{ENDPOINT}/redirect"})
                if response == "oversized":
                    return httpx2.Response(
                        200,
                        headers={"Content-Type": "application/json"},
                        stream=_ResponseBody(*([b" " * 65536] * 17)),
                    )
                if response == "invalid":
                    result = {"content": [{"type": "text", "text": "unexpected response"}]}
                elif response == "error":
                    result = {
                        "content": [{"type": "text", "text": OBJECTIVE}],
                        "isError": True,
                    }
                elif response == "text":
                    result = {
                        "content": [{"type": "text", "text": json.dumps({"results": [source]})}]
                    }
                else:
                    result = {"content": [], "structuredContent": {"results": [source]}}
            payload = {"id": message["id"], "jsonrpc": "2.0", "result": result}
            if method == "tools/call" and response in {"streamed", "oversized_streamed"}:
                comments = (
                    [b":" + b" " * 65534 + b"\n"] * 17 if response == "oversized_streamed" else []
                )
                return httpx2.Response(
                    200,
                    headers={"Content-Type": "text/event-stream"},
                    stream=_ResponseBody(
                        *comments,
                        b"event: message\n",
                        b"data: ",
                        json.dumps(payload).encode(),
                        b"\n\n",
                    ),
                )
            return httpx2.Response(200, json=payload)

        monkeypatch.setattr(
            httpx2, "AsyncClient", partial(client, transport=httpx2.MockTransport(handle))
        )
        return requests

    return install


@pytest.mark.parametrize("response", ["text", "structured", "streamed"])
def test_search_passes_release_notes_through_materialization(server, response):
    requests = server(response)
    resource = ParallelSearchResource(endpoint=ENDPOINT)

    @dg.asset
    async def release_sources(parallel_search: ParallelSearchResource):
        results = await parallel_search.search(objective=OBJECTIVE, search_queries=QUERIES)
        return [result.model_dump() for result in results]

    @dg.asset
    def review_queue(release_sources):
        return [row["url"] for row in release_sources]

    assert requests == []
    result = dg.materialize(
        [release_sources, review_queue], resources={"parallel_search": resource}
    )
    assert result.success
    assert result.output_for_node("release_sources") == [SOURCE]
    assert result.output_for_node("review_queue") == [SOURCE["url"]]
    assert [request["method"] for request in requests] == [
        "initialize",
        "notifications/initialized",
        "tools/call",
        "tools/list",
    ]


@pytest.mark.parametrize(
    ("response", "message"),
    [
        ("redirect", "Could not complete a request"),
        ("oversized", "returned an oversized response"),
        ("invalid", "returned an invalid search result"),
        ("error", "rejected the search request"),
    ],
)
def test_search_failures_do_not_echo_query_or_repeat_request(server, response, message):
    requests = server(response)
    resource = ParallelSearchResource(endpoint=ENDPOINT)
    with pytest.raises(RuntimeError, match=message) as failure:
        asyncio.run(resource.search(objective=OBJECTIVE, search_queries=QUERIES))
    assert OBJECTIVE not in str(failure.value)
    assert sum(request["method"] == "tools/call" for request in requests) == 1


@pytest.mark.parametrize(
    "source_url",
    [
        "/release-notes",
        "https:/example.com/release-notes",
        " https://example.com/release-notes",
        "https://example.com/release notes",
    ],
)
def test_search_rejects_malformed_source_urls(server, source_url):
    server("structured", source_url=source_url)
    resource = ParallelSearchResource(endpoint=ENDPOINT)

    with pytest.raises(RuntimeError, match="returned an invalid search result"):
        asyncio.run(resource.search(objective=OBJECTIVE, search_queries=QUERIES))


def test_search_preserves_valid_source_url(server):
    source_url = "HTTPS://Example.com/release%20notes?version=1.13.0#assets"
    server("structured", source_url=source_url)
    resource = ParallelSearchResource(endpoint=ENDPOINT)

    results = asyncio.run(resource.search(objective=OBJECTIVE, search_queries=QUERIES))

    assert [result.url for result in results] == [source_url]
    assert urlsplit(results[0].url).hostname == "example.com"


def test_oversized_event_stream_fails_promptly(server):
    requests = server("oversized_streamed")
    resource = ParallelSearchResource(endpoint=ENDPOINT)

    async def search():
        async with asyncio.timeout(5):
            await resource.search(objective=OBJECTIVE, search_queries=QUERIES)

    with pytest.raises(RuntimeError, match=r"^Parallel Search returned an oversized response\.$"):
        asyncio.run(search())
    assert sum(request["method"] == "tools/call" for request in requests) == 1


@pytest.mark.parametrize(
    ("objective", "queries", "message"),
    [
        (OBJECTIVE, QUERIES[0], "Pass search_queries as a sequence of strings"),
        (OBJECTIVE, {"release notes": 1}, "Pass search_queries as a sequence of strings"),
        (OBJECTIVE, ["release notes", None], "nonempty keyword string"),
        (OBJECTIVE, [" "], "nonempty keyword string"),
        (None, QUERIES, "nonempty search objective"),
        (" ", QUERIES, "nonempty search objective"),
    ],
)
def test_search_rejects_invalid_arguments_before_connecting(server, objective, queries, message):
    requests = server("structured")
    resource = ParallelSearchResource(endpoint=ENDPOINT)

    with pytest.raises(ValueError, match=message):
        asyncio.run(resource.search(objective=objective, search_queries=queries))

    assert requests == []


@pytest.mark.parametrize("endpoint", ["http://mcp.parallel.ai/mcp", f"{ENDPOINT}?login"])
def test_resource_rejects_other_endpoints(endpoint):
    with pytest.raises(ValueError, match="Input should be"):
        ParallelSearchResource(endpoint=endpoint)
