import asyncio
import logging
import urllib.parse
from functools import wraps
from typing import Any, Callable, Optional

import aiohttp
from aiohttp.client_exceptions import ClientResponseError

from dagster_omni.objects import OmniDocument, OmniPageInfo, OmniQuery, OmniState


def exponential_backoff(max_retries: int = 5, base_delay: float = 1.0):
    """Decorator that adds exponential backoff retry logic for rate limiting errors."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except ClientResponseError as e:
                    if e.status == 429 and attempt < max_retries - 1:
                        delay = base_delay * (2**attempt)
                        logging.warning(
                            f"Rate limited, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue
                    raise
                except aiohttp.ClientError as e:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2**attempt)
                        logging.warning(
                            f"Network error, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries}): {e}"
                        )
                        await asyncio.sleep(delay)
                        continue
                    raise
            raise Exception(f"Failed after {max_retries} retries")

        return wrapper

    return decorator


class OmniWorkspace:
    """Handles all interactions with the Omni API to fetch and manage state."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    @exponential_backoff(max_retries=5, base_delay=4.0)
    async def _make_api_request(
        self, endpoint: str, params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Make a request to the Omni API."""
        url = f"{self.base_url.rstrip('/')}/api/v1/{endpoint.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=url,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def _fetch_paginated(
        self,
        endpoint: str,
        parse_func: Callable[[dict[str, Any]], Any],
        base_params: Optional[dict[str, Any]] = None,
    ) -> list[Any]:
        """Generic method to fetch paginated data from the Omni API."""
        items = []
        next_cursor = None

        while True:
            params = base_params.copy() if base_params else {}
            if next_cursor:
                params["cursor"] = next_cursor

            response = await self._make_api_request(endpoint, params)

            # Parse items from this page
            for item_data in response.get("records", []):
                try:
                    items.append(parse_func(item_data))
                except (KeyError, TypeError) as e:
                    logging.warning(f"Failed to parse {endpoint} data {item_data}: {e}")
                    continue

            # Check if we need to fetch more pages
            if "pageInfo" not in response:
                break

            page_info = OmniPageInfo.from_json(response["pageInfo"])
            if not page_info.has_next_page:
                break

            next_cursor = page_info.next_cursor

        return items

    async def _fetch_document_queries(self, document_identifier: str) -> list[OmniQuery]:
        """Fetch all queries for a specific document."""
        endpoint = f"documents/{document_identifier}/queries"
        response = await self._make_api_request(endpoint)

        queries = []
        for query_data in response.get("queries", []):
            try:
                queries.append(OmniQuery.from_json(query_data))
            except (KeyError, TypeError) as e:
                logging.warning(
                    f"Failed to parse query data for document {document_identifier}: {e}"
                )
                continue

        return queries

    async def _fetch_documents(
        self, include_deleted: bool = False
    ) -> tuple[list[OmniDocument], list[OmniQuery]]:
        """Fetch all documents from the Omni API with their queries."""
        base_params = {"includeDeleted": "true"} if include_deleted else {}

        # First fetch all documents without queries
        raw_documents = []
        all_queries = []
        next_cursor = None

        while True:
            params = base_params.copy() if base_params else {}
            if next_cursor:
                params["cursor"] = next_cursor

            response = await self._make_api_request("documents", params)

            # Process documents from this page
            for doc_data in response.get("records", []):
                try:
                    # Fetch queries for this document
                    document_identifier = doc_data["identifier"]
                    queries = await self._fetch_document_queries(document_identifier)
                    query_ids = [query.id for query in queries]
                    all_queries.extend(queries)

                    # Create document with query IDs
                    document = OmniDocument.from_json(doc_data, query_ids)
                    raw_documents.append(document)
                except (KeyError, TypeError) as e:
                    logging.warning(f"Failed to parse document data {doc_data}: {e}")
                    continue
                except Exception as e:
                    logging.warning(f"Failed to fetch queries for document: {e}")
                    # Create document without queries
                    document = OmniDocument.from_json(doc_data, [])
                    raw_documents.append(document)

            # Check if we need to fetch more pages
            if "pageInfo" not in response:
                break

            page_info = OmniPageInfo.from_json(response["pageInfo"])
            if not page_info.has_next_page:
                break

            next_cursor = page_info.next_cursor

        return raw_documents, all_queries

    async def fetch_omni_state(self, include_deleted: bool = False) -> OmniState:
        """Fetch all documents and queries from the Omni API.

        This is the main public method for getting complete Omni state.
        """
        documents_with_queries, all_queries = await self._fetch_documents(include_deleted)

        return OmniState(documents=documents_with_queries, queries=all_queries)
