from typing import Annotated, Optional

import dagster as dg
from dagster._annotations import preview, public
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.sql_component.sql_client import ISQLClient
from pydantic import BaseModel, Field

from dagster_snowflake.resources import SnowflakeResource


@public
@preview
class SnowflakeConnectionComponent(dg.Component, dg.Resolvable, SnowflakeResource, ISQLClient):
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

    def connect_and_execute(self, sql: str) -> None:
        with self.get_connection() as conn:
            conn.cursor().execute(sql)
