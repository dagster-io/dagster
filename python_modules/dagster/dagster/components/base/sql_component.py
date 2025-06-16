from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Any, Generic, Optional, Union

from jinja2 import Template
from pydantic import BaseModel, Field
from typing_extensions import TypeVar

import dagster as dg
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.core_models import Resolvable, ResolvedAssetAttributes
from dagster.components.resolved.model import Resolver

T = TypeVar("T")


class SqlComponent(Resolvable, BaseModel, Component, Generic[T], ABC):
    """Base component which executes templated SQL."""

    asset_attributes: Annotated[
        Optional[ResolvedAssetAttributes],
        Field(default=None, description="Asset attributes to apply to the created assets"),
    ]

    @property
    @abstractmethod
    def sql_content(self) -> str:
        """The SQL content to execute."""
        ...

    @abstractmethod
    def execute(self, context: AssetExecutionContext, resource: T) -> None:
        """Execute the SQL content."""
        ...

    @abstractmethod
    def get_asset_key(self) -> dg.AssetKey:
        """The asset key or keys to associate with this model."""
        ...

    @property
    @abstractmethod
    def required_resource_key(self) -> str:
        """The resource key required by this component."""
        ...

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        @dg.asset(
            **(self.asset_attributes or {}),
            key=self.get_asset_key(),
            required_resource_keys={self.required_resource_key},
        )
        def _materialize_sql(context: dg.AssetExecutionContext):
            self.execute(context, getattr(context.resources, self.required_resource_key))

        asset_def: dg.AssetsDefinition = _materialize_sql  # type: ignore
        return dg.Definitions(assets=[asset_def])


class SqlFile(BaseModel):
    """A file containing SQL content."""

    path: str = Field(..., description="Path to the SQL file")


ResolvedSqlTemplate = Annotated[
    Union[str, SqlFile],
    Resolver(
        lambda ctx, template: template,
        model_field_type=Union[str, SqlFile],
        inject_before_resolve=False,
    ),
]


class TemplatedSqlComponent(SqlComponent[T]):
    """A component that executes templated SQL from a string or file."""

    sql_template: Annotated[
        ResolvedSqlTemplate,
        Field(description="The SQL template to execute, either as a string or from a file."),
    ]
    template_vars: Annotated[
        Optional[Mapping[str, Any]],
        Field(default=None, description="Template variables to pass to the SQL template."),
    ]

    @property
    def sql_content(self) -> str:
        template_str = self.sql_template
        if isinstance(template_str, SqlFile):
            template_str = Path(template_str.path).read_text()

        template = Template(template_str)
        return template.render(**(self.template_vars or {}))
