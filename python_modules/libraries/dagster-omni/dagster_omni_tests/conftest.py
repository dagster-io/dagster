import pytest
from dagster_omni.translator import OmniContentData, OmniContentType, OmniWorkspaceData


@pytest.fixture
def sample_model_data():
    """Sample Omni model data for testing.

    Based on the Omni Models API response structure documented at:
    https://docs.omni.co/docs/API/model

    The API returns models with these key fields:
    - id: Unique identifier for the model
    - name: Human-readable name
    - createdAt/updatedAt: ISO 8601 timestamps
    - connectionId: Reference to the data connection
    - modelKind: Type of model (e.g., "schema")
    """
    return {
        "id": "model_123",
        "name": "Sales Model",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-02T00:00:00Z",
        "connectionId": "conn_456",
        "modelKind": "schema",
    }


@pytest.fixture
def sample_workbook_data():
    """Sample Omni document data for testing (documents represent workbooks).

    Based on the Omni Documents API structure documented at:
    https://docs.omni.co/docs/API/documents

    Documents in Omni represent workbooks/dashboards and have these fields:
    - identifier: Unique identifier for the document
    - name: Document name
    - connectionId: Reference to data connection
    - owner: Document owner information
    - scope: Access scope
    - updatedAt: Last update timestamp
    """
    return {
        "identifier": "workbook_789",
        "name": "Sales Analysis",
        "connectionId": "conn_456",
        "owner": {"email": "analyst@company.com", "name": "Data Analyst"},
        "scope": "private",
        "updatedAt": "2024-01-02T00:00:00Z",
    }


@pytest.fixture
def sample_query_data():
    """Sample Omni query data for testing.

    Based on the Omni Query API structure documented at:
    https://docs.omni.co/docs/API/query-api

    The Query API allows running queries and returns results, but the exact
    structure of saved queries isn't fully detailed. Based on workbook docs
    and query view files mentioned at:
    https://docs.omni.co/docs/modeling/query-views

    Queries typically have:
    - id: Unique identifier
    - name: Query name/title
    - createdAt/updatedAt: Timestamps
    - sql: The actual SQL query string
    - workbook_id: Parent workbook (custom field for lineage)
    """
    return {
        "id": "query_abc",
        "name": "Monthly Sales",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-02T00:00:00Z",
        "sql": "SELECT * FROM sales WHERE month = 'January'",
        "workbook_id": "workbook_789",
    }


@pytest.fixture
def sample_workspace_data(sample_model_data, sample_workbook_data, sample_query_data):
    """Sample OmniWorkspaceData for testing."""
    content_data = [
        OmniContentData(
            content_type=OmniContentType.MODEL,
            properties=sample_model_data,
        ),
        OmniContentData(
            content_type=OmniContentType.WORKBOOK,
            properties=sample_workbook_data,
        ),
        OmniContentData(
            content_type=OmniContentType.QUERY,
            properties=sample_query_data,
        ),
    ]

    return OmniWorkspaceData.from_content_data(
        workspace_url="https://test.omniapp.co",
        content_data=content_data,
    )
