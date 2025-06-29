import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from unittest import mock

import pytest
from dagster import AssetKey, Definitions
from dagster._core.definitions.materialize import materialize
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.testing import scaffold_defs_sandbox
from dagster_snowflake.components import SnowflakeTemplatedSqlComponent
from dagster_snowflake.components.sql_component.component import BaseSnowflakeSqlComponent
from dagster_snowflake.constants import SNOWFLAKE_PARTNER_CONNECTION_IDENTIFIER
from dagster_snowflake.resources import SnowflakeResource

from dagster_snowflake_tests.utils import create_mock_connector


@contextmanager
def setup_snowflake_component(
    component_body: dict,
) -> Iterator[tuple[SnowflakeTemplatedSqlComponent, Definitions]]:
    """Sets up a components project with a snowflake component based on provided params."""
    with scaffold_defs_sandbox(
        component_cls=SnowflakeTemplatedSqlComponent,
    ) as defs_sandbox:
        with defs_sandbox.load(component_body=component_body) as (component, defs):
            assert isinstance(component, SnowflakeTemplatedSqlComponent)
            yield component, defs


BASIC_SNOWFLAKE_COMPONENT_BODY = {
    "type": "dagster_snowflake.SnowflakeTemplatedSqlComponent",
    "attributes": {
        "sql_template": "SELECT * FROM MY_TABLE;",
        "assets": [{"key": "TESTDB/TESTSCHEMA/TEST_TABLE"}],
    },
}


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_snowflake_sql_component(snowflake_connect):
    """Test that the SnowflakeTemplatedSqlComponent correctly builds and executes SQL."""
    with setup_snowflake_component(
        component_body=BASIC_SNOWFLAKE_COMPONENT_BODY,
    ) as (component, defs):
        defs_with_resource = defs.with_resources(
            {
                "snowflake": SnowflakeResource(
                    account="test_account",
                    user="test_user",
                    password="test_password",
                    database="TESTDB",
                    schema="TESTSCHEMA",
                )
            },
        )
        asset_key = AssetKey(["TESTDB", "TESTSCHEMA", "TEST_TABLE"])
        asset_def = defs_with_resource.get_assets_def(asset_key)
        result = materialize(
            [asset_def],
            resources=defs_with_resource.resources,
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
        assert defs_with_resource.resolve_asset_graph().get_all_asset_keys() == {
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
    """Test that the SnowflakeTemplatedSqlComponent correctly handles SQL templates from strings and files."""
    # If sql_template is None, create a temporary file with the template
    if sql_template is None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
            f.write(
                "SELECT * FROM TESTDB.TESTSCHEMA.TEST_TABLE WHERE date = '{{ date }}' LIMIT {{ limit }}"
            )
            sql_file_path = f.name
            sql_template = {"path": sql_file_path}

    try:
        component_body = {
            "type": "dagster_snowflake.SnowflakeTemplatedSqlComponent",
            "attributes": {
                "sql_template": sql_template,
                "assets": [{"key": "TESTDB/TESTSCHEMA/TEST_TABLE"}],
                "sql_template_vars": {
                    "date": "2024-03-20",
                    "limit": 100,
                },
            },
        }
        with setup_snowflake_component(
            component_body=component_body,
        ) as (component, defs):
            defs_with_resource = defs.with_resources(
                {
                    "snowflake": SnowflakeResource(
                        account="test_account",
                        user="test_user",
                        password="test_password",
                        database="TESTDB",
                        schema="TESTSCHEMA",
                    )
                }
            )
            asset_key = AssetKey(["TESTDB", "TESTSCHEMA", "TEST_TABLE"])
            asset_def = defs_with_resource.get_assets_def(asset_key)
            result = materialize(
                [asset_def],
                resources=defs_with_resource.resources,
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
                "SELECT * FROM TESTDB.TESTSCHEMA.TEST_TABLE WHERE date = '2024-03-20' LIMIT 100"
            )
            assert defs_with_resource.resolve_asset_graph().get_all_asset_keys() == {
                AssetKey(["TESTDB", "TESTSCHEMA", "TEST_TABLE"])
            }
    finally:
        # Clean up the temporary file if it was created
        if isinstance(sql_template, dict) and "path" in sql_template:
            os.unlink(sql_template["path"])


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_snowflake_sql_component_with_execution(snowflake_connect):
    """Test that the SnowflakeTemplatedSqlComponent correctly handles execution parameter with op description."""
    component_body = {
        "type": "dagster_snowflake.SnowflakeTemplatedSqlComponent",
        "attributes": {
            "sql_template": "SELECT * FROM MY_TABLE;",
            "assets": [{"key": "TESTDB/TESTSCHEMA/TEST_TABLE"}],
            "execution": {"description": "This is a test op description"},
        },
    }
    with setup_snowflake_component(
        component_body=component_body,
    ) as (component, defs):
        defs_with_resource = defs.with_resources(
            {
                "snowflake": SnowflakeResource(
                    account="test_account",
                    user="test_user",
                    password="test_password",
                    database="TESTDB",
                    schema="TESTSCHEMA",
                )
            }
        )

        asset_key = AssetKey(["TESTDB", "TESTSCHEMA", "TEST_TABLE"])
        asset_def = defs_with_resource.get_assets_def(asset_key)

        # Verify the op description is set correctly
        assert asset_def.op.description == "This is a test op description"


class RefreshExternalTableComponent(BaseSnowflakeSqlComponent):
    """A custom component which refreshes an external table in Snowflake."""

    table_name: str

    def get_sql_content(self, context: AssetExecutionContext) -> str:
        return f"ALTER TABLE {self.table_name} REFRESH;"


@mock.patch("snowflake.connector.connect", new_callable=create_mock_connector)
def test_custom_snowflake_sql_component(snowflake_connect):
    """Test that a custom SnowflakeSqlComponent subclass correctly builds and executes SQL."""
    component_body = {
        "type": "dagster_snowflake_tests.test_sql_component.RefreshExternalTableComponent",
        "attributes": {
            "table_name": "TESTDB.TESTSCHEMA.EXTERNAL_TABLE",
            "assets": [{"key": "TESTDB/TESTSCHEMA/EXTERNAL_TABLE"}],
        },
    }
    with scaffold_defs_sandbox(
        component_cls=RefreshExternalTableComponent,
    ) as defs_sandbox:
        with defs_sandbox.load(component_body=component_body) as (component, defs):
            defs_with_resource = defs.with_resources(
                {
                    "snowflake": SnowflakeResource(
                        account="test_account",
                        user="test_user",
                        password="test_password",
                        database="TESTDB",
                        schema="TESTSCHEMA",
                    )
                },
            )
            asset_key = AssetKey(["TESTDB", "TESTSCHEMA", "EXTERNAL_TABLE"])
            asset_def = defs_with_resource.get_assets_def(asset_key)
            result = materialize(
                [asset_def],
                resources=defs_with_resource.resources,
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
            assert defs_with_resource.resolve_asset_graph().get_all_asset_keys() == {
                AssetKey(["TESTDB", "TESTSCHEMA", "EXTERNAL_TABLE"])
            }
