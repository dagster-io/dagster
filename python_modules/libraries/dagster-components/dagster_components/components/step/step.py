from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Callable, Optional

from dagster._config.config_schema import UserConfigSchema
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.result import MaterializeResult
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster_dbt.asset_decorator import RetryPolicy
from typing_extensions import TypeAlias

from dagster_components.core.component import Component, ComponentLoadContext, loader
from dagster_components.scaffold import Scaffolder, ScaffoldRequest, scaffold_with


class ExecutionContext(AssetExecutionContext): ...


class AssetGraphStepScaffolder(Scaffolder):
    def scaffold(self, request: ScaffoldRequest, params):
        file_contents = """from dagster import AssetSpec
from dagster_components import step

@step(assets=[AssetSpec("the_key")])
def my_step(context: ExecutionContext) -> Optional[ExecutionResult]:
    ...
"""
        assert file_contents


@scaffold_with(AssetGraphStepScaffolder)
@dataclass(frozen=True)
class AssetGraphStep(Component):
    name: str
    fn: Callable[[ExecutionContext], Optional[MaterializeResult]]
    description: Optional[str] = None
    tags: Optional[Mapping[str, Any]] = None
    pool: Optional[str] = None
    retry_policy: Optional[RetryPolicy] = None
    config_schema: Optional[UserConfigSchema] = None
    assets: Optional[Sequence[AssetSpec]] = None
    checks: Optional[Sequence[AssetCheckSpec]] = None

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        @multi_asset(
            name=self.name,
            description=self.description,
            op_tags=self.tags,
            specs=self.assets,
            pool=self.pool,
            config_schema=self.config_schema,
            check_specs=self.checks,
            retry_policy=self.retry_policy,
        )
        def _the_asset(context: AssetExecutionContext):
            return self.fn(context)  # type: ignore

        return Definitions(assets=[_the_asset])


ExecutionFn: TypeAlias = Callable[[ExecutionContext], Optional[MaterializeResult]]
LoaderFn: TypeAlias = Callable[[ComponentLoadContext], Component]


# replaces asset, multi_asset, asset_check, multi_asset_check
# sort of replaces observable_source_asset and multi_observable_source_asset
def step(
    *,
    name: str,
    description: Optional[str] = None,
    tags: Optional[Mapping[str, Any]] = None,
    pool: Optional[str] = None,
    retry_policy: Optional[RetryPolicy] = None,
    config_schema: Optional[UserConfigSchema] = None,
    assets: Optional[Sequence[AssetSpec]] = None,
    checks: Optional[Sequence[AssetCheckSpec]] = None,
) -> Callable[[ExecutionFn], LoaderFn]:
    def _decorator(fn: ExecutionFn) -> LoaderFn:
        @loader
        def load(context: ComponentLoadContext) -> AssetGraphStep:
            return AssetGraphStep(
                name=name,
                description=description,
                tags=tags,
                pool=pool,
                retry_policy=retry_policy,
                config_schema=config_schema,
                fn=fn,
                assets=assets,
                checks=checks,
            )

        return load

    return _decorator
