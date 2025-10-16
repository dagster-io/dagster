from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Annotated, Any, Optional, Union

from dagster_shared import check
from pydantic import BaseModel, Field

from dagster._annotations import preview, public
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.asset_check_execution_context import AssetCheckExecutionContext
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.core.context import ComponentLoadContext
from dagster.components.lib.executable_component.component import ExecutableComponent
from dagster.components.lib.sql_component.sql_client import SQLClient
from dagster.components.resolved.core_models import OpSpec
from dagster.components.resolved.model import Resolver


@public
@preview
class SqlComponent(ExecutableComponent, ABC):
    """Base component which executes templated SQL. Subclasses
    implement instructions on where to load the SQL content from.
    """

    class Config:
        # Necessary to allow connection to be a SQLClient, which is an ABC
        arbitrary_types_allowed = True

    connection: Annotated[
        Annotated[
            SQLClient,
            Resolver(lambda ctx, value: value, model_field_type=str),
        ],
        Field(description="The SQL connection to use for executing the SQL content."),
    ]
    execution: Annotated[Optional[OpSpec], Field(default=None)] = None

    @abstractmethod
    def get_sql_content(
        self, context: AssetExecutionContext, component_load_context: ComponentLoadContext
    ) -> str:
        """The SQL content to execute."""
        ...

    def execute(
        self, context: AssetExecutionContext, component_load_context: ComponentLoadContext
    ) -> None:
        """Execute the SQL content using the Snowflake resource."""
        self.connection.connect_and_execute(self.get_sql_content(context, component_load_context))

    @property
    def op_spec(self) -> OpSpec:
        return self.execution or OpSpec()

    def invoke_execute_fn(
        self,
        context: Union[AssetExecutionContext, AssetCheckExecutionContext],
        component_load_context: ComponentLoadContext,
    ) -> Iterable[MaterializeResult]:
        self.execute(
            check.inst(context, AssetExecutionContext),
            component_load_context,
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


class TemplatedSqlComponent(SqlComponent):
    """A component which executes templated SQL from a string or file."""

    sql_template: Annotated[
        ResolvedSqlTemplate,
        Field(description="The SQL template to execute, either as a string or from a file."),
    ]

    sql_template_vars: Annotated[
        Optional[Mapping[str, Any]],
        Field(default=None, description="Template variables to pass to the SQL template."),
    ] = None

    def get_sql_content(
        self, context: AssetExecutionContext, component_load_context: ComponentLoadContext
    ) -> str:
        # Slow import, we do it here to avoid importing jinja2 when `dagster` is imported

        from jinja2 import Template

        template_str = self.sql_template
        if isinstance(template_str, SqlFile):
            template_str = (component_load_context.path / Path(template_str.path)).read_text()

        template = Template(template_str)
        return template.render(**(self.sql_template_vars or {}))
