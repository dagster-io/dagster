from collections.abc import Mapping, Sequence
from typing import AbstractSet, Any, Callable, Optional, Union, overload  # noqa: UP035

import dagster._check as check
from dagster._annotations import beta, beta_param, hidden_param, public
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.assets.definition.asset_spec import AssetExecutionType, AssetSpec
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.decorators.asset_decorator import (
    resolve_asset_key_and_name_for_decorator,
)
from dagster._core.definitions.decorators.decorator_assets_definition_builder import (
    DecoratorAssetsDefinitionBuilder,
    DecoratorAssetsDefinitionBuilderArgs,
    create_check_specs_by_output_name,
)
from dagster._core.definitions.events import CoercibleToAssetKey, CoercibleToAssetKeyPrefix
from dagster._core.definitions.freshness_policy import LegacyFreshnessPolicy
from dagster._core.definitions.metadata import RawMetadataMapping
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.source_asset import SourceAsset, SourceAssetObserveFunction
from dagster._utils.tags import normalize_tags
from dagster._utils.warnings import disable_dagster_warnings


@overload
def observable_source_asset(observe_fn: SourceAssetObserveFunction) -> SourceAsset: ...


@overload
def observable_source_asset(
    *,
    key: Optional[CoercibleToAssetKey] = None,
    name: Optional[str] = ...,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    metadata: Optional[RawMetadataMapping] = None,
    io_manager_key: Optional[str] = None,
    io_manager_def: Optional[object] = None,
    description: Optional[str] = None,
    group_name: Optional[str] = None,
    required_resource_keys: Optional[AbstractSet[str]] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    auto_observe_interval_minutes: Optional[float] = None,
    legacy_freshness_policy: Optional[LegacyFreshnessPolicy] = None,
    automation_condition: Optional[AutomationCondition] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
    tags: Optional[Mapping[str, str]] = None,
) -> "_ObservableSourceAsset": ...


@beta_param(param="io_manager_def")
@beta_param(param="resource_defs")
@hidden_param(
    param="auto_observe_interval_minutes",
    breaking_version="1.10.0",
    additional_warn_text="use `automation_condition` instead.",
)
@hidden_param(
    param="legacy_freshness_policy",
    breaking_version="1.12.0",
    additional_warn_text="use freshness checks instead.",
)
@public
@beta
def observable_source_asset(
    observe_fn: Optional[SourceAssetObserveFunction] = None,
    *,
    key: Optional[CoercibleToAssetKey] = None,
    name: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    metadata: Optional[RawMetadataMapping] = None,
    io_manager_key: Optional[str] = None,
    io_manager_def: Optional[object] = None,
    description: Optional[str] = None,
    group_name: Optional[str] = None,
    required_resource_keys: Optional[AbstractSet[str]] = None,
    resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    automation_condition: Optional[AutomationCondition] = None,
    op_tags: Optional[Mapping[str, Any]] = None,
    tags: Optional[Mapping[str, str]] = None,
    **kwargs,
) -> Union[SourceAsset, "_ObservableSourceAsset"]:
    """Create a `SourceAsset` with an associated observation function.

    The observation function of a source asset is wrapped inside of an op and can be executed as
    part of a job. Each execution generates an `AssetObservation` event associated with the source
    asset. The source asset observation function should return a :py:class:`~dagster.DataVersion`,
    a `~dagster.DataVersionsByPartition`, or an :py:class:`~dagster.ObserveResult`.

    Args:
        name (Optional[str]): The name of the source asset.  If not provided, defaults to the name of the
            decorated function. The asset's name must be a valid name in dagster (ie only contains
            letters, numbers, and _) and may not contain python reserved keywords.
        key_prefix (Optional[Union[str, Sequence[str]]]): If provided, the source asset's key is the
            concatenation of the key_prefix and the asset's name, which defaults to the name of
            the decorated function. Each item in key_prefix must be a valid name in dagster (ie only
            contains letters, numbers, and _) and may not contain python reserved keywords.
        metadata (Mapping[str, RawMetadataValue]): Metadata associated with the asset.
        io_manager_key (Optional[str]): The key for the IOManager that will be used to load the contents of
            the source asset when it's used as an input to other assets inside a job.
        io_manager_def (Optional[IOManagerDefinition]): (Beta) The definition of the IOManager that will be used to load the contents of
            the source asset when it's used as an input to other assets inside a job.
        description (Optional[str]): The description of the asset.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. If not provided,
            the name "default" is used.
        required_resource_keys (Optional[Set[str]]): Set of resource keys required by the observe op.
        resource_defs (Optional[Mapping[str, ResourceDefinition]]): (Beta) resource
            definitions that may be required by the :py:class:`dagster.IOManagerDefinition` provided in
            the `io_manager_def` argument.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the asset.
        op_tags (Optional[Dict[str, Any]]): A dictionary of tags for the op that computes the asset.
            Frameworks may expect and require certain metadata to be attached to a op. Values that
            are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.
        tags (Optional[Mapping[str, str]]): Tags for filtering and organizing. These tags are not
            attached to runs of the asset.
        observe_fn (Optional[SourceAssetObserveFunction]): Observation function for the source asset.
        automation_condition (Optional[AutomationCondition]): A condition describing when Dagster
            should materialize this asset.
    """
    if observe_fn is not None:
        return _ObservableSourceAsset()(observe_fn)

    return _ObservableSourceAsset(
        key,
        name,
        key_prefix,
        metadata,
        io_manager_key,
        io_manager_def,
        description,
        group_name,
        required_resource_keys,
        resource_defs,
        partitions_def,
        kwargs.get("auto_observe_interval_minutes"),
        kwargs.get("legacy_freshness_policy"),
        automation_condition,
        op_tags,
        tags=normalize_tags(tags, strict=True),
    )


class _ObservableSourceAsset:
    def __init__(
        self,
        key: Optional[CoercibleToAssetKey] = None,
        name: Optional[str] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        metadata: Optional[RawMetadataMapping] = None,
        io_manager_key: Optional[str] = None,
        io_manager_def: Optional[object] = None,
        description: Optional[str] = None,
        group_name: Optional[str] = None,
        required_resource_keys: Optional[AbstractSet[str]] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        auto_observe_interval_minutes: Optional[float] = None,
        legacy_freshness_policy: Optional[LegacyFreshnessPolicy] = None,
        automation_condition: Optional[AutomationCondition] = None,
        op_tags: Optional[Mapping[str, Any]] = None,
        tags: Optional[Mapping[str, str]] = None,
    ):
        self.key = key
        self.name = name
        if isinstance(key_prefix, str):
            key_prefix = [key_prefix]
        elif key_prefix is None:
            key_prefix = []
        self.key_prefix = key_prefix
        self.metadata = metadata
        self.io_manager_key = io_manager_key
        self.io_manager_def = io_manager_def
        self.description = description
        self.group_name = group_name
        self.required_resource_keys = required_resource_keys
        self.resource_defs = resource_defs
        self.partitions_def = partitions_def
        self.auto_observe_interval_minutes = auto_observe_interval_minutes
        self.legacy_freshness_policy = legacy_freshness_policy
        self.automation_condition = automation_condition
        self.op_tags = op_tags
        self.tags = tags

    def __call__(self, observe_fn: SourceAssetObserveFunction) -> SourceAsset:
        source_asset_key, source_asset_name = resolve_asset_key_and_name_for_decorator(
            key=self.key,
            key_prefix=self.key_prefix,
            name=self.name,
            fn=observe_fn,
            decorator_name="@observable_source_asset",
        )

        arg_resource_keys = {arg.name for arg in get_resource_args(observe_fn)}
        decorator_resource_keys = set(self.required_resource_keys or [])
        check.param_invariant(
            len(decorator_resource_keys) == 0 or len(arg_resource_keys) == 0,
            "Cannot specify resource requirements in both @op decorator and as arguments to the"
            " decorated function",
        )
        resolved_resource_keys = decorator_resource_keys.union(arg_resource_keys)

        with disable_dagster_warnings():
            return SourceAsset.dagster_internal_init(
                key=source_asset_key,
                metadata=self.metadata,
                io_manager_key=self.io_manager_key,
                io_manager_def=self.io_manager_def,
                description=self.description,
                group_name=self.group_name,
                _required_resource_keys=resolved_resource_keys,
                resource_defs=self.resource_defs,
                observe_fn=observe_fn,
                op_tags=self.op_tags,
                partitions_def=self.partitions_def,
                auto_observe_interval_minutes=self.auto_observe_interval_minutes,
                legacy_freshness_policy=self.legacy_freshness_policy,
                automation_condition=self.automation_condition,
                tags=self.tags,
            )


@beta_param(param="resource_defs")
@public
@beta
def multi_observable_source_asset(
    *,
    specs: Sequence[AssetSpec],
    name: Optional[str] = None,
    description: Optional[str] = None,
    partitions_def: Optional[PartitionsDefinition] = None,
    can_subset: bool = False,
    required_resource_keys: Optional[set[str]] = None,
    resource_defs: Optional[Mapping[str, object]] = None,
    group_name: Optional[str] = None,
    check_specs: Optional[Sequence[AssetCheckSpec]] = None,
):
    """Defines a set of assets that can be observed together with the same function.

    Args:
        name (Optional[str]): The name of the op.
        required_resource_keys (Optional[Set[str]]): Set of resource handles required by the
            underlying op.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the assets.
        can_subset (bool): If this asset's computation can emit a subset of the asset
            keys based on the context.selected_assets argument. Defaults to False.
        resource_defs (Optional[Mapping[str, object]]):
            (Beta) A mapping of resource keys to resources. These resources
            will be initialized during execution, and can be accessed from the
            context within the body of the function.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. This
            group name will be applied to all assets produced by this multi_asset.
        specs (Optional[Sequence[AssetSpec]]): The specifications for the assets
            observed by this function.
        check_specs (Optional[Sequence[AssetCheckSpec]]): Specs for asset checks that
            execute in the decorated function after observing the assets.

    Examples:
        .. code-block:: python

            @multi_observable_source_asset(
                specs=[AssetSpec("asset1"), AssetSpec("asset2")],
            )
            def my_function():
                yield ObserveResult(asset_key="asset1", metadata={"foo": "bar"})
                yield ObserveResult(asset_key="asset2", metadata={"baz": "qux"})

    """
    from dagster._core.execution.build_resources import wrap_resources_for_execution

    args = DecoratorAssetsDefinitionBuilderArgs(
        name=name,
        op_description=description,
        specs=check.opt_sequence_param(specs, "specs", of_type=AssetSpec),
        check_specs_by_output_name=create_check_specs_by_output_name(check_specs),
        asset_out_map={},
        upstream_asset_deps=None,
        asset_deps={},
        asset_in_map={},
        can_subset=can_subset,
        group_name=group_name,
        partitions_def=partitions_def,
        retry_policy=None,
        code_version=None,
        op_tags=None,
        config_schema={},
        compute_kind=None,
        required_resource_keys=check.opt_set_param(
            required_resource_keys, "required_resource_keys", of_type=str
        ),
        op_def_resource_defs=wrap_resources_for_execution(
            check.opt_mapping_param(resource_defs, "resource_defs", key_type=str)
        ),
        assets_def_resource_defs=wrap_resources_for_execution(
            check.opt_mapping_param(resource_defs, "resource_defs", key_type=str)
        ),
        backfill_policy=None,
        decorator_name="@multi_observable_source_asset",
        execution_type=AssetExecutionType.OBSERVATION,
        pool=None,
        hooks=None,
    )

    def inner(fn: Callable[..., Any]) -> AssetsDefinition:
        builder = DecoratorAssetsDefinitionBuilder.from_multi_asset_specs(
            can_subset=can_subset,
            asset_specs=specs,
            op_name=name or fn.__name__,
            asset_in_map={},
            passed_args=args,
            fn=fn,
        )

        with disable_dagster_warnings():
            return builder.create_assets_definition()

    return inner
