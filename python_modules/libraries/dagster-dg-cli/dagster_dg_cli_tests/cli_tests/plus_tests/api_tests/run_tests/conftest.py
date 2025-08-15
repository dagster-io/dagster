"""Test configuration specific to run API tests."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_graphql_client():
    """Mock GraphQL client for run tests."""
    return MagicMock()


@pytest.fixture
def mock_successful_run_client(mock_graphql_client):
    """Mock client that returns successful run response."""
    # This will be updated once we have actual fixture data
    mock_response = {
        "runOrError": {
            "__typename": "Run",
            "id": "test-id",
            "runId": "test-run",
            "status": "SUCCESS",
            "tags": [],
            "assets": [],
            "stats": {"__typename": "RunStatsSnapshot"},
        }
    }
    mock_graphql_client.execute.return_value = mock_response
    return mock_graphql_client
