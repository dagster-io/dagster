from collections import Counter
from inspect import Parameter
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
    overload,
)

import dagster._check as check
from dagster._annotations import deprecated_param, experimental_param
from dagster._builtins import Nothing
from dagster._config import UserConfigSchema
from dagster._core.decorator_utils import get_function_params, get_valid_name_permutations
from dagster._core.definitions.asset_dep import AssetDep, CoercibleToAssetDep
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.config import ConfigMapping
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.metadata import ArbitraryMetadataMapping, MetadataUserInput
from dagster._core.definitions.partition_mapping import PartitionMapping
from dagster._core.definitions.resource_annotation import (
    get_resource_args,
)
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster._core.types.dagster_type import DagsterType
from dagster._utils.warnings import (
    disable_dagster_warnings,
)

from ..asset_check_spec import AssetCheckSpec
from ..asset_in import AssetIn
from ..asset_out import AssetOut
from ..asset_spec import AssetSpec
from ..assets import AssetsDefinition
from ..backfill_policy import BackfillPolicy, BackfillPolicyType
from ..decorators.graph_decorator import graph
from ..decorators.op_decorator import _Op
from ..events import AssetKey, CoercibleToAssetKey, CoercibleToAssetKeyPrefix
from ..input import GraphIn, In
from ..output import GraphOut, Out
from ..partition import PartitionsDefinition
from ..policy import RetryPolicy
from ..resource_definition import ResourceDefinition
from ..utils import DEFAULT_IO_MANAGER_KEY, DEFAULT_OUTPUT, NoValueSentinel


@overload
def asset(
    compute_fn: Callable,
) -> AssetsDefinition: ...


@overload
def asset(
    *,
    name: Optional[str] = ...,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    ins: Optional[Mapping[str, AssetIn]] = ...,
    deps: Optional[Iterable[CoercibleToAssetDep]] = ...,
    metadata: Optional[Mapping[str, Any]] = ...,
    description: Optional[str] = ...,
    config_schema: Optional[UserConfigSchema] = None,
    required_resource_keys: Optional[Set[str]] = ...,
    resource_defs: Optional[Mapping[str, object]] = ...,
    io_manager_def: Optional[object] = ...,
    io_manager_key: Optional[str] = ...,
    compute_kind: Optional[str] = ...,
    dagster_type: Optional[DagsterType] = ...,
    partitions_def: Optional[PartitionsDefinition] = ...,
    op_tags: Optional[Mapping[str, Any]] = ...,
    group_name: Optional[str] = ...,
    output_required: bool = ...,
    freshness_policy: Optional[FreshnessPolicy] = ...,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = ...,
    backfill_policy: Optional[BackfillPolicy] = ...,
    retry_policy: Optional[RetryPolicy] = ...,
    code_version: Optional[str] = ...,
    key: Optional[CoercibleToAssetKey] = None,
    non_argument_deps: Optional[Union[Set[AssetKey], Set[str]]] = ...,
    check_specs: Optional[Sequence[AssetCheckSpec]] = ...,
) -> Callable[[Callable[..., Any]], AssetsDefinition]: ...


@experimental_param(param="resource_defs")
@experimental_param(param="io_manager_def")
@experimental_param(param="auto_materialize_policy")
@experimental_param(param="backfill_policy")
@deprecated_param(
    param="non_argument_deps", breaking_version="2.0.0", additional_warn_text="use `deps` instead."
)
def asset(
    compute_fn: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    deps: Optional[Iterable[CoercibleToAssetDep]] = None,
    metadata: Optional[ArbitraryMetadataMapping] = None,
    description: Optional[str] = None,
    config_schema: Optional[UserConfigSchema] = None,
    required_resource_keys: Optional[Set[str]] = None,
    resource_defs: Optional[Mapping[str, object]] = None,
    io_manager_def: Optional[object] = None,
    io_manager_key: Optional[str] = None,
    compute_kind: Optional[str] = None,
    dagster_type: Optional[DagsterType] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
    group_name: Optional[str] = None,
    output_required: bool = True,
    freshness_policy: Optional[FreshnessPolicy] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    retry_policy: Optional[RetryPolicy] = None,
    code_version: Optional[str] = None,
    key: Optional[CoercibleToAssetKey] = None,
    non_argument_deps: Optional[Union[Set[AssetKey], Set[str]]] = None,
    check_specs: Optional[Sequence[AssetCheckSpec]] = None,
) -> Union[AssetsDefinition, Callable[[Callable[..., Any]], AssetsDefinition]]:
    """Create a definition for how to compute an asset.

    A software-defined asset is the combination of:
      1. An asset key, e.g. the name of a table.
      2. A function, which can be run to compute the contents of the asset.
      3. A set of upstream assets that are provided as inputs to the function when computing the asset.

    Unlike an op, whose dependencies are determined by the graph it lives inside, an asset knows
    about the upstream assets it depends on. The upstream assets are inferred from the arguments
    to the decorated function. The name of the argument designates the name of the upstream asset.

    An asset has an op inside it to represent the function that computes it. The name of the op
    will be the segments of the asset key, separated by double-underscores.

    Args:
        name (Optional[str]): The name of the asset.  If not provided, defaults to the name of the
            decorated function. The asset's name must be a valid name in dagster (ie only contains
            letters, numbers, and _) and may not contain python reserved keywords.
        key_prefix (Optional[Union[str, Sequence[str]]]): If provided, the asset's key is the
            concatenation of the key_prefix and the asset's name, which defaults to the name of
            the decorated function. Each item in key_prefix must be a valid name in dagster (ie only
            contains letters, numbers, and _) and may not contain python reserved keywords.
        ins (Optional[Mapping[str, AssetIn]]): A dictionary that maps input names to information
            about the input.
        deps (Optional[Sequence[Union[AssetDep, AssetsDefinition, SourceAsset, AssetKey, str]]]):
            The assets that are upstream dependencies, but do not correspond to a parameter of the
            decorated function. If the AssetsDefinition for a multi_asset is provided, dependencies on
            all assets created by the multi_asset will be created.
        config_schema (Optional[ConfigSchema): The configuration schema for the asset's underlying
            op. If set, Dagster will check that config provided for the op matches this schema and fail
            if it does not. If not set, Dagster will accept any config provided for the op.
        metadata (Optional[Dict[str, Any]]): A dict of metadata entries for the asset.
        required_resource_keys (Optional[Set[str]]): Set of resource handles required by the op.
        io_manager_key (Optional[str]): The resource key of the IOManager used
            for storing the output of the op as an asset, and for loading it in downstream ops
            (default: "io_manager"). Only one of io_manager_key and io_manager_def can be provided.
        io_manager_def (Optional[object]): (Experimental) The IOManager used for
            storing the output of the op as an asset,  and for loading it in
            downstream ops. Only one of io_manager_def and io_manager_key can be provided.
        compute_kind (Optional[str]): A string to represent the kind of computation that produces
            the asset, e.g. "dbt" or "spark". It will be displayed in the Dagster UI as a badge on the asset.
        dagster_type (Optional[DagsterType]): Allows specifying type validation functions that
            will be executed on the output of the decorated function after it runs.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the asset.
        op_tags (Optional[Dict[str, Any]]): A dictionary of tags for the op that computes the asset.
            Frameworks may expect and require certain metadata to be attached to a op. Values that
            are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. If not provided,
            the name "default" is used.
        resource_defs (Optional[Mapping[str, object]]):
            (Experimental) A mapping of resource keys to resources. These resources
            will be initialized during execution, and can be accessed from the
            context within the body of the function.
        output_required (bool): Whether the decorated function will always materialize an asset.
            Defaults to True. If False, the function can return None, which will not be materialized to
            storage and will halt execution of downstream assets.
        freshness_policy (FreshnessPolicy): A constraint telling Dagster how often this asset is intended to be updated
            with respect to its root data.
        auto_materialize_policy (AutoMaterializePolicy): (Experimental) Configure Dagster to automatically materialize
            this asset according to its FreshnessPolicy and when upstream dependencies change.
        backfill_policy (BackfillPolicy): (Experimental) Configure Dagster to backfill this asset according to its
            BackfillPolicy.
        retry_policy (Optional[RetryPolicy]): The retry policy for the op that computes the asset.
        code_version (Optional[str]): (Experimental) Version of the code that generates this asset. In
            general, versions should be set only for code that deterministically produces the same
            output when given the same inputs.
        check_specs (Optional[Sequence[AssetCheckSpec]]): (Experimental) Specs for asset checks that
            execute in the decorated function after materializing the asset.
        non_argument_deps (Optional[Union[Set[AssetKey], Set[str]]]): Deprecated, use deps instead.
            Set of asset keys that are upstream dependencies, but do not pass an input to the asset.
        key (Optional[CoeercibleToAssetKey]): The key for this asset. If provided, cannot specify key_prefix or name.

    Examples:
        .. code-block:: python

            @asset
            def my_asset(my_upstream_asset: int) -> int:
                return my_upstream_asset + 1
    """

    def create_asset():
        upstream_asset_deps = _deps_and_non_argument_deps_to_asset_deps(
            deps=deps, non_argument_deps=non_argument_deps
        )

        return _Asset(
            name=cast(Optional[str], name),  # (mypy bug that it can't infer name is Optional[str])
            key_prefix=key_prefix,
            ins=ins,
            deps=upstream_asset_deps,
            metadata=metadata,
            description=description,
            config_schema=config_schema,
            required_resource_keys=required_resource_keys,
            resource_defs=resource_defs,
            io_manager_key=io_manager_key,
            io_manager_def=io_manager_def,
            compute_kind=check.opt_str_param(compute_kind, "compute_kind"),
            dagster_type=dagster_type,
            partitions_def=partitions_def,
            op_tags=op_tags,
            group_name=group_name,
            output_required=output_required,
            freshness_policy=freshness_policy,
            auto_materialize_policy=auto_materialize_policy,
            backfill_policy=backfill_policy,
            retry_policy=retry_policy,
            code_version=code_version,
            check_specs=check_specs,
            key=key,
        )

    if compute_fn is not None:
        return create_asset()(compute_fn)

    def inner(fn: Callable[..., Any]) -> AssetsDefinition:
        check.invariant(
            not (io_manager_key and io_manager_def),
            "Both io_manager_key and io_manager_def were provided to `@asset` decorator. Please"
            " provide one or the other. ",
        )
        return create_asset()(fn)

    return inner


def _resolve_key_and_name(
    *,
    key: Optional[CoercibleToAssetKey],
    key_prefix: Optional[CoercibleToAssetKeyPrefix],
    name: Optional[str],
    decorator: str,
    fn: Callable[..., Any],
) -> Tuple[AssetKey, str]:
    if (name or key_prefix) and key:
        raise DagsterInvalidDefinitionError(
            f"Cannot specify a name or key prefix for {decorator} when the key"
            " argument is provided."
        )
    key_prefix_list = [key_prefix] if isinstance(key_prefix, str) else key_prefix
    key = AssetKey.from_coercible(key) if key else None
    assigned_name = name or fn.__name__
    return (
        (
            # the filter here appears unnecessary per typing, but this exists
            # historically so keeping it here to be conservative in case users
            # can get Nones into the key_prefix_list somehow
            AssetKey(list(filter(None, [*(key_prefix_list or []), assigned_name])))
            if not key
            else key
        ),
        assigned_name,
    )


class _Asset:
    def __init__(
        self,
        name: Optional[str] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        ins: Optional[Mapping[str, AssetIn]] = None,
        deps: Optional[Iterable[AssetDep]] = None,
        metadata: Optional[ArbitraryMetadataMapping] = None,
        description: Optional[str] = None,
        config_schema: Optional[UserConfigSchema] = None,
        required_resource_keys: Optional[Set[str]] = None,
        resource_defs: Optional[Mapping[str, object]] = None,
        io_manager_key: Optional[str] = None,
        io_manager_def: Optional[object] = None,
        compute_kind: Optional[str] = None,
        dagster_type: Optional[DagsterType] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        op_tags: Optional[Mapping[str, Any]] = None,
        group_name: Optional[str] = None,
        output_required: bool = True,
        freshness_policy: Optional[FreshnessPolicy] = None,
        auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        retry_policy: Optional[RetryPolicy] = None,
        code_version: Optional[str] = None,
        key: Optional[CoercibleToAssetKey] = None,
        check_specs: Optional[Sequence[AssetCheckSpec]] = None,
    ):
        self.name = name
        self.key_prefix = key_prefix
        self.ins = ins or {}
        self.deps = deps or []
        self.metadata = metadata
        self.description = description
        self.required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys"
        )
        self.io_manager_key = io_manager_key
        self.io_manager_def = io_manager_def
        self.config_schema = config_schema
        self.compute_kind = compute_kind
        self.dagster_type = dagster_type
        self.partitions_def = partitions_def
        self.op_tags = op_tags
        self.resource_defs = dict(check.opt_mapping_param(resource_defs, "resource_defs"))
        self.group_name = group_name
        self.output_required = output_required
        self.freshness_policy = freshness_policy
        self.retry_policy = retry_policy
        self.auto_materialize_policy = auto_materialize_policy
        self.backfill_policy = backfill_policy
        self.code_version = code_version
        self.check_specs = check_specs
        self.key = key

    def __call__(self, fn: Callable) -> AssetsDefinition:
        from dagster._config.pythonic_config import (
            validate_resource_annotated_function,
        )
        from dagster._core.execution.build_resources import wrap_resources_for_execution

        validate_resource_annotated_function(fn)

        asset_ins = build_asset_ins(fn, self.ins or {}, {dep.asset_key for dep in self.deps})

        out_asset_key, asset_name = _resolve_key_and_name(
            key=self.key,
            key_prefix=self.key_prefix,
            name=self.name,
            fn=fn,
            decorator="@asset",
        )

        with disable_dagster_warnings():
            arg_resource_keys = {arg.name for arg in get_resource_args(fn)}

            bare_required_resource_keys = set(self.required_resource_keys)

            resource_defs_dict = self.resource_defs
            resource_defs_keys = set(resource_defs_dict.keys())
            decorator_resource_keys = bare_required_resource_keys | resource_defs_keys

            io_manager_key = self.io_manager_key
            if self.io_manager_def:
                if not io_manager_key:
                    io_manager_key = out_asset_key.to_python_identifier("io_manager")

                if (
                    io_manager_key in self.resource_defs
                    and self.resource_defs[io_manager_key] != self.io_manager_def
                ):
                    raise DagsterInvalidDefinitionError(
                        f"Provided conflicting definitions for io manager key '{io_manager_key}'."
                        " Please provide only one definition per key."
                    )

                resource_defs_dict[io_manager_key] = self.io_manager_def

            wrapped_resource_defs = wrap_resources_for_execution(resource_defs_dict)

            check.param_invariant(
                len(bare_required_resource_keys) == 0 or len(arg_resource_keys) == 0,
                "Cannot specify resource requirements in both @asset decorator and as arguments"
                " to the decorated function",
            )

            io_manager_key = cast(str, io_manager_key) if io_manager_key else DEFAULT_IO_MANAGER_KEY

            out = Out(
                metadata=self.metadata or {},
                io_manager_key=io_manager_key,
                dagster_type=self.dagster_type if self.dagster_type else NoValueSentinel,
                description=self.description,
                is_required=self.output_required,
                code_version=self.code_version,
            )

            check_specs_by_output_name = _validate_and_assign_output_names_to_check_specs(
                self.check_specs, [out_asset_key]
            )
            check_outs: Mapping[str, Out] = {
                output_name: Out(dagster_type=None)
                for output_name in check_specs_by_output_name.keys()
            }

            op_required_resource_keys = decorator_resource_keys - arg_resource_keys

            op = _Op(
                name=out_asset_key.to_python_identifier(),
                description=self.description,
                ins=dict(asset_ins.values()),
                out={DEFAULT_OUTPUT: out, **check_outs},
                # Any resource requirements specified as arguments will be identified as
                # part of the Op definition instantiation
                required_resource_keys=op_required_resource_keys,
                tags={
                    **({"kind": self.compute_kind} if self.compute_kind else {}),
                    **(self.op_tags or {}),
                },
                config_schema=self.config_schema,
                retry_policy=self.retry_policy,
                code_version=self.code_version,
            )(fn)

            # check backfill policy is BackfillPolicyType.SINGLE_RUN for non-partitioned asset
            if self.partitions_def is None:
                check.param_invariant(
                    (
                        self.backfill_policy.policy_type is BackfillPolicyType.SINGLE_RUN
                        if self.backfill_policy
                        else True
                    ),
                    "backfill_policy",
                    "Non partitioned asset can only have single run backfill policy",
                )

        keys_by_input_name = {
            input_name: asset_key for asset_key, (input_name, _) in asset_ins.items()
        }
        partition_mappings = {
            keys_by_input_name[input_name]: asset_in.partition_mapping
            for input_name, asset_in in self.ins.items()
            if asset_in.partition_mapping is not None
        }

        partition_mappings = _get_partition_mappings_from_deps(
            partition_mappings=partition_mappings, deps=self.deps, asset_name=asset_name
        )

        return AssetsDefinition.dagster_internal_init(
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name={"result": out_asset_key},
            node_def=op,
            partitions_def=self.partitions_def,
            partition_mappings=partition_mappings if partition_mappings else None,
            resource_defs=wrapped_resource_defs,
            group_names_by_key={out_asset_key: self.group_name} if self.group_name else None,
            freshness_policies_by_key=(
                {out_asset_key: self.freshness_policy} if self.freshness_policy else None
            ),
            auto_materialize_policies_by_key=(
                {out_asset_key: self.auto_materialize_policy}
                if self.auto_materialize_policy
                else None
            ),
            backfill_policy=self.backfill_policy,
            asset_deps=None,  # no asset deps in single-asset decorator
            selected_asset_keys=None,  # no subselection in decorator
            can_subset=False,
            metadata_by_key={out_asset_key: self.metadata} if self.metadata else None,
            # see comment in @multi_asset's call to dagster_internal_init for the gory details
            # this is best understood as an _override_ which @asset does not support
            descriptions_by_key=None,
            check_specs_by_output_name=check_specs_by_output_name,
            selected_asset_check_keys=None,  # no subselection in decorator
        )


@experimental_param(param="resource_defs")
@deprecated_param(
    param="non_argument_deps", breaking_version="2.0.0", additional_warn_text="use `deps` instead."
)
def multi_asset(
    *,
    outs: Optional[Mapping[str, AssetOut]] = None,
    name: Optional[str] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    deps: Optional[Iterable[CoercibleToAssetDep]] = None,
    description: Optional[str] = None,
    config_schema: Optional[UserConfigSchema] = None,
    required_resource_keys: Optional[Set[str]] = None,
    compute_kind: Optional[str] = None,
    internal_asset_deps: Optional[Mapping[str, Set[AssetKey]]] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
    can_subset: bool = False,
    resource_defs: Optional[Mapping[str, object]] = None,
    group_name: Optional[str] = None,
    retry_policy: Optional[RetryPolicy] = None,
    code_version: Optional[str] = None,
    specs: Optional[Sequence[AssetSpec]] = None,
    check_specs: Optional[Sequence[AssetCheckSpec]] = None,
    # deprecated
    non_argument_deps: Optional[Union[Set[AssetKey], Set[str]]] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    """Create a combined definition of multiple assets that are computed using the same op and same
    upstream assets.

    Each argument to the decorated function references an upstream asset that this asset depends on.
    The name of the argument designates the name of the upstream asset.

    You can set I/O managers keys, auto-materialize policies, freshness policies, group names, etc.
    on an individual asset within the multi-asset by attaching them to the :py:class:`AssetOut`
    corresponding to that asset in the `outs` parameter.

    Args:
        name (Optional[str]): The name of the op.
        outs: (Optional[Dict[str, AssetOut]]): The AssetOuts representing the assets materialized by
            this function. AssetOuts detail the output, IO management, and core asset properties.
            This argument is required except when AssetSpecs are used.
        ins (Optional[Mapping[str, AssetIn]]): A dictionary that maps input names to information
            about the input.
        deps (Optional[Sequence[Union[AssetsDefinition, SourceAsset, AssetKey, str]]]):
            The assets that are upstream dependencies, but do not correspond to a parameter of the
            decorated function. If the AssetsDefinition for a multi_asset is provided, dependencies on
            all assets created by the multi_asset will be created.
        config_schema (Optional[ConfigSchema): The configuration schema for the asset's underlying
            op. If set, Dagster will check that config provided for the op matches this schema and fail
            if it does not. If not set, Dagster will accept any config provided for the op.
        required_resource_keys (Optional[Set[str]]): Set of resource handles required by the underlying op.
        compute_kind (Optional[str]): A string to represent the kind of computation that produces
            the asset, e.g. "dbt" or "spark". It will be displayed in the Dagster UI as a badge on the asset.
        internal_asset_deps (Optional[Mapping[str, Set[AssetKey]]]): By default, it is assumed
            that all assets produced by a multi_asset depend on all assets that are consumed by that
            multi asset. If this default is not correct, you pass in a map of output names to a
            corrected set of AssetKeys that they depend on. Any AssetKeys in this list must be either
            used as input to the asset or produced within the op.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the assets.
        backfill_policy (Optional[BackfillPolicy]): The backfill policy for the op that computes the asset.
        op_tags (Optional[Dict[str, Any]]): A dictionary of tags for the op that computes the asset.
            Frameworks may expect and require certain metadata to be attached to a op. Values that
            are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.
        can_subset (bool): If this asset's computation can emit a subset of the asset
            keys based on the context.selected_assets argument. Defaults to False.
        resource_defs (Optional[Mapping[str, object]]):
            (Experimental) A mapping of resource keys to resources. These resources
            will be initialized during execution, and can be accessed from the
            context within the body of the function.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. This
            group name will be applied to all assets produced by this multi_asset.
        retry_policy (Optional[RetryPolicy]): The retry policy for the op that computes the asset.
        code_version (Optional[str]): (Experimental) Version of the code encapsulated by the multi-asset. If set,
            this is used as a default code version for all defined assets.
        specs (Optional[Sequence[AssetSpec]]): (Experimental) The specifications for the assets materialized
            by this function.
        check_specs (Optional[Sequence[AssetCheckSpec]]): (Experimental) Specs for asset checks that
            execute in the decorated function after materializing the assets.
        non_argument_deps (Optional[Union[Set[AssetKey], Set[str]]]): Deprecated, use deps instead. Set of asset keys that are upstream
            dependencies, but do not pass an input to the multi_asset.

    Examples:
        .. code-block:: python

            # Use IO managers to handle I/O:
            @multi_asset(
                outs={
                    "my_string_asset": AssetOut(),
                    "my_int_asset": AssetOut(),
                }
            )
            def my_function(upstream_asset: int):
                result = upstream_asset + 1
                return str(result), result

            # Handle I/O on your own:
            @multi_asset(
                outs={
                    "asset1": AssetOut(),
                    "asset2": AssetOut(),
                },
                deps=["asset0"],
            )
            def my_function():
                asset0_value = load(path="asset0")
                asset1_result, asset2_result = do_some_transformation(asset0_value)
                write(asset1_result, path="asset1")
                write(asset2_result, path="asset2")
                return None, None
    """
    from dagster._core.execution.build_resources import wrap_resources_for_execution

    specs = check.opt_list_param(specs, "specs", of_type=AssetSpec)

    upstream_asset_deps = _deps_and_non_argument_deps_to_asset_deps(
        deps=deps, non_argument_deps=non_argument_deps
    )

    asset_deps = check.opt_mapping_param(
        internal_asset_deps, "internal_asset_deps", key_type=str, value_type=set
    )
    required_resource_keys = check.opt_set_param(
        required_resource_keys, "required_resource_keys", of_type=str
    )
    resource_defs = wrap_resources_for_execution(
        check.opt_mapping_param(resource_defs, "resource_defs", key_type=str)
    )

    _config_schema = check.opt_mapping_param(
        config_schema,  # type: ignore
        "config_schema",
        additional_message="Only dicts are supported for asset config_schema.",
    )

    bare_required_resource_keys = set(required_resource_keys)
    resource_defs_keys = set(resource_defs.keys())
    required_resource_keys = bare_required_resource_keys | resource_defs_keys

    asset_out_map: Mapping[str, AssetOut] = {} if outs is None else outs

    def inner(fn: Callable[..., Any]) -> AssetsDefinition:
        op_name = name or fn.__name__

        if asset_out_map and specs:
            raise DagsterInvalidDefinitionError("Must specify only outs or specs but not both.")
        elif specs:
            output_tuples_by_asset_key = {}
            for asset_spec in specs:
                # output names are asset keys joined with _
                output_name = "_".join(asset_spec.key.path)
                output_tuples_by_asset_key[asset_spec.key] = (
                    output_name,
                    Out(
                        Nothing,
                        is_required=not (can_subset or asset_spec.skippable),
                        description=asset_spec.description,
                    ),
                )
            if upstream_asset_deps:
                raise DagsterInvalidDefinitionError(
                    "Can not pass deps and specs to @multi_asset, specify deps on the AssetSpecs"
                    " directly."
                )
            if internal_asset_deps:
                raise DagsterInvalidDefinitionError(
                    "Can not pass internal_asset_deps and specs to @multi_asset, specify deps on"
                    " the AssetSpecs directly."
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
            unexpected_upstreams = {
                key for key in loaded_upstreams.keys() if key not in upstream_keys
            }
            if unexpected_upstreams:
                raise DagsterInvalidDefinitionError(
                    f"Asset inputs {unexpected_upstreams} do not have dependencies on the passed"
                    " AssetSpec(s). Set the deps on the appropriate AssetSpec(s)."
                )
            remaining_upstream_keys = {key for key in upstream_keys if key not in loaded_upstreams}
            asset_ins = build_asset_ins(fn, explicit_ins, deps=remaining_upstream_keys)
        else:
            asset_ins = build_asset_ins(
                fn,
                ins or {},
                deps=(
                    {dep.asset_key for dep in upstream_asset_deps} if upstream_asset_deps else set()
                ),
            )
            output_tuples_by_asset_key = build_asset_outs(asset_out_map)
            # validate that the asset_deps make sense
            valid_asset_deps = set(asset_ins.keys()) | set(output_tuples_by_asset_key.keys())
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

        arg_resource_keys = {arg.name for arg in get_resource_args(fn)}
        check.param_invariant(
            len(bare_required_resource_keys or []) == 0 or len(arg_resource_keys) == 0,
            "Cannot specify resource requirements in both @multi_asset decorator and as"
            " arguments to the decorated function",
        )

        asset_outs_by_output_name: Mapping[str, Out] = dict(output_tuples_by_asset_key.values())

        check_specs_by_output_name = _validate_and_assign_output_names_to_check_specs(
            check_specs, list(output_tuples_by_asset_key.keys())
        )
        check_outs_by_output_name: Mapping[str, Out] = {
            output_name: Out(dagster_type=None, is_required=not can_subset)
            for output_name in check_specs_by_output_name.keys()
        }
        overlapping_output_names = (
            asset_outs_by_output_name.keys() & check_outs_by_output_name.keys()
        )
        check.invariant(
            len(overlapping_output_names) == 0,
            f"Check output names overlap with asset output names: {overlapping_output_names}",
        )
        combined_outs_by_output_name: Mapping[str, Out] = {
            **asset_outs_by_output_name,
            **check_outs_by_output_name,
        }

        with disable_dagster_warnings():
            op_required_resource_keys = required_resource_keys - arg_resource_keys

            op = _Op(
                name=op_name,
                description=description,
                ins=dict(asset_ins.values()),
                out=combined_outs_by_output_name,
                required_resource_keys=op_required_resource_keys,
                tags={
                    **({"kind": compute_kind} if compute_kind else {}),
                    **(op_tags or {}),
                },
                config_schema=_config_schema,
                retry_policy=retry_policy,
                code_version=code_version,
            )(fn)

        keys_by_input_name = {
            input_name: asset_key for asset_key, (input_name, _) in asset_ins.items()
        }
        keys_by_output_name = {
            output_name: asset_key
            for asset_key, (output_name, _) in output_tuples_by_asset_key.items()
        }
        partition_mappings = {
            keys_by_input_name[input_name]: asset_in.partition_mapping
            for input_name, asset_in in (ins or {}).items()
            if asset_in.partition_mapping is not None
        }

        if upstream_asset_deps:
            partition_mappings = _get_partition_mappings_from_deps(
                partition_mappings=partition_mappings, deps=upstream_asset_deps, asset_name=op_name
            )

        if specs:
            internal_deps = {
                spec.key: {dep.asset_key for dep in spec.deps}
                for spec in specs
                if spec.deps is not None
            }
            props_by_asset_key: Mapping[AssetKey, Union[AssetSpec, AssetOut]] = {
                spec.key: spec for spec in specs
            }
            # Add PartitionMappings specified via AssetSpec.deps to partition_mappings dictionary. Error on duplicates
            for spec in specs:
                for dep in spec.deps:
                    if dep.partition_mapping is None:
                        continue
                    if partition_mappings.get(dep.asset_key, None) is None:
                        partition_mappings[dep.asset_key] = dep.partition_mapping
                        continue
                    if partition_mappings[dep.asset_key] == dep.partition_mapping:
                        continue
                    else:
                        raise DagsterInvalidDefinitionError(
                            f"Two different PartitionMappings for {dep.asset_key} provided for"
                            f" multi_asset {op_name}. Please use the same PartitionMapping for"
                            f" {dep.asset_key}."
                        )

        else:
            internal_deps = {keys_by_output_name[name]: asset_deps[name] for name in asset_deps}
            props_by_asset_key = {
                keys_by_output_name[output_name]: asset_out
                for output_name, asset_out in asset_out_map.items()
            }

        # handle properties defined ons AssetSpecs or AssetOuts
        group_names_by_key = {
            asset_key: props.group_name
            for asset_key, props in props_by_asset_key.items()
            if props.group_name is not None
        }
        if group_name:
            check.invariant(
                not group_names_by_key,
                "Cannot set group_name parameter on multi_asset if one or more of the"
                " AssetSpecs/AssetOuts supplied to this multi_asset have a group_name defined.",
            )
            group_names_by_key = {asset_key: group_name for asset_key in props_by_asset_key}

        freshness_policies_by_key = {
            asset_key: props.freshness_policy
            for asset_key, props in props_by_asset_key.items()
            if props.freshness_policy is not None
        }
        auto_materialize_policies_by_key = {
            asset_key: props.auto_materialize_policy
            for asset_key, props in props_by_asset_key.items()
            if props.auto_materialize_policy is not None
        }
        metadata_by_key = {
            asset_key: props.metadata
            for asset_key, props in props_by_asset_key.items()
            if props.metadata is not None
        }

        return AssetsDefinition.dagster_internal_init(
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name=keys_by_output_name,
            node_def=op,
            asset_deps=internal_deps,
            partitions_def=partitions_def,
            partition_mappings=partition_mappings if partition_mappings else None,
            can_subset=can_subset,
            resource_defs=resource_defs,
            group_names_by_key=group_names_by_key,
            freshness_policies_by_key=freshness_policies_by_key,
            auto_materialize_policies_by_key=auto_materialize_policies_by_key,
            backfill_policy=backfill_policy,
            selected_asset_keys=None,  # no subselection in decorator
            # descriptions by key is more accurately understood as _overriding_ the descriptions
            # by key that are in the OutputDefinitions associated with the asset key.
            # This is a dangerous construction liable for bugs. Instead there should be a
            # canonical source of asset descriptions in AssetsDefinintion and if we need
            # to create a memoized cached dictionary of asset keys for perf or something we do
            # that in the `__init__` or on demand.
            #
            # This is actually an override. We do not override descriptions
            # in OutputDefinitions in @multi_asset
            descriptions_by_key=None,
            metadata_by_key=metadata_by_key,
            check_specs_by_output_name=check_specs_by_output_name,
            selected_asset_check_keys=None,  # no subselection in decorator
        )

    return inner


def get_function_params_without_context_or_config_or_resources(fn: Callable) -> List[Parameter]:
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


def stringify_asset_key_to_input_name(asset_key: AssetKey) -> str:
    return "_".join(asset_key.path).replace("-", "_")


def build_asset_ins(
    fn: Callable,
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


@overload
def graph_asset(
    compose_fn: Callable,
) -> AssetsDefinition: ...


@overload
def graph_asset(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    config: Optional[Union[ConfigMapping, Mapping[str, Any]]] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    group_name: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    metadata: Optional[MetadataUserInput] = ...,
    freshness_policy: Optional[FreshnessPolicy] = ...,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = ...,
    backfill_policy: Optional[BackfillPolicy] = ...,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = ...,
    check_specs: Optional[Sequence[AssetCheckSpec]] = None,
    key: Optional[CoercibleToAssetKey] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]: ...


def graph_asset(
    compose_fn: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    config: Optional[Union[ConfigMapping, Mapping[str, Any]]] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    group_name: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    metadata: Optional[MetadataUserInput] = None,
    freshness_policy: Optional[FreshnessPolicy] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    check_specs: Optional[Sequence[AssetCheckSpec]] = None,
    key: Optional[CoercibleToAssetKey] = None,
) -> Union[AssetsDefinition, Callable[[Callable[..., Any]], AssetsDefinition]]:
    """Creates a software-defined asset that's computed using a graph of ops.

    This decorator is meant to decorate a function that composes a set of ops or graphs to define
    the dependencies between them.

    Args:
        name (Optional[str]): The name of the asset.  If not provided, defaults to the name of the
            decorated function. The asset's name must be a valid name in Dagster (ie only contains
            letters, numbers, and underscores) and may not contain Python reserved keywords.
        description (Optional[str]):
            A human-readable description of the asset.
        ins (Optional[Mapping[str, AssetIn]]): A dictionary that maps input names to information
            about the input.
        config (Optional[Union[ConfigMapping], Mapping[str, Any]):
            Describes how the graph underlying the asset is configured at runtime.

            If a :py:class:`ConfigMapping` object is provided, then the graph takes on the config
            schema of this object. The mapping will be applied at runtime to generate the config for
            the graph's constituent nodes.

            If a dictionary is provided, then it will be used as the default run config for the
            graph. This means it must conform to the config schema of the underlying nodes. Note
            that the values provided will be viewable and editable in the Dagster UI, so be careful
            with secrets. its constituent nodes.

            If no value is provided, then the config schema for the graph is the default (derived
            from the underlying nodes).
        key_prefix (Optional[Union[str, Sequence[str]]]): If provided, the asset's key is the
            concatenation of the key_prefix and the asset's name, which defaults to the name of
            the decorated function. Each item in key_prefix must be a valid name in Dagster (ie only
            contains letters, numbers, and underscores) and may not contain Python reserved keywords.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. If
            not provided, the name "default" is used.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the asset.
        metadata (Optional[MetadataUserInput]): Dictionary of metadata to be associated with
            the asset.
        freshness_policy (Optional[FreshnessPolicy]): A constraint telling Dagster how often this asset is
            intended to be updated with respect to its root data.
        auto_materialize_policy (Optional[AutoMaterializePolicy]): The AutoMaterializePolicy to use
            for this asset.
        backfill_policy (Optional[BackfillPolicy]): The BackfillPolicy to use for this asset.
        key (Optional[CoeercibleToAssetKey]): The key for this asset. If provided, cannot specify key_prefix or name.

    Examples:
        .. code-block:: python

            @op
            def fetch_files_from_slack(context) -> pd.DataFrame:
                ...

            @op
            def store_files_in_table(files) -> None:
                files.to_sql(name="slack_files", con=create_db_connection())

            @graph_asset
            def slack_files_table():
                return store_files(fetch_files_from_slack())
    """
    if compose_fn is None:
        return lambda fn: graph_asset(  # type: ignore  # (decorator pattern)
            fn,
            name=name,
            description=description,
            ins=ins,
            config=config,
            key_prefix=key_prefix,
            group_name=group_name,
            partitions_def=partitions_def,
            metadata=metadata,
            freshness_policy=freshness_policy,
            auto_materialize_policy=auto_materialize_policy,
            backfill_policy=backfill_policy,
            resource_defs=resource_defs,
            check_specs=check_specs,
            key=key,
        )
    else:
        return graph_asset_no_defaults(
            compose_fn=compose_fn,
            name=name,
            description=description,
            ins=ins,
            config=config,
            key_prefix=key_prefix,
            group_name=group_name,
            partitions_def=partitions_def,
            metadata=metadata,
            freshness_policy=freshness_policy,
            auto_materialize_policy=auto_materialize_policy,
            backfill_policy=backfill_policy,
            resource_defs=resource_defs,
            check_specs=check_specs,
            key=key,
        )


def graph_asset_no_defaults(
    *,
    compose_fn: Callable,
    name: Optional[str],
    description: Optional[str],
    ins: Optional[Mapping[str, AssetIn]],
    config: Optional[Union[ConfigMapping, Mapping[str, Any]]],
    key_prefix: Optional[CoercibleToAssetKeyPrefix],
    group_name: Optional[str],
    partitions_def: Optional[PartitionsDefinition],
    metadata: Optional[MetadataUserInput],
    freshness_policy: Optional[FreshnessPolicy],
    auto_materialize_policy: Optional[AutoMaterializePolicy],
    backfill_policy: Optional[BackfillPolicy],
    resource_defs: Optional[Mapping[str, ResourceDefinition]],
    check_specs: Optional[Sequence[AssetCheckSpec]],
    key: Optional[CoercibleToAssetKey],
) -> AssetsDefinition:
    ins = ins or {}
    asset_ins = build_asset_ins(compose_fn, ins or {}, set())
    out_asset_key, _asset_name = _resolve_key_and_name(
        key=key,
        key_prefix=key_prefix,
        name=name,
        decorator="@graph_asset",
        fn=compose_fn,
    )

    keys_by_input_name = {input_name: asset_key for asset_key, (input_name, _) in asset_ins.items()}
    partition_mappings = {
        input_name: asset_in.partition_mapping
        for input_name, asset_in in ins.items()
        if asset_in.partition_mapping
    }

    check_specs_by_output_name = _validate_and_assign_output_names_to_check_specs(
        check_specs, [out_asset_key]
    )
    check_outs_by_output_name: Mapping[str, GraphOut] = {
        output_name: GraphOut() for output_name in check_specs_by_output_name.keys()
    }

    combined_outs_by_output_name: Mapping = {
        "result": GraphOut(),
        **check_outs_by_output_name,
    }

    op_graph = graph(
        name=out_asset_key.to_python_identifier(),
        description=description,
        config=config,
        ins={input_name: GraphIn() for _, (input_name, _) in asset_ins.items()},
        out=combined_outs_by_output_name,
    )(compose_fn)
    return AssetsDefinition.from_graph(
        op_graph,
        keys_by_input_name=keys_by_input_name,
        keys_by_output_name={"result": out_asset_key},
        partitions_def=partitions_def,
        partition_mappings=partition_mappings if partition_mappings else None,
        group_name=group_name,
        metadata_by_output_name={"result": metadata} if metadata else None,
        freshness_policies_by_output_name=(
            {"result": freshness_policy} if freshness_policy else None
        ),
        auto_materialize_policies_by_output_name=(
            {"result": auto_materialize_policy} if auto_materialize_policy else None
        ),
        backfill_policy=backfill_policy,
        descriptions_by_output_name={"result": description} if description else None,
        resource_defs=resource_defs,
        check_specs=check_specs,
    )


def graph_multi_asset(
    *,
    outs: Mapping[str, AssetOut],
    name: Optional[str] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    group_name: Optional[str] = None,
    can_subset: bool = False,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    check_specs: Optional[Sequence[AssetCheckSpec]] = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    """Create a combined definition of multiple assets that are computed using the same graph of
    ops, and the same upstream assets.

    Each argument to the decorated function references an upstream asset that this asset depends on.
    The name of the argument designates the name of the upstream asset.

    Args:
        name (Optional[str]): The name of the graph.
        outs: (Optional[Dict[str, AssetOut]]): The AssetOuts representing the produced assets.
        ins (Optional[Mapping[str, AssetIn]]): A dictionary that maps input names to information
            about the input.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the assets.
        backfill_policy (Optional[BackfillPolicy]): The backfill policy for the asset.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. This
            group name will be applied to all assets produced by this multi_asset.
        can_subset (bool): Whether this asset's computation can emit a subset of the asset
            keys based on the context.selected_assets argument. Defaults to False.
    """

    def inner(fn: Callable) -> AssetsDefinition:
        partition_mappings = {
            input_name: asset_in.partition_mapping
            for input_name, asset_in in (ins or {}).items()
            if asset_in.partition_mapping
        }

        asset_ins = build_asset_ins(fn, ins or {}, set())
        keys_by_input_name = {
            input_name: asset_key for asset_key, (input_name, _) in asset_ins.items()
        }
        asset_outs = build_asset_outs(outs)

        check_specs_by_output_name = _validate_and_assign_output_names_to_check_specs(
            check_specs, list(asset_outs.keys())
        )
        check_outs_by_output_name: Mapping[str, GraphOut] = {
            output_name: GraphOut() for output_name in check_specs_by_output_name.keys()
        }

        combined_outs_by_output_name = {
            **{output_name: GraphOut() for output_name, _ in asset_outs.values()},
            **check_outs_by_output_name,
        }

        op_graph = graph(
            name=name or fn.__name__,
            out=combined_outs_by_output_name,
        )(fn)

        # source metadata from the AssetOuts (if any)
        metadata_by_output_name = {
            output_name: out.metadata
            for output_name, out in outs.items()
            if isinstance(out, AssetOut) and out.metadata is not None
        }

        # source freshness policies from the AssetOuts (if any)
        freshness_policies_by_output_name = {
            output_name: out.freshness_policy
            for output_name, out in outs.items()
            if isinstance(out, AssetOut) and out.freshness_policy is not None
        }

        # source auto materialize policies from the AssetOuts (if any)
        auto_materialize_policies_by_output_name = {
            output_name: out.auto_materialize_policy
            for output_name, out in outs.items()
            if isinstance(out, AssetOut) and out.auto_materialize_policy is not None
        }

        # source descriptions from the AssetOuts (if any)
        descriptions_by_output_name = {
            output_name: out.description
            for output_name, out in outs.items()
            if isinstance(out, AssetOut) and out.description is not None
        }

        return AssetsDefinition.from_graph(
            op_graph,
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name={
                output_name: asset_key for asset_key, (output_name, _) in asset_outs.items()
            },
            partitions_def=partitions_def,
            partition_mappings=partition_mappings if partition_mappings else None,
            group_name=group_name,
            can_subset=can_subset,
            metadata_by_output_name=metadata_by_output_name,
            freshness_policies_by_output_name=freshness_policies_by_output_name,
            auto_materialize_policies_by_output_name=auto_materialize_policies_by_output_name,
            backfill_policy=backfill_policy,
            descriptions_by_output_name=descriptions_by_output_name,
            resource_defs=resource_defs,
            check_specs=check_specs,
        )

    return inner


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


def _deps_and_non_argument_deps_to_asset_deps(
    deps: Optional[Iterable[CoercibleToAssetDep]],
    non_argument_deps: Optional[Union[Set[AssetKey], Set[str]]],
) -> Optional[Iterable[AssetDep]]:
    """Helper function for managing deps and non_argument_deps while non_argument_deps is still an accepted parameter.
    Ensures only one of deps and non_argument_deps is provided, then converts the deps to AssetDeps.
    """
    if non_argument_deps is not None and deps is not None:
        raise DagsterInvalidDefinitionError(
            "Cannot specify both deps and non_argument_deps to @asset. Use only deps instead."
        )

    if deps is not None:
        return _make_asset_deps(deps)

    if non_argument_deps is not None:
        check.set_param(non_argument_deps, "non_argument_deps", of_type=(AssetKey, str))
        return _make_asset_deps(non_argument_deps)


def _make_asset_deps(deps: Optional[Iterable[CoercibleToAssetDep]]) -> Optional[Iterable[AssetDep]]:
    if deps is None:
        return None

    # expand any multi_assets into a list of keys
    all_deps = []
    for dep in deps:
        if isinstance(dep, AssetsDefinition) and len(dep.keys) > 1:
            all_deps.extend(dep.keys)
        else:
            all_deps.append(dep)

    with disable_dagster_warnings():
        dep_dict = {}
        for dep in all_deps:
            asset_dep = AssetDep.from_coercible(dep)

            # we cannot do deduplication via a set because MultiPartitionMappings have an internal
            # dictionary that cannot be hashed. Instead deduplicate by making a dictionary and checking
            # for existing keys. If an asset is specified as a dependency more than once, only error if the
            # dependency is different (ie has a different PartitionMapping)
            if (
                asset_dep.asset_key in dep_dict.keys()
                and asset_dep != dep_dict[asset_dep.asset_key]
            ):
                raise DagsterInvariantViolationError(
                    f"Cannot set a dependency on asset {asset_dep.asset_key} more than once per"
                    " asset."
                )
            dep_dict[asset_dep.asset_key] = asset_dep

    return list(dep_dict.values())


def _validate_and_assign_output_names_to_check_specs(
    check_specs: Optional[Sequence[AssetCheckSpec]], valid_asset_keys: Sequence[AssetKey]
) -> Mapping[str, AssetCheckSpec]:
    check_specs_by_output_name = {spec.get_python_identifier(): spec for spec in check_specs or []}
    if check_specs and len(check_specs_by_output_name) != len(check_specs):
        duplicates = {
            item: count
            for item, count in Counter(
                [(spec.asset_key, spec.name) for spec in check_specs]
            ).items()
            if count > 1
        }

        raise DagsterInvalidDefinitionError(f"Duplicate check specs: {duplicates}")

    for spec in check_specs_by_output_name.values():
        if spec.asset_key not in valid_asset_keys:
            raise DagsterInvalidDefinitionError(
                f"Invalid asset key {spec.asset_key} in check spec {spec.name}. Must be one of"
                f" {valid_asset_keys}"
            )

    return check_specs_by_output_name


def _get_partition_mappings_from_deps(
    partition_mappings: Dict[AssetKey, PartitionMapping], deps: Iterable[AssetDep], asset_name: str
):
    # Add PartitionMappings specified via AssetDeps to partition_mappings dictionary. Error on duplicates
    for dep in deps:
        if dep.partition_mapping is None:
            continue
        if partition_mappings.get(dep.asset_key, None) is None:
            partition_mappings[dep.asset_key] = dep.partition_mapping
            continue
        if partition_mappings[dep.asset_key] == dep.partition_mapping:
            continue
        else:
            raise DagsterInvalidDefinitionError(
                f"Two different PartitionMappings for {dep.asset_key} provided for"
                f" asset {asset_name}. Please use the same PartitionMapping for"
                f" {dep.asset_key}."
            )

    return partition_mappings
