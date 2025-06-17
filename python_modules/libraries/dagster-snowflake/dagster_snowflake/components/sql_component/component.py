from typing import Annotated

from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.base.sql_component import TemplatedSqlComponent
from pydantic import Field

from dagster_snowflake.resources import SnowflakeResource


class SnowflakeSqlComponent(TemplatedSqlComponent[SnowflakeResource]):
    """A component that executes SQL from a file in Snowflake."""

    resource_key: Annotated[
        str, Field(description="The resource key to use for the Snowflake resource.")
    ] = "snowflake"

    def execute(self, context: AssetExecutionContext, resource: SnowflakeResource) -> None:
        """Execute the SQL content using the Snowflake resource."""
        with resource.get_connection() as conn:
            conn.cursor().execute(self.sql_content)

    @property
    def resource_keys(self) -> set[str]:
        return {self.resource_key}
