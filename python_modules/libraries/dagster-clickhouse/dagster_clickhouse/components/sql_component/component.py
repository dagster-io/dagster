from functools import cached_property
from typing import Any, cast

import dagster as dg
from dagster._annotations import preview, public
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.sql_component.sql_client import SQLClient
from dagster.components.scaffold.scaffold import scaffold_with
from pydantic import BaseModel, create_model

from dagster_clickhouse.components.sql_component.scaffolder import (
    ClickhouseQueryComponentScaffolder,
)
from dagster_clickhouse.resource import ClickhouseResource


@public
@preview
class ClickhouseQueryComponentBase(dg.Component, dg.Resolvable, dg.Model, SQLClient):
    """A ClickHouse connection component for ``TemplatedSqlComponent`` and other SQL tooling."""

    @cached_property
    def _clickhouse_resource(self) -> ClickhouseResource:
        return ClickhouseResource(
            **{
                (field.alias or field_name): getattr(self, field_name)
                for field_name, field in self.__class__.model_fields.items()
            }
        )

    def connect_and_execute(self, sql: str) -> None:
        """Connect to ClickHouse and execute the SQL query."""
        return self._clickhouse_resource.connect_and_execute(sql)

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        return Definitions()


def _copy_fields_to_model(
    copy_from: type[BaseModel], copy_to: type[BaseModel], new_model_cls_name: str
) -> type[BaseModel]:
    field_definitions: dict[str, Any] = {
        field_name: (cast("type", field.annotation), field)
        for field_name, field in copy_from.model_fields.items()
    }

    return create_model(
        new_model_cls_name,
        __base__=copy_to,
        __doc__=copy_to.__doc__,
        **field_definitions,
    )


ClickhouseQueryComponent = public(preview)(
    scaffold_with(ClickhouseQueryComponentScaffolder)(
        _copy_fields_to_model(
            copy_from=ClickhouseResource,
            copy_to=ClickhouseQueryComponentBase,
            new_model_cls_name="ClickhouseQueryComponent",
        )
    )
)
