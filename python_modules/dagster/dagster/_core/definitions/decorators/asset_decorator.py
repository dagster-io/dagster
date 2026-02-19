from collections.abc import Iterable, Mapping, Sequence
from typing import AbstractSet, Any, Callable, NamedTuple, overload  # noqa: UP035

import dagster._check as check
from dagster._annotations import (
    beta_param,
    hidden_param,
    only_allow_hidden_params_in_kwargs,
    public,
)
from dagster._config.config_schema import UserConfigSchema
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.assets.definition.asset_dep import (
    AssetDep,
    CoercibleToAssetDep,
    coerce_to_deps_and_check_duplicates,
)
from dagster._core.definitions.assets.definition.asset_spec import (
    AssetExecutionType,
    AssetSpec,
    validate_kind_tags,
)
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.assets.job.asset_in import AssetIn
from dagster._core.definitions.assets.job.asset_out import AssetOut
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy, BackfillPolicyType
from dagster._core.definitions.config import ConfigMapping
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.decorators.decorator_assets_definition_builder import (
    DecoratorAssetsDefinitionBuilder,
    DecoratorAssetsDefinitionBuilderArgs,
    build_and_validate_named_ins,
    build_named_outs,
    create_check_specs_by_output_name,
    validate_and_assign_output_names_to_check_specs,
)
from dagster._core.definitions.decorators.graph_decorator import graph
from dagster._core.definitions.events import (
    AssetKey,
    CoercibleToAssetKey,
    CoercibleToAssetKeyPrefix,
)
from dagster._core.definitions.freshness import FreshnessPolicy
from dagster._core.definitions.freshness_policy import LegacyFreshnessPolicy
from dagster._core.definitions.hook_definition import HookDefinition
from dagster._core.definitions.input import GraphIn
from dagster._core.definitions.metadata import ArbitraryMetadataMapping, RawMetadataMapping
from dagster._core.definitions.output import GraphOut
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.utils import (
    DEFAULT_IO_MANAGER_KEY,
    DEFAULT_OUTPUT,
    NoValueSentinel,
    resolve_automation_condition,
)
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.storage.tags import KIND_PREFIX
from dagster._core.types.dagster_type import DagsterType
from dagster._utils.tags import normalize_tags
from dagster._utils.warnings import disable_dagster_warnings


@overload
def asset(
    *,
    name: str | None = ...,
    key_prefix: CoercibleToAssetKeyPrefix | None = None,
    ins: Mapping[str, AssetIn] | None = ...,
    deps: Iterable[CoercibleToAssetDep] | None = ...,
    metadata: Mapping[str, Any] | None = ...,
    tags: Mapping[str, str] | None = ...,
    description: str | None = ...,
    config_schema: UserConfigSchema | None = None,
    required_resource_keys: AbstractSet[str] | None = ...,
    resource_defs: Mapping[str, object] | None = ...,
    hooks: AbstractSet[HookDefinition] | None = ...,
    io_manager_def: object | None = ...,
    io_manager_key: str | None = ...,
    dagster_type: DagsterType | None = ...,
    partitions_def: PartitionsDefinition[str] | None = ...,
    op_tags: Mapping[str, Any] | None = ...,
    group_name: str | None = ...,
    output_required: bool = ...,
    automation_condition: AutomationCondition[AssetKey] | None = ...,
    backfill_policy: BackfillPolicy | None = ...,
    retry_policy: RetryPolicy | None = ...,
    code_version: str | None = ...,
    key: CoercibleToAssetKey | None = None,
    check_specs: Sequence[AssetCheckSpec] | None = ...,
    owners: Sequence[str] | None = ...,
    kinds: AbstractSet[str] | None = ...,
    pool: str | None = ...,
    **kwargs: Any,
) -> Callable[[Callable[..., Any]], AssetsDefinition]: ...


@overload
def asset(
    compute_fn: Callable[..., Any],
    **kwargs: Any,
) -> AssetsDefinition: ...


def _validate_hidden_non_argument_dep_param(
    non_argument_deps: Any,
) -> set[AssetKey] | set[str] | None:
    if non_argument_deps is None:
        return non_argument_deps

    if not isinstance(non_argument_deps, set):
        check.failed("non_arguments_deps must be a set if not None")

    assert isinstance(non_argument_deps, set)

    check.set_param(non_argument_deps, "non_argument_deps", of_type=(str, AssetKey))

    check.invariant(
        all(isinstance(dep, str) for dep in non_argument_deps)
        or all(isinstance(dep, AssetKey) for dep in non_argument_deps),
    )

    return non_argument_deps


@beta_param(param="resource_defs")
@beta_param(param="io_manager_def")
@beta_param(param="backfill_policy")
@hidden_param(
    param="non_argument_deps",
    breaking_version="2.0.0",
    additional_warn_text="use `deps` instead.",
)
@hidden_param(
    param="auto_materialize_policy",
    breaking_version="1.10.0",
    additional_warn_text="use `automation_condition` instead.",
)
@hidden_param(
    param="legacy_freshness_policy",
    breaking_version="1.12.0",
    additional_warn_text="use freshness checks instead.",
)
@public
@hidden_param(
    param="compute_kind",
    emit_runtime_warning=False,
    breaking_version="1.10.0",
)
def asset(
    compute_fn: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    key_prefix: CoercibleToAssetKeyPrefix | None = None,
    ins: Mapping[str, AssetIn] | None = None,
    deps: Iterable[CoercibleToAssetDep] | None = None,
    metadata: ArbitraryMetadataMapping | None = None,
    tags: Mapping[str, str] | None = None,
    description: str | None = None,
    config_schema: UserConfigSchema | None = None,
    required_resource_keys: AbstractSet[str] | None = None,
    resource_defs: Mapping[str, object] | None = None,
    hooks: AbstractSet[HookDefinition] | None = None,
    io_manager_def: object | None = None,
    io_manager_key: str | None = None,
    dagster_type: DagsterType | None = None,
    partitions_def: PartitionsDefinition[str] | None = None,
    op_tags: Mapping[str, Any] | None = None,
    group_name: str | None = None,
    output_required: bool = True,
    automation_condition: AutomationCondition[AssetKey] | None = None,
    freshness_policy: FreshnessPolicy | None = None,
    backfill_policy: BackfillPolicy | None = None,
    retry_policy: RetryPolicy | None = None,
    code_version: str | None = None,
    key: CoercibleToAssetKey | None = None,
    check_specs: Sequence[AssetCheckSpec] | None = None,
    owners: Sequence[str] | None = None,
    kinds: AbstractSet[str] | None = None,
    pool: str | None = None,
    **kwargs: Any,
) -> AssetsDefinition | Callable[[Callable[..., Any]], AssetsDefinition]:
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
        tags (Optional[Mapping[str, str]]): Tags for filtering and organizing. These tags are not
            attached to runs of the asset.
        required_resource_keys (Optional[Set[str]]): Set of resource handles required by the op.
        io_manager_key (Optional[str]): The resource key of the IOManager used
            for storing the output of the op as an asset, and for loading it in downstream ops
            (default: "io_manager"). Only one of io_manager_key and io_manager_def can be provided.
        io_manager_def (Optional[object]): (Beta) The IOManager used for
            storing the output of the op as an asset,  and for loading it in
            downstream ops. Only one of io_manager_def and io_manager_key can be provided.
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
            (Beta) A mapping of resource keys to resources. These resources
            will be initialized during execution, and can be accessed from the
            context within the body of the function.
        hooks (Optional[AbstractSet[HookDefinition]]): A set of hooks to attach to the asset.
            These hooks will be executed when the asset is materialized.
        output_required (bool): Whether the decorated function will always materialize an asset.
            Defaults to True. If False, the function can conditionally not `yield` a result. If
            no result is yielded, no output will be materialized to storage and downstream
            assets will not be materialized. Note that for `output_required` to work at all, you
            must use `yield` in your asset logic rather than `return`. `return` will not respect
            this setting and will always produce an asset materialization, even if `None` is
            returned.
        automation_condition (AutomationCondition): A condition describing when Dagster should materialize this asset.
        backfill_policy (BackfillPolicy): (Beta) Configure Dagster to backfill this asset according to its
            BackfillPolicy.
        retry_policy (Optional[RetryPolicy]): The retry policy for the op that computes the asset.
        code_version (Optional[str]): Version of the code that generates this asset. In
            general, versions should be set only for code that deterministically produces the same
            output when given the same inputs.
        check_specs (Optional[Sequence[AssetCheckSpec]]): Specs for asset checks that
            execute in the decorated function after materializing the asset.
        key (Optional[CoeercibleToAssetKey]): The key for this asset. If provided, cannot specify key_prefix or name.
        owners (Optional[Sequence[str]]): A list of strings representing owners of the asset. Each
            string can be a user's email address, or a team name prefixed with `team:`,
            e.g. `team:finops`.
        kinds (Optional[Set[str]]): A list of strings representing the kinds of the asset. These
            will be made visible in the Dagster UI.
        pool (Optional[str]): A string that identifies the concurrency pool that governs this asset's execution.
        non_argument_deps (Optional[Union[Set[AssetKey], Set[str]]]): Deprecated, use deps instead.
            Set of asset keys that are upstream dependencies, but do not pass an input to the asset.
            Hidden parameter not exposed in the decorator signature, but passed in kwargs.

    Examples:
        .. code-block:: python

            @asset
            def my_upstream_asset() -> int:
                return 5

            @asset
            def my_asset(my_upstream_asset: int) -> int:
                return my_upstream_asset + 1

            should_materialize = True

            @asset(output_required=False)
            def conditional_asset():
                if should_materialize:
                    yield Output(5)  # you must `yield`, not `return`, the result

            # Will also only materialize if `should_materialize` is `True`
            @asset
            def downstream_asset(conditional_asset):
                return conditional_asset + 1

    """
    compute_kind = check.opt_str_param(kwargs.get("compute_kind"), "compute_kind")
    required_resource_keys = check.opt_set_param(required_resource_keys, "required_resource_keys")
    upstream_asset_deps = _deps_and_non_argument_deps_to_asset_deps(
        deps=deps,
        non_argument_deps=_validate_hidden_non_argument_dep_param(kwargs.get("non_argument_deps")),
    )
    resource_defs = dict(check.opt_mapping_param(resource_defs, "resource_defs"))
    hooks = check.opt_set_param(hooks, "hooks", of_type=HookDefinition)

    if compute_kind and kinds:
        raise DagsterInvalidDefinitionError(
            "Cannot specify compute_kind and kinds on the @asset decorator."
        )
    validate_kind_tags(kinds)
    tags_with_kinds = {
        **(normalize_tags(tags, strict=True)),
        **{f"{KIND_PREFIX}{kind}": "" for kind in kinds or []},
    }

    only_allow_hidden_params_in_kwargs(asset, kwargs)

    args = AssetDecoratorArgs(
        name=name,
        key_prefix=key_prefix,
        ins=ins or {},
        deps=upstream_asset_deps or [],
        metadata=metadata,
        tags=tags_with_kinds,
        description=description,
        config_schema=config_schema,
        required_resource_keys=required_resource_keys,
        resource_defs=resource_defs,
        hooks=hooks,
        io_manager_key=io_manager_key,
        io_manager_def=io_manager_def,
        compute_kind=compute_kind,
        dagster_type=dagster_type,
        partitions_def=partitions_def,
        op_tags=op_tags,
        group_name=group_name,
        output_required=output_required,
        legacy_freshness_policy=kwargs.get("legacy_freshness_policy"),
        freshness_policy=freshness_policy,
        automation_condition=resolve_automation_condition(
            automation_condition, kwargs.get("auto_materialize_policy")
        ),
        backfill_policy=backfill_policy,
        retry_policy=retry_policy,
        code_version=code_version,
        check_specs=check_specs,
        key=key,
        owners=owners,
        pool=pool,
    )

    if compute_fn is not None:
        return create_assets_def_from_fn_and_decorator_args(args, compute_fn)

    def inner(fn: Callable[..., Any]) -> AssetsDefinition:
        check.invariant(
            not (io_manager_key and io_manager_def),
            "Both io_manager_key and io_manager_def were provided to `@asset` decorator. Please"
            " provide one or the other. ",
        )
        return create_assets_def_from_fn_and_decorator_args(args, fn)

    return inner


def resolve_asset_key_and_name_for_decorator(
    *,
    key: CoercibleToAssetKey | None,
    key_prefix: CoercibleToAssetKeyPrefix | None,
    name: str | None,
    decorator_name: str,
    fn: Callable[..., Any],
) -> tuple[AssetKey, str]:
    if (name or key_prefix) and key:
        raise DagsterInvalidDefinitionError(
            f"Cannot specify a name or key prefix for {decorator_name} when the key"
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


class AssetDecoratorArgs(NamedTuple):
    required_resource_keys: AbstractSet[str]
    name: str | None
    key_prefix: CoercibleToAssetKeyPrefix | None
    ins: Mapping[str, AssetIn]
    deps: Iterable[AssetDep]
    metadata: ArbitraryMetadataMapping | None
    tags: Mapping[str, str] | None
    description: str | None
    config_schema: UserConfigSchema | None
    resource_defs: dict[str, object]
    hooks: AbstractSet[HookDefinition] | None
    io_manager_key: str | None
    io_manager_def: object | None
    compute_kind: str | None
    dagster_type: DagsterType | None
    partitions_def: PartitionsDefinition | None
    op_tags: Mapping[str, Any] | None
    group_name: str | None
    output_required: bool
    legacy_freshness_policy: LegacyFreshnessPolicy | None
    freshness_policy: FreshnessPolicy | None
    automation_condition: AutomationCondition | None
    backfill_policy: BackfillPolicy | None
    retry_policy: RetryPolicy | None
    code_version: str | None
    key: CoercibleToAssetKey | None
    check_specs: Sequence[AssetCheckSpec] | None
    owners: Sequence[str] | None
    pool: str | None


class ResourceRelatedState(NamedTuple):
    io_manager_def: object | None
    io_manager_key: str | None
    resources: Mapping[str, object]
    out_asset_key: AssetKey

    @property
    def op_resource_defs(self) -> Mapping[str, ResourceDefinition]:
        from dagster._core.execution.build_resources import wrap_resources_for_execution

        return wrap_resources_for_execution(self.resources)

    @property
    def resolved_io_manager_key(self) -> str:
        if self.io_manager_def:
            return (
                self.io_manager_key
                if self.io_manager_key
                else self.out_asset_key.to_python_identifier("io_manager")
            )
        else:
            return self.io_manager_key if self.io_manager_key else DEFAULT_IO_MANAGER_KEY

    @property
    def asset_resource_defs(self) -> Mapping[str, ResourceDefinition]:
        from dagster._core.execution.build_resources import wrap_resources_for_execution

        # If these was no io_manager def directly passed in we can just wrap
        # the explicitly provided resource defs
        if not self.io_manager_def:
            return wrap_resources_for_execution(self.resources)

        io_manager_key = self.resolved_io_manager_key
        io_manager_def = self.io_manager_def
        if io_manager_key in self.resources and self.resources[io_manager_key] != io_manager_def:
            raise DagsterInvalidDefinitionError(
                f"Provided conflicting definitions for io manager key '{io_manager_key}'."
                " Please provide only one definition per key."
            )

        return wrap_resources_for_execution({**self.resources, **{io_manager_key: io_manager_def}})


def create_assets_def_from_fn_and_decorator_args(
    args: AssetDecoratorArgs, fn: Callable[..., Any]
) -> AssetsDefinition:
    from dagster._config.pythonic_config import validate_resource_annotated_function

    validate_resource_annotated_function(fn)

    out_asset_key, _asset_name = resolve_asset_key_and_name_for_decorator(
        key=args.key,
        key_prefix=args.key_prefix,
        name=args.name,
        fn=fn,
        decorator_name="@asset",
    )

    resource_related_state = ResourceRelatedState(
        io_manager_def=args.io_manager_def,
        io_manager_key=args.io_manager_key,
        resources=args.resource_defs,
        out_asset_key=out_asset_key,
    )

    with disable_dagster_warnings():
        # check backfill policy is BackfillPolicyType.SINGLE_RUN for non-partitioned asset
        if args.partitions_def is None:
            check.param_invariant(
                (
                    args.backfill_policy.policy_type is BackfillPolicyType.SINGLE_RUN
                    if args.backfill_policy
                    else True
                ),
                "backfill_policy",
                "Non partitioned asset can only have single run backfill policy",
            )

    with disable_dagster_warnings():
        builder_args = DecoratorAssetsDefinitionBuilderArgs(
            name=args.name,
            op_description=args.description,
            check_specs_by_output_name=create_check_specs_by_output_name(args.check_specs),
            group_name=args.group_name,
            partitions_def=args.partitions_def,
            retry_policy=args.retry_policy,
            code_version=args.code_version,
            op_tags=args.op_tags,
            config_schema=args.config_schema,
            compute_kind=args.compute_kind,
            required_resource_keys=args.required_resource_keys,
            op_def_resource_defs=resource_related_state.op_resource_defs,
            assets_def_resource_defs=resource_related_state.asset_resource_defs,
            backfill_policy=args.backfill_policy,
            asset_out_map={
                DEFAULT_OUTPUT: AssetOut(
                    key=out_asset_key,
                    metadata=args.metadata,
                    description=args.description,
                    is_required=args.output_required,
                    io_manager_key=resource_related_state.resolved_io_manager_key,
                    dagster_type=args.dagster_type if args.dagster_type else NoValueSentinel,
                    group_name=args.group_name,
                    code_version=args.code_version,
                    legacy_freshness_policy=args.legacy_freshness_policy,
                    freshness_policy=args.freshness_policy,
                    automation_condition=args.automation_condition,
                    backfill_policy=args.backfill_policy,
                    owners=args.owners,
                    tags=normalize_tags(args.tags or {}, strict=True),
                )
            },
            upstream_asset_deps=args.deps,
            asset_in_map=args.ins,
            # We will not be using specs to construct here
            # because they are assumption about output names. Non-spec
            # construction path assumptions apply here
            specs=[],
            # no internal asset deps
            asset_deps={},
            can_subset=False,
            decorator_name="@asset",
            execution_type=AssetExecutionType.MATERIALIZATION,
            pool=args.pool,
            hooks=args.hooks,
        )

        builder = DecoratorAssetsDefinitionBuilder.from_asset_outs_in_asset_centric_decorator(
            fn=fn,
            op_name=out_asset_key.to_python_identifier(),
            asset_in_map=builder_args.asset_in_map,
            asset_out_map=builder_args.asset_out_map,
            asset_deps=builder_args.asset_deps,
            upstream_asset_deps=builder_args.upstream_asset_deps,
            passed_args=builder_args,
        )

    return builder.create_assets_definition()


@beta_param(param="resource_defs")
@hidden_param(
    param="non_argument_deps",
    breaking_version="2.0.0",
    additional_warn_text="use `deps` instead.",
)
@hidden_param(
    param="compute_kind",
    emit_runtime_warning=False,
    breaking_version="1.10.0",
)
@hidden_param(
    param="allow_arbitrary_check_specs",
    emit_runtime_warning=False,
    # does this actually need to be set?
    breaking_version="",
)
@public
def multi_asset(
    *,
    outs: Mapping[str, AssetOut] | None = None,
    name: str | None = None,
    ins: Mapping[str, AssetIn] | None = None,
    deps: Iterable[CoercibleToAssetDep] | None = None,
    description: str | None = None,
    config_schema: UserConfigSchema | None = None,
    required_resource_keys: AbstractSet[str] | None = None,
    internal_asset_deps: Mapping[str, set[AssetKey]] | None = None,
    partitions_def: PartitionsDefinition[str] | None = None,
    hooks: AbstractSet[HookDefinition] | None = None,
    backfill_policy: BackfillPolicy | None = None,
    op_tags: Mapping[str, Any] | None = None,
    can_subset: bool = False,
    resource_defs: Mapping[str, object] | None = None,
    group_name: str | None = None,
    retry_policy: RetryPolicy | None = None,
    code_version: str | None = None,
    specs: Sequence[AssetSpec] | None = None,
    check_specs: Sequence[AssetCheckSpec] | None = None,
    pool: str | None = None,
    **kwargs: Any,
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
        internal_asset_deps (Optional[Mapping[str, Set[AssetKey]]]): By default, it is assumed
            that all assets produced by a multi_asset depend on all assets that are consumed by that
            multi asset. If this default is not correct, you pass in a map of output names to a
            corrected set of AssetKeys that they depend on. Any AssetKeys in this list must be either
            used as input to the asset or produced within the op.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the assets.
        hooks (Optional[AbstractSet[HookDefinition]]): A set of hooks to attach to the asset.
            These hooks will be executed when the asset is materialized.
        backfill_policy (Optional[BackfillPolicy]): The backfill policy for the op that computes the asset.
        op_tags (Optional[Dict[str, Any]]): A dictionary of tags for the op that computes the asset.
            Frameworks may expect and require certain metadata to be attached to a op. Values that
            are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.
        can_subset (bool): If this asset's computation can emit a subset of the asset
            keys based on the context.selected_asset_keys argument. Defaults to False.
        resource_defs (Optional[Mapping[str, object]]):
            (Beta) A mapping of resource keys to resources. These resources
            will be initialized during execution, and can be accessed from the
            context within the body of the function.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. This
            group name will be applied to all assets produced by this multi_asset.
        retry_policy (Optional[RetryPolicy]): The retry policy for the op that computes the asset.
        code_version (Optional[str]): Version of the code encapsulated by the multi-asset. If set,
            this is used as a default code version for all defined assets.
        specs (Optional[Sequence[AssetSpec]]): The specifications for the assets materialized
            by this function.
        check_specs (Optional[Sequence[AssetCheckSpec]]): Specs for asset checks that
            execute in the decorated function after materializing the assets.
        pool (Optional[str]): A string that identifies the concurrency pool that governs this
            multi-asset's execution.
        non_argument_deps (Optional[Union[Set[AssetKey], Set[str]]]): Deprecated, use deps instead.
            Set of asset keys that are upstream dependencies, but do not pass an input to the
            multi_asset.

    Examples:
        .. code-block:: python

            @multi_asset(
                specs=[
                    AssetSpec("asset1", deps=["asset0"]),
                    AssetSpec("asset2", deps=["asset0"]),
                ]
            )
            def my_function():
                asset0_value = load(path="asset0")
                asset1_result, asset2_result = do_some_transformation(asset0_value)
                write(asset1_result, path="asset1")
                write(asset2_result, path="asset2")

            # Or use IO managers to handle I/O:
            @multi_asset(
                outs={
                    "asset1": AssetOut(),
                    "asset2": AssetOut(),
                }
            )
            def my_function(asset0):
                asset1_value = do_some_transformation(asset0)
                asset2_value = do_some_other_transformation(asset0)
                return asset1_value, asset2_value
    """
    from dagster._core.execution.build_resources import wrap_resources_for_execution

    only_allow_hidden_params_in_kwargs(multi_asset, kwargs)

    args = DecoratorAssetsDefinitionBuilderArgs(
        name=name,
        op_description=description,
        specs=check.opt_sequence_param(specs, "specs", of_type=AssetSpec),
        check_specs_by_output_name=create_check_specs_by_output_name(check_specs),
        asset_out_map=check.opt_mapping_param(outs, "outs", key_type=str, value_type=AssetOut),
        upstream_asset_deps=_deps_and_non_argument_deps_to_asset_deps(
            deps=deps,
            non_argument_deps=_validate_hidden_non_argument_dep_param(
                kwargs.get("non_argument_deps")
            ),
        ),
        asset_deps=check.opt_mapping_param(
            internal_asset_deps, "internal_asset_deps", key_type=str, value_type=set
        ),
        asset_in_map=check.opt_mapping_param(ins, "ins", key_type=str, value_type=AssetIn),
        can_subset=can_subset,
        group_name=group_name,
        partitions_def=partitions_def,
        retry_policy=retry_policy,
        code_version=code_version,
        op_tags=op_tags,
        config_schema=check.opt_mapping_param(
            config_schema,  # type: ignore
            "config_schema",
            additional_message="Only dicts are supported for asset config_schema.",
        ),
        compute_kind=check.opt_str_param(kwargs.get("compute_kind"), "compute_kind"),
        required_resource_keys=check.opt_set_param(
            required_resource_keys, "required_resource_keys", of_type=str
        ),
        op_def_resource_defs=wrap_resources_for_execution(
            check.opt_mapping_param(resource_defs, "resource_defs", key_type=str)
        ),
        assets_def_resource_defs=wrap_resources_for_execution(
            check.opt_mapping_param(resource_defs, "resource_defs", key_type=str)
        ),
        backfill_policy=backfill_policy,
        decorator_name="@multi_asset",
        execution_type=AssetExecutionType.MATERIALIZATION,
        pool=pool,
        allow_arbitrary_check_specs=kwargs.get("allow_arbitrary_check_specs", False),
        hooks=check.opt_set_param(hooks, "hooks", of_type=HookDefinition),
    )

    def inner(fn: Callable[..., Any]) -> AssetsDefinition:
        builder = DecoratorAssetsDefinitionBuilder.for_multi_asset(args=args, fn=fn)

        check.invariant(
            len(builder.overlapping_output_names) == 0,
            f"Check output names overlap with asset output names: {builder.overlapping_output_names}",
        )

        with disable_dagster_warnings():
            return builder.create_assets_definition()

    return inner


@overload
def graph_asset(
    compose_fn: Callable[..., Any],
) -> AssetsDefinition: ...


@overload
def graph_asset(
    *,
    name: str | None = None,
    description: str | None = None,
    ins: Mapping[str, AssetIn] | None = None,
    config: ConfigMapping | Mapping[str, Any] | None = None,
    key_prefix: CoercibleToAssetKeyPrefix | None = None,
    group_name: str | None = None,
    partitions_def: PartitionsDefinition[str] | None = None,
    hooks: AbstractSet[HookDefinition] | None = None,
    metadata: RawMetadataMapping | None = ...,
    tags: Mapping[str, str] | None = ...,
    owners: Sequence[str] | None = None,
    kinds: AbstractSet[str] | None = None,
    legacy_freshness_policy: LegacyFreshnessPolicy | None = ...,
    auto_materialize_policy: AutoMaterializePolicy | None = ...,
    automation_condition: AutomationCondition[AssetKey] | None = ...,
    backfill_policy: BackfillPolicy | None = ...,
    resource_defs: Mapping[str, ResourceDefinition] | None = ...,
    check_specs: Sequence[AssetCheckSpec] | None = None,
    code_version: str | None = None,
    key: CoercibleToAssetKey | None = None,
) -> Callable[[Callable[..., Any]], AssetsDefinition]: ...


@hidden_param(
    param="legacy_freshness_policy",
    breaking_version="1.12.0",
    additional_warn_text="use freshness checks instead",
)
@hidden_param(
    param="auto_materialize_policy",
    breaking_version="1.10.0",
    additional_warn_text="use `automation_condition` instead",
)
@public
def graph_asset(
    compose_fn: Callable | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    ins: Mapping[str, AssetIn] | None = None,
    config: ConfigMapping | Mapping[str, Any] | None = None,
    key_prefix: CoercibleToAssetKeyPrefix | None = None,
    group_name: str | None = None,
    partitions_def: PartitionsDefinition[str] | None = None,
    hooks: AbstractSet[HookDefinition] | None = None,
    metadata: RawMetadataMapping | None = None,
    tags: Mapping[str, str] | None = None,
    owners: Sequence[str] | None = None,
    automation_condition: AutomationCondition[AssetKey] | None = None,
    backfill_policy: BackfillPolicy | None = None,
    resource_defs: Mapping[str, ResourceDefinition] | None = None,
    check_specs: Sequence[AssetCheckSpec] | None = None,
    code_version: str | None = None,
    key: CoercibleToAssetKey | None = None,
    kinds: AbstractSet[str] | None = None,
    **kwargs: Any,
) -> AssetsDefinition | Callable[[Callable[..., Any]], AssetsDefinition]:
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
            with secrets.

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
        hooks (Optional[AbstractSet[HookDefinition]]): A set of hooks to attach to the asset.
            These hooks will be executed when the asset is materialized.
        metadata (Optional[RawMetadataMapping]): Dictionary of metadata to be associated with
            the asset.
        tags (Optional[Mapping[str, str]]): Tags for filtering and organizing. These tags are not
            attached to runs of the asset.
        owners (Optional[Sequence[str]]): A list of strings representing owners of the asset. Each
            string can be a user's email address, or a team name prefixed with `team:`,
            e.g. `team:finops`.
        kinds (Optional[Set[str]]): A list of strings representing the kinds of the asset. These
            will be made visible in the Dagster UI.
        automation_condition (Optional[AutomationCondition]): The AutomationCondition to use
            for this asset.
        backfill_policy (Optional[BackfillPolicy]): The BackfillPolicy to use for this asset.
        code_version (Optional[str]): Version of the code that generates this asset. In
            general, versions should be set only for code that deterministically produces the same
            output when given the same inputs.
        key (Optional[CoeercibleToAssetKey]): The key for this asset. If provided, cannot specify key_prefix or name.

    Examples:
        .. code-block:: python

            @op
            def fetch_files_from_slack(context) -> pd.DataFrame:
                ...

            @op
            def store_files(files) -> None:
                files.to_sql(name="slack_files", con=create_db_connection())

            @graph_asset
            def slack_files_table():
                return store_files(fetch_files_from_slack())
    """
    only_allow_hidden_params_in_kwargs(graph_asset, kwargs)

    if compose_fn is None:
        return lambda fn: graph_asset(
            fn,  # type: ignore
            name=name,
            description=description,
            ins=ins,
            config=config,
            key_prefix=key_prefix,
            group_name=group_name,
            partitions_def=partitions_def,
            hooks=hooks,
            metadata=metadata,
            tags=tags,
            owners=owners,
            legacy_freshness_policy=kwargs.get("legacy_freshness_policy"),
            automation_condition=resolve_automation_condition(
                automation_condition, kwargs.get("auto_materialize_policy")
            ),
            backfill_policy=backfill_policy,
            resource_defs=resource_defs,
            check_specs=check_specs,
            code_version=code_version,
            key=key,
            kinds=kinds,
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
            hooks=hooks,
            metadata=metadata,
            tags=tags,
            owners=owners,
            legacy_freshness_policy=kwargs.get("legacy_freshness_policy"),
            automation_condition=resolve_automation_condition(
                automation_condition, kwargs.get("auto_materialize_policy")
            ),
            backfill_policy=backfill_policy,
            resource_defs=resource_defs,
            check_specs=check_specs,
            code_version=code_version,
            key=key,
            kinds=kinds,
        )


def graph_asset_no_defaults(
    *,
    compose_fn: Callable[..., Any],
    name: str | None,
    description: str | None,
    ins: Mapping[str, AssetIn] | None,
    config: ConfigMapping | Mapping[str, Any] | None,
    key_prefix: CoercibleToAssetKeyPrefix | None,
    group_name: str | None,
    partitions_def: PartitionsDefinition | None,
    hooks: AbstractSet[HookDefinition] | None,
    metadata: RawMetadataMapping | None,
    tags: Mapping[str, str] | None,
    owners: Sequence[str] | None,
    legacy_freshness_policy: LegacyFreshnessPolicy | None,
    automation_condition: AutomationCondition | None,
    backfill_policy: BackfillPolicy | None,
    resource_defs: Mapping[str, ResourceDefinition] | None,
    check_specs: Sequence[AssetCheckSpec] | None,
    code_version: str | None,
    key: CoercibleToAssetKey | None,
    kinds: AbstractSet[str] | None,
) -> AssetsDefinition:
    ins = ins or {}
    named_ins = build_and_validate_named_ins(compose_fn, set(), ins or {})
    out_asset_key, _asset_name = resolve_asset_key_and_name_for_decorator(
        key=key,
        key_prefix=key_prefix,
        name=name,
        decorator_name="@graph_asset",
        fn=compose_fn,
    )

    keys_by_input_name = {input_name: asset_key for asset_key, (input_name, _) in named_ins.items()}
    partition_mappings = {
        input_name: asset_in.partition_mapping
        for input_name, asset_in in ins.items()
        if asset_in.partition_mapping is not None
    }

    check_specs_by_output_name = validate_and_assign_output_names_to_check_specs(
        check_specs, [out_asset_key]
    )
    check_outs_by_output_name: Mapping[str, GraphOut] = {
        output_name: GraphOut() for output_name in check_specs_by_output_name.keys()
    }

    combined_outs_by_output_name: Mapping = {
        "result": GraphOut(),
        **check_outs_by_output_name,
    }

    validate_kind_tags(kinds)
    tags_with_kinds = {
        **(normalize_tags(tags, strict=True)),
        **{f"{KIND_PREFIX}{kind}": "" for kind in kinds or []},
    }

    op_graph = graph(
        name=out_asset_key.to_python_identifier(),
        description=description,
        config=config,
        ins={input_name: GraphIn() for _, (input_name, _) in named_ins.items()},
        out=combined_outs_by_output_name,
    )(compose_fn)
    return AssetsDefinition.from_graph(
        op_graph,
        keys_by_input_name=keys_by_input_name,
        keys_by_output_name={"result": out_asset_key},
        partitions_def=partitions_def,
        hook_defs=hooks,
        partition_mappings=partition_mappings if partition_mappings else None,
        group_name=group_name,
        metadata_by_output_name={"result": metadata} if metadata else None,
        tags_by_output_name={"result": tags_with_kinds} if tags_with_kinds else None,
        legacy_freshness_policies_by_output_name=(
            {"result": legacy_freshness_policy} if legacy_freshness_policy else None
        ),
        automation_conditions_by_output_name=(
            {"result": automation_condition} if automation_condition else None
        ),
        backfill_policy=backfill_policy,
        descriptions_by_output_name={"result": description} if description else None,
        resource_defs=resource_defs,
        check_specs=check_specs,
        owners_by_output_name={"result": owners} if owners else None,
        code_versions_by_output_name={"result": code_version} if code_version else None,
    )


@public
def graph_multi_asset(
    *,
    outs: Mapping[str, AssetOut],
    name: str | None = None,
    ins: Mapping[str, AssetIn] | None = None,
    partitions_def: PartitionsDefinition | None = None,
    hooks: AbstractSet[HookDefinition] | None = None,
    backfill_policy: BackfillPolicy | None = None,
    group_name: str | None = None,
    can_subset: bool = False,
    resource_defs: Mapping[str, ResourceDefinition] | None = None,
    check_specs: Sequence[AssetCheckSpec] | None = None,
    config: ConfigMapping | Mapping[str, Any] | None = None,
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
        hooks (Optional[AbstractSet[HookDefinition]]): A list of hooks to attach to the asset.
        backfill_policy (Optional[BackfillPolicy]): The backfill policy for the asset.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. This
            group name will be applied to all assets produced by this multi_asset.
        can_subset (bool): Whether this asset's computation can emit a subset of the asset
            keys based on the context.selected_assets argument. Defaults to False.
        config (Optional[Union[ConfigMapping], Mapping[str, Any]):
            Describes how the graph underlying the asset is configured at runtime.

            If a :py:class:`ConfigMapping` object is provided, then the graph takes on the config
            schema of this object. The mapping will be applied at runtime to generate the config for
            the graph's constituent nodes.

            If a dictionary is provided, then it will be used as the default run config for the
            graph. This means it must conform to the config schema of the underlying nodes. Note
            that the values provided will be viewable and editable in the Dagster UI, so be careful
            with secrets.

            If no value is provided, then the config schema for the graph is the default (derived
                from the underlying nodes).
    """

    def inner(fn: Callable[..., Any]) -> AssetsDefinition:
        partition_mappings = {
            input_name: asset_in.partition_mapping
            for input_name, asset_in in (ins or {}).items()
            if asset_in.partition_mapping
        }

        named_ins = build_and_validate_named_ins(fn, set(), ins or {})
        keys_by_input_name = {
            input_name: asset_key for asset_key, (input_name, _) in named_ins.items()
        }
        named_outs = build_named_outs(outs)

        check_specs_by_output_name = validate_and_assign_output_names_to_check_specs(
            check_specs, list(named_outs.keys())
        )
        check_outs_by_output_name: Mapping[str, GraphOut] = {
            output_name: GraphOut() for output_name in check_specs_by_output_name.keys()
        }

        combined_outs_by_output_name = {
            **{output_name: GraphOut() for output_name, _ in named_outs.values()},
            **check_outs_by_output_name,
        }

        op_graph = graph(
            name=name or fn.__name__,
            out=combined_outs_by_output_name,
            config=config,
            ins={input_name: GraphIn() for _, (input_name, _) in named_ins.items()},
        )(fn)

        # source metadata from the AssetOuts (if any)
        metadata_by_output_name = {
            output_name: out.metadata
            for output_name, out in outs.items()
            if isinstance(out, AssetOut) and out.metadata is not None
        }

        # source freshness policies from the AssetOuts (if any)
        legacy_freshness_policies_by_output_name = {
            output_name: out.legacy_freshness_policy
            for output_name, out in outs.items()
            if isinstance(out, AssetOut) and out.legacy_freshness_policy is not None
        }

        # source auto materialize policies from the AssetOuts (if any)
        automation_conditions_by_output_name = {
            output_name: out.automation_condition
            for output_name, out in outs.items()
            if isinstance(out, AssetOut) and out.automation_condition is not None
        }

        # source descriptions from the AssetOuts (if any)
        descriptions_by_output_name = {
            output_name: out.description
            for output_name, out in outs.items()
            if isinstance(out, AssetOut) and out.description is not None
        }

        # source code versions from the AssetOuts (if any)
        code_versions_by_output_name = {
            output_name: out.code_version
            for output_name, out in outs.items()
            if isinstance(out, AssetOut) and out.code_version is not None
        }

        tags_by_output_name = {
            output_name: out.tags
            for output_name, out in outs.items()
            if isinstance(out, AssetOut) and out.tags is not None
        }

        owners_by_output_name = {
            output_name: out.owners
            for output_name, out in outs.items()
            if isinstance(out, AssetOut) and out.owners is not None
        }

        return AssetsDefinition.from_graph(
            op_graph,
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name={
                output_name: asset_key for asset_key, (output_name, _) in named_outs.items()
            },
            partitions_def=partitions_def,
            partition_mappings=partition_mappings if partition_mappings else None,
            group_name=group_name,
            can_subset=can_subset,
            metadata_by_output_name=metadata_by_output_name,
            legacy_freshness_policies_by_output_name=legacy_freshness_policies_by_output_name,
            automation_conditions_by_output_name=automation_conditions_by_output_name,
            backfill_policy=backfill_policy,
            descriptions_by_output_name=descriptions_by_output_name,
            resource_defs=resource_defs,
            check_specs=check_specs,
            code_versions_by_output_name=code_versions_by_output_name,
            tags_by_output_name=tags_by_output_name,
            owners_by_output_name=owners_by_output_name,
            hook_defs=hooks,
        )

    return inner


def _deps_and_non_argument_deps_to_asset_deps(
    deps: Iterable[CoercibleToAssetDep] | None,
    non_argument_deps: set[AssetKey] | set[str] | None,
) -> Iterable[AssetDep] | None:
    """Helper function for managing deps and non_argument_deps while non_argument_deps is still an accepted parameter.
    Ensures only one of deps and non_argument_deps is provided, then converts the deps to AssetDeps.
    """
    if non_argument_deps is not None and deps is not None:
        raise DagsterInvalidDefinitionError(
            "Cannot specify both deps and non_argument_deps to @asset. Use only deps instead."
        )

    if deps is not None:
        return make_asset_deps(deps)

    if non_argument_deps is not None:
        check.set_param(non_argument_deps, "non_argument_deps", of_type=(AssetKey, str))
        return make_asset_deps(non_argument_deps)


def make_asset_deps(deps: Iterable[CoercibleToAssetDep] | None) -> Iterable[AssetDep] | None:
    if deps is None:
        return None

    return coerce_to_deps_and_check_duplicates(deps, key=None)
