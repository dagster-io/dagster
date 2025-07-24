from collections.abc import Iterator, Mapping
from typing import TYPE_CHECKING, AbstractSet, Any, Callable, Optional, cast  # noqa: UP035

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import PublicAttr, beta_param, deprecated, deprecated_param, public
from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.assets.definition.asset_spec import AssetExecutionType
from dagster._core.definitions.data_version import (
    DATA_VERSION_TAG,
    DataVersion,
    DataVersionsByPartition,
)
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.events import AssetKey, AssetObservation, CoercibleToAssetKey, Output
from dagster._core.definitions.freshness_policy import LegacyFreshnessPolicy
from dagster._core.definitions.metadata import (
    ArbitraryMetadataMapping,
    MetadataMapping,
    normalize_metadata,
)
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.resource_requirement import (
    ResourceAddable,
    ResourceKeyRequirement,
    ResourceRequirement,
    SourceAssetIOManagerRequirement,
    ensure_requirements_satisfied,
    get_resource_key_conflicts,
)
from dagster._core.definitions.result import ObserveResult
from dagster._core.definitions.utils import (
    DEFAULT_GROUP_NAME,
    DEFAULT_IO_MANAGER_KEY,
    normalize_group_name,
)
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvalidObservationError,
    DagsterInvariantViolationError,
)
from dagster._utils.internal_init import IHasInternalInit
from dagster._utils.tags import normalize_tags

if TYPE_CHECKING:
    from dagster._core.definitions.decorators.op_decorator import DecoratedOpFunction
from dagster._core.storage.io_manager import IOManagerDefinition
from dagster._utils.merger import merge_dicts
from dagster._utils.warnings import disable_dagster_warnings

# Going with this catch-all for the time-being to permit pythonic resources
SourceAssetObserveFunction: TypeAlias = Callable[..., Any]

# This is a private key that is attached to the Output emitted from a source asset observation
# function and used to prevent observations from being auto-generated from it. This is a workaround
# because we cannot currently auto-convert the observation function to use `ObserveResult`. It can
# be removed when that conversion is completed.
SYSTEM_METADATA_KEY_SOURCE_ASSET_OBSERVATION = "__source_asset_observation__"


def wrap_source_asset_observe_fn_in_op_compute_fn(
    source_asset: "SourceAsset",
) -> "DecoratedOpFunction":
    from dagster._core.definitions.decorators.op_decorator import (
        DecoratedOpFunction,
        is_context_provided,
    )
    from dagster._core.execution.context.compute import OpExecutionContext

    check.not_none(source_asset.observe_fn, "Must be an observable source asset")
    assert source_asset.observe_fn  # for type checker

    observe_fn = source_asset.observe_fn

    observe_fn_has_context = is_context_provided(get_function_params(observe_fn))

    def fn(context: OpExecutionContext) -> Output[None]:
        resource_kwarg_keys = [param.name for param in get_resource_args(observe_fn)]
        resource_kwargs = {
            key: context.resources.original_resource_dict.get(key) for key in resource_kwarg_keys
        }
        observe_fn_return_value = (
            observe_fn(context, **resource_kwargs)
            if observe_fn_has_context
            else observe_fn(**resource_kwargs)
        )

        if isinstance(observe_fn_return_value, (DataVersion, ObserveResult)):
            if source_asset.partitions_def is not None:
                raise DagsterInvalidObservationError(
                    f"{source_asset.key} is partitioned. Returning `{observe_fn_return_value.__class__}` not supported"
                    " for partitioned assets. Return `DataVersionsByPartition` instead."
                )

            if isinstance(observe_fn_return_value, ObserveResult):
                data_version = observe_fn_return_value.data_version
                metadata = observe_fn_return_value.metadata
                extra_tags = observe_fn_return_value.tags or {}

                if (
                    observe_fn_return_value.asset_key is not None
                    and observe_fn_return_value.asset_key != source_asset.key
                ):
                    raise DagsterInvariantViolationError(
                        f"Asset key {observe_fn_return_value.asset_key.to_user_string()} not found in AssetsDefinition"
                    )
            else:  # DataVersion
                data_version = observe_fn_return_value
                metadata = {}
                extra_tags = {}

            tags = {
                **({DATA_VERSION_TAG: data_version.value} if data_version is not None else {}),
                **extra_tags,
            }

            context.log_event(
                AssetObservation(
                    asset_key=source_asset.key,
                    tags=tags,
                    metadata=metadata,
                )
            )

        elif isinstance(observe_fn_return_value, DataVersionsByPartition):
            if source_asset.partitions_def is None:
                raise DagsterInvalidObservationError(
                    f"{source_asset.key} is not partitioned, so its observe function should return"
                    " a DataVersion, not a DataVersionsByPartition"
                )

            for (
                partition_key,
                data_version,
            ) in observe_fn_return_value.data_versions_by_partition.items():
                context.log_event(
                    AssetObservation(
                        asset_key=source_asset.key,
                        tags={DATA_VERSION_TAG: data_version.value},
                        partition=partition_key,
                    )
                )
        else:
            raise DagsterInvalidObservationError(
                f"Observe function for {source_asset.key} must return a DataVersion or"
                " DataVersionsByPartition, but returned a value of type"
                f" {type(observe_fn_return_value)}"
            )
        return Output(None, metadata={SYSTEM_METADATA_KEY_SOURCE_ASSET_OBSERVATION: True})

    return DecoratedOpFunction(fn)


@beta_param(param="resource_defs")
@beta_param(param="io_manager_def")
@deprecated_param(param="legacy_freshness_policy", breaking_version="1.12.0")
@deprecated(
    breaking_version="2.0.0",
    additional_warn_text="Use AssetSpec instead. If using the SourceAsset io_manager_key property, "
    "use AssetSpec(...).with_io_manager_key(...).",
)
@public
class SourceAsset(ResourceAddable, IHasInternalInit):
    """A SourceAsset represents an asset that will be loaded by (but not updated by) Dagster.

    Args:
        key (Union[AssetKey, Sequence[str], str]): The key of the asset.
        metadata (Mapping[str, MetadataValue]): Metadata associated with the asset.
        io_manager_key (Optional[str]): The key for the IOManager that will be used to load the contents of
            the asset when it's used as an input to other assets inside a job.
        io_manager_def (Optional[IOManagerDefinition]): (Beta) The definition of the IOManager that will be used to load the contents of
            the asset when it's used as an input to other assets inside a job.
        resource_defs (Optional[Mapping[str, ResourceDefinition]]): (Beta) resource definitions that may be required by the :py:class:`dagster.IOManagerDefinition` provided in the `io_manager_def` argument.
        description (Optional[str]): The description of the asset.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the asset.
        observe_fn (Optional[SourceAssetObserveFunction]) Observation function for the source asset.
        op_tags (Optional[Dict[str, Any]]): A dictionary of tags for the op that computes the asset.
            Frameworks may expect and require certain metadata to be attached to a op. Values that
            are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.
        auto_observe_interval_minutes (Optional[float]): While the asset daemon is turned on, a run
            of the observation function for this asset will be launched at this interval. `observe_fn`
            must be provided.
        freshness_policy (FreshnessPolicy): A constraint telling Dagster how often this asset is intended to be updated
            with respect to its root data.
        tags (Optional[Mapping[str, str]]): Tags for filtering and organizing. These tags are not
            attached to runs of the asset.
    """

    key: PublicAttr[AssetKey]
    metadata: PublicAttr[MetadataMapping]
    raw_metadata: PublicAttr[ArbitraryMetadataMapping]
    io_manager_key: PublicAttr[Optional[str]]
    _io_manager_def: PublicAttr[Optional[IOManagerDefinition]]
    description: PublicAttr[Optional[str]]
    partitions_def: PublicAttr[Optional[PartitionsDefinition]]
    group_name: PublicAttr[str]
    resource_defs: PublicAttr[dict[str, ResourceDefinition]]
    observe_fn: PublicAttr[Optional[SourceAssetObserveFunction]]
    op_tags: Optional[Mapping[str, Any]]
    _node_def: Optional[OpDefinition]  # computed lazily
    auto_observe_interval_minutes: Optional[float]
    legacy_freshness_policy: Optional[LegacyFreshnessPolicy]
    automation_condition: Optional[AutomationCondition]
    tags: Mapping[str, str]

    def __init__(
        self,
        key: CoercibleToAssetKey,
        metadata: Optional[ArbitraryMetadataMapping] = None,
        io_manager_key: Optional[str] = None,
        io_manager_def: Optional[object] = None,
        description: Optional[str] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        group_name: Optional[str] = None,
        resource_defs: Optional[Mapping[str, object]] = None,
        observe_fn: Optional[SourceAssetObserveFunction] = None,
        op_tags: Optional[Mapping[str, Any]] = None,
        *,
        auto_observe_interval_minutes: Optional[float] = None,
        legacy_freshness_policy: Optional[LegacyFreshnessPolicy] = None,
        automation_condition: Optional[AutomationCondition] = None,
        tags: Optional[Mapping[str, str]] = None,
        # This is currently private because it is necessary for source asset observation functions,
        # but we have not yet decided on a final API for associated one or more ops with a source
        # asset. If we were to make this public, then we would have a canonical public
        # `required_resource_keys` used for observation that might end up conflicting with a set of
        # required resource keys for a different operation.
        _required_resource_keys: Optional[AbstractSet[str]] = None,
        # Add additional fields to with_resources and with_group below
    ):
        from dagster._core.execution.build_resources import wrap_resources_for_execution

        self.key = AssetKey.from_coercible(key)
        metadata = check.opt_mapping_param(metadata, "metadata", key_type=str)
        self.raw_metadata = metadata
        self.metadata = normalize_metadata(metadata, allow_invalid=True)
        self.tags = normalize_tags(tags or {}, strict=True)

        resource_defs_dict = dict(check.opt_mapping_param(resource_defs, "resource_defs"))
        if io_manager_def:
            if not io_manager_key:
                io_manager_key = self.key.to_python_identifier("io_manager")

            if (
                io_manager_key in resource_defs_dict
                and resource_defs_dict[io_manager_key] != io_manager_def
            ):
                raise DagsterInvalidDefinitionError(
                    f"Provided conflicting definitions for io manager key '{io_manager_key}'."
                    " Please provide only one definition per key."
                )

            resource_defs_dict[io_manager_key] = io_manager_def

        self.resource_defs = wrap_resources_for_execution(resource_defs_dict)

        self.io_manager_key = check.opt_str_param(io_manager_key, "io_manager_key")
        self.partitions_def = check.opt_inst_param(
            partitions_def, "partitions_def", PartitionsDefinition
        )
        self.group_name = normalize_group_name(group_name)
        self.description = check.opt_str_param(description, "description")
        self.observe_fn = check.opt_callable_param(observe_fn, "observe_fn")
        self.op_tags = check.opt_mapping_param(op_tags, "op_tags")
        self._required_resource_keys = check.opt_set_param(
            _required_resource_keys, "_required_resource_keys", of_type=str
        )
        self._node_def = None
        self.auto_observe_interval_minutes = check.opt_numeric_param(
            auto_observe_interval_minutes, "auto_observe_interval_minutes"
        )
        self.legacy_freshness_policy = check.opt_inst_param(
            legacy_freshness_policy, "legacy_freshness_policy", LegacyFreshnessPolicy
        )
        self.automation_condition = check.opt_inst_param(
            automation_condition, "automation_condition", AutomationCondition
        )

    @staticmethod
    def dagster_internal_init(
        *,
        key: CoercibleToAssetKey,
        metadata: Optional[ArbitraryMetadataMapping],
        io_manager_key: Optional[str],
        io_manager_def: Optional[object],
        description: Optional[str],
        partitions_def: Optional[PartitionsDefinition],
        group_name: Optional[str],
        resource_defs: Optional[Mapping[str, object]],
        observe_fn: Optional[SourceAssetObserveFunction],
        op_tags: Optional[Mapping[str, Any]],
        auto_observe_interval_minutes: Optional[float],
        legacy_freshness_policy: Optional[LegacyFreshnessPolicy],
        automation_condition: Optional[AutomationCondition],
        tags: Optional[Mapping[str, str]],
        _required_resource_keys: Optional[AbstractSet[str]],
    ) -> "SourceAsset":
        return SourceAsset(
            key=key,
            metadata=metadata,
            io_manager_key=io_manager_key,
            io_manager_def=io_manager_def,
            description=description,
            partitions_def=partitions_def,
            group_name=group_name,
            resource_defs=resource_defs,
            observe_fn=observe_fn,
            op_tags=op_tags,
            auto_observe_interval_minutes=auto_observe_interval_minutes,
            legacy_freshness_policy=legacy_freshness_policy,
            automation_condition=automation_condition,
            tags=tags,
            _required_resource_keys=_required_resource_keys,
        )

    def get_io_manager_key(self) -> str:
        return self.io_manager_key or DEFAULT_IO_MANAGER_KEY

    @property
    def io_manager_def(self) -> Optional[IOManagerDefinition]:
        io_manager_key = self.get_io_manager_key()
        return cast(
            "Optional[IOManagerDefinition]",
            self.resource_defs.get(io_manager_key) if io_manager_key else None,
        )

    @public
    @property
    def op(self) -> OpDefinition:
        """OpDefinition: The OpDefinition associated with the observation function of an observable
        source asset.

        Throws an error if the asset is not observable.
        """
        check.invariant(
            isinstance(self.node_def, OpDefinition),
            "The NodeDefinition for this AssetsDefinition is not of type OpDefinition.",
        )
        return cast("OpDefinition", self.node_def)

    @property
    def execution_type(self) -> AssetExecutionType:
        return (
            AssetExecutionType.OBSERVATION
            if self.is_observable
            else AssetExecutionType.UNEXECUTABLE
        )

    @property
    def is_executable(self) -> bool:
        """bool: Whether the asset is observable."""
        return self.is_observable

    @public
    @property
    def is_observable(self) -> bool:
        """bool: Whether the asset is observable."""
        return self.node_def is not None

    @property
    def required_resource_keys(self) -> AbstractSet[str]:
        return {
            requirement.key
            for requirement in self.get_resource_requirements()
            if isinstance(requirement, ResourceKeyRequirement)
        }

    @property
    def node_def(self) -> Optional[OpDefinition]:
        """Op that generates observation metadata for a source asset."""
        if self.observe_fn is None:
            return None

        if self._node_def is None:
            self._node_def = OpDefinition(
                compute_fn=wrap_source_asset_observe_fn_in_op_compute_fn(self),
                name=self.key.to_python_identifier(),
                description=self.description,
                required_resource_keys=self._required_resource_keys,
                tags=self.op_tags,
            )
        return self._node_def

    def with_resources(self, resource_defs) -> "SourceAsset":
        from dagster._core.execution.resources_init import get_transitive_required_resource_keys

        overlapping_keys = get_resource_key_conflicts(self.resource_defs, resource_defs)
        if overlapping_keys:
            raise DagsterInvalidInvocationError(
                f"SourceAsset with key {self.key} has conflicting resource "
                "definitions with provided resources for the following keys: "
                f"{sorted(list(overlapping_keys))}. Either remove the existing "
                "resources from the asset or change the resource keys so that "
                "they don't overlap."
            )

        merged_resource_defs = merge_dicts(resource_defs, self.resource_defs)

        # Ensure top-level resource requirements are met - except for
        # io_manager, since that is a default it can be resolved later.
        ensure_requirements_satisfied(merged_resource_defs, list(self.get_resource_requirements()))

        io_manager_def = merged_resource_defs.get(self.get_io_manager_key())
        if not io_manager_def and self.get_io_manager_key() != DEFAULT_IO_MANAGER_KEY:
            raise DagsterInvalidDefinitionError(
                f"SourceAsset with asset key {self.key} requires IO manager with key"
                f" '{self.get_io_manager_key()}', but none was provided."
            )
        relevant_keys = get_transitive_required_resource_keys(
            {*self._required_resource_keys, self.get_io_manager_key()}, merged_resource_defs
        )

        relevant_resource_defs = {
            key: resource_def
            for key, resource_def in merged_resource_defs.items()
            if key in relevant_keys
        }

        io_manager_key = (
            self.get_io_manager_key()
            if self.get_io_manager_key() != DEFAULT_IO_MANAGER_KEY
            else None
        )
        with disable_dagster_warnings():
            return SourceAsset.dagster_internal_init(
                key=self.key,
                io_manager_key=io_manager_key,
                description=self.description,
                partitions_def=self.partitions_def,
                metadata=self.raw_metadata,
                io_manager_def=None,
                resource_defs=relevant_resource_defs,
                group_name=self.group_name,
                observe_fn=self.observe_fn,
                auto_observe_interval_minutes=self.auto_observe_interval_minutes,
                legacy_freshness_policy=self.legacy_freshness_policy,
                tags=self.tags,
                op_tags=self.op_tags,
                automation_condition=self.automation_condition,
                _required_resource_keys=self._required_resource_keys,
            )

    def with_attributes(
        self, group_name: Optional[str] = None, key: Optional[AssetKey] = None
    ) -> "SourceAsset":
        if (
            group_name is not None
            and self.group_name != DEFAULT_GROUP_NAME
            and self.group_name != group_name
        ):
            raise DagsterInvalidDefinitionError(
                f"Attempted to override group name to {group_name} for SourceAsset {self.key.to_user_string()}, which already has group name {self.group_name}."
                f" {self.key.to_user_string()}"
            )

        with disable_dagster_warnings():
            return SourceAsset.dagster_internal_init(
                key=key or self.key,
                metadata=self.raw_metadata,
                io_manager_key=self.io_manager_key,
                io_manager_def=self.io_manager_def,
                description=self.description,
                partitions_def=self.partitions_def,
                group_name=group_name or self.group_name,
                resource_defs=self.resource_defs,
                observe_fn=self.observe_fn,
                auto_observe_interval_minutes=self.auto_observe_interval_minutes,
                tags=self.tags,
                legacy_freshness_policy=self.legacy_freshness_policy,
                op_tags=self.op_tags,
                automation_condition=self.automation_condition,
                _required_resource_keys=self._required_resource_keys,
            )

    def get_resource_requirements(self) -> Iterator[ResourceRequirement]:
        if self.node_def is not None:
            yield from self.node_def.get_resource_requirements(
                asset_layer=None,
                handle=None,
            )
        yield SourceAssetIOManagerRequirement(
            key=self.get_io_manager_key(), asset_key=self.key.to_string()
        )
        for source_key, resource_def in self.resource_defs.items():
            yield from resource_def.get_resource_requirements(source_key=source_key)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SourceAsset):
            return False
        else:
            return (
                self.key == other.key
                and self.raw_metadata == other.raw_metadata
                and self.io_manager_key == other.io_manager_key
                and self.description == other.description
                and self.group_name == other.group_name
                and self.resource_defs == other.resource_defs
                and self.observe_fn == other.observe_fn
            )
