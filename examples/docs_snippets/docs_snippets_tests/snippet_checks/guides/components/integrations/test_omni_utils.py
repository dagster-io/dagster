from dagster_omni.component import OmniComponent
from dagster_omni.objects import (
    OmniDocument,
    OmniFolder,
    OmniOwner,
    OmniQuery,
    OmniQueryConfig,
    OmniUser,
    OmniWorkspaceData,
)
from dagster_omni.workspace import OmniWorkspace


class MockOmniWorkspace(OmniWorkspace):
    async def fetch_omni_state(self) -> OmniWorkspaceData:
        """Returns mock Omni workspace data."""
        # Create mock folder
        folder = OmniFolder(
            id="folder_1",
            name="Analytics",
            path="Analytics",
            scope="shared",
        )

        # Create mock owner
        owner = OmniOwner(
            id="user_1",
            name="Test User",
        )

        # Create mock user
        user = OmniUser(
            id="user_1",
            name="Test User",
            display_name="Test User",
            user_name="testuser",
            active=True,
            primary_email="test@example.com",
            groups=["analytics"],
            created="2024-01-01T00:00:00Z",
            last_modified="2024-01-01T00:00:00Z",
        )

        # Create mock documents
        sales_dashboard = OmniDocument(
            identifier="doc_1",
            name="sales_dashboard",
            scope="shared",
            connection_id="conn_1",
            deleted=False,
            has_dashboard=True,
            type="dashboard",
            updated_at="2024-01-01T00:00:00Z",
            folder=folder,
            owner=owner,
            labels=[],
            queries=[],
        )

        revenue_report = OmniDocument(
            identifier="doc_2",
            name="revenue_report",
            scope="shared",
            connection_id="conn_1",
            deleted=False,
            has_dashboard=True,
            type="dashboard",
            updated_at="2024-01-01T00:00:00Z",
            folder=folder,
            owner=owner,
            labels=[],
            queries=[],
        )

        customer_analysis = OmniDocument(
            identifier="doc_3",
            name="customer_analysis",
            scope="shared",
            connection_id="conn_1",
            deleted=False,
            has_dashboard=True,
            type="dashboard",
            updated_at="2024-01-01T00:00:00Z",
            folder=folder,
            owner=owner,
            labels=[],
            queries=[],
        )

        return OmniWorkspaceData(
            documents=[sales_dashboard, revenue_report, customer_analysis],
            users=[user],
        )


class MockOmniComponent(OmniComponent):
    async def write_state_to_path(self, state_path):
        """Override to use mock data."""
        import dagster as dg

        # Create a mock workspace with the same credentials
        mock_workspace = MockOmniWorkspace(**self.workspace.model_dump())

        # Fetch and store mock data
        mock_data = await mock_workspace.fetch_omni_state()

        # Serialize and write to path
        state_path.write_text(dg.serialize_value(mock_data))


def test_mock_omni_workspace() -> None:
    """Test that the mock Omni workspace returns the expected data."""
    import asyncio

    workspace = MockOmniWorkspace(
        base_url="https://test.omniapp.co",
        api_key="test_api_key",
    )

    workspace_data = asyncio.run(workspace.fetch_omni_state())

    # Verify we have the expected content
    assert len(workspace_data.documents) == 3
    assert len(workspace_data._users_by_id) == 1  # noqa

    # Verify specific content
    doc_names = [doc.name for doc in workspace_data.documents]
    assert "sales_dashboard" in doc_names
    assert "revenue_report" in doc_names
    assert "customer_analysis" in doc_names
