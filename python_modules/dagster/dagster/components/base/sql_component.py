from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Annotated, Any, Generic, Optional, Union

from dagster_shared import check
from jinja2 import Template
from pydantic import BaseModel, Field
from typing_extensions import TypeVar

from dagster._annotations import preview, public
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.asset_check_execution_context import AssetCheckExecutionContext
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.executable_component.component import ExecutableComponent
from dagster.components.resolved.core_models import OpSpec
from dagster.components.resolved.model import Model, Resolver

T = TypeVar("T")


@public
@preview
class SqlComponent(ExecutableComponent, Model, BaseModel, Generic[T], ABC):
    """Base component which executes templated SQL. Subclasses
    implement instructions on where to load the SQL content from
    and how to execute it.
    """

    execution: Optional[OpSpec] = None

    @abstractmethod
    def get_sql_content(
        self, context: AssetExecutionContext, component_load_context: ComponentLoadContext
    ) -> str:
        """The SQL content to execute."""
        ...

    @abstractmethod
    def execute(
        self,
        context: AssetExecutionContext,
        component_load_context: ComponentLoadContext,
        resource: T,
    ) -> None:
        """Execute the SQL content."""
        ...

    @property
    def op_spec(self) -> OpSpec:
        return self.execution or OpSpec()

    def invoke_execute_fn(
        self,
        context: Union[AssetExecutionContext, AssetCheckExecutionContext],
        component_load_context: ComponentLoadContext,
    ) -> Iterable[MaterializeResult]:
        check.invariant(
            len(self.resource_keys) == 1, "SqlComponent must have exactly one resource key."
        )
        self.execute(
            check.inst(context, AssetExecutionContext),
            component_load_context,
            getattr(context.resources, next(iter(self.resource_keys))),
        )
        for asset in self.assets or []:
            yield MaterializeResult(asset_key=asset.key)


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


class TemplatedSqlComponentMixin:
    """A component mixin that builds templated SQL from a string or file.
    User-defined components can inherit from this mixin to incorporate behavior
    of loading SQL from a string or file.
    """

    sql_template: Annotated[
        ResolvedSqlTemplate,
        Field(description="The SQL template to execute, either as a string or from a file."),
    ]
    sql_template_vars: Annotated[
        Optional[Mapping[str, Any]],
        Field(default=None, description="Template variables to pass to the SQL template."),
    ]

    def get_sql_content(
        self, context: AssetExecutionContext, component_load_context: ComponentLoadContext
    ) -> str:
        template_str = self.sql_template
        if isinstance(template_str, SqlFile):
            template_str = (component_load_context.path / Path(template_str.path)).read_text()

        template = Template(template_str)
        return template.render(**(self.sql_template_vars or {}))
