import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from unittest import mock

import pytest
from dagster import AssetKey, Definitions
from dagster._core.definitions.materialize import materialize
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.sql_component.sql_component import SqlComponent, TemplatedSqlComponent
from dagster.components.testing import create_defs_folder_sandbox
from dagster_snowflake.components.sql_component.component import SnowflakeConnectionComponent
from dagster_snowflake.constants import SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER

from dagster_snowflake_tests.utils import create_mock_connector


@contextmanager
def setup_snowflake_component_with_external_connection(
    execution_component_body: dict,
    connection_component_name: str = "sql_connection_component",
) -> Iterator[Definitions]:
    """Sets up a components project with a snowflake component using external connection."""
    with create_defs_folder_sandbox() as sandbox:
        sandbox.scaffold_component(
            component_cls=SqlComponent,
            defs_path="sql_execution_component",
            defs_yaml_contents=execution_component_body,
        )

        sandbox.scaffold_component(
            component_cls=SnowflakeConnectionComponent,
            defs_path=connection_component_name,
            defs_yaml_contents={
                "type": "dagster_snowflake.SnowflakeConnectionComponent",
                "attributes": {
                    "account": "test_account",
                    "user": "test_user",
                    "password": "test_password",
                    "database": "TESTDB",
                    "schema": "TESTSCHEMA",
                },
            },
        )

        with sandbox.build_all_defs() as defs:
            yield defs


@contextmanager
def setup_snowflake_component(
    component_body: dict,
) -> Iterator[tuple[TemplatedSqlComponent, Definitions]]:
    """Sets up a components project with a snowflake component based on provided params."""
    with create_defs_folder_sandbox() as sandbox:
        defs_path = sandbox.scaffold_component(
            component_cls=TemplatedSqlComponent,
            defs_yaml_contents=component_body,
        )
        with sandbox.load_component_and_build_defs(defs_path=defs_path) as (
            component,
            defs,
        ):
            assert isinstance(component, TemplatedSqlComponent)
            yield component, defs


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_snowflake_sql_component2(snowflake_connect):
    """Test that the TemplatedSqlComponent correctly builds and executes SQL."""
    execution_body = {
        "type": "dagster.TemplatedSqlComponent",
        "attributes": {
            "sql_template": "SELECT * FROM MY_TABLE;",
            "assets": [{"key": "TESTDB/TESTSCHEMA/TEST_TABLE"}],
            "connection": "{{ load_component_at_path('sql_connection_component') }}",
        },
    }

    with setup_snowflake_component_with_external_connection(
        execution_component_body=execution_body,
    ) as defs:
        asset_key = AssetKey(["TESTDB", "TESTSCHEMA", "TEST_TABLE"])
        asset_def = defs.get_assets_def(asset_key)
        result = materialize(
            [asset_def],
        )
        assert result.success
        snowflake_connect.assert_called_once_with(
            account="test_account",
            user="test_user",
            password="test_password",
            database="TESTDB",
            schema="TESTSCHEMA",
            application=SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER,
        )
        mock_cursor = snowflake_connect.return_value.cursor.return_value
        mock_cursor.execute.assert_called_once_with("SELECT * FROM MY_TABLE;")
        assert defs.resolve_asset_graph().get_all_asset_keys() == {
            AssetKey(["TESTDB", "TESTSCHEMA", "TEST_TABLE"])
        }


@pytest.mark.parametrize(
    "sql_template",
    [
        "SELECT * FROM TESTDB.TESTSCHEMA.TEST_TABLE WHERE date = '{{ date }}' LIMIT {{ limit }}",
        None,  # This will trigger the file template test
    ],
)
@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_snowflake_sql_component_with_templates(snowflake_connect, sql_template):
    """Test that the TemplatedSqlComponent correctly handles SQL templates from strings and files."""
    # If sql_template is None, create a temporary file with the template
    if sql_template is None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
            f.write(
                "SELECT * FROM TESTDB.TESTSCHEMA.TEST_TABLE WHERE date = '{{ date }}' LIMIT {{ limit }}"
            )
            sql_file_path = f.name
            sql_template = {"path": sql_file_path}

    try:
        execution_body = {
            "type": "dagster.TemplatedSqlComponent",
            "attributes": {
                "sql_template": sql_template,
                "assets": [{"key": "TESTDB/TESTSCHEMA/TEST_TABLE"}],
                "sql_template_vars": {
                    "date": "2024-03-20",
                    "limit": 100,
                },
                "connection": "{{ load_component_at_path('sql_connection_component') }}",
            },
        }
        with setup_snowflake_component_with_external_connection(
            execution_component_body=execution_body,
        ) as defs:
            asset_key = AssetKey(["TESTDB", "TESTSCHEMA", "TEST_TABLE"])
            asset_def = defs.get_assets_def(asset_key)
            result = materialize(
                [asset_def],
            )
            assert result.success
            mock_cursor = snowflake_connect.return_value.cursor.return_value
            mock_cursor.execute.assert_called_once_with(
                "SELECT * FROM TESTDB.TESTSCHEMA.TEST_TABLE WHERE date = '2024-03-20' LIMIT 100"
            )
            assert defs.resolve_asset_graph().get_all_asset_keys() == {
                AssetKey(["TESTDB", "TESTSCHEMA", "TEST_TABLE"])
            }
    finally:
        # Clean up the temporary file if it was created
        if isinstance(sql_template, dict) and "path" in sql_template:
            os.unlink(sql_template["path"])


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_snowflake_sql_component_with_execution(snowflake_connect):
    """Test that the TemplatedSqlComponent correctly handles execution parameter with op description."""
    execution_body = {
        "type": "dagster.TemplatedSqlComponent",
        "attributes": {
            "sql_template": "SELECT * FROM MY_TABLE;",
            "assets": [{"key": "TESTDB/TESTSCHEMA/TEST_TABLE"}],
            "execution": {"description": "This is a test op description"},
            "connection": "{{ load_component_at_path('sql_connection_component') }}",
        },
    }
    with setup_snowflake_component_with_external_connection(
        execution_component_body=execution_body,
    ) as defs:
        asset_key = AssetKey(["TESTDB", "TESTSCHEMA", "TEST_TABLE"])
        asset_def = defs.get_assets_def(asset_key)

        # Verify the op description is set correctly
        assert asset_def.op.description == "This is a test op description"

        # Materialize to actually execute the SQL
        result = materialize([asset_def])
        assert result.success


class RefreshExternalTableComponent(SqlComponent):
    """A custom component which refreshes an external table in Snowflake."""

    table_name: str

    def get_sql_content(
        self, context: AssetExecutionContext, component_load_context: ComponentLoadContext
    ) -> str:
        return f"ALTER TABLE {self.table_name} REFRESH;"


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_custom_snowflake_sql_component(snowflake_connect):
    """Test that a custom SnowflakeSqlComponent subclass correctly builds and executes SQL."""
    execution_body = {
        "type": "dagster_snowflake_tests.test_sql_component.RefreshExternalTableComponent",
        "attributes": {
            "table_name": "TESTDB.TESTSCHEMA.EXTERNAL_TABLE",
            "assets": [{"key": "TESTDB/TESTSCHEMA/EXTERNAL_TABLE"}],
            "connection": "{{ load_component_at_path('sql_connection_component') }}",
        },
    }

    with setup_snowflake_component_with_external_connection(
        execution_component_body=execution_body,
    ) as defs:
        asset_key = AssetKey(["TESTDB", "TESTSCHEMA", "EXTERNAL_TABLE"])
        asset_def = defs.get_assets_def(asset_key)
        result = materialize(
            [asset_def],
        )
        assert result.success
        snowflake_connect.assert_called_once_with(
            account="test_account",
            user="test_user",
            password="test_password",
            database="TESTDB",
            schema="TESTSCHEMA",
            application=SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER,
        )
        mock_cursor = snowflake_connect.return_value.cursor.return_value
        mock_cursor.execute.assert_called_once_with(
            "ALTER TABLE TESTDB.TESTSCHEMA.EXTERNAL_TABLE REFRESH;"
        )
        assert defs.resolve_asset_graph().get_all_asset_keys() == {
            AssetKey(["TESTDB", "TESTSCHEMA", "EXTERNAL_TABLE"])
        }
