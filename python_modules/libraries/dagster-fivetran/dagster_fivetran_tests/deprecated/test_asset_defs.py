from unittest.mock import MagicMock

import pytest
import responses
from dagster import AssetKey, DagsterStepOutputNotFoundError
from dagster._core.definitions import materialize
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.test_utils import environ
from dagster_fivetran import (
    DagsterFivetranTranslator,
    FivetranConnectorTableProps,
    fivetran_resource,
)
from dagster_fivetran.asset_defs import build_fivetran_assets, load_assets_from_fivetran_instance
from dagster_fivetran.resources import (
    FIVETRAN_API_BASE,
    FIVETRAN_API_VERSION_PATH,
    FIVETRAN_CONNECTOR_PATH,
    FivetranResource,
)

from dagster_fivetran_tests.conftest import TEST_API_KEY, TEST_API_SECRET, TEST_CONNECTOR_ID
from dagster_fivetran_tests.deprecated.utils import (
    DEFAULT_CONNECTOR_ID,
    get_sample_columns_response,
    get_sample_connector_response,
    get_sample_connector_schema_config,
    get_sample_sync_response,
    get_sample_update_response,
)


def test_fivetran_asset_keys():
    ft_assets = build_fivetran_assets(
        connector_id=DEFAULT_CONNECTOR_ID, destination_tables=["x.foo", "y.bar"]
    )
    assert ft_assets[0].keys == {AssetKey(["x", "foo"]), AssetKey(["y", "bar"])}


@pytest.mark.parametrize(
    "group_name,expected_group_name",
    [
        (None, "default"),
        ("my_group_name", "my_group_name"),
    ],
)
def test_fivetran_group_label(group_name, expected_group_name):
    ft_assets = build_fivetran_assets(
        connector_id=DEFAULT_CONNECTOR_ID,
        destination_tables=["x.foo", "y.bar"],
        group_name=group_name,
    )
    group_names = set(ft_assets[0].group_names_by_key.values())
    assert len(group_names) == 1
    assert next(iter(group_names)) == expected_group_name


@pytest.mark.parametrize("schema_prefix", ["", "the_prefix"])
@pytest.mark.parametrize(
    "tables,infer_missing_tables,should_error",
    [
        (["schema1.tracked"], False, False),
        (["schema1.tracked", "schema2.tracked"], False, False),
        (["does.not_exist"], False, True),
        (["schema1.tracked", "does.not_exist"], False, True),
        (["schema1.tracked", "does.not_exist"], True, False),
    ],
)
@pytest.mark.parametrize("op_tags", [None, {"key1": "value1"}])
def test_fivetran_asset_run(tables, infer_missing_tables, should_error, schema_prefix, op_tags):
    ft_resource = fivetran_resource.configured({"api_key": "foo", "api_secret": "bar"})
    final_data = {"succeeded_at": "2021-01-01T02:00:00.0Z"}
    api_prefix = f"{FIVETRAN_API_BASE}/{FIVETRAN_API_VERSION_PATH}{FIVETRAN_CONNECTOR_PATH}{DEFAULT_CONNECTOR_ID}"

    if schema_prefix:
        tables = [f"{schema_prefix}_{t}" for t in tables]

    fivetran_assets = build_fivetran_assets(
        connector_id=DEFAULT_CONNECTOR_ID,
        destination_tables=tables,
        poll_interval=0.1,
        poll_timeout=10,
        infer_missing_tables=infer_missing_tables,
        op_tags=op_tags,
    )

    # expect the multi asset to have one asset key and one output for each specified asset key
    assert fivetran_assets[0].keys == {AssetKey(table.split(".")) for table in tables}
    assert len(fivetran_assets[0].op.output_defs) == len(tables)

    assert fivetran_assets[0].op.tags == (op_tags or {})

    with responses.RequestsMock() as rsps:
        rsps.add(rsps.PATCH, api_prefix, json=get_sample_update_response())
        rsps.add(rsps.POST, f"{api_prefix}/force", json=get_sample_sync_response())
        # connector schema
        rsps.add(
            rsps.GET,
            f"{api_prefix}/schemas",
            json=get_sample_connector_schema_config(
                tables=[
                    ("schema1", "tracked"),
                    ("schema1", "untracked"),
                    ("schema2", "tracked"),
                ]
            ),
        )
        # initial state
        rsps.add(
            rsps.GET,
            api_prefix,
            json=get_sample_connector_response(),
        )

        final_json = get_sample_connector_response(data=final_data)
        if schema_prefix:
            final_json["data"]["config"]["schema_prefix"] = schema_prefix  # pyright: ignore[reportOptionalSubscript,reportArgumentType,reportIndexIssue]
        # final state will be updated
        rsps.add(rsps.GET, api_prefix, json=final_json)

        for schema, table in [
            ("schema1", "tracked"),
            ("schema1", "untracked"),
            ("schema2", "tracked"),
        ]:
            rsps.add(
                rsps.GET,
                f"{api_prefix}/schemas/{schema}/tables/{table}/columns",
                json=get_sample_columns_response(),
            )

        if should_error:
            with pytest.raises(DagsterStepOutputNotFoundError):
                materialize(fivetran_assets, resources={"fivetran": ft_resource})
        else:
            result = materialize(fivetran_assets, resources={"fivetran": ft_resource})
            assert result.success
            # make sure we only have outputs for the explicit asset keys
            outputs = [
                event
                for event in result.events_for_node(f"fivetran_sync_{DEFAULT_CONNECTOR_ID}")
                if event.event_type_value == "STEP_OUTPUT"
            ]
            assert len(outputs) == len(tables)

            # make sure we have asset materializations for all the schemas/tables that were actually sync'd
            asset_materializations = [
                event
                for event in result.events_for_node(f"fivetran_sync_{DEFAULT_CONNECTOR_ID}")
                if event.event_type_value == "ASSET_MATERIALIZATION"
            ]
            assert len(asset_materializations) == 4 if infer_missing_tables else 3
            found_asset_keys = set(
                mat.event_specific_data.materialization.asset_key  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
                for mat in asset_materializations
            )
            if schema_prefix:
                assert found_asset_keys == {
                    AssetKey(["the_prefix_schema1", "tracked"]),
                    AssetKey(["the_prefix_schema1", "untracked"]),
                    AssetKey(["the_prefix_schema2", "tracked"]),
                } | (
                    {AssetKey(["the_prefix_does", "not_exist"])} if infer_missing_tables else set()
                )
            else:
                assert found_asset_keys == {
                    AssetKey(["schema1", "tracked"]),
                    AssetKey(["schema1", "untracked"]),
                    AssetKey(["schema2", "tracked"]),
                } | ({AssetKey(["does", "not_exist"])} if infer_missing_tables else set())


class MyCustomTranslator(DagsterFivetranTranslator):
    def get_asset_spec(self, props: FivetranConnectorTableProps) -> AssetSpec:
        default_spec = super().get_asset_spec(props)
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("prefix"),
            metadata={**default_spec.metadata, "custom": "metadata"},
        )


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
        resource = FivetranResource(api_key=TEST_API_KEY, api_secret=TEST_API_SECRET)
        my_cacheable_fivetran_assets = load_assets_from_fivetran_instance(
            fivetran=resource, fetch_column_metadata=False, translator=translator
        )
        my_fivetran_assets = my_cacheable_fivetran_assets.build_definitions(
            my_cacheable_fivetran_assets.compute_cacheable_data()
        )
        my_fivetran_assets_def = next(
            assets_def
            for assets_def in my_fivetran_assets
            if TEST_CONNECTOR_ID in assets_def.op.name
        )
        result = materialize(
            [my_fivetran_assets_def],
        )

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
