import asyncio
import json
from collections.abc import AsyncIterator
from functools import partial
from typing import Literal

import dagster as dg
import httpx
import pytest
from dagster_parallel import ParallelSearchResource

ENDPOINT: Literal["https://mcp.parallel.ai/mcp"] = "https://mcp.parallel.ai/mcp"
SOURCE = {
    "url": "https://github.com/dagster-io/dagster/releases/tag/1.13.0",
    "title": "Dagster 1.13.0",
    "excerpts": ["Partitioned asset checks can target specific partitions of an upstream asset."],
}
OBJECTIVE = "Find the official Dagster 1.13.0 release notes."
QUERIES = ["site:github.com Dagster 1.13.0 release notes"]


class _OversizedBody(httpx.AsyncByteStream):
    async def __aiter__(self) -> AsyncIterator[bytes]:
        for _ in range(17):
            yield b" " * 65536


@pytest.fixture
def server(monkeypatch):
    client = httpx.AsyncClient
    requests = []

    def install(response: str):
        def handle(request: httpx.Request) -> httpx.Response:
            assert str(request.url) == ENDPOINT
            assert request.headers["User-Agent"] == f"Dagster/{dg.__version__}"
            assert "Authorization" not in request.headers
            message = json.loads(request.content)
            requests.append(message)
            method = message["method"]
            if method == "notifications/initialized":
                return httpx.Response(202)
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
                    return httpx.Response(307, headers={"Location": f"{ENDPOINT}/redirect"})
                if response == "oversized":
                    return httpx.Response(
                        200, headers={"Content-Type": "application/json"}, stream=_OversizedBody()
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
                        "content": [{"type": "text", "text": json.dumps({"results": [SOURCE]})}]
                    }
                else:
                    result = {"content": [], "structuredContent": {"results": [SOURCE]}}
            return httpx.Response(
                200, json={"id": message["id"], "jsonrpc": "2.0", "result": result}
            )

        monkeypatch.setattr(
            httpx, "AsyncClient", partial(client, transport=httpx.MockTransport(handle))
        )
        return requests

    return install


@pytest.mark.parametrize("response", ["text", "structured"])
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
        ("oversized", "Could not complete a request"),
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


@pytest.mark.parametrize("endpoint", ["http://mcp.parallel.ai/mcp", f"{ENDPOINT}?login"])
def test_resource_rejects_other_endpoints(endpoint):
    with pytest.raises(ValueError, match="Input should be"):
        ParallelSearchResource(endpoint=endpoint)
