import os
from typing import Any, Dict, cast

from dagster import (
    AssetExecutionContext,
    Output,
    TableColumn,
    TableSchema,
    materialize,
)
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.core.resources_v2 import DbtCliResource

from ...dbt_projects import test_jaffle_shop_path, test_metadata_path


def test_no_columns_metadata(test_jaffle_shop_manifest: Dict[str, Any]) -> None:
    @dbt_assets(manifest=test_jaffle_shop_manifest)
    def assert_no_columns_metadata(context: AssetExecutionContext, dbt: DbtCliResource):
        events = list(dbt.cli(["build"], context=context).stream())
        output_by_dbt_unique_id: Dict[str, Output] = {
            cast(str, dagster_event.metadata["unique_id"].value): dagster_event
            for dagster_event in events
            if isinstance(dagster_event, Output)
        }

        for output in output_by_dbt_unique_id.values():
            assert "columns" not in output.metadata

        yield from events

    result = materialize(
        [assert_no_columns_metadata],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_jaffle_shop_path))},
    )

    assert result.success


def test_columns_metadata(test_metadata_manifest: Dict[str, Any]) -> None:
    @dbt_assets(manifest=test_metadata_manifest)
    def assert_columns_metadata(context: AssetExecutionContext, dbt: DbtCliResource):
        events = list(dbt.cli(["build"], context=context).stream())
        output_by_dbt_unique_id: Dict[str, Output] = {
            cast(str, dagster_event.metadata["unique_id"].value): dagster_event
            for dagster_event in events
            if isinstance(dagster_event, Output)
        }

        for output in output_by_dbt_unique_id.values():
            assert "columns" in output.metadata

        customers_output = output_by_dbt_unique_id["model.test_dagster_metadata.customers"]
        assert (
            TableSchema(
                columns=[
                    TableColumn("customer_id", type="INTEGER"),
                    TableColumn("first_name", type="character varying(256)"),
                    TableColumn("last_name", type="character varying(256)"),
                    TableColumn("first_order", type="DATE"),
                    TableColumn("most_recent_order", type="DATE"),
                    TableColumn("number_of_orders", type="BIGINT"),
                    TableColumn("customer_lifetime_value", type="DOUBLE"),
                ]
            )
            == customers_output.metadata["columns"].value
        )

        yield from events

    result = materialize(
        [assert_columns_metadata],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_metadata_path))},
    )

    assert result.success


def test_dbt_cli_no_jinja_log_info() -> None:
    dbt = DbtCliResource(project_dir=os.fspath(test_metadata_path))
    dbt_cli_parse_invocation = dbt.cli(["parse"])

    assert dbt_cli_parse_invocation.is_successful()
    assert not any(
        event.raw_event["info"]["name"] == "JinjaLogInfo"
        for event in dbt_cli_parse_invocation.stream_raw_events()
    )
