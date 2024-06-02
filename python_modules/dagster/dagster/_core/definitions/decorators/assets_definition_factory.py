from collections import Counter
from functools import cached_property
from inspect import Parameter
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    cast,
)

import dagster._check as check
from dagster._core.decorator_utils import get_function_params, get_valid_name_permutations
from dagster._core.definitions.asset_in import AssetIn
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.input import In
from dagster._core.definitions.output import Out
from dagster._core.definitions.resource_annotation import (
    get_resource_args,
)
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.dagster_type import DagsterType, Nothing

from ..asset_check_spec import AssetCheckSpec
from ..utils import (
    NoValueSentinel,
)


def stringify_asset_key_to_input_name(asset_key: AssetKey) -> str:
    return "_".join(asset_key.path).replace("-", "_")


def get_function_params_without_context_or_config_or_resources(
    fn: Callable[..., Any],
) -> List[Parameter]:
    params = get_function_params(fn)
    is_context_provided = len(params) > 0 and params[0].name in get_valid_name_permutations(
        "context"
    )
    input_params = params[1:] if is_context_provided else params

    resource_arg_names = {arg.name for arg in get_resource_args(fn)}

    new_input_args = []
    for input_arg in input_params:
        if input_arg.name != "config" and input_arg.name not in resource_arg_names:
            new_input_args.append(input_arg)

    return new_input_args


def build_asset_ins(
    fn: Callable[..., Any],
    asset_ins: Mapping[str, AssetIn],
    deps: Optional[AbstractSet[AssetKey]],
) -> Mapping[AssetKey, Tuple[str, In]]:
    """Creates a mapping from AssetKey to (name of input, In object)."""
    deps = check.opt_set_param(deps, "deps", AssetKey)

    new_input_args = get_function_params_without_context_or_config_or_resources(fn)

    non_var_input_param_names = [
        param.name for param in new_input_args if param.kind == Parameter.POSITIONAL_OR_KEYWORD
    ]
    has_kwargs = any(param.kind == Parameter.VAR_KEYWORD for param in new_input_args)

    all_input_names = set(non_var_input_param_names) | asset_ins.keys()

    if not has_kwargs:
        for in_key, asset_in in asset_ins.items():
            if in_key not in non_var_input_param_names and (
                not isinstance(asset_in.dagster_type, DagsterType)
                or not asset_in.dagster_type.is_nothing
            ):
                raise DagsterInvalidDefinitionError(
                    f"Key '{in_key}' in provided ins dict does not correspond to any of the names "
                    "of the arguments to the decorated function"
                )

    ins_by_asset_key: Dict[AssetKey, Tuple[str, In]] = {}
    for input_name in all_input_names:
        asset_key = None

        if input_name in asset_ins:
            asset_key = asset_ins[input_name].key
            metadata = asset_ins[input_name].metadata or {}
            key_prefix = asset_ins[input_name].key_prefix
            input_manager_key = asset_ins[input_name].input_manager_key
            dagster_type = asset_ins[input_name].dagster_type
        else:
            metadata = {}
            key_prefix = None
            input_manager_key = None
            dagster_type = NoValueSentinel

        asset_key = asset_key or AssetKey(list(filter(None, [*(key_prefix or []), input_name])))

        ins_by_asset_key[asset_key] = (
            input_name.replace("-", "_"),
            In(metadata=metadata, input_manager_key=input_manager_key, dagster_type=dagster_type),
        )

    for asset_key in deps:
        if asset_key in ins_by_asset_key:
            raise DagsterInvalidDefinitionError(
                f"deps value {asset_key} also declared as input/AssetIn"
            )
            # mypy doesn't realize that Nothing is a valid type here
        ins_by_asset_key[asset_key] = (
            stringify_asset_key_to_input_name(asset_key),
            In(cast(type, Nothing)),
        )

    return ins_by_asset_key


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
    def from_specs(
        *,
        specs: Sequence[AssetSpec],
        check_specs: Sequence[AssetCheckSpec],
        can_subset: bool,
        ins: Mapping[str, AssetIn],
        fn: Callable[..., Any],
    ):
        output_tuples_by_asset_key = {}
        for asset_spec in specs:
            output_name = asset_spec.key.to_python_identifier()
            output_tuples_by_asset_key[asset_spec.key] = (
                output_name,
                Out(
                    Nothing,
                    is_required=not (can_subset or asset_spec.skippable),
                    description=asset_spec.description,
                    code_version=asset_spec.code_version,
                    metadata=asset_spec.metadata,
                ),
            )

        upstream_keys = set()
        for spec in specs:
            for dep in spec.deps:
                if dep.asset_key not in output_tuples_by_asset_key:
                    upstream_keys.add(dep.asset_key)
                if (
                    dep.asset_key in output_tuples_by_asset_key
                    and dep.partition_mapping is not None
                ):
                    # self-dependent asset also needs to be considered an upstream_key
                    upstream_keys.add(dep.asset_key)

        explicit_ins = ins or {}
        # get which asset keys have inputs set
        loaded_upstreams = build_asset_ins(fn, explicit_ins, deps=set())
        unexpected_upstreams = {key for key in loaded_upstreams.keys() if key not in upstream_keys}
        if unexpected_upstreams:
            raise DagsterInvalidDefinitionError(
                f"Asset inputs {unexpected_upstreams} do not have dependencies on the passed"
                " AssetSpec(s). Set the deps on the appropriate AssetSpec(s)."
            )
        remaining_upstream_keys = {key for key in upstream_keys if key not in loaded_upstreams}
        asset_ins = build_asset_ins(fn, explicit_ins, deps=remaining_upstream_keys)
        return InOutMapper.from_asset_ins_and_asset_outs(
            asset_ins, output_tuples_by_asset_key, check_specs, can_subset
        )

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
    def asset_keys_by_output_name(self) -> Mapping[str, AssetKey]:
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

    @cached_property
    def asset_ins_by_input_names(self) -> Mapping[str, In]:
        return {in_name: in_obj for in_name, in_obj in self.in_mappings.values()}

    @cached_property
    def asset_keys_by_input_names(self) -> Mapping[str, AssetKey]:
        return {
            in_mapping.input_name: asset_key for asset_key, in_mapping in self.in_mappings.items()
        }

    @cached_property
    def input_tuples_by_asset_key(self) -> Mapping[AssetKey, Tuple[str, In]]:
        return {
            asset_key: (in_mapping.input_name, in_mapping.input)
            for asset_key, in_mapping in self.in_mappings.items()
        }

    @cached_property
    def output_tuples_by_asset_key(self) -> Mapping[AssetKey, Tuple[str, Out]]:
        return {
            asset_key: (out_mapping.output_name, out_mapping.output)
            for asset_key, out_mapping in self.out_mappings.items()
        }


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
