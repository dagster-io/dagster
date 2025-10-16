from typing import Any, Optional

from dagster_omni.objects import (
    OmniDocument,
    OmniFolder,
    OmniLabel,
    OmniOwner,
    OmniQuery,
    OmniQueryConfig,
    OmniUser,
    OmniWorkspaceData,
)


def create_sample_folder() -> OmniFolder:
    """Create a sample OmniFolder for testing."""
    return OmniFolder(
        id="folder-123", name="Analytics", path="analytics/reports", scope="workspace"
    )


def create_sample_labels() -> list[OmniLabel]:
    """Create sample OmniLabels for testing."""
    return [OmniLabel(name="dashboard", verified=True), OmniLabel(name="sales", verified=False)]


def create_sample_query_config(table: str = "users") -> OmniQueryConfig:
    """Create a sample OmniQueryConfig for testing."""
    return OmniQueryConfig(table=table, fields=["id", "name", "email"])


def create_sample_query(query_id: str = "query-789", table: str = "users") -> OmniQuery:
    """Create a sample OmniQuery for testing."""
    return OmniQuery(
        id=query_id, name=f"Query for {table}", query_config=create_sample_query_config(table)
    )


def create_sample_document(
    identifier: str = "doc-123",
    name: str = "User Analysis",
    queries: Optional[list[OmniQuery]] = None,
    folder: Optional[OmniFolder] = create_sample_folder(),
    has_dashboard: bool = True,
) -> OmniDocument:
    """Create a sample OmniDocument for testing."""
    if queries is None:
        queries = [create_sample_query()]

    return OmniDocument(
        identifier=identifier,
        name=name,
        scope="workspace",
        connection_id="conn-456",
        deleted=False,
        has_dashboard=has_dashboard,
        type="document",
        updated_at="2023-01-01T00:00:00Z",
        owner=OmniOwner(id="owner-456", name="John Doe"),
        folder=folder,
        labels=create_sample_labels(),
        queries=queries,
    )


def create_sample_user(
    user_id: str = "user-123",
    name: str = "John Doe",
    display_name: str = "John Doe",
    user_name: str = "john.doe@example.com",
    active: bool = True,
) -> OmniUser:
    """Create a sample OmniUser for testing."""
    return OmniUser(
        id=user_id,
        name=name,
        display_name=display_name,
        user_name=user_name,
        active=active,
        primary_email="john.doe@example.com",
        groups=["Admins", "Analysts"],
        created="2023-01-01T00:00:00Z",
        last_modified="2023-06-01T00:00:00Z",
    )


def create_sample_workspace_data(
    documents: Optional[list[OmniDocument]] = None,
    users: Optional[list[OmniUser]] = None,
) -> OmniWorkspaceData:
    """Create sample OmniWorkspaceData for testing."""
    if documents is None:
        documents = [create_sample_document()]
    if users is None:
        users = [create_sample_user()]
    return OmniWorkspaceData(documents=documents, users=users)


def get_sample_documents_api_response() -> dict[str, Any]:
    """Create sample API response for documents endpoint.

    Based off of: https://docs.omni.co/docs/API/documents
    """
    return {
        "pageInfo": {
            "hasNextPage": False,
            "nextCursor": None,
            "pageSize": 20,
            "totalRecords": 58,
        },
        "records": [
            {
                "connectionId": "c0f12353-4817-4398-bcc0-d501e6dd2f64",
                "deleted": False,
                "folder": {
                    "id": "ce3b1dcd-c768-4f01-a479-353325c4c5b0",
                    "name": "In Progress Reports",
                    "path": "in-progress-reports",
                    "scope": "organization",
                },
                "hasDashboard": True,
                "identifier": "12db1a0a",
                "labels": [{"name": "Marketing", "verified": False}],
                "name": "Blob Web Traffic",
                "owner": {"id": "9e8719d9-276a-4964-9395-a493189a247c", "name": "Blobby"},
                "scope": "public",
                "type": "document",
                "updatedAt": "2025-01-07T10:00:00Z",
                "_count": {"favorites": 5, "views": 20},
            }
        ],
    }


def get_sample_queries_api_response() -> dict[str, Any]:
    """Create sample API response for queries endpoint.

    Based off of: https://docs.omni.co/docs/API/documents
    """
    return {
        "queries": [
            {
                "id": "f9467f90-b430-4381-b6b3-03436398421a",
                "name": "Monthly Sales",
                "query": {
                    "limit": 1000,
                    "sorts": [
                        {"column_name": "order_items.created_at[month]", "sort_descending": False}
                    ],
                    "table": "order_items",
                    "fields": ["order_items.created_at[month]", "order_items.sale_price_sum"],
                    "filters": {},
                },
            },
            {
                "id": "e8356bf1-be3a-4277-bd3c-9d4d54829b96",
                "name": "Product Categories",
                "query": {
                    "limit": 1000,
                    "sorts": [{"column_name": "products.category", "sort_descending": False}],
                    "table": "products",
                    "fields": ["products.category", "order_items.count"],
                    "filters": {},
                },
            },
        ]
    }


def get_sample_users_api_response() -> dict[str, Any]:
    """Create sample API response for SCIM users endpoint.

    Based off of: https://docs.omni.co/docs/API/users
    """
    return {
        "Resources": [
            {
                "id": "9e8719d9-276a-4964-9395-a493189a247c",
                "userName": "blobby@example.com",
                "displayName": "Blobby",
                "active": True,
                "emails": [{"value": "blobby@example.com", "primary": True, "type": "work"}],
                "groups": [
                    {"display": "Admins", "value": "admin-group-id"},
                    {"display": "Analysts", "value": "analyst-group-id"},
                ],
                "meta": {"created": "2023-01-01T00:00:00Z", "lastModified": "2023-06-01T00:00:00Z"},
            },
            {
                "id": "7f4219b8-165a-3854-8295-b483289b148d",
                "userName": "jane.smith@example.com",
                "displayName": "Jane Smith",
                "active": True,
                "emails": [{"value": "jane.smith@example.com", "primary": True, "type": "work"}],
                "groups": [{"display": "Analysts", "value": "analyst-group-id"}],
                "meta": {"created": "2023-02-15T00:00:00Z", "lastModified": "2023-07-01T00:00:00Z"},
            },
        ]
    }
