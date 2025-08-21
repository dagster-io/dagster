from functools import cached_property
from typing import Any, cast

import dagster as dg
from dagster._annotations import preview, public
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.sql_component.sql_client import SQLClient
from pydantic import BaseModel, create_model

from dagster_snowflake.resources import SnowflakeResource


@public
@preview
class SnowflakeConnectionComponentBase(dg.Component, dg.Resolvable, dg.Model, SQLClient):
    """A component that represents a Snowflake connection. Use this component if you are
    also using the TemplatedSqlComponent to execute SQL queries, and need to connect to Snowflake.
    """

    @cached_property
    def _snowflake_resource(self) -> SnowflakeResource:
        return SnowflakeResource(
            **{
                (field.alias or field_name): getattr(self, field_name)
                for field_name, field in self.__class__.model_fields.items()
            }
        )

    def connect_and_execute(self, sql: str) -> None:
        """Connect to the SQL database and execute the SQL query."""
        return self._snowflake_resource.connect_and_execute(sql)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()


def _copy_fields_to_model(
    copy_from: type[BaseModel], copy_to: type[BaseModel], new_model_cls_name: str
) -> None:
    """Given two models, creates a copy of the second model with the fields of the first model."""
    field_definitions: dict[str, tuple[type, Any]] = {
        field_name: (cast("type", field.annotation), field)
        for field_name, field in copy_from.model_fields.items()
    }

    return create_model(
        new_model_cls_name,
        __base__=copy_to,
        __doc__=copy_to.__doc__,
        **field_definitions,  # type: ignore
    )


SnowflakeConnectionComponent = public(preview)(
    _copy_fields_to_model(
        copy_from=SnowflakeResource,
        copy_to=SnowflakeConnectionComponentBase,
        new_model_cls_name="SnowflakeConnectionComponent",
    )
)
