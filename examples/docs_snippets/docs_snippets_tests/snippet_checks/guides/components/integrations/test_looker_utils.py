from functools import cached_property

from dagster_looker.api.components.looker_instance_component import (
    LookerInstanceComponent,
)
from dagster_looker.api.dagster_looker_api_translator import (
    LookerInstanceData,
    LookerStructureType,
)
from dagster_looker.api.resource import LookerResource
from looker_sdk.sdk.api40.models import (
    Dashboard,
    DashboardBase,
    DashboardFilter,
    FolderBase,
    LookmlModel,
    LookmlModelExplore,
    LookmlModelNavExplore,
)


class MockLookerResource(LookerResource):
    def get_sdk(self):
        """Returns a mock SDK - not actually used since we override fetch."""
        return None


class MockLookerInstanceData(LookerInstanceData):
    @classmethod
    def mock_data(cls):
        """Creates mock Looker instance data."""
        # Create mock explore
        explore = LookmlModelExplore(
            id="my_model::my_explore",
            view_name="my_view",
            sql_table_name="my_table",
        )

        # Create mock dashboard
        dashboard = Dashboard(
            title="my_dashboard",
            id="1",
            dashboard_filters=[
                DashboardFilter(model="my_model", explore="my_explore"),
            ],
            user_id="1",
            url="/dashboards/1",
        )

        return cls(
            explores_by_id={"my_model::my_explore": explore},
            dashboards_by_id={"1": dashboard},
        )


class MockLookerComponent(LookerInstanceComponent):
    @cached_property
    def looker_resource_cached(self) -> MockLookerResource:
        return MockLookerResource(**self.looker_resource.model_dump())

    def write_state_to_path(self, state_path):
        """Override to use mock data instead of fetching from API."""
        import dagster as dg

        # Create mock instance data
        mock_data = MockLookerInstanceData.mock_data()

        # Serialize to state
        state = mock_data.to_state(None)  # SDK is None for mock
        state_path.write_text(dg.serialize_value(state))


def test_mock_looker_resource() -> None:
    """Test that the mock Looker resource returns the expected data."""
    mock_data = MockLookerInstanceData.mock_data()

    # Verify we have the expected content
    assert len(mock_data.explores_by_id) == 1
    assert len(mock_data.dashboards_by_id) == 1

    # Verify specific content
    assert "my_model::my_explore" in mock_data.explores_by_id
    assert "1" in mock_data.dashboards_by_id
    assert mock_data.dashboards_by_id["1"].title == "my_dashboard"
