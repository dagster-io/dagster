from collections.abc import Sequence
from functools import cached_property
from typing import Optional

from dagster_powerbi import PowerBIWorkspace
from dagster_powerbi.components.power_bi_workspace.component import (
    PowerBIWorkspaceComponent,
)
from dagster_powerbi.resource import PowerBIToken
from dagster_powerbi.translator import (
    PowerBIContentData,
    PowerBIContentType,
    PowerBIWorkspaceData,
)

from dagster._utils.cached_method import cached_method


class MockPowerBIWorkspace(PowerBIWorkspace):
    @cached_method
    def _fetch_powerbi_workspace_data(
        self, use_workspace_scan: bool
    ) -> PowerBIWorkspaceData:
        """Retrieves all Power BI content from the workspace and returns it as a PowerBIWorkspaceData object.

        Returns:
            PowerBIWorkspaceData: A snapshot of the Power BI workspace's content.
        """
        # Create mock dashboard data
        dashboard_data = [
            PowerBIContentData(
                content_type=PowerBIContentType.DASHBOARD,
                properties={
                    "id": "dashboard_1",
                    "name": "Sales Dashboard",
                    "displayName": "Sales Dashboard",
                    "webUrl": "https://app.powerbi.com/dashboard/dashboard_1",
                    "tiles": [
                        {
                            "id": "tile_1",
                            "title": "Sales Overview",
                            "reportId": "report_1",
                        }
                    ],
                },
            ),
            PowerBIContentData(
                content_type=PowerBIContentType.DASHBOARD,
                properties={
                    "id": "dashboard_2",
                    "name": "Marketing Dashboard",
                    "displayName": "Marketing Dashboard",
                    "webUrl": "https://app.powerbi.com/dashboard/dashboard_2",
                    "tiles": [
                        {
                            "id": "tile_2",
                            "title": "Campaign Performance",
                            "reportId": "report_2",
                        }
                    ],
                },
            ),
        ]

        # Create mock report data
        report_data = [
            PowerBIContentData(
                content_type=PowerBIContentType.REPORT,
                properties={
                    "id": "report_1",
                    "name": "Sales Report",
                    "displayName": "Sales Report",
                    "webUrl": "https://app.powerbi.com/report/report_1",
                    "datasetId": "dataset_1",
                },
            ),
            PowerBIContentData(
                content_type=PowerBIContentType.REPORT,
                properties={
                    "id": "report_2",
                    "name": "Marketing Report",
                    "displayName": "Marketing Report",
                    "webUrl": "https://app.powerbi.com/report/report_2",
                    "datasetId": "dataset_2",
                },
            ),
        ]

        # Create mock semantic model data
        semantic_model_data = [
            PowerBIContentData(
                content_type=PowerBIContentType.SEMANTIC_MODEL,
                properties={
                    "id": "dataset_1",
                    "name": "Sales Data Model",
                    "displayName": "Sales Data Model",
                    "webUrl": "https://app.powerbi.com/dataset/dataset_1",
                    "sources": ["datasource_1"],
                    "tables": [
                        {
                            "name": "sales",
                            "columns": [
                                {"name": "id", "dataType": "int64"},
                                {"name": "amount", "dataType": "decimal"},
                                {"name": "date", "dataType": "datetime"},
                            ],
                        }
                    ],
                },
            ),
            PowerBIContentData(
                content_type=PowerBIContentType.SEMANTIC_MODEL,
                properties={
                    "id": "dataset_2",
                    "name": "Marketing Data Model",
                    "displayName": "Marketing Data Model",
                    "webUrl": "https://app.powerbi.com/dataset/dataset_2",
                    "sources": ["datasource_2"],
                    "tables": [
                        {
                            "name": "campaigns",
                            "columns": [
                                {"name": "campaign_id", "dataType": "string"},
                                {"name": "budget", "dataType": "decimal"},
                                {"name": "start_date", "dataType": "datetime"},
                            ],
                        }
                    ],
                },
            ),
        ]

        # Create mock data source data
        data_source_data = [
            PowerBIContentData(
                content_type=PowerBIContentType.DATA_SOURCE,
                properties={
                    "datasourceId": "datasource_1",
                    "name": "Sales Database",
                    "displayName": "Sales Database",
                    "type": "sql",
                    "connectionString": "Server=server1;Database=sales;",
                    "connectionDetails": {"server": "server1", "database": "sales"},
                },
            ),
            PowerBIContentData(
                content_type=PowerBIContentType.DATA_SOURCE,
                properties={
                    "datasourceId": "datasource_2",
                    "name": "Marketing Database",
                    "displayName": "Marketing Database",
                    "type": "sql",
                    "connectionString": "Server=server2;Database=marketing;",
                    "connectionDetails": {"server": "server2", "database": "marketing"},
                },
            ),
        ]

        all_content = (
            dashboard_data + report_data + semantic_model_data + data_source_data
        )
        return PowerBIWorkspaceData.from_content_data(self.workspace_id, all_content)


class MockPowerBIComponent(PowerBIWorkspaceComponent):
    @cached_property
    def workspace_resource(self) -> MockPowerBIWorkspace:
        return MockPowerBIWorkspace(**self.workspace.model_dump())


def test_mock_powerbi_workspace() -> None:
    """Test that the mock PowerBI workspace returns the expected data."""
    workspace = MockPowerBIWorkspace(
        credentials=PowerBIToken(api_token="test_token"),
        workspace_id="test_workspace",
    )

    workspace_data = workspace._fetch_powerbi_workspace_data(use_workspace_scan=True)  # noqa: SLF001

    # Verify we have the expected content
    assert len(workspace_data.dashboards_by_id) == 2
    assert len(workspace_data.reports_by_id) == 2
    assert len(workspace_data.semantic_models_by_id) == 2
    assert len(workspace_data.data_sources_by_id) == 2

    # Verify specific content
    assert "dashboard_1" in workspace_data.dashboards_by_id
    assert "report_1" in workspace_data.reports_by_id
    assert "dataset_1" in workspace_data.semantic_models_by_id
    assert "datasource_1" in workspace_data.data_sources_by_id
