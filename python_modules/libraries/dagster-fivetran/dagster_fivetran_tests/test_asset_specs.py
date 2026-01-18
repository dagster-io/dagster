from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

import pytest
import responses
from click.testing import CliRunner
from dagster import Failure
from dagster._config.field_utils import EnvVar
from dagster._core.code_pointer import CodePointer
from dagster._core.definitions import materialize
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.reconstruct import initialize_repository_def_from_pointer
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.instance_for_test import instance_for_test
from dagster._core.test_utils import environ
from dagster_fivetran import (
    DagsterFivetranTranslator,
    FivetranConnectorTableProps,
    FivetranWorkspace,
    fivetran_assets,
    load_fivetran_asset_specs,
)
from dagster_fivetran.asset_defs import build_fivetran_assets_definitions
from dagster_fivetran.translator import FivetranMetadataSet

from dagster_fivetran_tests.conftest import (
    TEST_ACCOUNT_ID,
    TEST_ANOTHER_ACCOUNT_ID,
    TEST_API_KEY,
    TEST_API_SECRET,
    TEST_CONNECTOR_ID,
    TEST_CONNECTOR_NAME,
    TEST_DESTINATION_ID,
    TEST_DESTINATION_SERVICE,
)


def test_fetch_fivetran_workspace_data(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    actual_workspace_data = resource.get_or_fetch_workspace_data()
    assert len(actual_workspace_data.connectors_by_id) == 1
    assert len(actual_workspace_data.destinations_by_id) == 1


@pytest.mark.parametrize(
    "attribute, value, expected_result_before_selection, expected_result_after_selection",
    [
        (None, None, 1, 1),
        ("name", TEST_CONNECTOR_NAME, 1, 1),
        ("id", TEST_CONNECTOR_ID, 1, 1),
        ("service", TEST_DESTINATION_SERVICE, 1, 1),
        ("name", "non_matching_name", 1, 0),
        ("id", "non_matching_id", 1, 0),
        ("service", "non_matching_service", 1, 0),
    ],
    ids=[
        "no_selector_present_connector",
        "connector_name_selector_present_connector",
        "connector_id_selector_present_connector",
        "service_selector_present_connector",
        "connector_name_selector_absent_connector",
        "connector_id_selector_absent_connector",
        "service_selector_absent_connector",
    ],
)
def test_fivetran_connector_selector(
    attribute: str,
    value: str,
    expected_result_before_selection: int,
    expected_result_after_selection: int,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    connector_selector_fn = (
        (lambda connector: getattr(connector, attribute) == value) if attribute else None
    )
    workspace_data = resource.get_or_fetch_workspace_data()
    assert len(workspace_data.connectors_by_id) == expected_result_before_selection

    workspace_data_selection = workspace_data.to_workspace_data_selection(
        connector_selector_fn=connector_selector_fn
    )
    assert len(workspace_data_selection.connectors_by_id) == expected_result_after_selection


def test_missing_schemas_fivetran_workspace_data(
    missing_schemas_fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    actual_workspace_data = resource.get_or_fetch_workspace_data()
    # The connector is discarded because it's missing its schemas
    assert len(actual_workspace_data.connectors_by_id) == 0
    assert len(actual_workspace_data.destinations_by_id) == 1


def test_incomplete_connector_fivetran_workspace_data(
    incomplete_connector_fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    actual_workspace_data = resource.get_or_fetch_workspace_data()
    # The connector is discarded because it's incomplete
    assert len(actual_workspace_data.connectors_by_id) == 0
    assert len(actual_workspace_data.destinations_by_id) == 1


def test_broken_connector_fivetran_workspace_data(
    broken_connector_fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    actual_workspace_data = resource.get_or_fetch_workspace_data()
    # The connector is discarded because it's broken
    assert len(actual_workspace_data.connectors_by_id) == 0
    assert len(actual_workspace_data.destinations_by_id) == 1


def test_not_found_schema_config_fivetran_workspace_data(
    not_found_schema_config_fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    actual_workspace_data = resource.get_or_fetch_workspace_data()
    # The connector is discarded because it's broken
    assert len(actual_workspace_data.connectors_by_id) == 0
    assert len(actual_workspace_data.destinations_by_id) == 1


def test_other_error_schema_config_fivetran_workspace_data(
    other_error_schema_config_fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = FivetranWorkspace(
        account_id=TEST_ACCOUNT_ID, api_key=TEST_API_KEY, api_secret=TEST_API_SECRET
    )

    with pytest.raises(Failure):
        resource.get_or_fetch_workspace_data()


def test_translator_spec(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        resource = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        all_assets = load_fivetran_asset_specs(resource)
        all_assets_keys = [asset.key for asset in all_assets]

        # 4 tables for the connector
        assert len(all_assets) == 4
        assert len(all_assets_keys) == 4

        # Sanity check outputs, translator tests cover details here
        first_asset_key = next(key for key in all_assets_keys)
        assert first_asset_key.path == [
            "schema_name_in_destination_1",
            "table_name_in_destination_1",
        ]

        first_asset_metadata = next(asset.metadata for asset in all_assets)
        assert FivetranMetadataSet.extract(first_asset_metadata).connector_id == TEST_CONNECTOR_ID
        assert (
            FivetranMetadataSet.extract(first_asset_metadata).connector_name == TEST_CONNECTOR_NAME
        )
        assert (
            FivetranMetadataSet.extract(first_asset_metadata).destination_id == TEST_DESTINATION_ID
        )


def test_cached_load_spec_single_resource(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        workspace = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        # load asset specs a first time
        workspace.load_asset_specs()
        assert len(fetch_workspace_data_api_mocks.calls) == 4

        # load asset specs a first time, no additional calls are made
        workspace.load_asset_specs()
        assert len(fetch_workspace_data_api_mocks.calls) == 4


def test_cached_load_spec_multiple_resources(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        workspace = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        another_workspace = FivetranWorkspace(
            account_id=TEST_ANOTHER_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        # load asset specs with a resource
        workspace.load_asset_specs()
        assert len(fetch_workspace_data_api_mocks.calls) == 4

        # load asset specs with another resource,
        # additional calls are made to load its specs
        another_workspace.load_asset_specs()
        assert len(fetch_workspace_data_api_mocks.calls) == 4 + 4


def test_cached_load_spec_with_asset_factory(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        resource = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        # build_fivetran_assets_definitions calls load_fivetran_asset_specs to get the connector IDs,
        # then load_fivetran_asset_specs is called once per connector ID in fivetran_assets
        build_fivetran_assets_definitions(workspace=resource)
        assert len(fetch_workspace_data_api_mocks.calls) == 4


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
        workspace = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        all_asset_specs = load_fivetran_asset_specs(
            workspace=workspace, dagster_fivetran_translator=MyCustomTranslator()
        )
        asset_spec = next(spec for spec in all_asset_specs)

        assert "custom" in asset_spec.metadata
        assert asset_spec.metadata["custom"] == "metadata"
        assert asset_spec.key.path == [
            "prefix",
            "schema_name_in_destination_1",
            "table_name_in_destination_1",
        ]
        assert "dagster/kind/fivetran" in asset_spec.tags


class MyCustomTranslatorWackyKeys(DagsterFivetranTranslator):
    def get_asset_spec(self, props: FivetranConnectorTableProps) -> AssetSpec:
        default_spec = super().get_asset_spec(props)
        return default_spec.replace_attributes(
            key=["wacky", *["".join(reversed(item)) for item in default_spec.key.path], "wow"],
        )


@pytest.mark.parametrize(
    "translator, expected_key",
    [
        (
            MyCustomTranslator,
            AssetKey(["prefix", "schema_name_in_destination_1", "table_name_in_destination_1"]),
        ),
        (
            MyCustomTranslatorWackyKeys,
            AssetKey(
                ["wacky", "1_noitanitsed_ni_eman_amehcs", "1_noitanitsed_ni_eman_elbat", "wow"]
            ),
        ),
    ],
    ids=["custom_translator", "custom_translator_wacky_keys"],
)
def test_translator_custom_metadata_materialize(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
    sync_and_poll: MagicMock,
    translator: type[DagsterFivetranTranslator],
    expected_key: AssetKey,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        resource = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        @fivetran_assets(
            connector_id=TEST_CONNECTOR_ID,
            workspace=resource,
            dagster_fivetran_translator=translator(),
        )
        def my_fivetran_assets_def(context: AssetExecutionContext, fivetran: FivetranWorkspace):
            yield from fivetran.sync_and_poll(context=context)

        result = materialize([my_fivetran_assets_def], resources={"fivetran": resource})

        assert result.success
        asset_materializations = [
            event
            for event in result.all_events
            if event.event_type_value == "ASSET_MATERIALIZATION"
        ]
        assert len(asset_materializations) == 4
        materialized_asset_keys = {
            asset_materialization.asset_key for asset_materialization in asset_materializations
        }
        assert len(materialized_asset_keys) == 4
        assert my_fivetran_assets_def.keys == materialized_asset_keys
        assert expected_key in materialized_asset_keys


class MyCustomTranslatorWithGroupName(DagsterFivetranTranslator):
    def get_asset_spec(self, data: FivetranConnectorTableProps) -> AssetSpec:  # pyright: ignore[reportIncompatibleMethodOverride]
        default_spec = super().get_asset_spec(data)
        return default_spec.replace_attributes(group_name="my_group_name")


def test_translator_custom_group_name_with_asset_factory(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        resource = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        my_fivetran_assets = build_fivetran_assets_definitions(
            workspace=resource, dagster_fivetran_translator=MyCustomTranslatorWithGroupName()
        )

        first_assets_def = next(assets_def for assets_def in my_fivetran_assets)
        first_asset_spec = next(asset_spec for asset_spec in first_assets_def.specs)
        assert first_asset_spec.group_name == "my_group_name"


def test_translator_invariant_group_name_with_asset_decorator(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ({"FIVETRAN_API_KEY": TEST_API_KEY, "FIVETRAN_API_SECRET": TEST_API_SECRET}):
        resource = FivetranWorkspace(
            account_id=TEST_ACCOUNT_ID,
            api_key=EnvVar("FIVETRAN_API_KEY"),
            api_secret=EnvVar("FIVETRAN_API_SECRET"),
        )

        with pytest.raises(
            DagsterInvariantViolationError,
            match="Cannot set group_name parameter on fivetran_assets",
        ):

            @fivetran_assets(
                connector_id=TEST_CONNECTOR_ID,
                workspace=resource,
                group_name="my_asset_decorator_group_name",
                dagster_fivetran_translator=MyCustomTranslatorWithGroupName(),
            )
            def my_fivetran_assets(): ...


@pytest.mark.parametrize(
    "pending_repo, expected_assets",
    [
        ("pending_repo_snapshot.py", 0),
        ("pending_repo_snapshot_with_assets.py", 4),
    ],
    ids=[
        "pending_repo_snapshot_without_assets",
        "pending_repo_snapshot_with_assets",
    ],
)
def test_load_fivetran_specs_with_snapshot(
    pending_repo: str,
    expected_assets: int,
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with instance_for_test() as _instance, TemporaryDirectory() as temp_dir:
        from dagster_fivetran.cli import fivetran_snapshot_command

        temp_file = Path(temp_dir) / "snapshot.snap"
        out = CliRunner().invoke(
            fivetran_snapshot_command,
            args=[
                "-f",
                str(Path(__file__).parent / pending_repo),
                "--output-path",
                str(temp_file),
            ],
        )
        assert out.exit_code == 0

        calls = len(responses.calls)
        # Ensure that we can reconstruct the repository from the snapshot without making any calls
        with environ({"FIVETRAN_SNAPSHOT_PATH": str(temp_file)}):
            repository_def = initialize_repository_def_from_pointer(
                CodePointer.from_python_file(
                    str(Path(__file__).parent / pending_repo), "defs", None
                ),
            )
            assert len(repository_def.assets_defs_by_key) == expected_assets

            assert len(responses.calls) == calls
