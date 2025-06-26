from abc import ABC
from typing import Annotated

from dagster._annotations import preview, public
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.base.sql_component import SqlComponent, TemplatedSqlComponentMixin
from dagster.components.core.context import ComponentLoadContext
from pydantic import Field

from dagster_snowflake.resources import SnowflakeResource


@public
@preview
class BaseSnowflakeSqlComponent(SqlComponent[SnowflakeResource], ABC):
    """A component which implements executing a SQL query using a Snowflake resource.
    This is an abstract base class which does not provide instructions on where to source
    the SQL content from.
    """

    resource_key: Annotated[
        str, Field(description="The resource key to use for the Snowflake resource.")
    ] = "snowflake"

    def execute(
        self,
        context: AssetExecutionContext,
        component_load_context: ComponentLoadContext,
        resource: SnowflakeResource,
    ) -> None:
        """Execute the SQL content using the Snowflake resource."""
        with resource.get_connection() as conn:
            conn.cursor().execute(self.get_sql_content(context, component_load_context))

    @property
    def resource_keys(self) -> set[str]:
        return {self.resource_key}


@public
@preview
class SnowflakeTemplatedSqlComponent(
    TemplatedSqlComponentMixin,
    BaseSnowflakeSqlComponent,
):
    """A component that executes templated SQL from a string or file in Snowflake."""
