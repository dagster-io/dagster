from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from functools import cached_property
from inspect import Parameter
from typing import AbstractSet, Any, Callable, NamedTuple, Optional  # noqa: UP035

import dagster._check as check
from dagster._config.config_schema import UserConfigSchema
from dagster._core.decorator_utils import get_function_params, get_valid_name_permutations
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.assets.definition.asset_dep import AssetDep
from dagster._core.definitions.assets.definition.asset_spec import (
    SYSTEM_METADATA_KEY_DAGSTER_TYPE,
    SYSTEM_METADATA_KEY_IO_MANAGER_KEY,
    AssetExecutionType,
    AssetSpec,
)
from dagster._core.definitions.assets.definition.assets_definition import (
    ASSET_SUBSET_INPUT_PREFIX,
    AssetsDefinition,
    get_partition_mappings_from_deps,
    stringify_asset_key_to_input_name,
)
from dagster._core.definitions.assets.job.asset_in import AssetIn
from dagster._core.definitions.assets.job.asset_out import AssetOut
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.decorators.op_decorator import _Op
from dagster._core.definitions.hook_definition import HookDefinition
from dagster._core.definitions.input import In
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.output import Out
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.mapping import PartitionMapping
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.utils import NoValueSentinel
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.storage.tags import COMPUTE_KIND_TAG
from dagster._core.types.dagster_type import (
    Any as DagsterAny,
    DagsterType,
    Nothing,
)


def get_function_params_without_context_or_config_or_resources(
    fn: Callable[..., Any],
) -> list[Parameter]:
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


def validate_can_coexist(asset_in: AssetIn, asset_dep: AssetDep) -> None:
    """Validates that the asset_in and asset_dep can coexist peacefully on the same asset key.
    If both asset_in and asset_dep are set on the same asset key, expect that _no_ properties
    are set on AssetIn except for the key itself.
    """
    if (
        asset_in.metadata
        or asset_in.key_prefix
        or asset_in.dagster_type != NoValueSentinel
        or asset_in.partition_mapping is not None
    ):
        raise DagsterInvalidDefinitionError(
            f"Asset key '{asset_dep.asset_key.to_user_string()}' is used as both an input (via AssetIn) and a dependency (via AssetDep). If an asset key is used as an input and also set as a dependency, the input should only define the relationship between the asset key and the input name, or optionally set the input_manager_key. Any other properties should either not be set, or should be set on the dependency."
        )


def build_and_validate_named_ins(
    fn: Callable[..., Any],
    deps: Optional[Iterable[AssetDep]],
    passed_asset_ins: Mapping[str, AssetIn],
) -> Mapping[AssetKey, "NamedIn"]:
    """Creates a mapping from AssetKey to (name of input, In object)."""
    deps = check.opt_iterable_param(deps, "deps", AssetDep)

    asset_input_params = get_function_params_without_context_or_config_or_resources(fn)

    # e.g. def fn(a, b, *, c)
    single_asset_input_params = [
        param for param in asset_input_params if param.kind == Parameter.POSITIONAL_OR_KEYWORD
    ]
    single_asset_input_param_names = {param.name for param in single_asset_input_params}
    # e.g. def fn(**kwargs)
    has_var_kwargs = any(param.kind == Parameter.VAR_KEYWORD for param in asset_input_params)

    # validate that all passed_asset_ins reference valid input names
    for input_name, asset_in in passed_asset_ins.items():
        if not (
            # function has non-definite kwargs
            has_var_kwargs
            # input name matches an existing param name
            or input_name in single_asset_input_param_names
            # input is not passed through params at all
            or (isinstance(asset_in.dagster_type, DagsterType) and asset_in.dagster_type.is_nothing)
        ):
            raise DagsterInvalidDefinitionError(
                f"Key '{input_name}' in provided ins dict does not correspond to any of the names "
                "of the arguments to the decorated function"
            )

    # get a mapping from AssetKey to respective AssetDep / AssetIn
    asset_ins_by_key = {
        asset_in.resolve_key(input_name): asset_in
        for input_name, asset_in in passed_asset_ins.items()
    }

    # if a key is referenced as both an AssetDep and an AssetIn, validate that they are compatible
    for dep in deps:
        if dep.asset_key in asset_ins_by_key:
            validate_can_coexist(asset_ins_by_key[dep.asset_key], dep)

    # create a default AssetIn for each input name, then override with any explicitly passed AssetIns
    asset_ins_by_input_name: dict[str, AssetIn] = {
        **{input_name: AssetIn() for input_name in single_asset_input_param_names},
        **passed_asset_ins,
    }

    # find the set of asset keys that are currently referenced as an AssetIn, then add AssetIns for
    # any deps that are not referenced
    asset_in_asset_keys = {
        asset_in.resolve_key(input_name) for input_name, asset_in in asset_ins_by_input_name.items()
    }
    for dep in deps:
        if dep.asset_key not in asset_in_asset_keys:
            input_name = stringify_asset_key_to_input_name(dep.asset_key)
            asset_ins_by_input_name[input_name] = AssetIn(key=dep.asset_key, dagster_type=Nothing)

    return {
        asset_in.resolve_key(input_name): NamedIn(
            input_name.replace("-", "_"),
            In(
                metadata=asset_in.metadata,
                input_manager_key=asset_in.input_manager_key,
                dagster_type=asset_in.dagster_type,
            ),
        )
        for input_name, asset_in in asset_ins_by_input_name.items()
    }


def build_named_outs(asset_outs: Mapping[str, AssetOut]) -> Mapping[AssetKey, "NamedOut"]:
    """Creates a mapping from AssetKey to (name of output, Out object)."""
    named_outs_by_asset_key: dict[AssetKey, NamedOut] = {}
    for output_name, asset_out in asset_outs.items():
        out = asset_out.to_out()
        asset_key = asset_out.key or AssetKey(
            list(filter(None, [*(asset_out.key_prefix or []), output_name]))
        )

        named_outs_by_asset_key[asset_key] = NamedOut(output_name.replace("-", "_"), out)

    return named_outs_by_asset_key


def build_subsettable_named_ins(
    asset_ins: Mapping[AssetKey, tuple[str, In]],
    asset_outs: Mapping[AssetKey, tuple[str, Out]],
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
    asset_outs: Mapping[AssetKey, tuple[str, Out]],
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
    asset_deps: Mapping[str, set[AssetKey]]
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
    hooks: Optional[AbstractSet[HookDefinition]]
    partitions_def: Optional[PartitionsDefinition]
    required_resource_keys: AbstractSet[str]
    retry_policy: Optional[RetryPolicy]
    retry_policy: Optional[RetryPolicy]
    specs: Sequence[AssetSpec]
    upstream_asset_deps: Optional[Iterable[AssetDep]]
    execution_type: Optional[AssetExecutionType]
    pool: Optional[str]
    allow_arbitrary_check_specs: bool = False

    @property
    def check_specs(self) -> Sequence[AssetCheckSpec]:
        return list(self.check_specs_by_output_name.values())


class DecoratorAssetsDefinitionBuilder:
    def __init__(
        self,
        *,
        named_ins_by_asset_key: Mapping[AssetKey, NamedIn],
        named_outs_by_asset_key: Mapping[AssetKey, NamedOut],
        internal_deps: Mapping[AssetKey, set[AssetKey]],
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

        if args.compute_kind and args.specs and any(spec.kinds for spec in args.specs):
            raise DagsterInvalidDefinitionError(
                "Can not specify compute_kind on both the @multi_asset and kinds on AssetSpecs."
            )

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
            if SYSTEM_METADATA_KEY_DAGSTER_TYPE in asset_spec.metadata:
                dagster_type = asset_spec.metadata[SYSTEM_METADATA_KEY_DAGSTER_TYPE]
            elif asset_spec.metadata.get(SYSTEM_METADATA_KEY_IO_MANAGER_KEY):
                dagster_type = DagsterAny
            else:
                dagster_type = Nothing
            named_outs_by_asset_key[asset_spec.key] = NamedOut(
                output_name,
                Out(
                    dagster_type=dagster_type,
                    is_required=not (can_subset or asset_spec.skippable),
                    description=asset_spec.description,
                    code_version=asset_spec.code_version,
                    metadata=asset_spec.metadata,
                    io_manager_key=asset_spec.metadata.get(SYSTEM_METADATA_KEY_IO_MANAGER_KEY),
                ),
            )

        upstream_deps = {}
        for spec in asset_specs:
            for dep in spec.deps:
                if dep.asset_key not in named_outs_by_asset_key:
                    upstream_deps[dep.asset_key] = dep
                if dep.asset_key in named_outs_by_asset_key and dep.partition_mapping is not None:
                    # self-dependent asset also needs to be considered an upstream_key
                    upstream_deps[dep.asset_key] = dep

        # get which asset keys have inputs set
        named_ins_by_asset_key = build_and_validate_named_ins(
            fn, upstream_deps.values(), asset_in_map
        )
        # We expect that asset_ins are a subset of asset_deps. The reason we do not check this in
        # `build_and_validate_named_ins` is because in other decorator pathways, we allow for argument-based
        # dependencies which are not specified in deps (such as the asset decorator).
        validate_named_ins_subset_of_deps(named_ins_by_asset_key, upstream_deps)

        internal_deps = {
            spec.key: {dep.asset_key for dep in spec.deps}
            for spec in asset_specs
            if spec.deps is not None
        }

        if not passed_args.allow_arbitrary_check_specs:
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
        asset_deps: Mapping[str, set[AssetKey]],
        upstream_asset_deps: Optional[Iterable[AssetDep]],
        passed_args: DecoratorAssetsDefinitionBuilderArgs,
    ):
        check.param_invariant(
            not passed_args.specs, "args", "This codepath for non-spec based create"
        )
        named_ins_by_asset_key = build_and_validate_named_ins(
            fn,
            upstream_asset_deps or set(),
            asset_in_map,
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
    def asset_keys(self) -> set[AssetKey]:
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
    def overlapping_output_names(self) -> set[str]:
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
            pool=self.args.pool,
        )(self.fn)

    def create_assets_definition(self) -> AssetsDefinition:
        return AssetsDefinition.dagster_internal_init(
            keys_by_input_name=self.asset_keys_by_input_names,
            keys_by_output_name=self.asset_keys_by_output_name,
            node_def=self.create_op_definition(),
            can_subset=self.args.can_subset,
            resource_defs=self.args.assets_def_resource_defs,
            backfill_policy=self.args.backfill_policy,
            check_specs_by_output_name=self.check_specs_by_output_name,
            specs=self.specs,
            hook_defs=self.args.hooks,
            is_subset=False,
            selected_asset_keys=None,  # not a subset so this is None
            selected_asset_check_keys=None,  # not a subset so this is none
            execution_type=self.args.execution_type,
        )

    @cached_property
    def specs(self) -> Sequence[AssetSpec]:
        if self.args.specs:
            specs = self.args.specs
            self._validate_spec_partitions_defs(specs, self.args.partitions_def)
        else:
            specs = self._synthesize_specs()

        check.invariant(
            not self.group_name
            or all(
                (spec.group_name is None or spec.group_name == self.group_name) for spec in specs
            ),
            "Cannot set group_name parameter on multi_asset if one or more of the"
            " AssetSpecs/AssetOuts supplied to this multi_asset have a group_name defined.",
        )

        if not self.group_name and not self.args.partitions_def:
            return specs

        return [
            spec.replace_attributes(
                group_name=spec.group_name or self.group_name,
                partitions_def=spec.partitions_def or self.args.partitions_def,
            )
            for spec in specs
        ]

    def _validate_spec_partitions_defs(
        self, specs: Sequence[AssetSpec], partitions_def: Optional[PartitionsDefinition]
    ) -> Optional[PartitionsDefinition]:
        any_spec_has_partitions_def = False
        any_spec_has_no_partitions_def = False
        if partitions_def is not None:
            for spec in specs:
                if spec.partitions_def is not None and spec.partitions_def != partitions_def:
                    check.failed(
                        f"AssetSpec for {spec.key.to_user_string()} has partitions_def "
                        f"(type={type(spec.partitions_def)}) which is different than the "
                        f"partitions_def provided to AssetsDefinition (type={type(partitions_def)}).",
                    )

                any_spec_has_partitions_def = (
                    any_spec_has_partitions_def or spec.partitions_def is not None
                )
                any_spec_has_no_partitions_def = (
                    any_spec_has_no_partitions_def or spec.partitions_def is None
                )

        if (
            partitions_def is not None
            and any_spec_has_partitions_def
            and any_spec_has_no_partitions_def
        ):
            check.failed(
                "If partitions_def is provided, then either all specs must have that PartitionsDefinition or none."
            )

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

            resolved_specs.append(
                asset_out.to_spec(key, deps=deps, partitions_def=self.args.partitions_def)
            )

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


def validate_named_ins_subset_of_deps(
    named_ins_per_key: Mapping[AssetKey, NamedIn],
    asset_deps_by_key: Mapping[AssetKey, AssetDep],
) -> None:
    """Validates that the asset_ins are a subset of the asset_deps. This is a common validation
    that we need to do in multiple places, so we've factored it out into a helper function.
    """
    asset_dep_keys = set(asset_deps_by_key.keys())
    asset_in_keys = set(named_ins_per_key.keys())

    if asset_in_keys - asset_dep_keys:
        invalid_asset_in_keys = asset_in_keys - asset_dep_keys
        raise DagsterInvalidDefinitionError(
            f"Invalid asset dependencies: `{invalid_asset_in_keys}` specified as AssetIns, but"
            " are not specified as `AssetDep` objects on any constituent AssetSpec objects. Asset inputs must be associated with an"
            " output produced by the asset."
        )
