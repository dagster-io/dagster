import importlib
from collections.abc import Iterator, Mapping, Sequence
from functools import cached_property
from typing import Annotated, Any, Callable, Literal, Optional

from dagster_shared import check
from typing_extensions import TypeAlias

from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.asset_spec import SYSTEM_METADATA_KEY_DAGSTER_TYPE, AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import Output
from dagster._core.definitions.metadata import RawMetadataMapping
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.result import MaterializeResult
from dagster._core.definitions.time_window_partitions import DailyPartitionsDefinition
from dagster._core.execution.context.asset_execution_context import AssetExecutionContext
from dagster._core.types.dagster_type import Any as DagsterAny
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


EMBEDDED_METADATA_KEY_VALUE = "__dagster_value"


# In lieu of adding value to materialize result itself, we are going
# to embed it in the metadata so we can do so in the context of
# an ExecutableComponent.
def make_materialize_result(
    *,
    asset_key: Optional[CoercibleToAssetKey] = None,
    metadata: Optional[RawMetadataMapping] = None,
    check_results: Optional[Sequence[AssetCheckResult]] = None,
    data_version: Optional[DataVersion] = None,
    tags: Optional[Mapping[str, str]] = None,
    value: Any = None,
) -> MaterializeResult:
    return MaterializeResult(
        asset_key=asset_key,
        metadata={**(metadata or {}), EMBEDDED_METADATA_KEY_VALUE: value},
        check_results=check_results,
        data_version=data_version,
        tags=tags,
    )


# Make it so that skip dagster type validation for now.
def anyify_specs(specs: Optional[list[AssetSpec]]) -> list[AssetSpec]:
    if specs is None:
        return []

    return [
        spec.merge_attributes(metadata={SYSTEM_METADATA_KEY_DAGSTER_TYPE: DagsterAny})
        for spec in specs
    ]


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

    @cached_property
    def resource_keys(self) -> set[str]:
        return {param.name for param in get_resource_args(self.execute_fn)}

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        required_resource_keys = self.resource_keys

        check.invariant(len(self.assets or []) > 0, "assets is required for now")

        @multi_asset(
            name=self.name or self.execute_fn.__name__,
            specs=anyify_specs(self.assets),
            partitions_def=self.partitions_def,
            required_resource_keys=required_resource_keys,
        )
        def _assets_def(context: AssetExecutionContext) -> Iterator:
            yield from _capture_assets_def_fn(context)

        def _capture_assets_def_fn(context: AssetExecutionContext) -> Iterator:
            yield from self._core_execute(context, _assets_def)

        return Definitions(assets=[_assets_def])

    @cached_property
    def asset_dict(self) -> dict[AssetKey, AssetSpec]:
        return {asset.key: asset for asset in self.assets or []}

    def _core_execute(
        self, context: AssetExecutionContext, assets_def: AssetsDefinition
    ) -> Iterator:
        result = self.execute_fn(context, **self.get_resources_to_pass(context))

        check.invariant(result is not None, "execute_fn must return a result")
        if isinstance(result, MaterializeResult):
            check.invariant(len(self.asset_dict) == 1, "Only one asset is supported")
            asset = next(iter(self.asset_dict.values()))
            asset_key = result.asset_key if result.asset_key else asset.key

            yield _to_output(assets_def, asset_key, result)
        elif isinstance(result, Iterator):
            for asset_result in result:
                assert isinstance(asset_result, MaterializeResult)
                assert asset_result.asset_key
                yield _to_output(assets_def, asset_result.asset_key, asset_result)

        else:
            raise Exception(f"Type not supported yet: {type(result)}")

    def get_resources_to_pass(self, context):
        rd = context.resources.original_resource_dict
        to_pass = {k: v for k, v in rd.items() if k in self.resource_keys}
        check.invariant(set(to_pass.keys()) == self.resource_keys, "Resource keys mismatch")
        return to_pass


def _to_output(
    assets_def: AssetsDefinition, asset_key: AssetKey, result: MaterializeResult
) -> Output:
    if not assets_def.has_output_for_asset_key(asset_key):
        raise Exception(f"Asset {asset_key} does not have an output")

    if result.asset_key:
        check.invariant(result.asset_key == asset_key, "Asset key mismatch")

    metadata = {**(result.metadata or {})}
    value = metadata.pop(EMBEDDED_METADATA_KEY_VALUE, None)

    return Output(
        value=value,
        output_name=asset_key.to_python_identifier(),
        metadata=metadata,
        data_version=result.data_version,
        tags=result.tags,
    )
