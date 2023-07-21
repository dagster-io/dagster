import warnings
from inspect import Parameter
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
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
from dagster._builtins import Nothing
from dagster._config import UserConfigSchema
from dagster._core.decorator_utils import get_function_params, get_valid_name_permutations
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.metadata import ArbitraryMetadataMapping, MetadataUserInput
from dagster._core.definitions.resource_annotation import (
    get_resource_args,
)
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.types.dagster_type import DagsterType
from dagster._utils.backcompat import (
    ExperimentalWarning,
    deprecation_warning,
    experimental_arg_warning,
)

from ..asset_in import AssetIn
from ..asset_out import AssetOut
from ..assets import AssetsDefinition
from ..backfill_policy import BackfillPolicy, BackfillPolicyType
from ..decorators.graph_decorator import graph
from ..decorators.op_decorator import _Op
from ..events import AssetKey, CoercibleToAssetKey, CoercibleToAssetKeyPrefix
from ..input import In
from ..output import GraphOut, Out
from ..partition import PartitionsDefinition
from ..policy import RetryPolicy
from ..resource_definition import ResourceDefinition
from ..utils import DEFAULT_IO_MANAGER_KEY, NoValueSentinel


@overload
def asset(
    compute_fn: Callable,
) -> AssetsDefinition:
    ...


@overload
def asset(
    *,
    name: Optional[str] = ...,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    ins: Optional[Mapping[str, AssetIn]] = ...,
    deps: Optional[Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]]] = ...,
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
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    ...


def asset(
    compute_fn: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    deps: Optional[Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]]] = None,
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
        deps (Optional[Sequence[Union[AssetsDefinition, SourceAsset, AssetKey, str]]]):
            The assets that are upstream dependencies, but do not correspond to a parameter of the
            decorated function.
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
        non_argument_deps (Optional[Union[Set[AssetKey], Set[str]]]): Deprecated, use deps instead.
            Set of asset keys that are upstream dependencies, but do not pass an input to the asset.

    Examples:
        .. code-block:: python

            @asset
            def my_asset(my_upstream_asset: int) -> int:
                return my_upstream_asset + 1
    """

    def create_asset():
        upstream_asset_deps = _type_check_deps_and_non_argument_deps(
            deps=deps, non_argument_deps=non_argument_deps
        )

        return _Asset(
            name=cast(Optional[str], name),  # (mypy bug that it can't infer name is Optional[str])
            key_prefix=key_prefix,
            ins=ins,
            deps=_make_asset_keys(upstream_asset_deps),
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
            key=key,
        )

    if compute_fn is not None:
        return create_asset()(compute_fn)

    def inner(fn: Callable[..., Any]) -> AssetsDefinition:
        check.invariant(
            not (io_manager_key and io_manager_def),
            (
                "Both io_manager_key and io_manager_def were provided to `@asset` decorator. Please"
                " provide one or the other. "
            ),
        )
        if resource_defs is not None:
            experimental_arg_warning("resource_defs", "asset")

        if io_manager_def is not None:
            experimental_arg_warning("io_manager_def", "asset")

        if auto_materialize_policy is not None:
            experimental_arg_warning("auto_materialize_policy", "asset")

        if backfill_policy is not None:
            experimental_arg_warning("backfill_policy", "asset")

        return create_asset()(fn)

    return inner


class _Asset:
    def __init__(
        self,
        name: Optional[str] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        ins: Optional[Mapping[str, AssetIn]] = None,
        deps: Optional[Set[AssetKey]] = None,
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
    ):
        self.name = name

        if isinstance(key_prefix, str):
            key_prefix = [key_prefix]
        self.key_prefix = key_prefix
        self.ins = ins or {}
        self.deps = deps
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

        if (name or key_prefix) and key:
            raise DagsterInvalidDefinitionError(
                "Cannot specify a name or key prefix for an asset when the key argument is"
                " provided."
            )

        self.key = AssetKey.from_coercible(key) if key is not None else None

    def __call__(self, fn: Callable) -> AssetsDefinition:
        from dagster._config.pythonic_config import (
            validate_resource_annotated_function,
        )
        from dagster._core.execution.build_resources import wrap_resources_for_execution

        validate_resource_annotated_function(fn)
        asset_name = self.name or fn.__name__

        asset_ins = build_asset_ins(fn, self.ins or {}, self.deps)

        out_asset_key = (
            AssetKey(list(filter(None, [*(self.key_prefix or []), asset_name])))
            if not self.key
            else self.key
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)

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
                (
                    "Cannot specify resource requirements in both @asset decorator and as arguments"
                    " to the decorated function"
                ),
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

            op_required_resource_keys = decorator_resource_keys - arg_resource_keys

            op = _Op(
                name=out_asset_key.to_python_identifier(),
                description=self.description,
                ins=dict(asset_ins.values()),
                out=out,
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
                    self.backfill_policy.policy_type is BackfillPolicyType.SINGLE_RUN
                    if self.backfill_policy
                    else True,
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

        return AssetsDefinition.dagster_internal_init(
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name={"result": out_asset_key},
            node_def=op,
            partitions_def=self.partitions_def,
            partition_mappings=partition_mappings if partition_mappings else None,
            resource_defs=wrapped_resource_defs,
            group_names_by_key={out_asset_key: self.group_name} if self.group_name else None,
            freshness_policies_by_key={out_asset_key: self.freshness_policy}
            if self.freshness_policy
            else None,
            auto_materialize_policies_by_key={out_asset_key: self.auto_materialize_policy}
            if self.auto_materialize_policy
            else None,
            backfill_policy=self.backfill_policy,
            asset_deps=None,  # no asset deps in single-asset decorator
            selected_asset_keys=None,  # no subselection in decorator
            can_subset=False,
            metadata_by_key={out_asset_key: self.metadata} if self.metadata else None,
            descriptions_by_key=None,  # not supported for now
        )


def multi_asset(
    *,
    outs: Mapping[str, AssetOut],
    name: Optional[str] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    deps: Optional[Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]]] = None,
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
        outs: (Optional[Dict[str, AssetOut]]): The AssetOuts representing the produced assets.
        ins (Optional[Mapping[str, AssetIn]]): A dictionary that maps input names to information
            about the input.
        deps (Optional[Sequence[Union[AssetsDefinition, SourceAsset, AssetKey, str]]]):
            The assets that are upstream dependencies, but do not correspond to a parameter of the
            decorated function.
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
                deps={"asset0"},
            )
            def my_function():
                asset0_value = load(path="asset0")
                asset1_result, asset2_result = do_some_transformation(asset0_value)
                write(asset1_result, path="asset1")
                write(asset2_result, path="asset2")
    """
    from dagster._core.execution.build_resources import wrap_resources_for_execution

    upstream_asset_deps = _type_check_deps_and_non_argument_deps(
        deps=deps, non_argument_deps=non_argument_deps
    )

    if resource_defs is not None:
        experimental_arg_warning("resource_defs", "multi_asset")

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
        config_schema,
        "config_schema",
        additional_message="Only dicts are supported for asset config_schema.",
    )

    bare_required_resource_keys = set(required_resource_keys)
    resource_defs_keys = set(resource_defs.keys())
    required_resource_keys = bare_required_resource_keys | resource_defs_keys

    def inner(fn: Callable[..., Any]) -> AssetsDefinition:
        op_name = name or fn.__name__
        asset_ins = build_asset_ins(fn, ins or {}, deps=_make_asset_keys(upstream_asset_deps))
        asset_outs = build_asset_outs(outs)

        arg_resource_keys = {arg.name for arg in get_resource_args(fn)}
        check.param_invariant(
            len(bare_required_resource_keys or []) == 0 or len(arg_resource_keys) == 0,
            (
                "Cannot specify resource requirements in both @multi_asset decorator and as"
                " arguments to the decorated function"
            ),
        )

        # validate that the asset_deps make sense
        valid_asset_deps = set(asset_ins.keys()) | set(asset_outs.keys())
        for out_name, asset_keys in asset_deps.items():
            check.invariant(
                out_name in outs,
                (
                    f"Invalid out key '{out_name}' supplied to `internal_asset_deps` argument for"
                    f" multi-asset {op_name}. Must be one of the outs for this multi-asset"
                    f" {list(outs.keys())[:20]}."
                ),
            )
            invalid_asset_deps = asset_keys.difference(valid_asset_deps)
            check.invariant(
                not invalid_asset_deps,
                (
                    f"Invalid asset dependencies: {invalid_asset_deps} specified in"
                    f" `internal_asset_deps` argument for multi-asset '{op_name}' on key"
                    f" '{out_name}'. Each specified asset key must be associated with an input to"
                    " the asset or produced by this asset. Valid keys:"
                    f" {list(valid_asset_deps)[:20]}"
                ),
            )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)

            op_required_resource_keys = required_resource_keys - arg_resource_keys

            op = _Op(
                name=op_name,
                description=description,
                ins=dict(asset_ins.values()),
                out=dict(asset_outs.values()),
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
            output_name: asset_key for asset_key, (output_name, _) in asset_outs.items()
        }

        # source group names from the AssetOuts (if any)
        group_names_by_key = {
            keys_by_output_name[output_name]: out.group_name
            for output_name, out in outs.items()
            if out.group_name is not None
        }
        if group_name:
            check.invariant(
                not group_names_by_key,
                (
                    "Cannot set group_name parameter on multi_asset if one or more of the AssetOuts"
                    " supplied to this multi_asset have a group_name defined."
                ),
            )
            group_names_by_key = {
                asset_key: group_name for asset_key in keys_by_output_name.values()
            }

        # source freshness policies from the AssetOuts (if any)
        freshness_policies_by_key = {
            keys_by_output_name[output_name]: out.freshness_policy
            for output_name, out in outs.items()
            if out.freshness_policy is not None
        }
        auto_materialize_policies_by_key = {
            keys_by_output_name[output_name]: out.auto_materialize_policy
            for output_name, out in outs.items()
            if out.auto_materialize_policy is not None
        }

        partition_mappings = {
            keys_by_input_name[input_name]: asset_in.partition_mapping
            for input_name, asset_in in (ins or {}).items()
            if asset_in.partition_mapping is not None
        }
        metadata_by_key = {
            keys_by_output_name[output_name]: out.metadata
            for output_name, out in outs.items()
            if out.metadata is not None
        }

        return AssetsDefinition.dagster_internal_init(
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name=keys_by_output_name,
            node_def=op,
            asset_deps={keys_by_output_name[name]: asset_deps[name] for name in asset_deps},
            partitions_def=partitions_def,
            partition_mappings=partition_mappings if partition_mappings else None,
            can_subset=can_subset,
            resource_defs=resource_defs,
            group_names_by_key=group_names_by_key,
            freshness_policies_by_key=freshness_policies_by_key,
            auto_materialize_policies_by_key=auto_materialize_policies_by_key,
            backfill_policy=backfill_policy,
            selected_asset_keys=None,  # no subselection in decorator
            descriptions_by_key=None,  # not supported for now
            metadata_by_key=metadata_by_key,
        )

    return inner


def build_asset_ins(
    fn: Callable,
    asset_ins: Mapping[str, AssetIn],
    deps: Optional[AbstractSet[AssetKey]],
) -> Mapping[AssetKey, Tuple[str, In]]:
    """Creates a mapping from AssetKey to (name of input, In object)."""
    deps = check.opt_set_param(deps, "deps", AssetKey)

    params = get_function_params(fn)
    is_context_provided = len(params) > 0 and params[0].name in get_valid_name_permutations(
        "context"
    )
    input_params = params[1:] if is_context_provided else params

    # Filter config, resource args
    resource_arg_names = {arg.name for arg in get_resource_args(fn)}

    new_input_args = []
    for input_arg in input_params:
        if input_arg.name != "config" and input_arg.name not in resource_arg_names:
            new_input_args.append(input_arg)
    input_params = new_input_args

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
        stringified_asset_key = "_".join(asset_key.path).replace("-", "_")
        # mypy doesn't realize that Nothing is a valid type here
        ins_by_asset_key[asset_key] = (stringified_asset_key, In(cast(type, Nothing)))

    return ins_by_asset_key


@overload
def graph_asset(compose_fn: Callable) -> AssetsDefinition:
    ...


@overload
def graph_asset(
    *,
    name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    description: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    group_name: Optional[str] = None,
    metadata: Optional[MetadataUserInput] = ...,
    freshness_policy: Optional[FreshnessPolicy] = ...,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = ...,
    backfill_policy: Optional[BackfillPolicy] = ...,
) -> Callable[[Callable[..., Any]], AssetsDefinition]:
    ...


def graph_asset(
    compose_fn: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    description: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    group_name: Optional[str] = None,
    metadata: Optional[MetadataUserInput] = None,
    freshness_policy: Optional[FreshnessPolicy] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
) -> Union[AssetsDefinition, Callable[[Callable[..., Any]], AssetsDefinition]]:
    """Creates a software-defined asset that's computed using a graph of ops.

    This decorator is meant to decorate a function that composes a set of ops or graphs to define
    the dependencies between them.

    Args:
        name (Optional[str]): The name of the asset.  If not provided, defaults to the name of the
            decorated function. The asset's name must be a valid name in Dagster (ie only contains
            letters, numbers, and underscores) and may not contain Python reserved keywords.
        key_prefix (Optional[Union[str, Sequence[str]]]): If provided, the asset's key is the
            concatenation of the key_prefix and the asset's name, which defaults to the name of
            the decorated function. Each item in key_prefix must be a valid name in Dagster (ie only
            contains letters, numbers, and underscores) and may not contain Python reserved keywords.
        ins (Optional[Mapping[str, AssetIn]]): A dictionary that maps input names to information
            about the input.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the asset.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. If
            not provided, the name "default" is used.
        metadata (Optional[MetadataUserInput]): Dictionary of metadata to be associated with
            the asset.
        freshness_policy (Optional[FreshnessPolicy]): A constraint telling Dagster how often this asset is
            intended to be updated with respect to its root data.
        auto_materialize_policy (Optional[AutoMaterializePolicy]): The AutoMaterializePolicy to use
            for this asset.
        backfill_policy (Optional[BackfillPolicy]): The BackfillPolicy to use for this asset.

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
    if compose_fn is not None:
        return _GraphBackedAsset()(compose_fn)

    def inner(fn: Callable[..., Any]) -> AssetsDefinition:
        return _GraphBackedAsset(
            name=cast(Optional[str], name),  # (mypy bug that it can't infer name is Optional[str])
            key_prefix=key_prefix,
            ins=ins,
            description=description,
            partitions_def=partitions_def,
            group_name=group_name,
            metadata=metadata,
            freshness_policy=freshness_policy,
            auto_materialize_policy=auto_materialize_policy,
            backfill_policy=backfill_policy,
            resource_defs=resource_defs,
        )(fn)

    return inner


class _GraphBackedAsset:
    def __init__(
        self,
        name: Optional[str] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        ins: Optional[Mapping[str, AssetIn]] = None,
        description: Optional[str] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        group_name: Optional[str] = None,
        metadata: Optional[MetadataUserInput] = None,
        freshness_policy: Optional[FreshnessPolicy] = None,
        auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    ):
        self.name = name

        if isinstance(key_prefix, str):
            key_prefix = [key_prefix]
        self.key_prefix = key_prefix
        self.ins = ins or {}
        self.description = description
        self.partitions_def = partitions_def
        self.group_name = group_name
        self.metadata = metadata
        self.freshness_policy = freshness_policy
        self.auto_materialize_policy = auto_materialize_policy
        self.backfill_policy = backfill_policy
        self.resource_defs = resource_defs

    def __call__(self, fn: Callable) -> AssetsDefinition:
        asset_name = self.name or fn.__name__
        asset_ins = build_asset_ins(fn, self.ins or {}, set())
        out_asset_key = AssetKey(list(filter(None, [*(self.key_prefix or []), asset_name])))

        keys_by_input_name = {
            input_name: asset_key for asset_key, (input_name, _) in asset_ins.items()
        }
        partition_mappings = {
            input_name: asset_in.partition_mapping
            for input_name, asset_in in self.ins.items()
            if asset_in.partition_mapping
        }

        op_graph = graph(name=out_asset_key.to_python_identifier(), description=self.description)(
            fn
        )
        return AssetsDefinition.from_graph(
            op_graph,
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name={"result": out_asset_key},
            partitions_def=self.partitions_def,
            partition_mappings=partition_mappings if partition_mappings else None,
            group_name=self.group_name,
            metadata_by_output_name={"result": self.metadata} if self.metadata else None,
            freshness_policies_by_output_name={"result": self.freshness_policy}
            if self.freshness_policy
            else None,
            auto_materialize_policies_by_output_name={"result": self.auto_materialize_policy}
            if self.auto_materialize_policy
            else None,
            backfill_policy=self.backfill_policy,
            descriptions_by_output_name={"result": self.description} if self.description else None,
            resource_defs=self.resource_defs,
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
        op_graph = graph(
            name=name or fn.__name__,
            out={out_name: GraphOut() for out_name, _ in asset_outs.values()},
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


def _type_check_deps_and_non_argument_deps(
    deps: Optional[Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]]],
    non_argument_deps: Optional[Union[Set[AssetKey], Set[str]]],
):
    """Helper function for managing deps and non_argument_deps while non_argument_deps is still an accepted parameter.
    Ensures:
    1. only one of deps and non_argument_deps is provided.
    2. multi assets AssetsDefinition is not passed to deps.
    3. deprecation warning is fired for non_argument_deps.
    """
    if non_argument_deps is not None and deps is not None:
        raise DagsterInvalidDefinitionError(
            "Cannot specify both deps and non_argument_deps to @asset. Use only deps instead."
        )

    upstream_asset_deps: Optional[
        Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]]
    ] = None
    if deps is not None:
        for dep in deps:
            if isinstance(dep, AssetsDefinition):
                # Only AssetsDefinition with a single asset can be passed
                if len(dep.keys) > 1:
                    raise DagsterInvalidDefinitionError(
                        "Cannot pass a multi_asset AssetsDefinition as an argument to deps."
                        " Instead, specify dependencies on the assets created by the multi_asset"
                        f" via AssetKeys or strings. For the multi_asset {dep.node_def.name}, the"
                        f" available keys are: {dep.keys}."
                    )
            elif isinstance(dep, SourceAsset):
                # no additional type checking needed for SourceAssets
                continue
            else:
                # confirm that dep is coercible to AssetKey
                try:
                    AssetKey.from_coercible(dep)
                except check.CheckError:
                    raise DagsterInvalidDefinitionError(
                        f"Cannot pass an instance of type {type(dep)} to deps parameter of @asset."
                        " Instead, pass AssetsDefinitions or AssetKeys."
                    )

        upstream_asset_deps = deps

    if non_argument_deps is not None:
        deprecation_warning("non_argument_deps", "2.0.0", "use parameter deps instead")
        # this set -> list conversion is a side effect of the type changing from
        # Union[Set[AssetKey], Set[str]] to Sequence[Union[AssetsDefinition, CoercibleToAssetKey, SourceAsset]]
        check.set_param(non_argument_deps, "non_argument_deps", of_type=(AssetKey, str))
        upstream_asset_deps = list(non_argument_deps)

    return upstream_asset_deps


def _make_asset_keys(
    deps: Optional[Sequence[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]]]
) -> Optional[Set[AssetKey]]:
    """Convert all items to AssetKey in a set. By putting all of the AssetKeys in a set, it will also deduplicate them.
    """
    if deps is None:
        return deps

    deps_asset_keys: Set[AssetKey] = set()
    for dep in deps:
        if isinstance(dep, AssetsDefinition):
            # this will error if the AssetsDefinition is a multi_asset, but we should have caught that
            # earlier in execution
            deps_asset_keys.add(dep.key)
        elif isinstance(dep, SourceAsset):
            deps_asset_keys.add(dep.key)
        else:
            deps_asset_keys.add(AssetKey.from_coercible(dep))

    return deps_asset_keys
