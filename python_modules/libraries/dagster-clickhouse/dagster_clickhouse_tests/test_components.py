"""dg component scaffold and TemplatedSqlComponent materialization against real ClickHouse."""

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from dagster import AssetKey
from dagster._core.definitions.materialize import materialize
from dagster.components.lib.sql_component.sql_component import SqlComponent
from dagster.components.testing import create_defs_folder_sandbox
from dagster_clickhouse import ClickhouseQueryComponent

pytestmark = pytest.mark.filterwarnings("ignore::dagster.PreviewWarning")


@contextmanager
def setup_clickhouse_component_with_external_connection(
    execution_component_body: dict,
    clickhouse_connection: dict,
    connection_component_name: str = "sql_connection_component",
) -> Iterator:
    """Components project with ClickHouse connection + templated SQL execution (real server)."""
    with create_defs_folder_sandbox() as sandbox:
        sandbox.scaffold_component(
            component_cls=SqlComponent,
            defs_path="sql_execution_component",
            defs_yaml_contents=execution_component_body,
        )

        sandbox.scaffold_component(
            component_cls=ClickhouseQueryComponent,
            defs_path=connection_component_name,
            defs_yaml_contents={
                "type": "dagster_clickhouse.ClickhouseQueryComponent",
                "attributes": {
                    "host": clickhouse_connection["host"],
                    "port": clickhouse_connection["port"],
                    "user": clickhouse_connection["user"],
                    "password": clickhouse_connection["password"],
                    "database": clickhouse_connection["database"],
                },
            },
        )

        with sandbox.build_all_defs() as defs:
            yield defs


def test_clickhouse_query_component_scaffold_creates_defs():
    """Scaffold ClickhouseQueryComponent and verify defs.yaml is written (no live server)."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=ClickhouseQueryComponent,
            defs_yaml_contents={
                "type": "dagster_clickhouse.ClickhouseQueryComponent",
                "attributes": {
                    "host": "localhost",
                    "port": 9000,
                    "user": "default",
                    "password": "",
                    "database": "default",
                },
            },
        )
        assert (sandbox.project_root / defs_path / "defs.yaml").exists()


@pytest.mark.integration
def test_templated_sql_component_materialize(clickhouse_connection):
    """TemplatedSqlComponent executes SQL via ClickhouseQueryComponent (no mocks)."""
    execution_body = {
        "type": "dagster.TemplatedSqlComponent",
        "attributes": {
            "sql_template": "SELECT 1 AS one",
            "assets": [{"key": "CH/TESTDB/TEST_TABLE"}],
            "connection": "{{ context.load_component('sql_connection_component') }}",
        },
    }
    with setup_clickhouse_component_with_external_connection(
        execution_component_body=execution_body,
        clickhouse_connection=clickhouse_connection,
    ) as defs:
        asset_key = AssetKey(["CH", "TESTDB", "TEST_TABLE"])
        asset_def = defs.get_assets_def(asset_key)
        result = materialize([asset_def])
        assert result.success
        assert defs.resolve_asset_graph().get_all_asset_keys() == {asset_key}
