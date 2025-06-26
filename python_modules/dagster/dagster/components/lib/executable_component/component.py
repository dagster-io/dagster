from abc import ABC, abstractmethod
from collections.abc import Generator, Iterable
from functools import cached_property
from typing import Any, Optional, TypeVar, Union

from dagster_shared import check

from dagster._config.field import Field
from dagster._core.definitions.asset_checks.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_checks.asset_checks_definition import AssetChecksDefinition
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.decorators.asset_check_decorator import multi_asset_check
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.asset_check_execution_context import AssetCheckExecutionContext
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.core_models import (
    OpSpec,
    ResolvedAssetCheckSpec,
    ResolvedAssetSpec,
)
from dagster.components.resolved.model import Model

T = TypeVar("T", bound=Union[MaterializeResult, AssetCheckResult])


def to_iterable(
    result: Any, of_type: Union[type[T], tuple[type[T], ...]]
) -> Generator[T, None, None]:
    if isinstance(result, of_type):
        yield result
    elif isinstance(result, Iterable):
        for item in result:
            if not isinstance(item, of_type):
                check.failed(f"Expected a {of_type}, got {type(item).__name__}")
            yield item
    elif result:
        check.failed(f"Expected a {of_type}, got {type(result).__name__}")


class ExecutableComponent(Component, Resolvable, Model, ABC):
    """Executable Component represents an executable node in the asset graph.

    It is comprised of an execute_fn, which is can be specified as a fully
    resolved symbol reference in yaml. This makes it a plain ole' Python function
    that does the execution within the asset graph.

    You can pass an arbitrary number of assets or asset checks to the component.

    With this structure this component replaces @asset, @multi_asset, @asset_check, and @multi_asset_check.
    which can all be expressed as a single ExecutableComponent.
    """

    assets: Optional[list[ResolvedAssetSpec]] = None
    checks: Optional[list[ResolvedAssetCheckSpec]] = None

    @property
    @abstractmethod
    def op_spec(self) -> OpSpec: ...

    @property
    def resource_keys(self) -> set[str]:
        return set()

    @cached_property
    def config_fields(self) -> Optional[dict[str, Field]]:
        return None

    @abstractmethod
    def invoke_execute_fn(
        self,
        context: Union[AssetExecutionContext, AssetCheckExecutionContext],
        component_load_context: ComponentLoadContext,
    ) -> Iterable[Union[MaterializeResult, AssetCheckResult]]: ...

    def build_underlying_assets_def(
        self, component_load_context: ComponentLoadContext
    ) -> AssetsDefinition:
        if self.assets:

            @multi_asset(
                name=self.op_spec.name,
                op_tags=self.op_spec.tags,
                description=self.op_spec.description,
                specs=self.assets,
                check_specs=self.checks,
                required_resource_keys=self.resource_keys,
                pool=self.op_spec.pool,
                config_schema=self.config_fields,
            )
            def _assets_def(context: AssetExecutionContext, **kwargs):
                return to_iterable(
                    self.invoke_execute_fn(context, component_load_context=component_load_context),
                    of_type=(MaterializeResult, AssetCheckResult),
                )

            return _assets_def
        elif self.checks:

            @multi_asset_check(
                name=self.op_spec.name,
                op_tags=self.op_spec.tags,
                specs=self.checks,
                description=self.op_spec.description,
                required_resource_keys=self.resource_keys,
                pool=self.op_spec.pool,
                config_schema=self.config_fields,
            )
            def _asset_check_def(context: AssetCheckExecutionContext, **kwargs):
                return to_iterable(
                    self.invoke_execute_fn(context, component_load_context=component_load_context),
                    of_type=AssetCheckResult,
                )

            return _asset_check_def

        check.failed("No assets or checks provided")

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        assets_def = self.build_underlying_assets_def(component_load_context=context)
        if isinstance(assets_def, AssetChecksDefinition):
            return Definitions(asset_checks=[assets_def])
        else:
            return Definitions(assets=[assets_def])
