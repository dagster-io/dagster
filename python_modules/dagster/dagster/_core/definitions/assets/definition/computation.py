from collections.abc import Iterator, Mapping, Sequence
from typing import TYPE_CHECKING, Callable, Optional, Union

from dagster_shared import check
from dagster_shared.record import record
from typing_extensions import TypeAlias

from dagster._core.definitions.asset_checks.asset_check_result import AssetCheckResult
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets.definition.asset_effect import (
    AssetEffect,
    CoercibleToEffect,
    Effect,
)
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.decorators.decorator_assets_definition_builder import (
    build_and_validate_named_ins,
)
from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction
from dagster._core.definitions.inference import get_config_param_type
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.result import AssetResult
from dagster.components.resolved.core_models import OpSpec

if TYPE_CHECKING:
    from dagster._core.definitions.assets.definition.asset_dep import AssetDep

ComputationFn: TypeAlias = Callable[..., Iterator[Union[AssetResult, AssetCheckResult]]]


@record
class Computation:
    """Generalized class for represting a single computation that has effects on entities in the
    asset graph.

    For now, this is a simple translation layer that swiftly gets turned into an AssetsDefinition,
    but in the future this relationship will flip, and this Computation class will take over the
    role of AssetsDefinition in the internals of the system.
    """

    node_def: NodeDefinition
    input_mappings: Mapping[str, AssetKey]
    output_mappings: Mapping[str, Effect]

    can_subset: bool

    @staticmethod
    def from_fn(
        fn: ComputationFn, *, op_spec: OpSpec, effects: Sequence[Effect], can_subset: bool
    ) -> "Computation":
        """Create a computation from a single function. Output definitions are created from the
        provided effects. Input definitions are inferred from the function signature and provided
        dependencies. The underlying node will be an OpDefinition that wraps the provided function.

        Args:
            fn: The function to create a computation from.
            op_spec: The spec for the op that will be created.
            effects: The effects that the function will have when executed.
            can_subset: Whether the computation can be subsetted.
        """
        wrapped_fn = DecoratedOpFunction(fn)

        # construct inputs from the deps of the specs and the params of the function
        deps: set[AssetDep] = set().union(*(effect.spec.deps for effect in effects))
        if not can_subset:
            # if the computation is not subsettable, then we can avoid creating inputs for
            # any upstream assets that are produced by this computation and are not self
            # dependencies
            output_keys = {effect.spec.key for effect in effects}
            deps = {
                dep
                for dep in deps
                if dep.asset_key not in output_keys and dep.partition_mapping is None
            }

        named_ins = build_and_validate_named_ins(fn=fn, deps=deps, passed_asset_ins={})

        # construct outputs from the specs that this function affects
        output_mappings = {effect.spec.key.to_python_identifier(): effect for effect in effects}

        config_type = get_config_param_type(fn)
        op_def = OpDefinition(
            compute_fn=wrapped_fn,
            name=op_spec.name or wrapped_fn.name,
            ins={named_in.input_name: named_in.input for named_in in named_ins.values()},
            outs={
                output_name: effect.to_out(can_subset=can_subset)
                for output_name, effect in output_mappings.items()
            },
            description=op_spec.description,
            tags=op_spec.tags,
            config_schema=config_type.to_config_schema() if config_type else None,
            required_resource_keys={arg.name for arg in wrapped_fn.get_resource_args()},
            pool=op_spec.pool,
        )
        return Computation(
            node_def=op_def,
            input_mappings={named_in.input_name: key for key, named_in in named_ins.items()},
            output_mappings=output_mappings,
            can_subset=can_subset,
        )

    def to_assets_def(self) -> AssetsDefinition:
        """Convert this Computation into an AssetsDefinition."""
        execution_types = {
            effect.execution_type
            for effect in self.output_mappings.values()
            if isinstance(effect, AssetEffect)
        }
        check.invariant(
            len(execution_types) <= 1,
            f"All output effects must have the same execution type, found: {execution_types}",
        )
        execution_type = next(iter(execution_types), None)

        return AssetsDefinition(
            node_def=self.node_def,
            execution_type=execution_type,
            specs=[
                effect.spec
                for effect in self.output_mappings.values()
                if isinstance(effect, AssetEffect)
            ],
            keys_by_input_name={input_name: key for input_name, key in self.input_mappings.items()},
            keys_by_output_name={
                output_name: effect.spec.key
                for output_name, effect in self.output_mappings.items()
                if isinstance(effect.spec, AssetSpec)
            },
            check_specs_by_output_name={
                output_name: effect.spec
                for output_name, effect in self.output_mappings.items()
                if isinstance(effect.spec, AssetCheckSpec)
            },
            can_subset=self.can_subset,
        )


def computation(
    effects: Sequence[CoercibleToEffect],
    op_spec: Optional[OpSpec] = None,
    can_subset: bool = False,
) -> Callable[[ComputationFn], Computation]:
    def wrapper(fn: ComputationFn) -> Computation:
        return Computation.from_fn(
            fn,
            op_spec=op_spec or OpSpec(),
            effects=[Effect.from_coercible(effect) for effect in effects],
            can_subset=can_subset,
        )

    return wrapper
