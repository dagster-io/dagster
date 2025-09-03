import asyncio
from unittest.mock import MagicMock, patch

import pytest
from aiohttp import ClientResponseError
from dagster_omni.objects import OmniWorkspaceData
from dagster_omni.workspace import OmniWorkspace

from dagster_omni_tests.utils import (
    get_sample_documents_api_response,
    get_sample_queries_api_response,
)


def test_fetch_omni_state_success(omni_workspace):
    """Test successful fetching and parsing of workspace data."""

    async def mock_make_request(self, endpoint, params=None, headers=None):
        if endpoint == "documents":
            return get_sample_documents_api_response()
        elif endpoint.startswith("documents/") and endpoint.endswith("/queries"):
            return get_sample_queries_api_response()
        else:
            raise ValueError(f"Unexpected endpoint: {endpoint}")

    with patch(
        "dagster_omni.workspace.OmniWorkspace.make_request",
        mock_make_request,
    ):

        async def run_test():
            workspace_data = await omni_workspace.fetch_omni_state()
            return workspace_data

        workspace_data = asyncio.run(run_test())

    # Verify the workspace data structure
    assert isinstance(workspace_data, OmniWorkspaceData)
    assert len(workspace_data.documents) == 1

    doc = workspace_data.documents[0]
    assert doc.identifier == "12db1a0a"
    assert doc.name == "Blob Web Traffic"
    assert doc.has_dashboard is True
    assert len(doc.queries) == 2
    assert doc.queries[0].id == "f9467f90-b430-4381-b6b3-03436398421a"
    assert doc.queries[0].query_config.table == "order_items"

    assert doc.queries[1].id == "e8356bf1-be3a-4277-bd3c-9d4d54829b96"
    assert doc.queries[1].query_config.table == "products"


@pytest.mark.asyncio
def test_fetch_omni_state_pagination(omni_workspace):
    """Test handling of paginated document responses."""
    page_1_response = {
        "records": [
            {
                "identifier": "doc-1",
                "name": "Document 1",
                "scope": "workspace",
                "connectionId": "conn-1",
                "deleted": False,
                "hasDashboard": True,
                "type": "document",
                "updatedAt": "2023-01-01T00:00:00Z",
                "owner": {"id": "owner-1", "name": "User 1"},
                "folder": None,
                "labels": [],
            }
        ],
        "pageInfo": {"nextCursor": "cursor123"},
    }

    page_2_response = {
        "records": [
            {
                "identifier": "doc-2",
                "name": "Document 2",
                "scope": "workspace",
                "connectionId": "conn-2",
                "deleted": False,
                "hasDashboard": False,
                "type": "document",
                "updatedAt": "2023-01-02T00:00:00Z",
                "owner": {"id": "owner-2", "name": "User 2"},
                "folder": None,
                "labels": [],
            }
        ],
        "pageInfo": {"nextCursor": None},
    }

    async def mock_make_request(self, endpoint, params=None, headers=None):
        if endpoint == "documents":
            if params and params.get("cursor") == "cursor123":
                return page_2_response
            else:
                return page_1_response
        elif endpoint.startswith("documents/") and endpoint.endswith("/queries"):
            return {"queries": []}  # No queries for these docs
        else:
            raise ValueError(f"Unexpected endpoint: {endpoint}")

    with patch.object(OmniWorkspace, "make_request", mock_make_request):

        async def run_test():
            return await omni_workspace.fetch_omni_state()

        workspace_data = asyncio.run(run_test())

    # Should have both documents from both pages
    assert len(workspace_data.documents) == 2
    assert workspace_data.documents[0].identifier == "doc-1"
    assert workspace_data.documents[1].identifier == "doc-2"


@pytest.mark.asyncio
def test_fetch_document_queries_404_handling(omni_workspace):
    """Test that 404 errors when fetching queries are handled gracefully."""

    async def mock_make_request(self, endpoint, params=None, headers=None):
        if endpoint == "documents":
            return get_sample_documents_api_response()
        elif endpoint.startswith("documents/") and endpoint.endswith("/queries"):
            # Simulate 404 - document has no queries
            raise ClientResponseError(MagicMock(), MagicMock(), status=404)
        else:
            raise ValueError(f"Unexpected endpoint: {endpoint}")

    with patch.object(OmniWorkspace, "make_request", mock_make_request):

        async def run_test():
            return await omni_workspace.fetch_omni_state()

        workspace_data = asyncio.run(run_test())

    # Document should exist but with empty queries list
    assert len(workspace_data.documents) == 1
    doc = workspace_data.documents[0]
    assert doc.identifier == "12db1a0a"
    assert len(doc.queries) == 0


@pytest.mark.asyncio
def test_fetch_document_queries_other_error_propagates(omni_workspace):
    """Test that non-404 errors when fetching queries are propagated."""

    async def mock_make_request(self, endpoint, params=None, headers=None):
        if endpoint == "documents":
            return get_sample_documents_api_response()
        elif endpoint.startswith("documents/") and endpoint.endswith("/queries"):
            # Simulate server error
            raise ClientResponseError(MagicMock(), MagicMock(), status=500)
        else:
            raise ValueError(f"Unexpected endpoint: {endpoint}")

    with patch.object(OmniWorkspace, "make_request", mock_make_request):

        async def run_test():
            return await omni_workspace.fetch_omni_state()

        with pytest.raises(ClientResponseError) as exc_info:
            asyncio.run(run_test())

        assert exc_info.value.status == 500


def test_retry_configuration():
    """Test that retry parameters are properly configured."""
    workspace = OmniWorkspace(
        base_url="https://test.omni.co", api_key="test-key", max_retries=10, base_delay=2.5
    )

    assert workspace.max_retries == 10
    assert workspace.base_delay == 2.5


@pytest.mark.asyncio
def test_retry_logic_client_error_no_retry(omni_workspace):
    """Test that client errors (4xx except 429) do not trigger retries."""
    call_count = 0

    async def mock_make_request(self, endpoint, params=None, headers=None):
        nonlocal call_count
        call_count += 1
        # 401 Unauthorized should not trigger retry
        raise ClientResponseError(MagicMock(), MagicMock(), status=401)

    with patch.object(OmniWorkspace, "make_request", mock_make_request):

        async def run_test():
            return await omni_workspace.fetch_omni_state()

        with pytest.raises(ClientResponseError) as exc_info:
            asyncio.run(run_test())

        assert exc_info.value.status == 401

    # Should only be called once (no retries)
    assert call_count == 1


@pytest.mark.asyncio
def test_429_rate_limit_retry_behavior():
    """Test that 429 errors trigger actual retries and eventually succeed."""
    # Create workspace with fast retry for testing
    workspace = OmniWorkspace(
        base_url="https://test.omni.co",
        api_key="test-key",
        max_retries=3,
        base_delay=0.001,  # Very fast for testing
    )

    call_count = 0

    class MockResponse:
        def __init__(self, json_data, status=200):
            self.json_data = json_data
            self.status = status

        def raise_for_status(self):
            if self.status >= 400:
                raise ClientResponseError(MagicMock(), MagicMock(), status=self.status)

        async def json(self):
            return self.json_data

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockSession:
        def get(self, url, headers=None):
            nonlocal call_count
            call_count += 1

            # First 2 calls return 429 rate limit error
            if call_count <= 2:
                return MockResponse({}, status=429)

            # Third call and beyond succeed
            if "documents/" in url and url.endswith("/queries"):
                return MockResponse(get_sample_queries_api_response())
            else:  # documents endpoint
                return MockResponse(get_sample_documents_api_response())

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    # Patch _get_session to return our mock session
    with patch.object(workspace, "_get_session", return_value=MockSession()):

        async def run_test():
            return await workspace.fetch_omni_state()

        # Should eventually succeed after retries
        workspace_data = asyncio.run(run_test())

        # Verify the data was successfully fetched
        assert isinstance(workspace_data, OmniWorkspaceData)
        assert len(workspace_data.documents) == 1
        assert workspace_data.documents[0].identifier == "12db1a0a"
        assert workspace_data.documents[0].name == "Blob Web Traffic"

        # Verify it actually retried - should be called at least 4 times:
        # 1st call (documents) -> 429
        # 2nd call (documents retry) -> 429
        # 3rd call (documents retry) -> success
        # 4th call (queries) -> success
        assert call_count >= 4


@pytest.mark.asyncio
def test_429_rate_limit_max_retries_exhausted():
    """Test that 429 errors eventually fail when max retries are exhausted."""
    # Create workspace with fast retry for testing
    workspace = OmniWorkspace(
        base_url="https://test.omni.co",
        api_key="test-key",
        max_retries=2,  # Low retry limit
        base_delay=0.001,  # Very fast for testing
    )

    call_count = 0

    class MockResponse:
        def __init__(self, status=429):
            self.status = status

        def raise_for_status(self):
            raise ClientResponseError(MagicMock(), MagicMock(), status=self.status)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockSession:
        def get(self, url, headers=None):
            nonlocal call_count
            call_count += 1
            # Always return 429 to exhaust retries
            return MockResponse(status=429)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    # Patch _get_session to return our mock session
    with patch.object(workspace, "_get_session", return_value=MockSession()):

        async def run_test():
            return await workspace.fetch_omni_state()

        # Should eventually fail after exhausting retries
        with pytest.raises(ClientResponseError) as exc_info:
            asyncio.run(run_test())

        # Verify it was a 429 error
        assert exc_info.value.status == 429

        # Verify it tried the expected number of times: initial + max_retries
        expected_calls = 1 + workspace.max_retries
        assert call_count == expected_calls


@pytest.mark.asyncio
def test_parallel_query_fetching(omni_workspace):
    """Test that queries for multiple documents are fetched in parallel."""
    documents_response = {
        "records": [
            {
                "identifier": "doc-1",
                "name": "Document 1",
                "scope": "workspace",
                "connectionId": "conn-1",
                "deleted": False,
                "hasDashboard": True,
                "type": "document",
                "updatedAt": "2023-01-01T00:00:00Z",
                "owner": {"id": "owner-1", "name": "User 1"},
                "folder": None,
                "labels": [],
            },
            {
                "identifier": "doc-2",
                "name": "Document 2",
                "scope": "workspace",
                "connectionId": "conn-2",
                "deleted": False,
                "hasDashboard": True,
                "type": "document",
                "updatedAt": "2023-01-02T00:00:00Z",
                "owner": {"id": "owner-2", "name": "User 2"},
                "folder": None,
                "labels": [],
            },
        ],
        "pageInfo": {"nextCursor": None},
    }

    query_call_count = 0

    async def mock_make_request(self, endpoint, params=None, headers=None):
        nonlocal query_call_count

        if endpoint == "documents":
            return documents_response
        elif endpoint.startswith("documents/") and endpoint.endswith("/queries"):
            query_call_count += 1
            doc_id = endpoint.split("/")[1]  # Extract doc ID from "documents/{id}/queries"
            return {
                "queries": [
                    {
                        "id": f"query-{doc_id}",
                        "name": f"Query for {doc_id}",
                        "query": {"table": f"table_{doc_id}", "fields": ["id"]},
                    }
                ]
            }

    with patch.object(OmniWorkspace, "make_request", mock_make_request):

        async def run_test():
            return await omni_workspace.fetch_omni_state()

        workspace_data = asyncio.run(run_test())

    # Should have fetched queries for both documents
    assert len(workspace_data.documents) == 2
    assert query_call_count == 2

    # Verify both documents got their queries
    for i, doc in enumerate(workspace_data.documents, 1):
        assert len(doc.queries) == 1
        assert doc.queries[0].query_config.table == f"table_doc-{i}"
