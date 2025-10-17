from functools import cached_property

from dagster_looker.api.components.looker_component import LookerComponent
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
    User,
)


class MockLookerResource(LookerResource):
    def get_sdk(self):
        """Returns None - we'll override serialization methods to avoid needing SDK."""
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

        # Create mock user
        user = User(
            id="1",
            email="user@example.com",
        )

        return cls(
            explores_by_id={"my_model::my_explore": explore},
            dashboards_by_id={"1": dashboard},
            users_by_id={"1": user},
        )


class MockLookerComponent(LookerComponent):
    @cached_property
    def looker_resource_cached(self) -> MockLookerResource:
        return MockLookerResource(**self.looker_resource.model_dump())

    # Store mock data as a class variable to share between methods
    _mock_data = None

    def write_state_to_path(self, state_path):
        """Override to use mock data - we store it directly without serialization."""
        import dagster as dg

        # Create and store mock instance data
        MockLookerComponent._mock_data = MockLookerInstanceData.mock_data()

        # Write a placeholder - we'll use the in-memory data in build_defs_from_state
        state_path.write_text(dg.serialize_value({"mock": True}))

    def build_defs_from_state(self, context, state_path):
        """Override to use the stored mock data instead of deserializing."""
        import dagster as dg

        if state_path is None or MockLookerComponent._mock_data is None:
            return dg.Definitions()

        # Use the stored mock data
        specs = self._load_asset_specs(MockLookerComponent._mock_data)

        return dg.Definitions(assets=specs)


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
