import asyncio
import urllib.parse
from typing import Any, Optional

import aiohttp
import dagster as dg
from aiohttp.client_exceptions import ClientResponseError
from dagster._utils.backoff import async_backoff, exponential_delay_generator
from pydantic import Field

from dagster_omni.objects import OmniDocument, OmniQuery, OmniUser, OmniWorkspaceData


class OmniWorkspace(dg.Resolvable, dg.Model):
    """Handles all interactions with the Omni API to fetch and manage state."""

    base_url: str = Field(
        description="The base URL to your Omni instance.", examples=["https://acme.omniapp.co"]
    )
    api_key: str = Field(
        description="The API key to your Omni instance.",
        examples=['"{{ env.OMNI_API_KEY }}"'],
        repr=False,
    )
    max_retries: int = Field(
        default=5, description="The maximum number of retries to make when rate-limited."
    )
    base_delay: float = Field(
        default=4.0,
        description="The base delay for exponential backoff between retries in seconds.",
    )

    @property
    def base_api_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/v1"

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

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    async def make_request(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Make a GET request to the API with retry logic."""
        url = self._build_url(endpoint)
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
        endpoint = f"api/v1/documents/{document_identifier}/queries"
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
        base_params = {"pageSize": "100", "include": "_count"}
        documents = []
        next_cursor = None

        while True:
            params = base_params.copy()
            if next_cursor:
                params["cursor"] = next_cursor

            response = await self.make_request("api/v1/documents", params)

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

    async def _fetch_users(self) -> list[OmniUser]:
        """Fetch all users from the Omni SCIM API."""
        base_params = {"count": "100"}
        users = []
        start_index = 1

        while True:
            params = base_params.copy()
            params["startIndex"] = str(start_index)

            response = await self.make_request("api/scim/v2/users", params)

            user_resources = response.get("Resources", [])
            if not user_resources:
                break

            users.extend([OmniUser.from_json(user_data) for user_data in user_resources])

            # Check if we've received fewer users than requested, indicating we're done
            if len(user_resources) < int(base_params["count"]):
                break

            start_index += len(user_resources)

        return users

    async def fetch_omni_state(self) -> OmniWorkspaceData:
        """Fetch all documents and users from the Omni API.

        This is the main public method for getting complete Omni state.
        """
        # Fetch documents and users concurrently
        documents, users = await asyncio.gather(self._fetch_documents(), self._fetch_users())
        return OmniWorkspaceData(documents=documents, users=users)
