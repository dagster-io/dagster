from abc import ABC
from typing import Annotated, Optional

import dagster as dg
from dagster._annotations import preview, public
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.base.sql_component import SqlComponent, TemplatedSqlComponentMixin
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.base import resolve_fields
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.model import Model, Resolver
from pydantic import BaseModel, Field, create_model

from dagster_snowflake.resources import SnowflakeResource

# Dynamically create SnowflakeResourceModel from SnowflakeResource without validators
field_definitions = {}
for field_name, field in SnowflakeResource.model_fields.items():
    field_definitions[field_name] = (field.annotation, field)
SnowflakeResourceModel = create_model(
    "SnowflakeResourceModel",
    __base__=Model,
    **field_definitions,
)


def resolve_snowflake_resource(context: ResolutionContext, value) -> SnowflakeResource:
    return SnowflakeResource(**resolve_fields(value, SnowflakeResource, context))


@public
@preview
class BaseSnowflakeSqlComponent(SqlComponent, ABC):
    """A component which implements executing a SQL query using a Snowflake resource.
    This is an abstract base class which does not provide instructions on where to source
    the SQL content from.
    """

    connection: Annotated[
        Annotated[
            SnowflakeResource,
            Resolver(
                resolve_snowflake_resource,
                model_field_type=SnowflakeResourceModel,
            ),
        ],
        Field(description="The resource key to use for the Snowflake resource."),
    ]

    def execute(self, context: AssetExecutionContext) -> None:
        """Execute the SQL content using the Snowflake resource."""
        with self.connection.get_connection() as conn:
            conn.cursor().execute(self.get_sql_content(context))


@public
@preview
class SnowflakeTemplatedSqlComponent(
    TemplatedSqlComponentMixin,
    BaseSnowflakeSqlComponent,
):
    """A component that executes templated SQL from a string or file in Snowflake."""


@public
@preview
class SnowflakeConnectionComponent(dg.Component, dg.Resolvable, SnowflakeResource):
    """A component that represents a Snowflake connection."""

    resource_key: Annotated[
        Optional[str],
        Field(
            description="A resource key to expose this connection to use in other Dagster assets."
        ),
    ] = None

    @classmethod
    def load(
        cls, attributes: Optional[BaseModel], context: "ComponentLoadContext"
    ) -> "SnowflakeConnectionComponent":
        return super().load(attributes, context)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return (
            Definitions(resources={self.resource_key: self}) if self.resource_key else Definitions()
        )
