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
from dagster._config.config_schema import UserConfigSchema
from dagster._core.decorator_utils import get_function_params, get_valid_name_permutations
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_in import AssetIn
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_out import AssetOut
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import (
    ASSET_SUBSET_INPUT_PREFIX,
    AssetsDefinition,
    get_partition_mappings_from_deps,
)
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.input import In
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.output import Out
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.storage.tags import COMPUTE_KIND_TAG
from dagster._core.types.dagster_type import DagsterType, Nothing

from ..asset_check_spec import AssetCheckSpec
from ..utils import NoValueSentinel
from .op_decorator import _Op


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


def build_named_ins(
    fn: Callable[..., Any],
    asset_ins: Mapping[str, AssetIn],
    deps: Optional[AbstractSet[AssetKey]],
) -> Mapping[AssetKey, "NamedIn"]:
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

    named_ins_by_asset_key: Dict[AssetKey, NamedIn] = {}
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

        named_ins_by_asset_key[asset_key] = NamedIn(
            input_name.replace("-", "_"),
            In(metadata=metadata, input_manager_key=input_manager_key, dagster_type=dagster_type),
        )

    for asset_key in deps:
        if asset_key in named_ins_by_asset_key:
            raise DagsterInvalidDefinitionError(
                f"deps value {asset_key} also declared as input/AssetIn"
            )
            # mypy doesn't realize that Nothing is a valid type here
        named_ins_by_asset_key[asset_key] = NamedIn(
            stringify_asset_key_to_input_name(asset_key),
            In(cast(type, Nothing)),
        )

    return named_ins_by_asset_key


def build_named_outs(asset_outs: Mapping[str, AssetOut]) -> Mapping[AssetKey, "NamedOut"]:
    """Creates a mapping from AssetKey to (name of output, Out object)."""
    named_outs_by_asset_key: Dict[AssetKey, NamedOut] = {}
    for output_name, asset_out in asset_outs.items():
        out = asset_out.to_out()
        asset_key = asset_out.key or AssetKey(
            list(filter(None, [*(asset_out.key_prefix or []), output_name]))
        )

        named_outs_by_asset_key[asset_key] = NamedOut(output_name.replace("-", "_"), out)

    return named_outs_by_asset_key


def build_subsettable_named_ins(
    asset_ins: Mapping[AssetKey, Tuple[str, In]],
    asset_outs: Mapping[AssetKey, Tuple[str, Out]],
    internal_upstream_deps: Iterable[AbstractSet[AssetKey]],
) -> Mapping[AssetKey, "NamedIn"]:
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
        key: NamedIn(f"{ASSET_SUBSET_INPUT_PREFIX}{name}", In(Nothing))
        for key, (name, _) in asset_outs.items()
        if key in potential_deps
    }


class NamedIn(NamedTuple):
    input_name: str
    input: In


class NamedOut(NamedTuple):
    output_name: str
    output: Out


def make_keys_by_output_name(
    asset_outs: Mapping[AssetKey, Tuple[str, Out]],
) -> Mapping[str, AssetKey]:
    return {output_name: asset_key for asset_key, (output_name, _) in asset_outs.items()}


def compute_required_resource_keys(
    required_resource_keys: AbstractSet[str],
    resource_defs: Mapping[str, ResourceDefinition],
    fn: Callable[..., Any],
    decorator_name: str,
) -> AbstractSet[str]:
    bare_required_resource_keys = set(required_resource_keys)
    resource_defs_keys = set(resource_defs.keys())
    required_resource_keys = bare_required_resource_keys | resource_defs_keys
    arg_resource_keys = {arg.name for arg in get_resource_args(fn)}
    check.param_invariant(
        len(bare_required_resource_keys or []) == 0 or len(arg_resource_keys) == 0,
        f"Cannot specify resource requirements in both {decorator_name} decorator and as"
        " arguments to the decorated function",
    )
    return required_resource_keys - arg_resource_keys


class DecoratorAssetsDefinitionBuilderArgs(NamedTuple):
    asset_deps: Mapping[str, Set[AssetKey]]
    asset_in_map: Mapping[str, AssetIn]
    asset_out_map: Mapping[str, AssetOut]
    assets_def_resource_defs: Mapping[str, ResourceDefinition]
    backfill_policy: Optional[BackfillPolicy]
    can_subset: bool
    check_specs_by_output_name: Mapping[str, AssetCheckSpec]
    code_version: Optional[str]
    compute_kind: Optional[str]
    config_schema: Optional[UserConfigSchema]
    decorator_name: str
    group_name: Optional[str]
    name: Optional[str]
    op_def_resource_defs: Mapping[str, ResourceDefinition]
    op_description: Optional[str]
    op_tags: Optional[Mapping[str, Any]]
    partitions_def: Optional[PartitionsDefinition]
    required_resource_keys: AbstractSet[str]
    retry_policy: Optional[RetryPolicy]
    retry_policy: Optional[RetryPolicy]
    specs: Sequence[AssetSpec]
    upstream_asset_deps: Optional[Iterable[AssetDep]]

    @property
    def check_specs(self) -> Sequence[AssetCheckSpec]:
        return list(self.check_specs_by_output_name.values())


class DecoratorAssetsDefinitionBuilder:
    def __init__(
        self,
        *,
        named_ins_by_asset_key: Mapping[AssetKey, NamedIn],
        named_outs_by_asset_key: Mapping[AssetKey, NamedOut],
        internal_deps: Mapping[AssetKey, Set[AssetKey]],
        op_name: str,
        args: DecoratorAssetsDefinitionBuilderArgs,
        fn: Callable[..., Any],
    ) -> None:
        self.named_outs_by_asset_key = named_outs_by_asset_key
        self.internal_deps = internal_deps
        self.op_name = op_name
        self.args = args
        self.fn = fn

        self.named_ins_by_asset_key = (
            (
                {
                    **named_ins_by_asset_key,
                    **build_subsettable_named_ins(
                        named_ins_by_asset_key,
                        named_outs_by_asset_key,
                        self.internal_deps.values(),
                    ),
                }
            )
            if self.args.can_subset and self.internal_deps
            else named_ins_by_asset_key
        )

    @staticmethod
    def for_multi_asset(
        *, fn: Callable[..., Any], args: DecoratorAssetsDefinitionBuilderArgs
    ) -> "DecoratorAssetsDefinitionBuilder":
        op_name = args.name or fn.__name__

        if args.asset_out_map and args.specs:
            raise DagsterInvalidDefinitionError("Must specify only outs or specs but not both.")

        if args.specs:
            check.invariant(
                args.decorator_name == "@multi_asset", "Only hit this code path in multi_asset."
            )
            if args.upstream_asset_deps:
                raise DagsterInvalidDefinitionError(
                    "Can not pass deps and specs to @multi_asset, specify deps on the AssetSpecs"
                    " directly."
                )
            if args.asset_deps:
                raise DagsterInvalidDefinitionError(
                    "Can not pass internal_asset_deps and specs to @multi_asset, specify deps on"
                    " the AssetSpecs directly."
                )
            return DecoratorAssetsDefinitionBuilder.from_multi_asset_specs(
                fn=fn,
                op_name=op_name,
                passed_args=args,
                asset_specs=args.specs,
                can_subset=args.can_subset,
                asset_in_map=args.asset_in_map,
            )

        return DecoratorAssetsDefinitionBuilder.from_asset_outs_in_asset_centric_decorator(
            fn=fn,
            op_name=op_name,
            asset_in_map=args.asset_in_map,
            asset_out_map=args.asset_out_map,
            asset_deps=args.asset_deps,
            upstream_asset_deps=args.upstream_asset_deps,
            passed_args=args,
        )

    @staticmethod
    def from_multi_asset_specs(
        *,
        fn: Callable[..., Any],
        op_name: str,
        asset_specs: Sequence[AssetSpec],
        can_subset: bool,
        asset_in_map: Mapping[str, AssetIn],
        passed_args: DecoratorAssetsDefinitionBuilderArgs,
    ) -> "DecoratorAssetsDefinitionBuilder":
        check.param_invariant(passed_args.specs, "passed_args", "Must use specs in this codepath")

        named_outs_by_asset_key: Mapping[AssetKey, NamedOut] = {}
        for asset_spec in asset_specs:
            output_name = asset_spec.key.to_python_identifier()
            named_outs_by_asset_key[asset_spec.key] = NamedOut(
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
        for spec in asset_specs:
            for dep in spec.deps:
                if dep.asset_key not in named_outs_by_asset_key:
                    upstream_keys.add(dep.asset_key)
                if dep.asset_key in named_outs_by_asset_key and dep.partition_mapping is not None:
                    # self-dependent asset also needs to be considered an upstream_key
                    upstream_keys.add(dep.asset_key)

        # get which asset keys have inputs set
        loaded_upstreams = build_named_ins(fn, asset_in_map, deps=set())
        unexpected_upstreams = {key for key in loaded_upstreams.keys() if key not in upstream_keys}
        if unexpected_upstreams:
            raise DagsterInvalidDefinitionError(
                f"Asset inputs {unexpected_upstreams} do not have dependencies on the passed"
                " AssetSpec(s). Set the deps on the appropriate AssetSpec(s)."
            )
        remaining_upstream_keys = {key for key in upstream_keys if key not in loaded_upstreams}
        named_ins_by_asset_key = build_named_ins(fn, asset_in_map, deps=remaining_upstream_keys)

        internal_deps = {
            spec.key: {dep.asset_key for dep in spec.deps}
            for spec in asset_specs
            if spec.deps is not None
        }

        _validate_check_specs_target_relevant_asset_keys(
            passed_args.check_specs, [spec.key for spec in asset_specs]
        )

        return DecoratorAssetsDefinitionBuilder(
            named_ins_by_asset_key=named_ins_by_asset_key,
            named_outs_by_asset_key=named_outs_by_asset_key,
            internal_deps=internal_deps,
            op_name=op_name,
            args=passed_args,
            fn=fn,
        )

    @staticmethod
    def from_asset_outs_in_asset_centric_decorator(
        *,
        fn: Callable[..., Any],
        op_name: str,
        asset_in_map: Mapping[str, AssetIn],
        asset_out_map: Mapping[str, AssetOut],
        asset_deps: Mapping[str, Set[AssetKey]],
        upstream_asset_deps: Optional[Iterable[AssetDep]],
        passed_args: DecoratorAssetsDefinitionBuilderArgs,
    ):
        check.param_invariant(
            not passed_args.specs, "args", "This codepath for non-spec based create"
        )
        named_ins_by_asset_key = build_named_ins(
            fn,
            asset_in_map,
            deps=({dep.asset_key for dep in upstream_asset_deps} if upstream_asset_deps else set()),
        )
        named_outs_by_asset_key = build_named_outs(asset_out_map)

        # validate that the asset_ins are a subset of the upstream asset_deps.
        upstream_internal_asset_keys = set().union(*asset_deps.values())
        asset_in_keys = set(named_ins_by_asset_key.keys())
        if asset_deps and not asset_in_keys.issubset(upstream_internal_asset_keys):
            invalid_asset_in_keys = asset_in_keys - upstream_internal_asset_keys
            check.failed(
                f"Invalid asset dependencies: `{invalid_asset_in_keys}` specified as asset"
                " inputs, but are not specified in `internal_asset_deps`. Asset inputs must"
                " be associated with an output produced by the asset."
            )

        # validate that the asset_deps make sense
        valid_asset_deps = asset_in_keys | set(named_outs_by_asset_key.keys())
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

        keys_by_output_name = make_keys_by_output_name(named_outs_by_asset_key)
        internal_deps = {keys_by_output_name[name]: asset_deps[name] for name in asset_deps}

        _validate_check_specs_target_relevant_asset_keys(
            passed_args.check_specs, list(named_outs_by_asset_key.keys())
        )

        return DecoratorAssetsDefinitionBuilder(
            named_ins_by_asset_key=named_ins_by_asset_key,
            named_outs_by_asset_key=named_outs_by_asset_key,
            internal_deps=internal_deps,
            op_name=op_name,
            args=passed_args,
            fn=fn,
        )

    @property
    def group_name(self) -> Optional[str]:
        return self.args.group_name

    @cached_property
    def outs_by_output_name(self) -> Mapping[str, Out]:
        return dict(self.named_outs_by_asset_key.values())

    @cached_property
    def asset_keys_by_input_name(self) -> Mapping[str, AssetKey]:
        return {
            in_mapping.input_name: asset_key
            for asset_key, in_mapping in self.named_ins_by_asset_key.items()
        }

    @cached_property
    def asset_keys_by_output_name(self) -> Mapping[str, AssetKey]:
        return {
            out_mapping.output_name: asset_key
            for asset_key, out_mapping in self.named_outs_by_asset_key.items()
        }

    @cached_property
    def asset_keys(self) -> Set[AssetKey]:
        return set(self.named_outs_by_asset_key.keys())

    @cached_property
    def check_specs_by_output_name(self) -> Mapping[str, AssetCheckSpec]:
        return self.args.check_specs_by_output_name

    @cached_property
    def check_outs_by_output_name(self) -> Mapping[str, Out]:
        return {
            output_name: Out(dagster_type=None, is_required=not self.args.can_subset)
            for output_name in self.check_specs_by_output_name.keys()
        }

    @cached_property
    def combined_outs_by_output_name(self) -> Mapping[str, Out]:
        return {
            **self.outs_by_output_name,
            **self.check_outs_by_output_name,
        }

    @cached_property
    def overlapping_output_names(self) -> Set[str]:
        return set(self.outs_by_output_name.keys()) & set(self.check_outs_by_output_name.keys())

    @cached_property
    def ins_by_input_names(self) -> Mapping[str, In]:
        return {in_name: in_obj for in_name, in_obj in self.named_ins_by_asset_key.values()}

    @cached_property
    def asset_keys_by_input_names(self) -> Mapping[str, AssetKey]:
        return {
            in_mapping.input_name: asset_key
            for asset_key, in_mapping in self.named_ins_by_asset_key.items()
        }

    @cached_property
    def partition_mappings(self) -> Mapping[AssetKey, PartitionMapping]:
        partition_mappings = {
            self.asset_keys_by_input_names[input_name]: asset_in.partition_mapping
            for input_name, asset_in in self.args.asset_in_map.items()
            if asset_in.partition_mapping is not None
        }

        if not self.args.upstream_asset_deps:
            return partition_mappings

        return get_partition_mappings_from_deps(
            partition_mappings=partition_mappings,
            deps=self.args.upstream_asset_deps,
            asset_name=self.op_name,
        )

    @cached_property
    def required_resource_keys(self) -> AbstractSet[str]:
        return compute_required_resource_keys(
            required_resource_keys=self.args.required_resource_keys,
            resource_defs=self.args.op_def_resource_defs,
            fn=self.fn,
            decorator_name=self.args.decorator_name,
        )

    def create_op_definition(self) -> OpDefinition:
        return _Op(
            name=self.op_name,
            description=self.args.op_description,
            ins=self.ins_by_input_names,
            out=self.combined_outs_by_output_name,
            required_resource_keys=self.required_resource_keys,
            tags={
                **({COMPUTE_KIND_TAG: self.args.compute_kind} if self.args.compute_kind else {}),
                **(self.args.op_tags or {}),
            },
            config_schema=self.args.config_schema,
            retry_policy=self.args.retry_policy,
            code_version=self.args.code_version,
        )(self.fn)

    def create_assets_definition(self) -> AssetsDefinition:
        return AssetsDefinition.dagster_internal_init(
            keys_by_input_name=self.asset_keys_by_input_names,
            keys_by_output_name=self.asset_keys_by_output_name,
            node_def=self.create_op_definition(),
            partitions_def=self.args.partitions_def,
            can_subset=self.args.can_subset,
            resource_defs=self.args.assets_def_resource_defs,
            backfill_policy=self.args.backfill_policy,
            check_specs_by_output_name=self.check_specs_by_output_name,
            specs=self.specs,
            is_subset=False,
            selected_asset_keys=None,  # not a subset so this is None
            selected_asset_check_keys=None,  # not a subset so this is none
        )

    @cached_property
    def specs(self) -> Sequence[AssetSpec]:
        specs = self.args.specs if self.args.specs else self._synthesize_specs()

        if not self.group_name:
            return specs

        check.invariant(
            all((spec.group_name is None or spec.group_name == self.group_name) for spec in specs),
            "Cannot set group_name parameter on multi_asset if one or more of the"
            " AssetSpecs/AssetOuts supplied to this multi_asset have a group_name defined.",
        )

        return [spec._replace(group_name=self.group_name) for spec in specs]

    def _synthesize_specs(self) -> Sequence[AssetSpec]:
        resolved_specs = []
        input_deps_by_key = {
            key: AssetDep(asset=key, partition_mapping=self.partition_mappings.get(key))
            for key in self.asset_keys_by_input_names.values()
        }
        input_deps = list(input_deps_by_key.values())
        for output_name, asset_out in self.args.asset_out_map.items():
            key = self.asset_keys_by_output_name[output_name]
            if self.args.asset_deps:
                deps = [
                    input_deps_by_key.get(
                        dep_key,
                        AssetDep(
                            asset=dep_key,
                            partition_mapping=self.partition_mappings.get(key),
                        ),
                    )
                    for dep_key in self.args.asset_deps.get(output_name, [])
                ]
            else:
                deps = input_deps

            resolved_specs.append(asset_out.to_spec(key, deps=deps))

        specs = resolved_specs
        return specs


def validate_and_assign_output_names_to_check_specs(
    check_specs: Optional[Sequence[AssetCheckSpec]], valid_asset_keys: Sequence[AssetKey]
) -> Mapping[str, AssetCheckSpec]:
    _validate_check_specs_target_relevant_asset_keys(check_specs, valid_asset_keys)
    return create_check_specs_by_output_name(check_specs)


def create_check_specs_by_output_name(
    check_specs: Optional[Sequence[AssetCheckSpec]],
) -> Mapping[str, AssetCheckSpec]:
    checks_by_output_name = {
        spec.get_python_identifier(): spec
        for spec in check.opt_sequence_param(check_specs, "check_specs", of_type=AssetCheckSpec)
    }
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
