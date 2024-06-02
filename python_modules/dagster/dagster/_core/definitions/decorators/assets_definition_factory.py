from collections import Counter
from functools import cached_property
from inspect import Parameter
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    Iterable,
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
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_in import AssetIn
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_out import AssetOut
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import (
    ASSET_SUBSET_INPUT_PREFIX,
    get_partition_mappings_from_deps,
)
from dagster._core.definitions.input import In
from dagster._core.definitions.output import Out
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.dagster_type import DagsterType, Nothing

from ..asset_check_spec import AssetCheckSpec
from ..utils import NoValueSentinel


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


def build_asset_outs(asset_outs: Mapping[str, AssetOut]) -> Mapping[AssetKey, Tuple[str, Out]]:
    """Creates a mapping from AssetKey to (name of output, Out object)."""
    outs_by_asset_key: Dict[AssetKey, Tuple[str, Out]] = {}
    for output_name, asset_out in asset_outs.items():
        out = asset_out.to_out()
        asset_key = asset_out.key or AssetKey(
            list(filter(None, [*(asset_out.key_prefix or []), output_name]))
        )

        outs_by_asset_key[asset_key] = (output_name.replace("-", "_"), out)

    return outs_by_asset_key


def build_subsettable_asset_ins(
    asset_ins: Mapping[AssetKey, Tuple[str, In]],
    asset_outs: Mapping[AssetKey, Tuple[str, Out]],
    internal_upstream_deps: Iterable[AbstractSet[AssetKey]],
) -> Mapping[AssetKey, Tuple[str, In]]:
    """Creates a mapping from AssetKey to (name of input, In object) for any asset key that is not
    currently an input, but may become one if this asset is subset.

    For example, if a subsettable multi-asset produces both A and C, where C depends on both A and
    some other asset B, there are some situations where executing just A and C without B will result
    in these assets being generated by different steps within the same job. In this case, we need
    a separate input to represent the fact that C depends on A.
    """
    # set of asset keys which are upstream of another asset, and are not currently inputs
    potential_deps = set().union(*internal_upstream_deps).difference(set(asset_ins.keys()))
    return {
        key: (f"{ASSET_SUBSET_INPUT_PREFIX}{name}", In(Nothing))
        for key, (name, _) in asset_outs.items()
        if key in potential_deps
    }


class InMapping(NamedTuple):
    input_name: str
    input: In


class OutMapping(NamedTuple):
    output_name: str
    output: Out


def make_keys_by_output_name(
    asset_outs: Mapping[AssetKey, Tuple[str, Out]],
) -> Mapping[str, AssetKey]:
    return {output_name: asset_key for asset_key, (output_name, _) in asset_outs.items()}


class InOutMapper:
    def __init__(
        self,
        *,
        directly_passed_asset_ins: Mapping[str, AssetIn],
        input_tuples_by_asset_key: Mapping[AssetKey, Tuple[str, In]],
        output_tables_by_asset_key: Mapping[AssetKey, Tuple[str, Out]],
        check_specs: Sequence[AssetCheckSpec],
        internal_deps: Mapping[AssetKey, Set[AssetKey]],
        can_subset: bool,
        deps_directly_passed_to_multi_asset: Optional[Iterable[AssetDep]],
        spec_resolver: Callable[["InOutMapper"], Sequence[AssetSpec]],
        op_name: str,
        group_name: Optional[str] = None,
    ) -> None:
        self.directly_passed_asset_ins = directly_passed_asset_ins
        self._passed_input_tuples_by_asset_key = input_tuples_by_asset_key
        self.output_tuples_by_asset_key = output_tables_by_asset_key
        self.check_specs = check_specs
        self.internal_deps = internal_deps
        self.can_subset = can_subset
        self.deps_directly_passed_to_multi_asset = deps_directly_passed_to_multi_asset
        self.spec_resolver = spec_resolver
        self.op_name = op_name
        self.group_name = group_name

    @staticmethod
    def from_specs(
        *,
        specs: Sequence[AssetSpec],
        check_specs: Sequence[AssetCheckSpec],
        can_subset: bool,
        ins: Mapping[str, AssetIn],
        fn: Callable[..., Any],
        op_name: str,
        group_name: Optional[str],
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
        input_tuples_by_asset_key = build_asset_ins(fn, explicit_ins, deps=remaining_upstream_keys)

        internal_deps = {
            spec.key: {dep.asset_key for dep in spec.deps}
            for spec in specs
            if spec.deps is not None
        }

        return InOutMapper(
            directly_passed_asset_ins=ins,
            input_tuples_by_asset_key=input_tuples_by_asset_key,
            output_tables_by_asset_key=output_tuples_by_asset_key,
            check_specs=check_specs,
            internal_deps=internal_deps,
            can_subset=can_subset,
            # when specs are used deps are never passed to multi-asset
            deps_directly_passed_to_multi_asset=None,
            spec_resolver=lambda _: specs,
            op_name=op_name,
            group_name=group_name,
        )

    @staticmethod
    def from_asset_outs(
        *,
        asset_out_map: Mapping[str, AssetOut],
        asset_deps: Mapping[str, Set[AssetKey]],
        deps_directly_passed_to_multi_asset: Optional[Iterable[AssetDep]],
        ins: Mapping[str, AssetIn],
        fn: Callable[..., Any],
        check_specs: Sequence[AssetCheckSpec],
        can_subset: bool,
        op_name: str,
        group_name: Optional[str],
    ):
        inputs_tuples_by_asset_key = build_asset_ins(
            fn,
            ins or {},
            deps=(
                {dep.asset_key for dep in deps_directly_passed_to_multi_asset}
                if deps_directly_passed_to_multi_asset
                else set()
            ),
        )
        output_tuples_by_asset_key = build_asset_outs(asset_out_map)

        # validate that the asset_ins are a subset of the upstream asset_deps.
        upstream_internal_asset_keys = set().union(*asset_deps.values())
        asset_in_keys = set(inputs_tuples_by_asset_key.keys())
        if asset_deps and not asset_in_keys.issubset(upstream_internal_asset_keys):
            invalid_asset_in_keys = asset_in_keys - upstream_internal_asset_keys
            check.failed(
                f"Invalid asset dependencies: `{invalid_asset_in_keys}` specified as asset"
                " inputs, but are not specified in `internal_asset_deps`. Asset inputs must"
                " be associated with an output produced by the asset."
            )

        # validate that the asset_deps make sense
        valid_asset_deps = asset_in_keys | set(output_tuples_by_asset_key.keys())
        for out_name, asset_keys in asset_deps.items():
            if asset_out_map and out_name not in asset_out_map:
                check.failed(
                    f"Invalid out key '{out_name}' supplied to `internal_asset_deps` argument"
                    f" for multi-asset {op_name}. Must be one of the outs for this multi-asset"
                    f" {list(asset_out_map.keys())[:20]}.",
                )
            invalid_asset_deps = asset_keys.difference(valid_asset_deps)
            check.invariant(
                not invalid_asset_deps,
                f"Invalid asset dependencies: {invalid_asset_deps} specified in"
                f" `internal_asset_deps` argument for multi-asset '{op_name}' on key"
                f" '{out_name}'. Each specified asset key must be associated with an input to"
                " the asset or produced by this asset. Valid keys:"
                f" {list(valid_asset_deps)[:20]}",
            )

        keys_by_output_name = make_keys_by_output_name(output_tuples_by_asset_key)
        internal_deps = {keys_by_output_name[name]: asset_deps[name] for name in asset_deps}

        def _spec_resolver(in_out_mapper: "InOutMapper") -> Sequence[AssetSpec]:
            resolved_specs = []
            input_deps_by_key = {
                key: AssetDep(
                    asset=key, partition_mapping=in_out_mapper.partition_mappings.get(key)
                )
                for key in in_out_mapper.asset_keys_by_input_names.values()
            }
            input_deps = list(input_deps_by_key.values())
            for output_name, asset_out in asset_out_map.items():
                key = in_out_mapper.asset_keys_by_output_name[output_name]
                if asset_deps:
                    deps = [
                        input_deps_by_key.get(
                            dep_key,
                            AssetDep(
                                asset=dep_key,
                                partition_mapping=in_out_mapper.partition_mappings.get(key),
                            ),
                        )
                        for dep_key in asset_deps.get(output_name, [])
                    ]
                else:
                    deps = input_deps

                resolved_specs.append(asset_out.to_spec(key, deps=deps))
            return resolved_specs

        return InOutMapper(
            directly_passed_asset_ins=ins,
            input_tuples_by_asset_key=inputs_tuples_by_asset_key,
            output_tables_by_asset_key=output_tuples_by_asset_key,
            check_specs=check_specs or [],
            internal_deps=internal_deps,
            can_subset=can_subset,
            deps_directly_passed_to_multi_asset=deps_directly_passed_to_multi_asset,
            spec_resolver=_spec_resolver,
            op_name=op_name,
            group_name=group_name,
        )

    @cached_property
    def input_tuples_by_asset_key(self) -> Mapping[AssetKey, Tuple[str, In]]:
        if self.can_subset and self.internal_deps:
            return {
                **self._passed_input_tuples_by_asset_key,
                **build_subsettable_asset_ins(
                    self._passed_input_tuples_by_asset_key,
                    self.output_tuples_by_asset_key,
                    self.internal_deps.values(),
                ),
            }
        else:
            return self._passed_input_tuples_by_asset_key

    @cached_property
    def in_mappings(self) -> Mapping[AssetKey, InMapping]:
        return {
            asset_key: InMapping(input_name, in_)
            for asset_key, (input_name, in_) in self.input_tuples_by_asset_key.items()
        }

    @cached_property
    def out_mappings(self) -> Mapping[AssetKey, OutMapping]:
        return {
            asset_key: OutMapping(output_name, out_)
            for asset_key, (output_name, out_) in self.output_tuples_by_asset_key.items()
        }

    @cached_property
    def asset_outs_by_output_name(self) -> Mapping[str, Out]:
        return dict(self.out_mappings.values())

    @cached_property
    def asset_keys_by_input_name(self) -> Mapping[str, AssetKey]:
        return {
            in_mapping.input_name: asset_key for asset_key, in_mapping in self.in_mappings.items()
        }

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
    def partition_mappings(self) -> Mapping[AssetKey, PartitionMapping]:
        partition_mappings = {
            self.asset_keys_by_input_names[input_name]: asset_in.partition_mapping
            for input_name, asset_in in self.directly_passed_asset_ins.items()
            if asset_in.partition_mapping is not None
        }

        if not self.deps_directly_passed_to_multi_asset:
            return partition_mappings

        return get_partition_mappings_from_deps(
            partition_mappings=partition_mappings,
            deps=self.deps_directly_passed_to_multi_asset,
            asset_name=self.op_name,
        )

    @cached_property
    def resolved_specs(self) -> Sequence[AssetSpec]:
        specs = self.spec_resolver(self)
        if not self.group_name:
            return specs

        check.invariant(
            all(spec.group_name is None for spec in specs),
            "Cannot set group_name parameter on multi_asset if one or more of the"
            " AssetSpecs/AssetOuts supplied to this multi_asset have a group_name defined.",
        )

        return [spec._replace(group_name=self.group_name) for spec in specs]


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
