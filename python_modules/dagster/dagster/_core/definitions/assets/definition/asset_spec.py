from collections.abc import Iterable, Mapping, Sequence
from enum import Enum
from functools import cached_property
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Optional,
    Union,
    overload,
)

from dagster_shared.serdes import whitelist_for_serdes

import dagster._check as check
from dagster._annotations import (
    PublicAttr,
    hidden_param,
    only_allow_hidden_params_in_kwargs,
    public,
)
from dagster._check import checked
from dagster._core.definitions.assets.definition.asset_dep import AssetDep, CoercibleToAssetDep
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.definitions.freshness import InternalFreshnessPolicy
from dagster._core.definitions.freshness_policy import LegacyFreshnessPolicy
from dagster._core.definitions.partitions.definition import PartitionsDefinition
from dagster._core.definitions.partitions.mapping import PartitionMapping
from dagster._core.definitions.utils import (
    resolve_automation_condition,
    validate_asset_owner,
    validate_group_name,
)
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.storage.tags import KIND_PREFIX
from dagster._record import IHaveNew, LegacyNamedTupleMixin, record_custom
from dagster._utils.internal_init import IHasInternalInit
from dagster._utils.tags import normalize_tags
from dagster._utils.warnings import disable_dagster_warnings

if TYPE_CHECKING:
    from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition

# SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE lives on the metadata of an asset
# (which currently ends up on the Output associated with the asset key)
# whih encodes the execution type the of asset. "Unexecutable" assets are assets
# that cannot be materialized in Dagster, but can have events in the event
# log keyed off of them, making Dagster usable as a observability and lineage tool
# for externally materialized assets.
SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE = "dagster/asset_execution_type"


# SYSTEM_METADATA_KEY_IO_MANAGER_KEY lives on the metadata of an asset without a node def and
# determines the io_manager_key that can be used to load it. This is necessary because IO manager
# keys are otherwise encoded inside OutputDefinitions within NodeDefinitions.
SYSTEM_METADATA_KEY_IO_MANAGER_KEY = "dagster/io_manager_key"

# SYSTEM_METADATA_KEY_DAGSTER_TYPE lives on the metadata of an asset without a node def and
# determines the dagster_type that it is expected to output as. This is necessary because
# dagster types are otherwise encoded inside OutputDefinitions within NodeDefinitions.
SYSTEM_METADATA_KEY_DAGSTER_TYPE = "dagster/dagster_type"

# SYSTEM_METADATA_KEY_AUTO_OBSERVE_INTERVAL_MINUTES lives on the metadata of
# external assets resulting from a source asset conversion. It contains the
# `auto_observe_interval_minutes` value from the source asset and is consulted
# in the auto-materialize daemon. It should eventually be eliminated in favor
# of an implementation of `auto_observe_interval_minutes` in terms of
# `AutoMaterializeRule`.
SYSTEM_METADATA_KEY_AUTO_OBSERVE_INTERVAL_MINUTES = "dagster/auto_observe_interval_minutes"

# SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET lives on the metadata of external assets that are
# created for undefined but referenced assets during asset graph normalization. For example, in the
# below definitions, `foo` is referenced by upstream `bar` but has no corresponding definition:
#
#
#     @asset(deps=["foo"])
#     def bar(context: AssetExecutionContext):
#         ...
#
#     defs=Definitions(assets=[bar])
#
# During normalization we create a "stub" definition for `foo` and attach this metadata to it.
SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET = "dagster/auto_created_stub_asset"


@whitelist_for_serdes
class AssetExecutionType(Enum):
    OBSERVATION = "OBSERVATION"
    UNEXECUTABLE = "UNEXECUTABLE"
    MATERIALIZATION = "MATERIALIZATION"


def validate_kind_tags(kinds: Optional[AbstractSet[str]]) -> None:
    if kinds is not None and len(kinds) > 3:
        raise DagsterInvalidDefinitionError("Assets can have at most three kinds currently.")


@hidden_param(
    param="legacy_freshness_policy",
    breaking_version="1.12.0",
    additional_warn_text="use the freshness policy abstraction instead.",
)
@hidden_param(
    param="auto_materialize_policy",
    breaking_version="1.10.0",
    additional_warn_text="use `automation_condition` instead",
)
@public
@record_custom
class AssetSpec(IHasInternalInit, IHaveNew, LegacyNamedTupleMixin):
    """Specifies the core attributes of an asset, except for the function that materializes or
    observes it.

    An asset spec plus any materialization or observation function for the asset constitutes an
    "asset definition".

    Args:
        key (AssetKey): The unique identifier for this asset.
        deps (Optional[AbstractSet[AssetKey]]): The asset keys for the upstream assets that
            materializing this asset depends on.
        description (Optional[str]): Human-readable description of this asset.
        metadata (Optional[Dict[str, Any]]): A dict of static metadata for this asset.
            For example, users can provide information about the database table this
            asset corresponds to.
        skippable (bool): Whether this asset can be omitted during materialization, causing downstream
            dependencies to skip.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. If
            not provided, the name "default" is used.
        code_version (Optional[str]): The version of the code for this specific asset,
            overriding the code version of the materialization function
        backfill_policy (Optional[BackfillPolicy]): BackfillPolicy to apply to the specified asset.
        owners (Optional[Sequence[str]]): A list of strings representing owners of the asset. Each
            string can be a user's email address, or a team name prefixed with `team:`,
            e.g. `team:finops`.
        automation_condition (Optional[AutomationCondition]): The automation condition to apply to
            the asset.
        tags (Optional[Mapping[str, str]]): Tags for filtering and organizing. These tags are not
            attached to runs of the asset.
        kinds: (Optional[Set[str]]): A set of strings representing the kinds of the asset. These
            will be made visible in the Dagster UI.
        partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
            compose the asset.
    """

    key: PublicAttr[AssetKey]
    deps: PublicAttr[Iterable[AssetDep]]
    description: PublicAttr[Optional[str]]
    metadata: PublicAttr[Mapping[str, Any]]
    group_name: PublicAttr[Optional[str]]
    skippable: PublicAttr[bool]
    code_version: PublicAttr[Optional[str]]
    legacy_freshness_policy: PublicAttr[Optional[LegacyFreshnessPolicy]]
    freshness_policy: PublicAttr[Optional[InternalFreshnessPolicy]]
    automation_condition: PublicAttr[Optional[AutomationCondition]]
    owners: PublicAttr[Sequence[str]]
    tags: PublicAttr[Mapping[str, str]]
    partitions_def: PublicAttr[Optional[PartitionsDefinition]]

    def __new__(
        cls,
        key: CoercibleToAssetKey,
        *,
        deps: Optional[Iterable["CoercibleToAssetDep"]] = None,
        description: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        skippable: bool = False,
        group_name: Optional[str] = None,
        code_version: Optional[str] = None,
        automation_condition: Optional[AutomationCondition] = None,
        owners: Optional[Sequence[str]] = None,
        tags: Optional[Mapping[str, str]] = None,
        kinds: Optional[set[str]] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        freshness_policy: Optional[InternalFreshnessPolicy] = None,
        **kwargs,
    ):
        from dagster._core.definitions.assets.definition.asset_dep import (
            coerce_to_deps_and_check_duplicates,
        )

        only_allow_hidden_params_in_kwargs(AssetSpec, kwargs)

        key = AssetKey.from_coercible(key)
        asset_deps = coerce_to_deps_and_check_duplicates(deps, key)

        validate_group_name(group_name)

        owners = check.opt_sequence_param(owners, "owners", of_type=str)
        for owner in owners:
            validate_asset_owner(owner, key)

        tags_with_kinds = {
            **(normalize_tags(tags or {}, strict=True)),
            **{f"{KIND_PREFIX}{kind}": "" for kind in kinds or []},
        }

        kind_tags = {
            tag_key for tag_key in tags_with_kinds.keys() if tag_key.startswith(KIND_PREFIX)
        }
        validate_kind_tags(kind_tags)

        return super().__new__(
            cls,
            key=key,
            deps=asset_deps,
            description=check.opt_str_param(description, "description"),
            metadata=check.opt_mapping_param(metadata, "metadata", key_type=str),
            skippable=check.bool_param(skippable, "skippable"),
            group_name=check.opt_str_param(group_name, "group_name"),
            code_version=check.opt_str_param(code_version, "code_version"),
            freshness_policy=check.opt_inst_param(
                freshness_policy,
                "freshness_policy",
                InternalFreshnessPolicy,
                additional_message="If you are using a LegacyFreshnessPolicy, pass this in with the `legacy_freshness_policy` parameter instead.",
            ),
            legacy_freshness_policy=check.opt_inst_param(
                kwargs.get("legacy_freshness_policy"),
                "legacy_freshness_policy",
                LegacyFreshnessPolicy,
            ),
            automation_condition=check.opt_inst_param(
                resolve_automation_condition(
                    automation_condition, kwargs.get("auto_materialize_policy")
                ),
                "automation_condition",
                AutomationCondition,
            ),
            owners=owners,
            tags=tags_with_kinds,
            partitions_def=check.opt_inst_param(
                partitions_def, "partitions_def", PartitionsDefinition
            ),
        )

    @staticmethod
    def dagster_internal_init(
        *,
        key: CoercibleToAssetKey,
        deps: Optional[Iterable["CoercibleToAssetDep"]],
        description: Optional[str],
        metadata: Optional[Mapping[str, Any]],
        skippable: bool,
        group_name: Optional[str],
        code_version: Optional[str],
        automation_condition: Optional[AutomationCondition],
        owners: Optional[Sequence[str]],
        tags: Optional[Mapping[str, str]],
        kinds: Optional[set[str]],
        partitions_def: Optional[PartitionsDefinition],
        **kwargs,
    ) -> "AssetSpec":
        check.invariant(kwargs.get("auto_materialize_policy") is None)
        return AssetSpec(
            key=key,
            deps=deps,
            description=description,
            metadata=metadata,
            skippable=skippable,
            group_name=group_name,
            code_version=code_version,
            legacy_freshness_policy=kwargs.get("legacy_freshness_policy"),
            freshness_policy=kwargs.get("freshness_policy"),
            automation_condition=automation_condition,
            owners=owners,
            tags=tags,
            kinds=kinds,
            partitions_def=partitions_def,
        )

    @cached_property
    def partition_mappings(self) -> Mapping[AssetKey, PartitionMapping]:
        return {
            dep.asset_key: dep.partition_mapping
            for dep in self.deps
            if dep.partition_mapping is not None
        }

    @property
    def auto_materialize_policy(self) -> Optional[AutoMaterializePolicy]:
        return (
            self.automation_condition.as_auto_materialize_policy()
            if self.automation_condition
            else None
        )

    @cached_property
    def kinds(self) -> set[str]:
        return {tag[len(KIND_PREFIX) :] for tag in self.tags if tag.startswith(KIND_PREFIX)}

    @public
    def with_io_manager_key(self, io_manager_key: str) -> "AssetSpec":
        """Returns a copy of this AssetSpec with an extra metadata value that dictates which I/O
        manager to use to load the contents of this asset in downstream computations.

        Args:
            io_manager_key (str): The I/O manager key. This will be used as the value for the
                "dagster/io_manager_key" metadata key.

        Returns:
            AssetSpec
        """
        return self._replace(
            metadata={**self.metadata, SYSTEM_METADATA_KEY_IO_MANAGER_KEY: io_manager_key}
        )

    @public
    def replace_attributes(
        self,
        *,
        key: CoercibleToAssetKey = ...,
        deps: Optional[Iterable["CoercibleToAssetDep"]] = ...,
        description: Optional[str] = ...,
        metadata: Optional[Mapping[str, Any]] = ...,
        skippable: bool = ...,
        group_name: Optional[str] = ...,
        code_version: Optional[str] = ...,
        automation_condition: Optional[AutomationCondition] = ...,
        owners: Optional[Sequence[str]] = ...,
        tags: Optional[Mapping[str, str]] = ...,
        kinds: Optional[set[str]] = ...,
        partitions_def: Optional[PartitionsDefinition] = ...,
        legacy_freshness_policy: Optional[LegacyFreshnessPolicy] = ...,
        freshness_policy: Optional[InternalFreshnessPolicy] = ...,
    ) -> "AssetSpec":
        """Returns a new AssetSpec with the specified attributes replaced."""
        current_tags_without_kinds = {
            tag_key: tag_value
            for tag_key, tag_value in self.tags.items()
            if not tag_key.startswith(KIND_PREFIX)
        }
        with disable_dagster_warnings():
            return self.dagster_internal_init(
                key=key if key is not ... else self.key,
                deps=deps if deps is not ... else self.deps,
                description=description if description is not ... else self.description,
                metadata=metadata if metadata is not ... else self.metadata,
                skippable=skippable if skippable is not ... else self.skippable,
                group_name=group_name if group_name is not ... else self.group_name,
                code_version=code_version if code_version is not ... else self.code_version,
                legacy_freshness_policy=self.legacy_freshness_policy,
                freshness_policy=freshness_policy
                if freshness_policy is not ...
                else self.freshness_policy,
                automation_condition=automation_condition
                if automation_condition is not ...
                else self.automation_condition,
                owners=owners if owners is not ... else self.owners,
                tags=tags if tags is not ... else current_tags_without_kinds,
                kinds=kinds if kinds is not ... else self.kinds,
                partitions_def=partitions_def if partitions_def is not ... else self.partitions_def,
            )

    @public
    def merge_attributes(
        self,
        *,
        deps: Iterable["CoercibleToAssetDep"] = ...,
        metadata: Mapping[str, Any] = ...,
        owners: Sequence[str] = ...,
        tags: Mapping[str, str] = ...,
        kinds: set[str] = ...,
    ) -> "AssetSpec":
        """Returns a new AssetSpec with the specified attributes merged with the current attributes.

        Args:
            deps (Optional[Iterable[CoercibleToAssetDep]]): A set of asset dependencies to add to
                the asset self.
            metadata (Optional[Mapping[str, Any]]): A set of metadata to add to the asset self.
                Will overwrite any existing metadata with the same key.
            owners (Optional[Sequence[str]]): A set of owners to add to the asset self.
            tags (Optional[Mapping[str, str]]): A set of tags to add to the asset self.
                Will overwrite any existing tags with the same key.
            kinds (Optional[Set[str]]): A set of kinds to add to the asset self.

        Returns:
            AssetSpec
        """
        current_tags_without_kinds = {
            tag_key: tag_value
            for tag_key, tag_value in self.tags.items()
            if not tag_key.startswith(KIND_PREFIX)
        }
        with disable_dagster_warnings():
            return self.dagster_internal_init(
                key=self.key,
                deps=[*self.deps, *(deps if deps is not ... else [])],
                description=self.description,
                metadata={**self.metadata, **(metadata if metadata is not ... else {})},
                skippable=self.skippable,
                group_name=self.group_name,
                code_version=self.code_version,
                legacy_freshness_policy=self.legacy_freshness_policy,
                freshness_policy=self.freshness_policy,
                automation_condition=self.automation_condition,
                owners=[*self.owners, *(owners if owners is not ... else [])],
                tags={**current_tags_without_kinds, **(tags if tags is not ... else {})},
                kinds={*self.kinds, *(kinds if kinds is not ... else {})},
                partitions_def=self.partitions_def,
            )


@overload
def map_asset_specs(
    func: Callable[[AssetSpec], AssetSpec], iterable: Iterable[AssetSpec]
) -> Sequence[AssetSpec]: ...


@overload
def map_asset_specs(
    func: Callable[[AssetSpec], AssetSpec], iterable: Iterable["AssetsDefinition"]
) -> Sequence["AssetsDefinition"]: ...


@overload
def map_asset_specs(
    func: Callable[[AssetSpec], AssetSpec], iterable: Iterable[Union["AssetsDefinition", AssetSpec]]
) -> Sequence[Union["AssetsDefinition", AssetSpec]]: ...


@public
def map_asset_specs(
    func: Callable[[AssetSpec], AssetSpec], iterable: Iterable[Union["AssetsDefinition", AssetSpec]]
) -> Sequence[Union["AssetsDefinition", AssetSpec]]:
    """Map a function over a sequence of AssetSpecs or AssetsDefinitions, replacing specs in the sequence
    or specs in an AssetsDefinitions with the result of the function.

    Args:
        func (Callable[[AssetSpec], AssetSpec]): The function to apply to each AssetSpec.
        iterable (Iterable[Union[AssetsDefinition, AssetSpec]]): The sequence of AssetSpecs or AssetsDefinitions.

    Returns:
        Sequence[Union[AssetsDefinition, AssetSpec]]: A sequence of AssetSpecs or AssetsDefinitions with the function applied
            to each spec.

    Examples:
        .. code-block:: python

            from dagster import AssetSpec, map_asset_specs

            asset_specs = [
                AssetSpec(key="my_asset"),
                AssetSpec(key="my_asset_2"),
            ]

            mapped_specs = map_asset_specs(lambda spec: spec.replace_attributes(owners=["nelson@hooli.com"]), asset_specs)

    """
    from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition

    return [
        obj.map_asset_specs(func) if isinstance(obj, AssetsDefinition) else func(obj)
        for obj in iterable
    ]


@checked
def apply_freshness_policy(
    spec: AssetSpec, policy: InternalFreshnessPolicy, overwrite_existing=True
) -> AssetSpec:
    """Apply a freshness policy to an asset spec.

    You can use this in Definitions.map_asset_specs to attach a freshness policy to a selection of asset specs.
    """
    if overwrite_existing:
        return spec._replace(freshness_policy=policy)
    else:
        return spec._replace(freshness_policy=spec.freshness_policy or policy)
