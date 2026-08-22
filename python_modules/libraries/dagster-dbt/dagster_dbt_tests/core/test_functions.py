"""Tests for dbt functions (UDFs), which are available in dbt-core 1.11+.

dbt functions are stored in the top-level `functions` collection of the manifest rather than
alongside models, seeds, and snapshots in `nodes`.
"""

import os
from typing import Any

import pytest
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetMaterialization,
    AssetSelection,
    TableColumnDep,
    materialize,
)
from dagster._core.definitions.metadata import TableMetadataSet, TextMetadataValue
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.compat import DBT_PYTHON_VERSION
from dagster_dbt.core.dbt_cli_event import DbtCoreCliEventMessage
from dagster_dbt.core.resource import DbtCliResource
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from dagster_dbt.metadata_set import DbtMetadataSet
from packaging import version

from dagster_dbt_tests.dbt_projects import test_dbt_functions_path

FUNCTION_UNIQUE_ID = "function.test_dagster_dbt_functions.is_positive_int"
FUNCTION_ASSET_KEY = AssetKey(["is_positive_int"])
# the model in the test project which calls the function
MODEL_USING_FUNCTION_ASSET_KEY = AssetKey(["customers_with_valid_ids"])

requires_dbt_functions = pytest.mark.skipif(
    DBT_PYTHON_VERSION is not None and DBT_PYTHON_VERSION < version.parse("1.11.0"),
    reason="dbt udf support is only available in `dbt-core>=1.11.0`",
)


def test_log_function_result_to_asset_materialization() -> None:
    """`LogFunctionResult` is the event dbt emits once a function has been created in the
    warehouse. Since function nodes are not in `manifest["nodes"]`, generating an event for one
    used to raise a `KeyError`.

    Below is an example of a `LogFunctionResult` produced by an actual dbt==1.11.12 invocation.
    """
    log_function_result = {
        "data": {
            "description": "function dev.is_positive_int",
            "execution_time": 0.038336992,
            "index": 1,
            "node_info": {
                "materialized": "function",
                "meta": {},
                "node_finished_at": "2026-08-06T02:27:11.441493",
                "node_name": "is_positive_int",
                "node_path": "is_positive_int.sql",
                "node_relation": {
                    "alias": "is_positive_int",
                    "database": "local",
                    "relation_name": "",
                    "schema": "dev",
                },
                "node_started_at": "2026-08-06T02:27:11.402435",
                "node_status": "success",
                "resource_type": "function",
                "unique_id": FUNCTION_UNIQUE_ID,
            },
            "status": "success",
            "total": 1,
        },
        "info": {
            "category": "",
            "code": "Q047",
            "extra": {},
            "invocation_id": "ff829904-01c6-49ed-b235-935d45582992",
            "level": "info",
            "msg": "1 of 1 OK created function dev.is_positive_int  [SUCCESS in 0.04s]",
            "name": "LogFunctionResult",
            "pid": 98784,
            "thread": "Thread-1 (worker)",
            "ts": "2026-08-06T02:27:11.441699Z",
        },
    }

    manifest = {
        "metadata": {
            "adapter_type": "duckdb",
            "invocation_id": "ff829904-01c6-49ed-b235-935d45582992",
        },
        "nodes": {},
        "functions": {
            FUNCTION_UNIQUE_ID: {
                "unique_id": FUNCTION_UNIQUE_ID,
                "name": "is_positive_int",
                "resource_type": "function",
                "database": "local",
                "schema": "dev",
                "alias": "is_positive_int",
                "original_file_path": "functions/is_positive_int.sql",
                "config": {"materialized": "function"},
                "depends_on": {"nodes": []},
                "description": "",
                "raw_code": "regexp_matches(a_string, '^[0-9]+$')::integer",
            }
        },
    }

    event_message = DbtCoreCliEventMessage(raw_event=log_function_result, event_history_metadata={})
    assert event_message.is_result_event

    [asset_event] = list(event_message.to_default_asset_events(manifest, DagsterDbtTranslator()))

    assert isinstance(asset_event, AssetMaterialization)
    assert asset_event.asset_key == FUNCTION_ASSET_KEY
    assert asset_event.metadata["unique_id"] == TextMetadataValue(FUNCTION_UNIQUE_ID)


@requires_dbt_functions
def test_function_asset_specs(test_dbt_functions_manifest: dict[str, Any]) -> None:
    @dbt_assets(manifest=test_dbt_functions_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource): ...

    # the function is an asset of its own
    assert FUNCTION_ASSET_KEY in my_dbt_assets.keys

    # and the model which calls it depends on it
    model_spec = my_dbt_assets.get_asset_spec(MODEL_USING_FUNCTION_ASSET_KEY)
    assert FUNCTION_ASSET_KEY in {dep.asset_key for dep in model_spec.deps}

    function_spec = my_dbt_assets.get_asset_spec(FUNCTION_ASSET_KEY)
    assert function_spec.deps == []
    assert DbtMetadataSet.extract(function_spec.metadata).materialization_type == "function"


@requires_dbt_functions
def test_select_only_functions(test_dbt_functions_manifest: dict[str, Any]) -> None:
    @dbt_assets(manifest=test_dbt_functions_manifest, select="resource_type:function")
    def my_dbt_functions(context: AssetExecutionContext, dbt: DbtCliResource): ...

    assert my_dbt_functions.keys == {FUNCTION_ASSET_KEY}


@requires_dbt_functions
def test_unselected_function_is_upstream_of_model(
    test_dbt_functions_manifest: dict[str, Any],
) -> None:
    """A function which is not selected is still an upstream dependency of the models which use
    it, in the same way that an unselected model is.
    """

    @dbt_assets(manifest=test_dbt_functions_manifest, select="resource_type:model")
    def my_dbt_models(context: AssetExecutionContext, dbt: DbtCliResource): ...

    assert FUNCTION_ASSET_KEY not in my_dbt_models.keys

    model_spec = my_dbt_models.get_asset_spec(MODEL_USING_FUNCTION_ASSET_KEY)
    assert FUNCTION_ASSET_KEY in {dep.asset_key for dep in model_spec.deps}


@requires_dbt_functions
def test_materialize_functions(test_dbt_functions_manifest: dict[str, Any]) -> None:
    @dbt_assets(manifest=test_dbt_functions_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from dbt.cli(["build"], context=context).stream()

    resources = {"dbt": DbtCliResource(project_dir=os.fspath(test_dbt_functions_path))}

    result = materialize([my_dbt_assets], resources=resources)
    assert result.success
    materialized_keys = {
        event.asset_key for event in result.get_asset_materialization_events() if event.asset_key
    }
    assert FUNCTION_ASSET_KEY in materialized_keys
    assert MODEL_USING_FUNCTION_ASSET_KEY in materialized_keys

    # subsetted execution: the function is selected by itself
    result = materialize(
        [my_dbt_assets], resources=resources, selection=AssetSelection.assets(FUNCTION_ASSET_KEY)
    )
    assert result.success
    assert [event.asset_key for event in result.get_asset_materialization_events()] == [
        FUNCTION_ASSET_KEY
    ]

    # subsetted execution: only the model which depends on the function is selected
    result = materialize(
        [my_dbt_assets],
        resources=resources,
        selection=AssetSelection.assets(MODEL_USING_FUNCTION_ASSET_KEY),
    )
    assert result.success
    assert [event.asset_key for event in result.get_asset_materialization_events()] == [
        MODEL_USING_FUNCTION_ASSET_KEY
    ]


@requires_dbt_functions
@pytest.mark.derived_metadata
def test_materialize_functions_with_derived_metadata(
    test_dbt_functions_manifest: dict[str, Any],
) -> None:
    @dbt_assets(manifest=test_dbt_functions_manifest)
    def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
        yield from (
            dbt.cli(["build"], context=context).stream().fetch_row_counts().fetch_column_metadata()
        )

    result = materialize(
        [my_dbt_assets],
        resources={"dbt": DbtCliResource(project_dir=os.fspath(test_dbt_functions_path))},
    )
    assert result.success

    materializations_by_key = {
        event.asset_key: event.materialization
        for event in result.get_asset_materialization_events()
        if event.asset_key
    }

    # a function is not a relation, so it has no rows to count and no columns to fetch
    function_table_metadata = TableMetadataSet.extract(
        materializations_by_key[FUNCTION_ASSET_KEY].metadata
    )
    assert function_table_metadata.row_count is None
    assert function_table_metadata.column_schema is None

    # a model which depends on a function still gets column lineage for its other dependencies
    model_column_lineage = TableMetadataSet.extract(
        materializations_by_key[MODEL_USING_FUNCTION_ASSET_KEY].metadata
    ).column_lineage
    assert model_column_lineage
    assert model_column_lineage.deps_by_column["customer_id"] == [
        TableColumnDep(asset_key=AssetKey(["stg_customers"]), column_name="customer_id")
    ]
