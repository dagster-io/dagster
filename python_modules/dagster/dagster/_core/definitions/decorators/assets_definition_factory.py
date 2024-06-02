from collections import Counter
from functools import cached_property
from typing import (
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
)

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.input import In
from dagster._core.definitions.output import Out
from dagster._core.errors import DagsterInvalidDefinitionError

from ..asset_check_spec import AssetCheckSpec


class InMapping(NamedTuple):
    input_name: str
    input: In


class OutMapping(NamedTuple):
    output_name: str
    output: Out


class InOutMapper:
    def __init__(
        self,
        in_mappings: Mapping[AssetKey, InMapping],
        out_mappings: Mapping[AssetKey, OutMapping],
        check_specs: Sequence[AssetCheckSpec],
        can_subset: bool,
    ) -> None:
        self.in_mappings = in_mappings
        self.out_mappings = out_mappings
        self.check_specs = check_specs
        self.can_subset = can_subset

    @staticmethod
    def from_asset_ins_and_asset_outs(
        asset_ins: Mapping[AssetKey, Tuple[str, In]],
        asset_outs: Mapping[AssetKey, Tuple[str, Out]],
        check_specs: Sequence[AssetCheckSpec],
        can_subset: bool,
    ):
        in_mappings = {
            asset_key: InMapping(input_name, in_)
            for asset_key, (input_name, in_) in asset_ins.items()
        }
        out_mappings = {
            asset_key: OutMapping(output_name, out_)
            for asset_key, (output_name, out_) in asset_outs.items()
        }
        return InOutMapper(in_mappings, out_mappings, check_specs, can_subset)

    @cached_property
    def asset_outs_by_output_name(self) -> Mapping[str, Out]:
        return dict(self.out_mappings.values())

    @cached_property
    def keys_by_output_name(self) -> Mapping[str, AssetKey]:
        return {
            out_mapping.output_name: asset_key
            for asset_key, out_mapping in self.out_mappings.items()
        }

    @cached_property
    def asset_keys(self) -> Set[AssetKey]:
        return set(self.out_mappings.keys())

    @cached_property
    def check_specs_by_output_name(self) -> Mapping[str, AssetCheckSpec]:
        return validate_and_assign_output_names_to_check_specs(
            self.check_specs, list(self.asset_keys)
        )

    @cached_property
    def check_outs_by_output_name(self) -> Mapping[str, Out]:
        return {
            output_name: Out(dagster_type=None, is_required=not self.can_subset)
            for output_name in self.check_specs_by_output_name.keys()
        }

    @cached_property
    def combined_outs_by_output_name(self) -> Mapping[str, Out]:
        return {
            **self.asset_outs_by_output_name,
            **self.check_outs_by_output_name,
        }

    @cached_property
    def overlapping_output_names(self) -> Set[str]:
        return set(self.asset_outs_by_output_name.keys()) & set(
            self.check_outs_by_output_name.keys()
        )


def validate_and_assign_output_names_to_check_specs(
    check_specs: Optional[Sequence[AssetCheckSpec]], valid_asset_keys: Sequence[AssetKey]
) -> Mapping[str, AssetCheckSpec]:
    _validate_check_specs_target_relevant_asset_keys(check_specs, valid_asset_keys)
    return _assign_output_names_to_check_specs(check_specs)


def _assign_output_names_to_check_specs(
    check_specs: Optional[Sequence[AssetCheckSpec]],
) -> Mapping[str, AssetCheckSpec]:
    checks_by_output_name = {spec.get_python_identifier(): spec for spec in check_specs or []}
    if check_specs and len(checks_by_output_name) != len(check_specs):
        duplicates = {
            item: count
            for item, count in Counter(
                [(spec.asset_key, spec.name) for spec in check_specs]
            ).items()
            if count > 1
        }

        raise DagsterInvalidDefinitionError(f"Duplicate check specs: {duplicates}")

    return checks_by_output_name


def _validate_check_specs_target_relevant_asset_keys(
    check_specs: Optional[Sequence[AssetCheckSpec]], valid_asset_keys: Sequence[AssetKey]
) -> None:
    for spec in check_specs or []:
        if spec.asset_key not in valid_asset_keys:
            raise DagsterInvalidDefinitionError(
                f"Invalid asset key {spec.asset_key} in check spec {spec.name}. Must be one of"
                f" {valid_asset_keys}"
            )
