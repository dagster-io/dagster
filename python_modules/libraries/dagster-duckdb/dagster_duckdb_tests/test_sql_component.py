import importlib
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import duckdb
import pytest
import yaml
from dagster import AssetKey, Definitions
from dagster._check import check
from dagster._core.definitions.materialize import materialize
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._utils import alter_sys_path
from dagster.components.core.tree import ComponentTree
from dagster.components.lib.sql_component.sql_component import SqlComponent


@contextmanager
def setup_duckdb_component_with_external_connection(
    execution_component_body: dict,
    connection_component_name: str = "sql_connection_component",
) -> Iterator[tuple[Definitions, str]]:
    """Sets up a components project with a duckdb component using external connection."""
    with tempfile.TemporaryDirectory() as project_root_str:
        project_root = Path(project_root_str)
        defs_folder_path = project_root / "src" / "my_project" / "defs"
        defs_folder_path.mkdir(parents=True, exist_ok=True)

        # Create a temporary DuckDB database file with test data
        db_file = project_root / "test.duckdb"
        conn = duckdb.connect(str(db_file))
        conn.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER, name VARCHAR, date DATE)")
        conn.execute(
            "INSERT INTO test_table VALUES (1, 'Alice', '2024-03-20'), (2, 'Bob', '2024-03-21')"
        )
        conn.close()

        # Create execution component
        execution_component_path = defs_folder_path / "sql_execution_component"
        execution_component_path.mkdir(parents=True, exist_ok=True)
        (execution_component_path / "defs.yaml").write_text(yaml.dump(execution_component_body))

        # Create connection component
        connection_body = {
            "type": "dagster_duckdb.DuckDBConnectionComponent",
            "attributes": {"database": str(db_file), "connection_config": {}},
        }
        connection_component_path = defs_folder_path / connection_component_name
        connection_component_path.mkdir(parents=True, exist_ok=True)
        (connection_component_path / "defs.yaml").write_text(yaml.dump(connection_body))

        with alter_sys_path(to_add=[str(project_root / "src")], to_remove=[]):
            defs = ComponentTree(
                defs_module=importlib.import_module("my_project.defs"),
                project_root=Path(project_root),
            ).build_defs()

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

    def get_sql_content(self, context: AssetExecutionContext) -> str:
        return f"CREATE TABLE IF NOT EXISTS {self.table_name} ({self.columns});"


def test_custom_duckdb_sql_component():
    """Test that a custom DuckDBSqlComponent subclass correctly builds and executes SQL."""
    execution_body = {
        "type": "dagster_duckdb_tests.test_sql_component.CreateTableComponent",
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
