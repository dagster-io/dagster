from typing import Annotated, Optional

import dagster as dg
from dagster._annotations import preview, public
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.core.context import ComponentLoadContext
from pydantic import BaseModel, Field

from dagster_duckdb.resource import DuckDBResource


@public
@preview
class DuckDBConnectionComponent(dg.Component, dg.Resolvable, DuckDBResource):
    """A component that represents a DuckDB connection."""

    resource_key: Annotated[
        Optional[str],
        Field(
            description="A resource key to expose this connection to use in other Dagster assets."
        ),
    ] = None

    @classmethod
    def load(
        cls, attributes: Optional[BaseModel], context: "ComponentLoadContext"
    ) -> "DuckDBConnectionComponent":
        return super().load(attributes, context)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return (
            Definitions(resources={self.resource_key: self}) if self.resource_key else Definitions()
        )
