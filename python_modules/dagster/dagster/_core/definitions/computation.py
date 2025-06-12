from collections.abc import Mapping, Sequence, Set
from typing import TYPE_CHECKING, Optional, Union

from dagster_shared import check
from dagster_shared.record import copy, record

from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_key import AssetKey, EntityKey
from dagster._core.definitions.asset_spec import AssetExecutionType, AssetSpec
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.op_definition import OpDefinition

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition


@record
class Effect:
    spec: Union[AssetSpec, AssetCheckSpec]
    execution_type: Optional[AssetExecutionType]

    @staticmethod
    def materialize(spec: AssetSpec) -> "Effect":
        return Effect(spec=spec, execution_type=AssetExecutionType.MATERIALIZATION)

    @staticmethod
    def observe(spec: AssetSpec) -> "Effect":
        return Effect(spec=spec, execution_type=AssetExecutionType.OBSERVATION)

    @staticmethod
    def check(spec: AssetCheckSpec) -> "Effect":
        return Effect(spec=spec, execution_type=None)


@record
class Computation:
    node_def: NodeDefinition
    input_mappings: Mapping[str, AssetKey]
    output_mappings: Mapping[str, Effect]

    # subsetting
    inactive_outputs: Set[str]

    @property
    def is_subset(self) -> bool:
        return len(self.inactive_outputs) > 0

    @property
    def asset_specs(self) -> Sequence[AssetSpec]:
        return [
            effect.spec
            for output_name, effect in self.output_mappings.items()
            if isinstance(effect.spec, AssetSpec) and output_name not in self.inactive_outputs
        ]

    @property
    def asset_check_specs(self) -> Sequence[AssetCheckSpec]:
        return [
            effect.spec
            for output_name, effect in self.output_mappings.items()
            if isinstance(effect.spec, AssetCheckSpec) and output_name in self.inactive_outputs
        ]

    def subset_for(self, keys: Set[EntityKey]) -> "Computation":
        # TODO: handle graph definitions
        check.inst(self.node_def, OpDefinition)
        return copy(
            self,
            selected_outputs={
                output_name
                for output_name, effect in self.output_mappings.items()
                if effect.spec.key in keys
            },
        )

    def to_assets_def(self) -> "AssetsDefinition":
        from dagster._core.definitions.assets import AssetsDefinition

        execution_types = {effect.execution_type for effect in self.output_mappings.values()}
        execution_types.discard(None)
        check.invariant(
            len(execution_types) <= 1,
            f"All output effects must have the same execution type, found: {execution_types}",
        )
        execution_type = next(iter(execution_types))

        return AssetsDefinition(
            node_def=self.node_def,
            execution_type=execution_type,
            specs=self.asset_specs,
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
            selected_asset_keys={
                effect.spec.key
                for output_name, effect in self.output_mappings.items()
                if isinstance(effect.spec, AssetSpec) and output_name not in self.inactive_outputs
            },
            selected_asset_check_keys={
                effect.spec.key
                for output_name, effect in self.output_mappings.items()
                if isinstance(effect.spec, AssetCheckSpec)
                and output_name not in self.inactive_outputs
            },
        )
