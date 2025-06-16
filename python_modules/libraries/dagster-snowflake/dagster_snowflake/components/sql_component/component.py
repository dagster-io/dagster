from typing import Annotated

import dagster as dg
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.base.sql_component import TemplatedSqlComponent
from dagster.components.resolved.core_models import Resolvable
from pydantic import Field

from dagster_snowflake.resources import SnowflakeResource


class SnowflakeSqlComponent(TemplatedSqlComponent[SnowflakeResource], Resolvable):
    """A component that executes SQL from a file in Snowflake."""

    database: Annotated[str, Field(description="The Snowflake database name.")]
    schema: Annotated[str, Field(description="The Snowflake schema name.")]
    table_name: Annotated[str, Field(description="The Snowflake table name.")]
    resource_key: Annotated[
        str, Field(description="The resource key to use for the Snowflake resource.")
    ] = "snowflake"

    class Config:
        extra = "allow"

    def execute(self, context: AssetExecutionContext, resource: SnowflakeResource) -> None:
        """Execute the SQL content using the Snowflake resource."""
        with resource.get_connection() as conn:
            conn.cursor().execute(self.sql_content)

    def get_asset_key(self) -> dg.AssetKey:
        """Get the asset key for this component."""
        return dg.AssetKey([self.database, self.schema, self.table_name])

    @property
    def required_resource_key(self) -> str:
        """Get the required resource key."""
        return self.resource_key
