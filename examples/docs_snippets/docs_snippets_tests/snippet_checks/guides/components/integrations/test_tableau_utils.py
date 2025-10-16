from functools import cached_property

from dagster_tableau import TableauCloudWorkspace
from dagster_tableau.components.tableau_workspace_component import (
    TableauWorkspaceComponent,
)
from dagster_tableau.translator import (
    TableauContentData,
    TableauContentType,
    TableauWorkspaceData,
)


class MockTableauWorkspace(TableauCloudWorkspace):
    def fetch_tableau_workspace_data(self) -> TableauWorkspaceData:
        """Returns mock Tableau workspace data."""
        # Create mock workbook
        workbook = TableauContentData(
            content_type=TableauContentType.WORKBOOK,
            properties={
                "luid": "test_workbook_id",
                "name": "test_workbook",
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z",
                "uri": "sites/test/workbooks/test_workbook_id",
                "projectName": "test_project",
                "projectLuid": "test_project_id",
                "sheets": [],
                "dashboards": [],
            },
        )

        # Create mock sheet
        sheet = TableauContentData(
            content_type=TableauContentType.SHEET,
            properties={
                "luid": "test_sheet_id",
                "name": "sales",
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z",
                "path": "test_workbook/sales",
                "workbook": {"luid": "test_workbook_id"},
                "parentEmbeddedDatasources": [],
            },
        )

        # Create mock dashboard
        dashboard = TableauContentData(
            content_type=TableauContentType.DASHBOARD,
            properties={
                "luid": "test_dashboard_id",
                "name": "dashboard_sales",
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z",
                "path": "test_workbook/dashboard_sales",
                "workbook": {"luid": "test_workbook_id"},
                "sheets": [],
            },
        )

        # Create mock data source
        data_source = TableauContentData(
            content_type=TableauContentType.DATA_SOURCE,
            properties={
                "luid": "test_datasource_id",
                "name": "superstore_datasource",
                "hasExtracts": False,
                "isPublished": True,
            },
        )

        return TableauWorkspaceData(
            site_name=self.site_name,
            workbooks_by_id={"test_workbook_id": workbook},
            sheets_by_id={"test_sheet_id": sheet},
            dashboards_by_id={"test_dashboard_id": dashboard},
            data_sources_by_id={"test_datasource_id": data_source},
        )


class MockTableauComponent(TableauWorkspaceComponent):
    @cached_property
    def workspace_resource(self) -> MockTableauWorkspace:
        return MockTableauWorkspace(**self.workspace.model_dump())


def test_mock_tableau_workspace() -> None:
    """Test that the mock Tableau workspace returns the expected data."""
    workspace = MockTableauWorkspace(
        connected_app_client_id="test_client_id",
        connected_app_secret_id="test_secret_id",
        connected_app_secret_value="test_secret_value",
        username="test_username",
        site_name="test_site",
        pod_name="10ax",
    )

    workspace_data = workspace.fetch_tableau_workspace_data()

    # Verify we have the expected content
    assert len(workspace_data.workbooks_by_id) == 1
    assert len(workspace_data.sheets_by_id) == 1
    assert len(workspace_data.dashboards_by_id) == 1
    assert len(workspace_data.data_sources_by_id) == 1

    # Verify specific content
    assert "test_workbook_id" in workspace_data.workbooks_by_id
    assert "test_sheet_id" in workspace_data.sheets_by_id
    assert "test_dashboard_id" in workspace_data.dashboards_by_id
    assert "test_datasource_id" in workspace_data.data_sources_by_id
