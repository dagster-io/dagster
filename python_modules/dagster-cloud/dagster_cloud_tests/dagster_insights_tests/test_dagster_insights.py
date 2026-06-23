import os
from contextlib import nullcontext
from datetime import datetime

import pytest
from dagster import AssetExecutionContext, materialize
from dagster_cloud.dagster_insights import dbt_with_bigquery_insights, dbt_with_snowflake_insights
from dagster_cloud.dagster_insights.bigquery.bigquery_utils import (
    BIGQUERY_METADATA_BYTES_BILLED,
    BIGQUERY_METADATA_SLOTS_MS,
)
from dagster_cloud.dagster_insights.snowflake.dagster_snowflake_insights import (
    get_cost_data_for_hour,
)
from dagster_cloud.dagster_insights.snowflake.snowflake_utils import OPAQUE_ID_METADATA_KEY_PREFIX
from dagster_dbt import DbtCliResource, dbt_assets

from dagster_cloud_tests.dagster_insights_tests.conftest import (
    JAFFLE_SHOP_ASSET_KEYS,
    bigquery_client,
)


@pytest.mark.parametrize(
    "use_iterator_chain",
    [True, False],
)
def test_snowflake_asset_metadata_added(
    snowflake_manifest_path, snowflake_jaffle_dir, use_iterator_chain: bool
):
    @dbt_assets(manifest=snowflake_manifest_path)
    def jaffle_shop_dbt_assets(
        context: AssetExecutionContext,
        dbt: DbtCliResource,
    ):
        if use_iterator_chain:
            yield from (
                dbt.cli(["build", "--profile", "unittest"], context=context)
                .stream()
                .with_insights()
            )
        else:
            dbt_cli_invocation = dbt.cli(["build", "--profile", "unittest"], context=context)
            yield from dbt_with_snowflake_insights(context, dbt_cli_invocation)

    result = materialize(
        [jaffle_shop_dbt_assets],
        resources={
            "dbt": DbtCliResource(project_dir=os.fspath(snowflake_jaffle_dir)),
        },
    )

    asset_keys_with_metadata = set()
    for event in result.all_events:
        if event.event_type != "ASSET_OBSERVATION":
            continue
        for key in event.asset_observation_data.asset_observation.metadata.keys():
            if key.startswith(OPAQUE_ID_METADATA_KEY_PREFIX):
                asset_keys_with_metadata.add(
                    event.asset_observation_data.asset_observation.asset_key.to_user_string()
                )

    assert asset_keys_with_metadata == {
        "customers",
        "orders",
        "raw_customers",
        "raw_orders",
        "raw_payments",
        "stg_customers",
        "stg_orders",
        "stg_payments",
    }


def test_retrieving_cost_data():
    class MockResult:
        def __init__(self, result):
            self._result = result

        def fetchall(self):
            return self._result

    class MockSnowflakeResource:
        def get_connection(self):
            return nullcontext(self)

        def cursor(self):
            return nullcontext(self)

        def execute(self, query: str):
            assert "HAVING ARRAY_SIZE(opaque_ids)" in query
            return MockResult(
                [
                    [
                        '["model.jaffle_shop.customers:ed530106-5713-4dfe-8b34-e206cb9eed3e"]',
                        1,
                        "queryid1",
                    ],
                    [
                        '["model.jaffle_shop.orders:ed530106-5713-4dfe-8b34-e206cb9eed3e"]',
                        2,
                        "queryid2",
                    ],
                    [
                        '["model.jaffle_shop.stg_customers:ed530106-5713-4dfe-8b34-e206cb9eed3e"]',
                        3,
                        "queryid3",
                    ],
                ]
            )

    snowflake = MockSnowflakeResource()
    start_hour = datetime(2023, 1, 1, 1)
    end_hour = datetime(2023, 1, 1, 2)

    results = get_cost_data_for_hour(snowflake, start_hour, end_hour)  # ty: ignore[invalid-argument-type]
    assert set(results) == {
        ("model.jaffle_shop.customers:ed530106-5713-4dfe-8b34-e206cb9eed3e", 1.0, "queryid1"),
        ("model.jaffle_shop.orders:ed530106-5713-4dfe-8b34-e206cb9eed3e", 2.0, "queryid2"),
        ("model.jaffle_shop.stg_customers:ed530106-5713-4dfe-8b34-e206cb9eed3e", 3.0, "queryid3"),
    }


@pytest.mark.parametrize(
    "use_iterator_chain",
    [True, False],
)
def test_bigquery_asset_metadata_added(
    bigquery_manifest_path,
    bigquery_jaffle_dir,
    default_bigquery_client,
    use_iterator_chain: bool,
):
    @dbt_assets(manifest=bigquery_manifest_path)
    def jaffle_shop_dbt_assets(
        context: AssetExecutionContext,
        dbt: DbtCliResource,
    ):
        if use_iterator_chain:
            yield from (
                dbt.cli(["build", "--profile", "unittest"], context=context)
                .stream()
                .with_insights()
            )
        else:
            dbt_cli_invocation = dbt.cli(["build", "--profile", "unittest"], context=context)
            yield from dbt_with_bigquery_insights(context, dbt_cli_invocation)

    result = materialize(
        [jaffle_shop_dbt_assets],
        resources={
            "dbt": DbtCliResource(project_dir=os.fspath(bigquery_jaffle_dir)),
        },
    )

    asset_keys_with_metadata = set()
    for event in result.get_asset_observation_events():
        for key in event.asset_observation_data.asset_observation.metadata.keys():
            if key == BIGQUERY_METADATA_BYTES_BILLED or key == BIGQUERY_METADATA_SLOTS_MS:
                asset_keys_with_metadata.add(
                    event.asset_observation_data.asset_observation.asset_key.to_user_string()
                )

    assert asset_keys_with_metadata == JAFFLE_SHOP_ASSET_KEYS


@pytest.mark.parametrize(
    "bq_client_args",
    [
        ("US", "foo", None, None, "`foo`.`region-us`.INFORMATION_SCHEMA.JOBS"),
        (None, None, "US", "foo", "`foo`.`region-us`.INFORMATION_SCHEMA.JOBS"),
        ("EU", "bar", "US", "foo", "`bar`.`region-eu`.INFORMATION_SCHEMA.JOBS"),
        (None, None, None, None, None),
        (None, "foo", None, None, None),
        ("US", None, None, None, None),
    ],
)
def test_bigquery_client(bigquery_manifest_path, bigquery_jaffle_dir, bq_client_args):
    @dbt_assets(manifest=bigquery_manifest_path)
    def jaffle_shop_dbt_assets(
        context: AssetExecutionContext,
        dbt: DbtCliResource,
    ):
        dbt_cli_invocation = dbt.cli(["build", "--profile", "unittest"], context=context)
        yield from dbt_with_bigquery_insights(context, dbt_cli_invocation)

    client_location, client_project, dataset_location, dataset_project, expected_cost_table = (
        bq_client_args
    )
    with bigquery_client(
        client_location=client_location,
        client_project=client_project,
        dataset_location=dataset_location,
        dataset_project=dataset_project,
    ) as client:
        materialize(
            [jaffle_shop_dbt_assets],
            resources={
                "dbt": DbtCliResource(project_dir=os.fspath(bigquery_jaffle_dir)),
            },
        )

    if expected_cost_table is None:
        assert client.query.call_count == 0
    else:
        assert client.query.call_count == 1
        query_arg = client.query.call_args[0][0]
        assert f"FROM {expected_cost_table}" in query_arg


def test_bigquery_with_check_failures_cost_metadata_added(
    bigquery_with_check_failure_manifest_path,
    bigquery_with_check_failure_jaffle_dir,
    default_bigquery_client,
):
    @dbt_assets(manifest=bigquery_with_check_failure_manifest_path)
    def jaffle_shop_dbt_assets(
        context: AssetExecutionContext,
        dbt: DbtCliResource,
    ):
        dbt_cli_invocation = dbt.cli(["build", "--profile", "unittest"], context=context)
        yield from dbt_with_bigquery_insights(context, dbt_cli_invocation)

    result = materialize(
        [jaffle_shop_dbt_assets],
        resources={
            "dbt": DbtCliResource(project_dir=os.fspath(bigquery_with_check_failure_jaffle_dir)),
        },
        raise_on_error=False,
    )

    asset_keys_with_metadata = set()
    for event in result.get_asset_observation_events():
        for key in event.asset_observation_data.asset_observation.metadata.keys():
            if key == BIGQUERY_METADATA_BYTES_BILLED or key == BIGQUERY_METADATA_SLOTS_MS:
                asset_keys_with_metadata.add(
                    event.asset_observation_data.asset_observation.asset_key.to_user_string()
                )

    assert asset_keys_with_metadata == JAFFLE_SHOP_ASSET_KEYS
    assert not result.success


def test_bigquery_with_execution_project(
    bigquery_with_execution_project_manifest_path,
    bigquery_with_execution_project_jaffle_dir,
    bigquery_client_with_execution_project,
):
    @dbt_assets(manifest=bigquery_with_execution_project_manifest_path)
    def jaffle_shop_dbt_assets(
        context: AssetExecutionContext,
        dbt: DbtCliResource,
    ):
        dbt_cli_invocation = dbt.cli(["build", "--profile", "unittest"], context=context)
        yield from dbt_with_bigquery_insights(context, dbt_cli_invocation)

    result = materialize(
        [jaffle_shop_dbt_assets],
        resources={
            "dbt": DbtCliResource(
                project_dir=os.fspath(bigquery_with_execution_project_jaffle_dir)
            ),
        },
        raise_on_error=False,
    )

    asset_keys_with_metadata = set()
    for event in result.get_asset_observation_events():
        for key in event.asset_observation_data.asset_observation.metadata.keys():
            if key == BIGQUERY_METADATA_BYTES_BILLED or key == BIGQUERY_METADATA_SLOTS_MS:
                asset_keys_with_metadata.add(
                    event.asset_observation_data.asset_observation.asset_key.to_user_string()
                )

    assert asset_keys_with_metadata == JAFFLE_SHOP_ASSET_KEYS
    assert not result.success

    # Assert that the query was executed in the execution project, not the default project
    assert (
        "`fake_exec_project`.`region-us`.INFORMATION_SCHEMA.JOBS"
        in bigquery_client_with_execution_project.query.call_args[0][0]
    )
