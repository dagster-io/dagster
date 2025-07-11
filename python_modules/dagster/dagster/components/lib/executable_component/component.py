from abc import ABC, abstractmethod
from collections.abc import Generator, Iterable
from typing import Any, Optional, TypeVar, Union

from dagster_shared import check
from pydantic import BaseModel

from dagster._core.definitions.asset_checks.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_checks.asset_checks_definition import AssetChecksDefinition
from dagster._core.definitions.assets.definition.asset_effect import AssetCheckEffect, AssetEffect
from dagster._core.definitions.assets.definition.asset_spec import AssetExecutionType
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.assets.definition.computation import Computation, ComputationFn
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.result import MaterializeResult
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


class ExecutableComponent(Component, Resolvable, Model, BaseModel, ABC):
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
    asset_execution_type: AssetExecutionType = AssetExecutionType.MATERIALIZATION

    @property
    @abstractmethod
    def op_spec(self) -> OpSpec: ...

    @property
    def resource_keys(self) -> set[str]:
        return set()

    @abstractmethod
    def get_execute_fn(self, component_load_context: ComponentLoadContext) -> ComputationFn: ...

    def build_underlying_assets_def(
        self, component_load_context: ComponentLoadContext
    ) -> AssetsDefinition:
        asset_effects = [
            AssetEffect.from_spec(spec=asset_spec, execution_type=self.asset_execution_type)
            for asset_spec in (self.assets or [])
        ]
        check_effects = [AssetCheckEffect(spec=check_spec) for check_spec in (self.checks or [])]
        effects = [*asset_effects, *check_effects]
        check.invariant(
            len(effects) > 0,
            "No assets or checks provided",
        )

        computation = Computation.from_fn(
            fn=self.get_execute_fn(component_load_context=component_load_context),
            op_spec=self.op_spec,
            effects=effects,
            can_subset=False,
            additional_resource_keys=self.resource_keys,
        )

        return computation.to_assets_def()

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        assets_def = self.build_underlying_assets_def(component_load_context=context)
        if isinstance(assets_def, AssetChecksDefinition):
            return Definitions(asset_checks=[assets_def])
        else:
            return Definitions(assets=[assets_def])
