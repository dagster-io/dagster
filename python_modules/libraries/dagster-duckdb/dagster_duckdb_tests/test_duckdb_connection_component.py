import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Union

import duckdb
import pytest
from dagster import AssetKey, Definitions
from dagster._core.definitions.materialize import materialize
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.sql_component.sql_component import SqlComponent
from dagster.components.testing import create_defs_folder_sandbox
from dagster_duckdb.components.sql_component.component import DuckDBConnectionComponent
from dagster_shared import check


@contextmanager
def setup_duckdb_component_with_external_connection(
    execution_component_body: dict,
    connection_defs_path: Union[str, Path] = "sql_connection_component",
) -> Iterator[tuple[Definitions, str]]:
    """Sets up a components project with a duckdb component using external connection."""
    with tempfile.TemporaryDirectory() as project_root_str:
        # Create a temporary DuckDB database file with test data
        db_file = Path(project_root_str) / "test.duckdb"
        conn = duckdb.connect(str(db_file))
        conn.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER, name VARCHAR, date DATE)")
        conn.execute(
            "INSERT INTO test_table VALUES (1, 'Alice', '2024-03-20'), (2, 'Bob', '2024-03-21')"
        )
        conn.close()

        with create_defs_folder_sandbox() as sandbox:
            sandbox.scaffold_component(
                component_cls=SqlComponent,
                defs_path="sql_execution_component",
                defs_yaml_contents=execution_component_body,
            )

            sandbox.scaffold_component(
                component_cls=DuckDBConnectionComponent,
                defs_path=connection_defs_path,
                defs_yaml_contents={
                    "type": "dagster_duckdb.DuckDBConnectionComponent",
                    "attributes": {"database": str(db_file), "connection_config": {}},
                },
            )

            with sandbox.build_all_defs() as defs:
                yield defs, str(db_file)


def test_duckdb_sql_component():
    """Test that the TemplatedSqlComponent correctly builds and executes SQL."""
    execution_body = {
        "type": "dagster.TemplatedSqlComponent",
        "attributes": {
            "sql_template": "INSERT INTO test_table (id, name, date) VALUES (3, 'Charlie', '2024-03-22')",
            "assets": [{"key": "test_table_updated"}],
            "connection": "{{ load_component_at_path('sql_connection_component') }}",
        },
    }

    with setup_duckdb_component_with_external_connection(
        execution_component_body=execution_body,
    ) as (defs, db_path):
        asset_key = AssetKey(["test_table_updated"])
        asset_def = defs.get_assets_def(asset_key)
        result = materialize(
            [asset_def],
        )
        assert result.success
        assert defs.resolve_asset_graph().get_all_asset_keys() == {AssetKey(["test_table_updated"])}

        conn = duckdb.connect(db_path)
        try:
            # Verify we now have 3 rows (original 2 + the new one)
            rows = conn.execute("SELECT * FROM test_table ORDER BY id").fetchall()
            assert len(rows) == 3
            assert rows[0][1] == "Alice"
            assert rows[1][1] == "Bob"
            assert rows[2][1] == "Charlie"
        finally:
            conn.close()


@pytest.mark.parametrize(
    "sql_template",
    [
        "UPDATE test_table SET name = '{{ name_prefix }}' || name WHERE date = '{{ date }}'",
        None,  # This will load from a file instead of a SQL literal
    ],
)
def test_duckdb_sql_component_with_templates(sql_template):
    """Test that the TemplatedSqlComponent correctly handles SQL templates from strings and files."""
    if sql_template is None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
            f.write(
                "UPDATE test_table SET name = '{{ name_prefix }}' || name WHERE date = '{{ date }}'"
            )
            sql_file_path = f.name
            sql_template = {"path": sql_file_path}

    execution_body = {
        "type": "dagster.TemplatedSqlComponent",
        "attributes": {
            "sql_template": sql_template,
            "assets": [{"key": "test_table_updated"}],
            "sql_template_vars": {
                "date": "2024-03-20",
                "name_prefix": "Updated_",
            },
            "connection": "{{ load_component_at_path('sql_connection_component') }}",
        },
    }
    with setup_duckdb_component_with_external_connection(
        execution_component_body=execution_body,
    ) as (defs, db_path):
        asset_key = AssetKey(["test_table_updated"])
        asset_def = defs.get_assets_def(asset_key)
        result = materialize(
            [asset_def],
        )
        assert result.success
        assert defs.resolve_asset_graph().get_all_asset_keys() == {AssetKey(["test_table_updated"])}

        # Verify that the UPDATE statement actually modified the data
        conn = duckdb.connect(db_path)
        try:
            alice_row = check.not_none(
                conn.execute("SELECT name FROM test_table WHERE id = 1").fetchone()
            )
            assert alice_row[0] == "Updated_Alice"
        finally:
            conn.close()


def test_duckdb_sql_component_with_execution():
    """Test that the TemplatedSqlComponent correctly handles execution parameter with op description."""
    execution_body = {
        "type": "dagster.TemplatedSqlComponent",
        "attributes": {
            "sql_template": "DELETE FROM test_table WHERE id = 2",
            "assets": [{"key": "test_table_cleaned"}],
            "execution": {"description": "This is a test op description"},
            "connection": "{{ load_component_at_path('sql_connection_component') }}",
        },
    }
    with setup_duckdb_component_with_external_connection(
        execution_component_body=execution_body,
    ) as (defs, db_path):
        asset_key = AssetKey(["test_table_cleaned"])
        asset_def = defs.get_assets_def(asset_key)

        # Verify the op description is set correctly
        assert asset_def.op.description == "This is a test op description"

        result = materialize([asset_def])
        assert result.success

        conn = duckdb.connect(db_path)
        try:
            rows = conn.execute("SELECT * FROM test_table ORDER BY id").fetchall()
            assert len(rows) == 1
            assert rows[0][1] == "Alice"
        finally:
            conn.close()


class CreateTableComponent(SqlComponent):
    """A custom component which creates a table in DuckDB."""

    table_name: str
    columns: str

    def get_sql_content(
        self, context: AssetExecutionContext, component_load_context: ComponentLoadContext
    ) -> str:
        return f"CREATE TABLE IF NOT EXISTS {self.table_name} ({self.columns});"


def test_custom_duckdb_sql_component():
    """Test that a custom DuckDBSqlComponent subclass correctly builds and executes SQL."""
    execution_body = {
        "type": "dagster_duckdb_tests.test_duckdb_connection_component.CreateTableComponent",
        "attributes": {
            "table_name": "new_test_table",
            "columns": "id INTEGER PRIMARY KEY, name VARCHAR(100)",
            "assets": [{"key": "new_test_table"}],
            "connection": "{{ load_component_at_path('sql_connection_component') }}",
        },
    }

    with setup_duckdb_component_with_external_connection(
        execution_component_body=execution_body,
    ) as (defs, db_path):
        asset_key = AssetKey(["new_test_table"])
        asset_def = defs.get_assets_def(asset_key)
        result = materialize(
            [asset_def],
        )
        assert result.success
        assert defs.resolve_asset_graph().get_all_asset_keys() == {AssetKey(["new_test_table"])}

        # Verify that the CREATE TABLE statement actually created the new table

        # Connect to the database and verify the new table exists and has the correct schema
        conn = duckdb.connect(db_path)
        try:
            result_rows = conn.execute("DESCRIBE new_test_table").fetchall()
            column_info = {row[0]: row[1] for row in result_rows}
            assert "id" in column_info
            assert "name" in column_info
            assert "INTEGER" in column_info["id"].upper()
            assert "VARCHAR" in column_info["name"].upper()
            conn.execute("INSERT INTO new_test_table (id, name) VALUES (999, 'test_user')")
            query_result = check.not_none(
                conn.execute("SELECT name FROM new_test_table WHERE id = 999").fetchone()
            )
            assert query_result[0] == "test_user"
        finally:
            conn.close()


@pytest.mark.parametrize(
    "connection_defs_path,expected_resource_key",
    [
        ("sql_connection_component", "sql_connection_component"),
        (Path("connections/duckdb"), "connections__duckdb"),
        (Path("data/connections/primary-db"), "data__connections__primary_db"),
    ],
)
def test_duckdb_connection_component_resource_key_from_path(
    connection_defs_path, expected_resource_key
):
    """Test that resource keys are correctly generated from component paths."""
    execution_body = {
        "type": "dagster.TemplatedSqlComponent",
        "attributes": {
            "sql_template": "SELECT 1",
            "assets": [{"key": "test_asset"}],
            "connection": "{{ load_component_at_path('" + str(connection_defs_path) + "') }}",
        },
    }

    with setup_duckdb_component_with_external_connection(
        execution_component_body=execution_body,
        connection_defs_path=connection_defs_path,
    ) as (defs, _db_path):
        # Check that the connection component resource is exposed with correct key
        resources = defs.resources or {}

        # Verify the expected resource key exists
        assert expected_resource_key in resources

        # Verify it's actually a DuckDBResource
        resource_def = resources[expected_resource_key]
        from dagster_duckdb.resource import DuckDBResource

        assert isinstance(resource_def, DuckDBResource)
