import json
from collections.abc import Callable

import responses
from dagster._config.field_utils import EnvVar
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.test_utils import environ
from dagster_fivetran import (
    DagsterFivetranTranslator,
    FivetranConnectorTableProps,
    FivetranWorkspace,
)
from dagster_fivetran.translator import FivetranMetadataSet

from dagster_fivetran_tests.conftest import TEST_ACCOUNT_ID, TEST_API_KEY, TEST_API_SECRET


def test_fivetran_workspace_data_to_fivetran_connector_table_props_data(
    fetch_workspace_data_api_mocks: Callable,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    actual_workspace_data = resource.get_or_fetch_workspace_data()
    table_props_data = actual_workspace_data.to_fivetran_connector_table_props_data()
    assert len(table_props_data) == 4
    assert table_props_data[0].table == "schema_name_in_destination_1.table_name_in_destination_1"
    assert table_props_data[1].table == "schema_name_in_destination_1.table_name_in_destination_2"
    assert table_props_data[2].table == "schema_name_in_destination_2.table_name_in_destination_1"
    assert table_props_data[3].table == "schema_name_in_destination_2.table_name_in_destination_2"


class MyCustomTranslator(DagsterFivetranTranslator):
    def get_asset_spec(self, props: FivetranConnectorTableProps) -> AssetSpec:
        default_spec = super().get_asset_spec(props)
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("prefix"),
            metadata={**default_spec.metadata, "custom": "metadata"},
        )


def test_translator_custom_metadata(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        resource = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        actual_workspace_data = resource.get_or_fetch_workspace_data()
        table_props_data = actual_workspace_data.to_fivetran_connector_table_props_data()

        first_table_props_data = next(props for props in table_props_data)

        asset_spec = MyCustomTranslator().get_asset_spec(first_table_props_data)

        assert "custom" in asset_spec.metadata
        assert asset_spec.metadata["custom"] == "metadata"
        assert asset_spec.key.path == [
            "prefix",
            "schema_name_in_destination_1",
            "table_name_in_destination_1",
        ]
        assert "dagster/kind/fivetran" in asset_spec.tags


def test_translator_sync_schedule_metadata(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    """Test that sync schedule metadata is included in asset specs."""
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        resource = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        actual_workspace_data = resource.get_or_fetch_workspace_data()
        table_props_data = actual_workspace_data.to_fivetran_connector_table_props_data()

        first_table_props = next(props for props in table_props_data)

        # Verify props contain the new schedule fields
        assert first_table_props.sync_frequency == 360
        assert first_table_props.schedule_type == "auto"
        assert first_table_props.daily_sync_time == "14:00"

        # Get asset spec and verify metadata
        asset_spec = DagsterFivetranTranslator().get_asset_spec(first_table_props)
        metadata_set = FivetranMetadataSet.extract(asset_spec.metadata)

        assert metadata_set.sync_frequency_minutes == 360
        assert metadata_set.schedule_type == "auto"
        assert metadata_set.daily_sync_time == "14:00"


def test_translator_connector_config_in_props(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    """Test that connector config is passed through to table props."""
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        resource = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        actual_workspace_data = resource.get_or_fetch_workspace_data()
        table_props_data = actual_workspace_data.to_fivetran_connector_table_props_data()

        first_table_props = next(props for props in table_props_data)

        # Verify connector config is passed through
        assert first_table_props.connector_config is not None
        assert "property1" in first_table_props.connector_config
        assert "property2" in first_table_props.connector_config


def test_translator_custom_report_detection_via_props() -> None:
    """Test that custom reports are detected from connector config via FivetranConnectorTableProps."""
    from dagster_fivetran.translator import (
        FivetranConnector,
        FivetranDestination,
        FivetranSchemaConfig,
        FivetranWorkspaceData,
    )

    def create_workspace_with_config(
        config: dict, table_name: str
    ) -> list[FivetranConnectorTableProps]:
        connector = FivetranConnector(
            id="test_connector",
            name="test_schema",
            service="google_ads",
            group_id="test_group",
            setup_state="connected",
            sync_state="scheduled",
            paused=False,
            succeeded_at="2024-01-01T00:00:00Z",
            failed_at=None,
            config=config,
        )
        destination = FivetranDestination(id="test_group", database="test_db", service="bigquery")
        schema_config = FivetranSchemaConfig.from_schema_config_details(
            {
                "schemas": {
                    "schema1": {
                        "name_in_destination": "test_schema",
                        "enabled": True,
                        "tables": {
                            "table1": {
                                "name_in_destination": table_name,
                                "enabled": True,
                                "columns": {},
                            }
                        },
                    }
                }
            }
        )
        workspace_data = FivetranWorkspaceData(
            connectors_by_id={connector.id: connector},
            destinations_by_id={destination.id: destination},
            schema_configs_by_connector_id={connector.id: schema_config},
        )
        return list(workspace_data.to_fivetran_connector_table_props_data())

    translator = DagsterFivetranTranslator()

    # Test with custom_reports key - matching table
    config_with_custom_reports = {
        "custom_reports": [
            {"table_name": "my_custom_report", "dimensions": ["date", "campaign"]},
        ]
    }
    props = create_workspace_with_config(config_with_custom_reports, "my_custom_report")[0]
    asset_spec = translator.get_asset_spec(props)
    metadata_set = FivetranMetadataSet.extract(asset_spec.metadata)
    assert metadata_set.is_custom_report is True
    assert metadata_set.custom_report_config is not None
    custom_config = json.loads(metadata_set.custom_report_config)
    assert custom_config["table_name"] == "my_custom_report"

    # Test with custom_reports key - non-matching table
    props = create_workspace_with_config(config_with_custom_reports, "regular_table")[0]
    asset_spec = translator.get_asset_spec(props)
    metadata_set = FivetranMetadataSet.extract(asset_spec.metadata)
    assert metadata_set.is_custom_report is None
    assert metadata_set.custom_report_config is None

    # Test with reports key using 'table' field
    config_with_reports = {"reports": [{"table": "report_table", "type": "daily"}]}
    props = create_workspace_with_config(config_with_reports, "report_table")[0]
    asset_spec = translator.get_asset_spec(props)
    metadata_set = FivetranMetadataSet.extract(asset_spec.metadata)
    assert metadata_set.is_custom_report is True

    # Test with empty config
    props = create_workspace_with_config({}, "any_table")[0]
    asset_spec = translator.get_asset_spec(props)
    metadata_set = FivetranMetadataSet.extract(asset_spec.metadata)
    assert metadata_set.is_custom_report is None
    assert metadata_set.custom_report_config is None


def test_translator_custom_report_metadata_in_asset_spec() -> None:
    """Test that custom report metadata is included in asset specs when detected."""
    from dagster_fivetran.translator import (
        FivetranConnector,
        FivetranDestination,
        FivetranSchemaConfig,
        FivetranWorkspaceData,
    )

    # Create a connector with custom report config
    connector = FivetranConnector(
        id="test_connector",
        name="test_schema",
        service="google_ads",
        group_id="test_group",
        setup_state="connected",
        sync_state="scheduled",
        paused=False,
        succeeded_at="2024-01-01T00:00:00Z",
        failed_at=None,
        sync_frequency=360,
        schedule_type="auto",
        daily_sync_time="06:00",
        config={
            "custom_reports": [
                {
                    "table_name": "custom_campaign_report",
                    "dimensions": ["date", "campaign_id"],
                    "metrics": ["clicks", "impressions"],
                }
            ]
        },
    )

    destination = FivetranDestination(
        id="test_group",
        database="test_db",
        service="bigquery",
    )

    # Create schema config with the custom report table
    schema_config = FivetranSchemaConfig.from_schema_config_details(
        {
            "schemas": {
                "schema1": {
                    "name_in_destination": "test_schema",
                    "enabled": True,
                    "tables": {
                        "table1": {
                            "name_in_destination": "custom_campaign_report",
                            "enabled": True,
                            "columns": {},
                        }
                    },
                }
            }
        }
    )

    workspace_data = FivetranWorkspaceData(
        connectors_by_id={connector.id: connector},
        destinations_by_id={destination.id: destination},
        schema_configs_by_connector_id={connector.id: schema_config},
    )

    table_props_data = workspace_data.to_fivetran_connector_table_props_data()
    assert len(table_props_data) == 1

    props = table_props_data[0]
    assert props.table == "test_schema.custom_campaign_report"
    assert props.connector_config is not None

    # Get asset spec
    asset_spec = DagsterFivetranTranslator().get_asset_spec(props)
    metadata_set = FivetranMetadataSet.extract(asset_spec.metadata)

    # Verify custom report metadata
    assert metadata_set.is_custom_report is True
    assert metadata_set.custom_report_config is not None

    # Parse the JSON config
    custom_config = json.loads(metadata_set.custom_report_config)
    assert custom_config["table_name"] == "custom_campaign_report"
    assert custom_config["dimensions"] == ["date", "campaign_id"]
    assert custom_config["metrics"] == ["clicks", "impressions"]

    # Verify schedule metadata is also present
    assert metadata_set.sync_frequency_minutes == 360
    assert metadata_set.schedule_type == "auto"
    assert metadata_set.daily_sync_time == "06:00"


def test_translator_non_custom_report_metadata() -> None:
    """Test that non-custom-report tables have is_custom_report as None."""
    from dagster_fivetran.translator import (
        FivetranConnector,
        FivetranDestination,
        FivetranSchemaConfig,
        FivetranWorkspaceData,
    )

    # Create a connector without custom reports
    connector = FivetranConnector(
        id="test_connector",
        name="test_schema",
        service="postgres",
        group_id="test_group",
        setup_state="connected",
        sync_state="scheduled",
        paused=False,
        succeeded_at="2024-01-01T00:00:00Z",
        failed_at=None,
        sync_frequency=60,
        schedule_type="manual",
        daily_sync_time=None,
        config={"host": "localhost", "port": 5432},
    )

    destination = FivetranDestination(
        id="test_group",
        database="test_db",
        service="snowflake",
    )

    schema_config = FivetranSchemaConfig.from_schema_config_details(
        {
            "schemas": {
                "schema1": {
                    "name_in_destination": "public",
                    "enabled": True,
                    "tables": {
                        "table1": {
                            "name_in_destination": "users",
                            "enabled": True,
                            "columns": {},
                        }
                    },
                }
            }
        }
    )

    workspace_data = FivetranWorkspaceData(
        connectors_by_id={connector.id: connector},
        destinations_by_id={destination.id: destination},
        schema_configs_by_connector_id={connector.id: schema_config},
    )

    table_props_data = workspace_data.to_fivetran_connector_table_props_data()
    props = table_props_data[0]

    asset_spec = DagsterFivetranTranslator().get_asset_spec(props)
    metadata_set = FivetranMetadataSet.extract(asset_spec.metadata)

    # Non-custom-report tables should have None for these fields
    assert metadata_set.is_custom_report is None
    assert metadata_set.custom_report_config is None

    # But schedule metadata should still be present
    assert metadata_set.sync_frequency_minutes == 60
    assert metadata_set.schedule_type == "manual"
    assert metadata_set.daily_sync_time is None
