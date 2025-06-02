import importlib
import inspect
from typing import Annotated, Callable, Literal, Optional

from dagster_shared import check
from typing_extensions import TypeAlias

from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.time_window_partitions import DailyPartitionsDefinition
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import ResolvedAssetSpec
from dagster.components.resolved.model import Model, Resolver


class DailyPartitionDefinitionModel(Resolvable, Model):
    type: Literal["daily"] = "daily"
    start_date: str
    end_offset: int = 0


def resolve_partition_definition(
    context: ResolutionContext, model: DailyPartitionDefinitionModel
) -> DailyPartitionsDefinition:
    return DailyPartitionsDefinition(
        start_date=model.start_date,
        end_offset=model.end_offset,
    )


ResolvedPartitionDefinition: TypeAlias = Annotated[
    DailyPartitionsDefinition,
    Resolver(
        resolve_partition_definition,
        model_field_type=DailyPartitionDefinitionModel,
    ),
]


def resolve_callable(context: ResolutionContext, model: str) -> Callable:
    module_path, fn_name = model.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, fn_name)


ResolvableCallable: TypeAlias = Annotated[
    Callable, Resolver(resolve_callable, model_field_type=str)
]


def get_resources_from_callable(func: Callable) -> list[str]:
    sig = inspect.signature(func)
    return [param.name for param in sig.parameters.values() if param.name != "context"]


class ExecutableComponent(Component, Resolvable, Model):
    """Executable Component represents an executable node in the asset graph.

    It is comprised of an execute_fn, which is can be specified as a fully
    resolved symbol reference in yaml. This makes it a plain ole' Python function
    that does the execution within the asset graph.

    You can pass an arbitrary number of assets or asset checks to the component.

    With this structure this component replaces @asset, @multi_asset, @asset_check, and @multi_asset_check.
    which can all be expressed as a single ExecutableComponent.
    """

    # inferred from the function name if not provided
    name: Optional[str] = None
    partitions_def: Optional[ResolvedPartitionDefinition] = None
    assets: Optional[list[ResolvedAssetSpec]] = None
    execute_fn: ResolvableCallable

    def get_resource_keys(self) -> set[str]:
        return set(get_resources_from_callable(self.execute_fn))

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        required_resource_keys = self.get_resource_keys()

        check.invariant(len(self.assets or []) > 0, "assets is required for now")

        @multi_asset(
            name=self.name or self.execute_fn.__name__,
            specs=self.assets,
            partitions_def=self.partitions_def,
            required_resource_keys=required_resource_keys,
        )
        def _assets_def(context: AssetExecutionContext, **kwargs):
            rd = context.resources.original_resource_dict
            to_pass = {k: v for k, v in rd.items() if k in required_resource_keys}
            check.invariant(set(to_pass.keys()) == required_resource_keys, "Resource keys mismatch")
            return self.execute_fn(context, **to_pass)

        return Definitions(assets=[_assets_def])
