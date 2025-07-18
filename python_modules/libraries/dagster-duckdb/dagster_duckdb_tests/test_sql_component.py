import importlib
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

import pytest
import yaml
from dagster import AssetKey, Definitions
from dagster._core.definitions.materialize import materialize
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._utils import alter_sys_path
from dagster.components.core.tree import ComponentTree
from dagster.components.lib.sql_component.sql_component import SqlComponent


@contextmanager
def setup_duckdb_component_with_external_connection(
    execution_component_body: dict,
    connection_component_name: str = "sql_connection_component",
) -> Iterator[Definitions]:
    """Sets up a components project with a duckdb component using external connection."""
    with tempfile.TemporaryDirectory() as project_root_str:
        project_root = Path(project_root_str)
        defs_folder_path = project_root / "src" / "my_project" / "defs"
        defs_folder_path.mkdir(parents=True, exist_ok=True)

        # Create execution component
        execution_component_path = defs_folder_path / "sql_execution_component"
        execution_component_path.mkdir(parents=True, exist_ok=True)
        (execution_component_path / "defs.yaml").write_text(yaml.dump(execution_component_body))

        # Create connection component
        connection_body = {
            "type": "dagster_duckdb.DuckDBConnectionComponent",
            "attributes": {"database": ":memory:", "connection_config": {}},
        }
        connection_component_path = defs_folder_path / connection_component_name
        connection_component_path.mkdir(parents=True, exist_ok=True)
        (connection_component_path / "defs.yaml").write_text(yaml.dump(connection_body))

        with alter_sys_path(to_add=[str(project_root / "src")], to_remove=[]):
            defs = ComponentTree(
                defs_module=importlib.import_module("my_project.defs"),
                project_root=Path(project_root),
            ).build_defs()

            yield defs


@mock.patch("duckdb.connect")
def test_duckdb_sql_component(duckdb_connect):
    """Test that the TemplatedSqlComponent correctly builds and executes SQL."""
    mock_conn = mock.Mock()
    mock_conn.execute = mock.Mock()
    mock_conn.close = mock.Mock()
    duckdb_connect.return_value = mock_conn

    execution_body = {
        "type": "dagster.TemplatedSqlComponent",
        "attributes": {
            "sql_template": "SELECT * FROM test_table;",
            "assets": [{"key": "test_table"}],
            "connection": "{{ load_component_at_path('sql_connection_component') }}",
        },
    }

    with setup_duckdb_component_with_external_connection(
        execution_component_body=execution_body,
    ) as defs:
        asset_key = AssetKey(["test_table"])
        asset_def = defs.get_assets_def(asset_key)
        result = materialize(
            [asset_def],
        )
        assert result.success
        duckdb_connect.assert_called_once_with(
            database=":memory:",
            read_only=False,
            config={"custom_user_agent": "dagster"},
        )
        mock_conn.execute.assert_called_once_with("SELECT * FROM test_table;")
        assert defs.resolve_asset_graph().get_all_asset_keys() == {AssetKey(["test_table"])}


@pytest.mark.parametrize(
    "sql_template",
    [
        "SELECT * FROM test_table WHERE date = '{{ date }}' LIMIT {{ limit }}",
        None,  # This will trigger the file template test
    ],
)
@mock.patch("duckdb.connect")
def test_duckdb_sql_component_with_templates(duckdb_connect, sql_template):
    """Test that the TemplatedSqlComponent correctly handles SQL templates from strings and files."""
    mock_conn = mock.Mock()
    mock_conn.execute = mock.Mock()
    mock_conn.close = mock.Mock()
    duckdb_connect.return_value = mock_conn

    # If sql_template is None, create a temporary file with the template
    if sql_template is None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
            f.write("SELECT * FROM test_table WHERE date = '{{ date }}' LIMIT {{ limit }}")
            sql_file_path = f.name
            sql_template = {"path": sql_file_path}

    try:
        execution_body = {
            "type": "dagster.TemplatedSqlComponent",
            "attributes": {
                "sql_template": sql_template,
                "assets": [{"key": "test_table"}],
                "sql_template_vars": {
                    "date": "2024-03-20",
                    "limit": 100,
                },
                "connection": "{{ load_component_at_path('sql_connection_component') }}",
            },
        }
        with setup_duckdb_component_with_external_connection(
            execution_component_body=execution_body,
        ) as defs:
            asset_key = AssetKey(["test_table"])
            asset_def = defs.get_assets_def(asset_key)
            result = materialize(
                [asset_def],
            )
            assert result.success
            mock_conn.execute.assert_called_once_with(
                "SELECT * FROM test_table WHERE date = '2024-03-20' LIMIT 100"
            )
            assert defs.resolve_asset_graph().get_all_asset_keys() == {AssetKey(["test_table"])}
    finally:
        # Clean up the temporary file if it was created
        if isinstance(sql_template, dict) and "path" in sql_template:
            os.unlink(sql_template["path"])


@mock.patch("duckdb.connect")
def test_duckdb_sql_component_with_execution(duckdb_connect):
    """Test that the TemplatedSqlComponent correctly handles execution parameter with op description."""
    mock_conn = mock.Mock()
    mock_conn.execute = mock.Mock()
    mock_conn.close = mock.Mock()
    duckdb_connect.return_value = mock_conn

    execution_body = {
        "type": "dagster.TemplatedSqlComponent",
        "attributes": {
            "sql_template": "SELECT * FROM test_table;",
            "assets": [{"key": "test_table"}],
            "execution": {"description": "This is a test op description"},
            "connection": "{{ load_component_at_path('sql_connection_component') }}",
        },
    }
    with setup_duckdb_component_with_external_connection(
        execution_component_body=execution_body,
    ) as defs:
        asset_key = AssetKey(["test_table"])
        asset_def = defs.get_assets_def(asset_key)

        # Verify the op description is set correctly
        assert asset_def.op.description == "This is a test op description"

        # Materialize to actually execute the SQL
        result = materialize([asset_def])
        assert result.success


class CreateTableComponent(SqlComponent):
    """A custom component which creates a table in DuckDB."""

    table_name: str
    columns: str

    def get_sql_content(self, context: AssetExecutionContext) -> str:
        return f"CREATE TABLE IF NOT EXISTS {self.table_name} ({self.columns});"


@mock.patch("duckdb.connect")
def test_custom_duckdb_sql_component(duckdb_connect):
    """Test that a custom DuckDBSqlComponent subclass correctly builds and executes SQL."""
    mock_conn = mock.Mock()
    mock_conn.execute = mock.Mock()
    mock_conn.close = mock.Mock()
    duckdb_connect.return_value = mock_conn

    execution_body = {
        "type": "dagster_duckdb_tests.test_sql_component.CreateTableComponent",
        "attributes": {
            "table_name": "test_table",
            "columns": "id INTEGER PRIMARY KEY, name VARCHAR(100)",
            "assets": [{"key": "test_table"}],
            "connection": "{{ load_component_at_path('sql_connection_component') }}",
        },
    }

    with setup_duckdb_component_with_external_connection(
        execution_component_body=execution_body,
    ) as defs:
        asset_key = AssetKey(["test_table"])
        asset_def = defs.get_assets_def(asset_key)
        result = materialize(
            [asset_def],
        )
        assert result.success
        duckdb_connect.assert_called_once_with(
            database=":memory:",
            read_only=False,
            config={"custom_user_agent": "dagster"},
        )
        mock_conn.execute.assert_called_once_with(
            "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name VARCHAR(100));"
        )
        assert defs.resolve_asset_graph().get_all_asset_keys() == {AssetKey(["test_table"])}
