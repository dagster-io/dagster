import asyncio
from unittest.mock import MagicMock, patch

import pytest
from aiohttp import ClientResponseError
from dagster_omni.objects import OmniWorkspaceData
from dagster_omni.workspace import OmniWorkspace

from dagster_omni_tests.utils import (
    get_sample_documents_api_response,
    get_sample_queries_api_response,
    get_sample_users_api_response,
)


def test_fetch_omni_state_success(omni_workspace):
    """Test successful fetching and parsing of workspace data."""

    async def mock_make_request(self, endpoint, params=None, headers=None):
        if endpoint == "api/v1/documents":
            return get_sample_documents_api_response()
        elif endpoint.startswith("api/v1/documents/") and endpoint.endswith("/queries"):
            return get_sample_queries_api_response()
        elif endpoint == "api/scim/v2/users":
            return get_sample_users_api_response()
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
    assert len(workspace_data.users) == 2

    # Verify document data
    doc = workspace_data.documents[0]
    assert doc.identifier == "12db1a0a"
    assert doc.name == "Blob Web Traffic"
    assert doc.has_dashboard is True
    assert len(doc.queries) == 2
    assert doc.queries[0].id == "f9467f90-b430-4381-b6b3-03436398421a"
    assert doc.queries[0].query_config.table == "order_items"

    assert doc.queries[1].id == "e8356bf1-be3a-4277-bd3c-9d4d54829b96"
    assert doc.queries[1].query_config.table == "products"

    # Verify user data
    user1 = workspace_data.users[0]
    assert user1.id == "9e8719d9-276a-4964-9395-a493189a247c"
    assert user1.name == "Blobby"
    assert user1.user_name == "blobby@example.com"

    user2 = workspace_data.users[1]
    assert user2.id == "7f4219b8-165a-3854-8295-b483289b148d"
    assert user2.name == "Jane Smith"
    assert user2.user_name == "jane.smith@example.com"


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
        if endpoint == "api/v1/documents":
            if params and params.get("cursor") == "cursor123":
                return page_2_response
            else:
                return page_1_response
        elif endpoint.startswith("api/v1/documents/") and endpoint.endswith("/queries"):
            return {"queries": []}  # No queries for these docs
        elif endpoint == "api/scim/v2/users":
            return get_sample_users_api_response()
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
        if endpoint == "api/v1/documents":
            return get_sample_documents_api_response()
        elif endpoint.startswith("api/v1/documents/") and endpoint.endswith("/queries"):
            # Simulate 404 - document has no queries
            raise ClientResponseError(MagicMock(), MagicMock(), status=404)
        elif endpoint == "api/scim/v2/users":
            return get_sample_users_api_response()
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
        if endpoint == "api/v1/documents":
            return get_sample_documents_api_response()
        elif endpoint.startswith("api/v1/documents/") and endpoint.endswith("/queries"):
            # Simulate server error
            raise ClientResponseError(MagicMock(), MagicMock(), status=500)
        elif endpoint == "api/scim/v2/users":
            return get_sample_users_api_response()
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

    # Should only be called twice (once for documents, once for users - no retries)
    assert call_count == 2


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
            if "api/v1/documents/" in url and url.endswith("/queries"):
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

        # With concurrent requests for documents and users, and retries on both:
        # Each endpoint will be tried: initial + max_retries = 1 + 2 = 3 times
        # So total calls = 3 (documents) + 3 (users) = 6
        expected_calls = 2 * (1 + workspace.max_retries)  # 2 endpoints, each retried
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

        if endpoint == "api/v1/documents":
            return documents_response
        elif endpoint.startswith("api/v1/documents/") and endpoint.endswith("/queries"):
            query_call_count += 1
            doc_id = endpoint.split("/")[-2]  # Extract doc ID from "api/v1/documents/{id}/queries"
            return {
                "queries": [
                    {
                        "id": f"query-{doc_id}",
                        "name": f"Query for {doc_id}",
                        "query": {"table": f"table_{doc_id}", "fields": ["id"]},
                    }
                ]
            }
        elif endpoint == "api/scim/v2/users":
            return get_sample_users_api_response()

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


@pytest.mark.asyncio
def test_fetch_users_success(omni_workspace):
    """Test successful fetching and parsing of user data via fetch_omni_state."""

    async def mock_make_request(self, endpoint, params=None, headers=None):
        if endpoint == "api/v1/documents":
            return {"records": [], "pageInfo": {"nextCursor": None}}  # No documents
        elif endpoint == "api/scim/v2/users":
            return get_sample_users_api_response()
        else:
            raise ValueError(f"Unexpected endpoint: {endpoint}")

    with patch.object(OmniWorkspace, "make_request", mock_make_request):

        async def run_test():
            workspace_data = await omni_workspace.fetch_omni_state()
            return workspace_data.users

        users = asyncio.run(run_test())

    # Should have 2 users from sample response
    assert len(users) == 2

    user1 = users[0]
    assert user1.id == "9e8719d9-276a-4964-9395-a493189a247c"
    assert user1.name == "Blobby"
    assert user1.user_name == "blobby@example.com"
    assert user1.active is True
    assert user1.groups == ["Admins", "Analysts"]

    user2 = users[1]
    assert user2.id == "7f4219b8-165a-3854-8295-b483289b148d"
    assert user2.name == "Jane Smith"
    assert user2.user_name == "jane.smith@example.com"
    assert user2.active is True
    assert user2.groups == ["Analysts"]


@pytest.mark.asyncio
def test_fetch_users_pagination(omni_workspace):
    """Test handling of paginated user responses by creating a realistic large dataset."""
    # Create first page with 100 users (full page)
    page_1_users = [
        {
            "id": f"user-{i}",
            "userName": f"user{i}@example.com",
            "displayName": f"User {i}",
            "active": True,
            "emails": [{"value": f"user{i}@example.com", "primary": True, "type": "work"}],
            "groups": [],
            "meta": {"created": "2023-01-01T00:00:00Z", "lastModified": "2023-01-01T00:00:00Z"},
        }
        for i in range(1, 101)  # 100 users
    ]

    # Create second page with 25 users (partial page, will stop pagination)
    page_2_users = [
        {
            "id": f"user-{i}",
            "userName": f"user{i}@example.com",
            "displayName": f"User {i}",
            "active": True,
            "emails": [{"value": f"user{i}@example.com", "primary": True, "type": "work"}],
            "groups": [],
            "meta": {"created": "2023-01-01T00:00:00Z", "lastModified": "2023-01-01T00:00:00Z"},
        }
        for i in range(101, 126)  # 25 more users
    ]

    call_count = 0

    async def mock_make_request(self, endpoint, params=None, headers=None):
        nonlocal call_count
        call_count += 1

        if endpoint == "api/v1/documents":
            return {"records": [], "pageInfo": {"nextCursor": None}}  # No documents
        elif endpoint == "api/scim/v2/users":
            start_index = int(params.get("startIndex", "1")) if params else 1
            if start_index == 1:
                return {"Resources": page_1_users}  # 100 users (equals page size, continues)
            elif start_index == 101:  # 1 + 100 = 101
                return {"Resources": page_2_users}  # 25 users (less than page size, stops)
            else:
                raise ValueError(f"Unexpected start_index: {start_index}")
        else:
            raise ValueError(f"Unexpected endpoint: {endpoint}")

    with patch.object(OmniWorkspace, "make_request", mock_make_request):

        async def run_test():
            workspace_data = await omni_workspace.fetch_omni_state()
            return workspace_data.users

        users = asyncio.run(run_test())

    # Should have users from both pages: 100 + 25 = 125 total
    assert len(users) == 125
    assert users[0].id == "user-1"
    assert users[99].id == "user-100"  # Last user from first page
    assert users[100].id == "user-101"  # First user from second page
    assert users[-1].id == "user-125"  # Last user overall
    # Should have made 3 API calls (1 for documents, 2 for users)
    assert call_count == 3


@pytest.mark.asyncio
def test_fetch_users_empty_response(omni_workspace):
    """Test handling of empty user response."""

    async def mock_make_request(self, endpoint, params=None, headers=None):
        if endpoint == "api/v1/documents":
            return {"records": [], "pageInfo": {"nextCursor": None}}  # No documents
        elif endpoint == "api/scim/v2/users":
            return {"Resources": []}
        else:
            raise ValueError(f"Unexpected endpoint: {endpoint}")

    with patch.object(OmniWorkspace, "make_request", mock_make_request):

        async def run_test():
            workspace_data = await omni_workspace.fetch_omni_state()
            return workspace_data.users

        users = asyncio.run(run_test())

    # Should have no users
    assert len(users) == 0


@pytest.mark.asyncio
def test_fetch_users_large_page_size(omni_workspace):
    """Test that pagination stops when fewer results than page size are returned."""
    # Return 50 users (less than page size of 100)
    users_response = {
        "Resources": [
            {
                "id": f"user-{i}",
                "userName": f"user{i}@example.com",
                "displayName": f"User {i}",
                "active": True,
                "emails": [{"value": f"user{i}@example.com", "primary": True}],
                "groups": [],
                "meta": {"created": "2023-01-01T00:00:00Z", "lastModified": "2023-01-01T00:00:00Z"},
            }
            for i in range(1, 51)
        ]
    }

    call_count = 0

    async def mock_make_request(self, endpoint, params=None, headers=None):
        nonlocal call_count
        call_count += 1

        if endpoint == "api/v1/documents":
            return {"records": [], "pageInfo": {"nextCursor": None}}  # No documents
        elif endpoint == "api/scim/v2/users":
            return users_response
        else:
            raise ValueError(f"Unexpected endpoint: {endpoint}")

    with patch.object(OmniWorkspace, "make_request", mock_make_request):

        async def run_test():
            workspace_data = await omni_workspace.fetch_omni_state()
            return workspace_data.users

        users = asyncio.run(run_test())

    # Should have 50 users
    assert len(users) == 50
    # Should make 2 API calls (1 for documents, 1 for users since result count < page size)
    assert call_count == 2

    # Verify first and last users
    assert users[0].id == "user-1"
    assert users[-1].id == "user-50"


@pytest.mark.asyncio
def test_fetch_omni_state_concurrent_requests(omni_workspace):
    """Test that documents and users are fetched concurrently."""
    call_order = []

    async def mock_make_request(self, endpoint, params=None, headers=None):
        call_order.append(endpoint)

        if endpoint == "api/v1/documents":
            # Simulate some delay for documents
            await asyncio.sleep(0.01)
            return get_sample_documents_api_response()
        elif endpoint.startswith("api/v1/documents/") and endpoint.endswith("/queries"):
            return get_sample_queries_api_response()
        elif endpoint == "api/scim/v2/users":
            # Simulate some delay for users
            await asyncio.sleep(0.01)
            return get_sample_users_api_response()
        else:
            raise ValueError(f"Unexpected endpoint: {endpoint}")

    with patch.object(OmniWorkspace, "make_request", mock_make_request):

        async def run_test():
            return await omni_workspace.fetch_omni_state()

        workspace_data = asyncio.run(run_test())

    # Should have both documents and users
    assert len(workspace_data.documents) == 1
    assert len(workspace_data.users) == 2

    # Both documents and users endpoints should have been called
    # Note: documents endpoint might be called multiple times due to pagination and query fetching
    assert "api/v1/documents" in call_order
    assert "api/scim/v2/users" in call_order
