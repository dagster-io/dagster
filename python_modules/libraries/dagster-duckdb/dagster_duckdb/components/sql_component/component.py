from functools import cached_property

import dagster as dg
from dagster._annotations import preview, public
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.sql_component.sql_client import SQLClient
from dagster.components.utils import copy_fields_to_model

from dagster_duckdb.resource import DuckDBResource


@public
@preview
class DuckDBConnectionComponentBase(dg.Component, dg.Resolvable, dg.Model, SQLClient):
    """A component that represents a DuckDB connection."""

    @cached_property
    def _duckdb_resource(self) -> DuckDBResource:
        return DuckDBResource(
            **{
                (field.alias or field_name): getattr(self, field_name)
                for field_name, field in self.__class__.model_fields.items()
            }
        )

    def connect_and_execute(self, sql: str) -> None:
        """Connect to the SQL database and execute the SQL query."""
        return self._duckdb_resource.connect_and_execute(sql)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        # Use path relative to defs folder to create resource key
        relative_path = context.component_decl.path.file_path.relative_to(context.defs_module_path)
        resource_key = relative_path.as_posix().replace("/", "__").replace("-", "_")
        return Definitions(resources={resource_key: self._duckdb_resource})


@public
@preview
class DuckDBConnectionComponent(
    copy_fields_to_model(
        copy_from=DuckDBResource,
        copy_to=DuckDBConnectionComponentBase,
    )
):
    pass
