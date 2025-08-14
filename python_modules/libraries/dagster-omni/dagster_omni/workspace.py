import asyncio
import urllib.parse
from typing import Any, Optional

import aiohttp
from aiohttp.client_exceptions import ClientResponseError
from dagster._utils.backoff import async_backoff, exponential_delay_generator

from dagster_omni.objects import OmniDocument, OmniQuery, OmniState


class OmniWorkspace:
    """Handles all interactions with the Omni API to fetch and manage state."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = f"{base_url.rstrip('/')}/api/v1"
        self.api_key = api_key
        self.max_retries = 5
        self.base_delay = 4.0

    def _get_session(self) -> aiohttp.ClientSession:
        """Create configured session with Bearer token authentication."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        return aiohttp.ClientSession(headers=headers)

    def _should_retry(self, exc: BaseException) -> bool:
        """Determine if an exception should trigger a retry."""
        if isinstance(exc, ClientResponseError):
            return exc.status == 429 or 500 <= exc.status < 600
        return isinstance(exc, aiohttp.ClientError)

    async def make_request(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a GET request to the API with retry logic."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        async def _make_request():
            async with self._get_session() as session:
                request_headers = headers or {}
                async with session.get(url, headers=request_headers) as response:
                    response.raise_for_status()
                    return await response.json()

        return await async_backoff(
            _make_request,
            retry_on=self._should_retry,
            max_retries=self.max_retries,
            delay_generator=exponential_delay_generator(base_delay=self.base_delay),
        )

    async def _fetch_document_queries(self, document_identifier: str) -> list[OmniQuery]:
        """Fetch all queries for a specific document."""
        endpoint = f"documents/{document_identifier}/queries"
        try:
            response = await self.make_request(endpoint)
            return [OmniQuery.from_json(query_data) for query_data in response.get("queries", [])]
        except ClientResponseError as e:
            # When a document has no queries, this will return 404
            if e.status == 404:
                return []
            raise

    async def _fetch_document_with_queries(self, document_data: dict[str, Any]) -> OmniDocument:
        """Returns an OmniDocument with its queries embedded."""
        queries = await self._fetch_document_queries(document_data["identifier"])
        return OmniDocument.from_json(document_data, queries)

    async def _fetch_documents(self) -> list[OmniDocument]:
        """Fetch all documents from the Omni API with their queries embedded."""
        base_params = {"pageSize": "100"}
        documents = []
        next_cursor = None

        while True:
            params = base_params.copy()
            if next_cursor:
                params["cursor"] = next_cursor

            response = await self.make_request("documents", params)

            # Fan out the requests to fetch queries for each document in parallel
            coroutines = [
                self._fetch_document_with_queries(doc_data)
                for doc_data in response.get("records", [])
            ]
            documents.extend(await asyncio.gather(*coroutines))

            next_cursor = response.get("pageInfo", {}).get("nextCursor")
            if not next_cursor:
                break

        return documents

    async def fetch_omni_state(self) -> OmniState:
        """Fetch all documents from the Omni API with queries embedded.

        This is the main public method for getting complete Omni state.
        """
        documents = await self._fetch_documents()
        return OmniState(documents=documents)
