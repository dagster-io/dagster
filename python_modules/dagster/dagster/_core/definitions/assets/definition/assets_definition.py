import itertools
import json
import warnings
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping, Sequence
from functools import cached_property
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Optional,
    TypeVar,
    Union,
    cast,
)

from dagster_shared.record import replace

import dagster._check as check
from dagster._annotations import beta_param, deprecated_param, public
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey, EntityKey
from dagster._core.definitions.assets.definition.asset_dep import AssetDep
from dagster._core.definitions.assets.definition.asset_graph_computation import (
    AssetGraphComputation,
)
from dagster._core.definitions.assets.definition.asset_spec import (
    SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET,
    SYSTEM_METADATA_KEY_AUTO_OBSERVE_INTERVAL_MINUTES,
    SYSTEM_METADATA_KEY_IO_MANAGER_KEY,
    AssetExecutionType,
    AssetSpec,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.dependency import NodeHandle
from dagster._core.definitions.events import CoercibleToAssetKey, CoercibleToAssetKeyPrefix
from dagster._core.definitions.freshness_policy import LegacyFreshnessPolicy
from dagster._core.definitions.hook_definition import HookDefinition
from dagster._core.definitions.metadata import ArbitraryMetadataMapping
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.op_invocation import direct_invocation_result
from dagster._core.definitions.partitions.definition import (
    MultiPartitionsDefinition,
    PartitionsDefinition,
    TimeWindowPartitionsDefinition,
)
from dagster._core.definitions.partitions.mapping import (
    MultiPartitionMapping,
    PartitionMapping,
    TimeWindowPartitionMapping,
)
from dagster._core.definitions.partitions.utils import (
    infer_partition_mapping,
    warn_if_partition_mapping_not_builtin,
)
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.resource_requirement import (
    ExternalAssetIOManagerRequirement,
    ResourceAddable,
    ResourceKeyRequirement,
    ResourceRequirement,
    merge_resource_defs,
)
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.utils import (
    DEFAULT_GROUP_NAME,
    DEFAULT_IO_MANAGER_KEY,
    normalize_group_name,
    validate_asset_owner,
)
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster._utils import IHasInternalInit
from dagster._utils.cached_method import cached_method
from dagster._utils.merger import merge_dicts, reverse_dict
from dagster._utils.security import non_secure_md5_hash_str
from dagster._utils.tags import normalize_tags
from dagster._utils.warnings import BetaWarning, PreviewWarning, disable_dagster_warnings

if TYPE_CHECKING:
    from dagster._core.definitions.asset_checks.asset_checks_definition import AssetChecksDefinition
    from dagster._core.definitions.graph_definition import GraphDefinition

ASSET_SUBSET_INPUT_PREFIX = "__subset_input__"


def stringify_asset_key_to_input_name(asset_key: AssetKey) -> str:
    return "_".join(asset_key.path).replace("-", "_")


@public
class AssetsDefinition(ResourceAddable, IHasInternalInit):
    """Defines a set of assets that are produced by the same op or graph.

    AssetsDefinitions are typically not instantiated directly, but rather produced using the
    :py:func:`@asset <asset>` or :py:func:`@multi_asset <multi_asset>` decorators.
    """

    # Constructor arguments that are redundant with the specs argument
    _dagster_internal_init_excluded_args = {
        "group_names_by_key",
        "metadata_by_key",
        "tags_by_key",
        "legacy_freshness_policies_by_key",
        "auto_materialize_policies_by_key",
        "partition_mappings",
        "descriptions_by_key",
        "asset_deps",
        "owners_by_key",
        "partitions_def",
    }

    # partition mappings are also tracked inside the AssetSpecs, but this enables faster access by
    # upstream asset key
    _partition_mappings: Mapping[AssetKey, PartitionMapping]
    _resource_defs: Mapping[str, ResourceDefinition]

    _specs_by_key: Mapping[AssetKey, AssetSpec]
    _computation: Optional[AssetGraphComputation]
    _hook_defs: AbstractSet[HookDefinition]

    @beta_param(param="execution_type")
    def __init__(
        self,
        *,
        keys_by_input_name: Optional[Mapping[str, AssetKey]] = None,
        keys_by_output_name: Optional[Mapping[str, AssetKey]] = None,
        node_def: Optional[NodeDefinition] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_mappings: Optional[Mapping[AssetKey, PartitionMapping]] = None,
        asset_deps: Optional[Mapping[AssetKey, AbstractSet[AssetKey]]] = None,
        selected_asset_keys: Optional[AbstractSet[AssetKey]] = None,
        can_subset: bool = False,
        resource_defs: Optional[Mapping[str, object]] = None,
        group_names_by_key: Optional[Mapping[AssetKey, str]] = None,
        metadata_by_key: Optional[Mapping[AssetKey, ArbitraryMetadataMapping]] = None,
        tags_by_key: Optional[Mapping[AssetKey, Mapping[str, str]]] = None,
        legacy_freshness_policies_by_key: Optional[Mapping[AssetKey, LegacyFreshnessPolicy]] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        # descriptions by key is more accurately understood as _overriding_ the descriptions
        # by key that are in the OutputDefinitions associated with the asset key.
        # This is a dangerous construction liable for bugs. Instead there should be a
        # canonical source of asset descriptions in AssetsDefinintion and if we need
        # to create a memoized cached dictionary of asset keys for perf or something we do
        # that in the `__init__` or on demand.
        #
        # This is actually an override. We do not override descriptions
        # in OutputDefinitions in @multi_asset
        descriptions_by_key: Optional[Mapping[AssetKey, str]] = None,
        check_specs_by_output_name: Optional[Mapping[str, AssetCheckSpec]] = None,
        selected_asset_check_keys: Optional[AbstractSet[AssetCheckKey]] = None,
        is_subset: bool = False,
        owners_by_key: Optional[Mapping[AssetKey, Sequence[str]]] = None,
        specs: Optional[Sequence[AssetSpec]] = None,
        execution_type: Optional[AssetExecutionType] = None,
        # TODO: FOU-243
        auto_materialize_policies_by_key: Optional[Mapping[AssetKey, AutoMaterializePolicy]] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
        # if adding new fields, make sure to handle them in the with_attributes, from_graph,
        # from_op, and get_attributes_dict methods
    ):
        from dagster._core.definitions.graph_definition import GraphDefinition
        from dagster._core.definitions.hook_definition import HookDefinition
        from dagster._core.execution.build_resources import wrap_resources_for_execution

        if isinstance(node_def, GraphDefinition):
            _validate_graph_def(node_def)

        self._check_specs_by_output_name = check.opt_mapping_param(
            check_specs_by_output_name,
            "check_specs_by_output_name",
            key_type=str,
            value_type=AssetCheckSpec,
        )

        self._hook_defs = check.opt_set_param(hook_defs, "hook_defs", HookDefinition)

        automation_conditions_by_key = (
            {k: v.to_automation_condition() for k, v in auto_materialize_policies_by_key.items()}
            if auto_materialize_policies_by_key
            else None
        )

        if node_def is None:
            check.invariant(
                not keys_by_input_name,
                "node_def is None, so keys_by_input_name must be empty",
            )
            check.invariant(
                not keys_by_output_name,
                "node_def is None, so keys_by_output_name must be empty",
            )
            check.invariant(
                backfill_policy is None,
                "node_def is None, so backfill_policy must be None",
            )
            check.invariant(not can_subset, "node_def is None, so can_subset must be False")
            self._computation = None
        else:
            selected_asset_keys, selected_asset_check_keys = _resolve_selections(
                all_asset_keys={spec.key for spec in specs}
                if specs
                else set(check.not_none(keys_by_output_name).values()),
                all_check_keys={spec.key for spec in (check_specs_by_output_name or {}).values()},
                selected_asset_keys=selected_asset_keys,
                selected_asset_check_keys=selected_asset_check_keys,
            )

            self._computation = AssetGraphComputation(
                node_def=node_def,
                keys_by_input_name=check.opt_mapping_param(
                    keys_by_input_name,
                    "keys_by_input_name",
                    key_type=str,
                    value_type=AssetKey,
                ),
                keys_by_output_name=check.opt_mapping_param(
                    keys_by_output_name,
                    "keys_by_output_name",
                    key_type=str,
                    value_type=AssetKey,
                ),
                check_keys_by_output_name={
                    output_name: spec.key
                    for output_name, spec in self._check_specs_by_output_name.items()
                },
                can_subset=can_subset,
                backfill_policy=check.opt_inst_param(
                    backfill_policy, "backfill_policy", BackfillPolicy
                ),
                is_subset=check.bool_param(is_subset, "is_subset"),
                selected_asset_keys=selected_asset_keys,
                selected_asset_check_keys=selected_asset_check_keys,
                execution_type=execution_type or AssetExecutionType.MATERIALIZATION,
            )

        self._resource_defs = wrap_resources_for_execution(
            check.opt_mapping_param(resource_defs, "resource_defs")
        )

        if specs is not None:
            check.invariant(group_names_by_key is None)
            check.invariant(metadata_by_key is None)
            check.invariant(tags_by_key is None)
            check.invariant(legacy_freshness_policies_by_key is None)
            check.invariant(auto_materialize_policies_by_key is None)
            check.invariant(automation_conditions_by_key is None)
            check.invariant(descriptions_by_key is None)
            check.invariant(owners_by_key is None)
            check.invariant(partition_mappings is None)
            check.invariant(asset_deps is None)
            check.invariant(partitions_def is None)
            resolved_specs = specs

        else:
            computation_not_none = check.not_none(
                self._computation,
                "If specs are not provided, a node_def must be provided",
            )
            all_asset_keys = set(computation_not_none.keys_by_output_name.values())

            if asset_deps:
                check.invariant(
                    set(asset_deps.keys()) == all_asset_keys,
                    "The set of asset keys with dependencies specified in the asset_deps argument must "
                    "equal the set of asset keys produced by this AssetsDefinition. \n"
                    f"asset_deps keys: {set(asset_deps.keys())} \n"
                    f"expected keys: {all_asset_keys}",
                )

            if partition_mappings:
                _validate_partition_mappings(
                    partition_mappings=partition_mappings,
                    input_asset_keys=set(computation_not_none.keys_by_input_name.values()),
                    all_asset_keys=all_asset_keys,
                )

            check.invariant(node_def, "Must provide node_def if not providing specs")

            resolved_specs = _asset_specs_from_attr_key_params(
                all_asset_keys=all_asset_keys,
                keys_by_input_name=computation_not_none.keys_by_input_name,
                deps_by_asset_key=asset_deps,
                partition_mappings=partition_mappings,
                tags_by_key=tags_by_key,
                owners_by_key=owners_by_key,
                group_names_by_key=group_names_by_key,
                legacy_freshness_policies_by_key=legacy_freshness_policies_by_key,
                automation_conditions_by_key=automation_conditions_by_key,
                metadata_by_key=metadata_by_key,
                descriptions_by_key=descriptions_by_key,
                code_versions_by_key=None,
                partitions_def=partitions_def,
            )

        normalized_specs: list[AssetSpec] = []

        for spec in resolved_specs:
            if spec.owners:
                for owner in spec.owners:
                    validate_asset_owner(owner, spec.key)

            group_name = normalize_group_name(spec.group_name)

            if self._computation is not None:
                output_def, _ = self._computation.full_node_def.resolve_output_to_origin(
                    self._computation.output_names_by_key[spec.key], None
                )
                node_def_description = self._computation.node_def.description
                output_def_metadata = output_def.metadata
                output_def_description = output_def.description
                output_def_code_version = output_def.code_version
                skippable = not output_def.is_required
            else:
                node_def_description = None
                output_def_metadata = {}
                output_def_description = None
                output_def_code_version = None
                skippable = False

            metadata = {**output_def_metadata, **(spec.metadata or {})}
            # We construct description from three sources of truth here. This
            # highly unfortunate. See commentary in @multi_asset's call to dagster_internal_init.
            description = spec.description or output_def_description or node_def_description
            code_version = spec.code_version or output_def_code_version

            check.invariant(
                not (
                    spec.legacy_freshness_policy
                    and spec.partitions_def is not None
                    and not isinstance(spec.partitions_def, TimeWindowPartitionsDefinition)
                ),
                "FreshnessPolicies are currently unsupported for assets with partitions of type"
                f" {spec.partitions_def}.",
            )

            normalized_specs.append(
                replace(
                    spec,
                    group_name=group_name,
                    code_version=code_version,
                    metadata=metadata,
                    description=description,
                    skippable=skippable,
                )
            )

        unique_partitions_defs = {
            spec.partitions_def for spec in normalized_specs if spec.partitions_def is not None
        }
        if len(unique_partitions_defs) > 1 and not can_subset:
            raise DagsterInvalidDefinitionError(
                "If different AssetSpecs have different partitions_defs, can_subset must be True"
            )

        _validate_self_deps(normalized_specs)

        self._specs_by_key = {}
        for spec in normalized_specs:
            if spec.key in self._specs_by_key and self._specs_by_key[spec.key] != spec:
                raise DagsterInvalidDefinitionError(
                    "Received conflicting AssetSpecs with the same key:\n"
                    f"{self._specs_by_key[spec.key]}\n"
                    f"{spec}\n"
                    "This warning will become an exception in version 1.11"
                )
            self._specs_by_key[spec.key] = spec

        self._partition_mappings = get_partition_mappings_from_deps(
            {},
            [dep for spec in normalized_specs for dep in spec.deps],
            node_def.name if node_def else "external assets",
        )

        self._check_specs_by_key = {
            spec.key: spec for spec in self._check_specs_by_output_name.values()
        }

    def dagster_internal_init(
        *,
        keys_by_input_name: Mapping[str, AssetKey],
        keys_by_output_name: Mapping[str, AssetKey],
        node_def: NodeDefinition,
        selected_asset_keys: Optional[AbstractSet[AssetKey]],
        can_subset: bool,
        resource_defs: Optional[Mapping[str, object]],
        backfill_policy: Optional[BackfillPolicy],
        check_specs_by_output_name: Optional[Mapping[str, AssetCheckSpec]],
        selected_asset_check_keys: Optional[AbstractSet[AssetCheckKey]],
        is_subset: bool,
        specs: Optional[Sequence[AssetSpec]],
        execution_type: Optional[AssetExecutionType],
        hook_defs: Optional[AbstractSet[HookDefinition]],
    ) -> "AssetsDefinition":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=PreviewWarning)
            warnings.simplefilter("ignore", category=BetaWarning)
            return AssetsDefinition(
                keys_by_input_name=keys_by_input_name,
                keys_by_output_name=keys_by_output_name,
                node_def=node_def,
                selected_asset_keys=selected_asset_keys,
                can_subset=can_subset,
                resource_defs=resource_defs,
                hook_defs=hook_defs,
                backfill_policy=backfill_policy,
                check_specs_by_output_name=check_specs_by_output_name,
                selected_asset_check_keys=selected_asset_check_keys,
                is_subset=is_subset,
                specs=specs,
                execution_type=execution_type,
            )

    def __call__(self, *args: object, **kwargs: object) -> object:
        from dagster._core.definitions.composition import is_in_composition
        from dagster._core.definitions.graph_definition import GraphDefinition

        # defer to GraphDefinition.__call__ for graph backed assets, or if invoked in composition
        if (
            self._computation and isinstance(self._computation.node_def, GraphDefinition)
        ) or is_in_composition():
            return self.node_def(*args, **kwargs)

        # invoke against self to allow assets def information to be used
        return direct_invocation_result(self, *args, **kwargs)

    @public
    @beta_param(param="resource_defs")
    @deprecated_param(param="legacy_freshness_policies_by_output_name", breaking_version="1.12.0")
    @staticmethod
    def from_graph(
        graph_def: "GraphDefinition",
        *,
        keys_by_input_name: Optional[Mapping[str, AssetKey]] = None,
        keys_by_output_name: Optional[Mapping[str, AssetKey]] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        internal_asset_deps: Optional[Mapping[str, set[AssetKey]]] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_mappings: Optional[Mapping[str, PartitionMapping]] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        group_name: Optional[str] = None,
        group_names_by_output_name: Optional[Mapping[str, Optional[str]]] = None,
        descriptions_by_output_name: Optional[Mapping[str, str]] = None,
        metadata_by_output_name: Optional[Mapping[str, Optional[ArbitraryMetadataMapping]]] = None,
        tags_by_output_name: Optional[Mapping[str, Optional[Mapping[str, str]]]] = None,
        legacy_freshness_policies_by_output_name: Optional[
            Mapping[str, Optional[LegacyFreshnessPolicy]]
        ] = None,
        automation_conditions_by_output_name: Optional[
            Mapping[str, Optional[AutomationCondition]]
        ] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        can_subset: bool = False,
        check_specs: Optional[Sequence[AssetCheckSpec]] = None,
        owners_by_output_name: Optional[Mapping[str, Sequence[str]]] = None,
        code_versions_by_output_name: Optional[Mapping[str, Optional[str]]] = None,
        # TODO: FOU-243
        auto_materialize_policies_by_output_name: Optional[
            Mapping[str, Optional[AutoMaterializePolicy]]
        ] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
    ) -> "AssetsDefinition":
        """Constructs an AssetsDefinition from a GraphDefinition.

        Args:
            graph_def (GraphDefinition): The GraphDefinition that is an asset.
            keys_by_input_name (Optional[Mapping[str, AssetKey]]): A mapping of the input
                names of the decorated graph to their corresponding asset keys. If not provided,
                the input asset keys will be created from the graph input names.
            keys_by_output_name (Optional[Mapping[str, AssetKey]]): A mapping of the output
                names of the decorated graph to their corresponding asset keys. If not provided,
                the output asset keys will be created from the graph output names.
            key_prefix (Optional[Union[str, Sequence[str]]]): If provided, key_prefix will be prepended
                to each key in keys_by_output_name. Each item in key_prefix must be a valid name in
                dagster (ie only contains letters, numbers, and _) and may not contain python
                reserved keywords.
            internal_asset_deps (Optional[Mapping[str, Set[AssetKey]]]): By default, it is assumed
                that all assets produced by the graph depend on all assets that are consumed by that
                graph. If this default is not correct, you pass in a map of output names to a
                corrected set of AssetKeys that they depend on. Any AssetKeys in this list must be
                either used as input to the asset or produced within the graph.
            partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
                compose the assets.
            partition_mappings (Optional[Mapping[str, PartitionMapping]]): Defines how to map partition
                keys for this asset to partition keys of upstream assets. Each key in the dictionary
                correponds to one of the input assets, and each value is a PartitionMapping.
                If no entry is provided for a particular asset dependency, the partition mapping defaults
                to the default partition mapping for the partitions definition, which is typically maps
                partition keys to the same partition keys in upstream assets.
            resource_defs (Optional[Mapping[str, ResourceDefinition]]):
                (Beta) A mapping of resource keys to resource definitions. These resources
                will be initialized during execution, and can be accessed from the
                body of ops in the graph during execution.
            group_name (Optional[str]): A group name for the constructed asset. Assets without a
                group name are assigned to a group called "default".
            group_names_by_output_name (Optional[Mapping[str, Optional[str]]]): Defines a group name to be
                associated with some or all of the output assets for this node. Keys are names of the
                outputs, and values are the group name. Cannot be used with the group_name argument.
            descriptions_by_output_name (Optional[Mapping[str, Optional[str]]]): Defines a description to be
                associated with each of the output asstes for this graph.
            metadata_by_output_name (Optional[Mapping[str, Optional[RawMetadataMapping]]]): Defines metadata to
                be associated with each of the output assets for this node. Keys are names of the
                outputs, and values are dictionaries of metadata to be associated with the related
                asset.
            tags_by_output_name (Optional[Mapping[str, Optional[Mapping[str, str]]]]): Defines
                tags to be associated with each of the output assets for this node. Keys are the names
                of outputs, and values are dictionaries of tags to be associated with the related
                asset.
            legacy_freshness_policies_by_output_name (Optional[Mapping[str, Optional[FreshnessPolicy]]]): Defines a
                FreshnessPolicy to be associated with some or all of the output assets for this node.
                Keys are the names of the outputs, and values are the FreshnessPolicies to be attached
                to the associated asset.
            automation_conditions_by_output_name (Optional[Mapping[str, Optional[AutomationCondition]]]): Defines an
                AutomationCondition to be associated with some or all of the output assets for this node.
                Keys are the names of the outputs, and values are the AutoMaterializePolicies to be attached
                to the associated asset.
            backfill_policy (Optional[BackfillPolicy]): Defines this asset's BackfillPolicy
            owners_by_key (Optional[Mapping[AssetKey, Sequence[str]]]): Defines
                owners to be associated with each of the asset keys for this node.

        """
        return AssetsDefinition._from_node(
            node_def=graph_def,
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name=keys_by_output_name,
            key_prefix=key_prefix,
            internal_asset_deps=internal_asset_deps,
            partitions_def=partitions_def,
            partition_mappings=partition_mappings,
            resource_defs=resource_defs,
            hook_defs=hook_defs,
            group_name=group_name,
            group_names_by_output_name=group_names_by_output_name,
            descriptions_by_output_name=descriptions_by_output_name,
            metadata_by_output_name=metadata_by_output_name,
            tags_by_output_name=tags_by_output_name,
            legacy_freshness_policies_by_output_name=legacy_freshness_policies_by_output_name,
            automation_conditions_by_output_name=_resolve_automation_conditions_by_output_name(
                automation_conditions_by_output_name,
                auto_materialize_policies_by_output_name,
            ),
            backfill_policy=backfill_policy,
            can_subset=can_subset,
            check_specs=check_specs,
            owners_by_output_name=owners_by_output_name,
            code_versions_by_output_name=code_versions_by_output_name,
        )

    @public
    @staticmethod
    @deprecated_param(param="legacy_freshness_policies_by_output_name", breaking_version="1.12.0")
    def from_op(
        op_def: OpDefinition,
        *,
        keys_by_input_name: Optional[Mapping[str, AssetKey]] = None,
        keys_by_output_name: Optional[Mapping[str, AssetKey]] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        internal_asset_deps: Optional[Mapping[str, set[AssetKey]]] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_mappings: Optional[Mapping[str, PartitionMapping]] = None,
        group_name: Optional[str] = None,
        group_names_by_output_name: Optional[Mapping[str, Optional[str]]] = None,
        descriptions_by_output_name: Optional[Mapping[str, str]] = None,
        metadata_by_output_name: Optional[Mapping[str, Optional[ArbitraryMetadataMapping]]] = None,
        tags_by_output_name: Optional[Mapping[str, Optional[Mapping[str, str]]]] = None,
        legacy_freshness_policies_by_output_name: Optional[
            Mapping[str, Optional[LegacyFreshnessPolicy]]
        ] = None,
        automation_conditions_by_output_name: Optional[
            Mapping[str, Optional[AutomationCondition]]
        ] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        can_subset: bool = False,
        # TODO: FOU-243
        auto_materialize_policies_by_output_name: Optional[
            Mapping[str, Optional[AutoMaterializePolicy]]
        ] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
    ) -> "AssetsDefinition":
        """Constructs an AssetsDefinition from an OpDefinition.

        Args:
            op_def (OpDefinition): The OpDefinition that is an asset.
            keys_by_input_name (Optional[Mapping[str, AssetKey]]): A mapping of the input
                names of the decorated op to their corresponding asset keys. If not provided,
                the input asset keys will be created from the op input names.
            keys_by_output_name (Optional[Mapping[str, AssetKey]]): A mapping of the output
                names of the decorated op to their corresponding asset keys. If not provided,
                the output asset keys will be created from the op output names.
            key_prefix (Optional[Union[str, Sequence[str]]]): If provided, key_prefix will be prepended
                to each key in keys_by_output_name. Each item in key_prefix must be a valid name in
                dagster (ie only contains letters, numbers, and _) and may not contain python
                reserved keywords.
            internal_asset_deps (Optional[Mapping[str, Set[AssetKey]]]): By default, it is assumed
                that all assets produced by the op depend on all assets that are consumed by that
                op. If this default is not correct, you pass in a map of output names to a
                corrected set of AssetKeys that they depend on. Any AssetKeys in this list must be
                either used as input to the asset or produced within the op.
            partitions_def (Optional[PartitionsDefinition]): Defines the set of partition keys that
                compose the assets.
            partition_mappings (Optional[Mapping[str, PartitionMapping]]): Defines how to map partition
                keys for this asset to partition keys of upstream assets. Each key in the dictionary
                correponds to one of the input assets, and each value is a PartitionMapping.
                If no entry is provided for a particular asset dependency, the partition mapping defaults
                to the default partition mapping for the partitions definition, which is typically maps
                partition keys to the same partition keys in upstream assets.
            group_name (Optional[str]): A group name for the constructed asset. Assets without a
                group name are assigned to a group called "default".
            group_names_by_output_name (Optional[Mapping[str, Optional[str]]]): Defines a group name to be
                associated with some or all of the output assets for this node. Keys are names of the
                outputs, and values are the group name. Cannot be used with the group_name argument.
            descriptions_by_output_name (Optional[Mapping[str, Optional[str]]]): Defines a description to be
                associated with each of the output asstes for this graph.
            metadata_by_output_name (Optional[Mapping[str, Optional[RawMetadataMapping]]]): Defines metadata to
                be associated with each of the output assets for this node. Keys are names of the
                outputs, and values are dictionaries of metadata to be associated with the related
                asset.
            tags_by_output_name (Optional[Mapping[str, Optional[Mapping[str, str]]]]): Defines
                tags to be associated with each othe output assets for this node. Keys are the names
                of outputs, and values are dictionaries of tags to be associated with the related
                asset.
            legacy_freshness_policies_by_output_name (Optional[Mapping[str, Optional[LegacyFreshnessPolicy]]]): Defines a
                LegacyFreshnessPolicy to be associated with some or all of the output assets for this node.
                Keys are the names of the outputs, and values are the LegacyFreshnessPolicies to be attached
                to the associated asset.
            automation_conditions_by_output_name (Optional[Mapping[str, Optional[AutomationCondition]]]): Defines an
                AutomationCondition to be associated with some or all of the output assets for this node.
                Keys are the names of the outputs, and values are the AutoMaterializePolicies to be attached
                to the associated asset.
            backfill_policy (Optional[BackfillPolicy]): Defines this asset's BackfillPolicy
        """
        return AssetsDefinition._from_node(
            node_def=op_def,
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name=keys_by_output_name,
            key_prefix=key_prefix,
            internal_asset_deps=internal_asset_deps,
            partitions_def=partitions_def,
            partition_mappings=partition_mappings,
            group_name=group_name,
            group_names_by_output_name=group_names_by_output_name,
            descriptions_by_output_name=descriptions_by_output_name,
            metadata_by_output_name=metadata_by_output_name,
            tags_by_output_name=tags_by_output_name,
            legacy_freshness_policies_by_output_name=legacy_freshness_policies_by_output_name,
            automation_conditions_by_output_name=_resolve_automation_conditions_by_output_name(
                automation_conditions_by_output_name,
                auto_materialize_policies_by_output_name,
            ),
            backfill_policy=backfill_policy,
            can_subset=can_subset,
            hook_defs=hook_defs,
        )

    @staticmethod
    def _from_node(
        node_def: NodeDefinition,
        *,
        keys_by_input_name: Optional[Mapping[str, AssetKey]] = None,
        keys_by_output_name: Optional[Mapping[str, AssetKey]] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        internal_asset_deps: Optional[Mapping[str, set[AssetKey]]] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_mappings: Optional[Mapping[str, PartitionMapping]] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        group_name: Optional[str] = None,
        group_names_by_output_name: Optional[Mapping[str, Optional[str]]] = None,
        descriptions_by_output_name: Optional[Mapping[str, str]] = None,
        metadata_by_output_name: Optional[Mapping[str, Optional[ArbitraryMetadataMapping]]] = None,
        tags_by_output_name: Optional[Mapping[str, Optional[Mapping[str, str]]]] = None,
        legacy_freshness_policies_by_output_name: Optional[
            Mapping[str, Optional[LegacyFreshnessPolicy]]
        ] = None,
        code_versions_by_output_name: Optional[Mapping[str, Optional[str]]] = None,
        automation_conditions_by_output_name: Optional[
            Mapping[str, Optional[AutomationCondition]]
        ] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        can_subset: bool = False,
        check_specs: Optional[Sequence[AssetCheckSpec]] = None,
        owners_by_output_name: Optional[Mapping[str, Sequence[str]]] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
    ) -> "AssetsDefinition":
        from dagster._core.definitions.decorators.decorator_assets_definition_builder import (
            _validate_check_specs_target_relevant_asset_keys,
            create_check_specs_by_output_name,
        )
        from dagster._core.definitions.hook_definition import HookDefinition

        node_def = check.inst_param(node_def, "node_def", NodeDefinition)
        keys_by_input_name = _infer_keys_by_input_names(
            node_def,
            check.opt_mapping_param(
                keys_by_input_name,
                "keys_by_input_name",
                key_type=str,
                value_type=AssetKey,
            ),
        )
        keys_by_output_name = check.opt_mapping_param(
            keys_by_output_name,
            "keys_by_output_name",
            key_type=str,
            value_type=AssetKey,
        )
        check_specs_by_output_name = create_check_specs_by_output_name(check_specs)
        keys_by_output_name = _infer_keys_by_output_names(
            node_def, keys_by_output_name or {}, check_specs_by_output_name
        )

        internal_asset_deps = check.opt_mapping_param(
            internal_asset_deps, "internal_asset_deps", key_type=str, value_type=set
        )
        resource_defs = check.opt_mapping_param(
            resource_defs, "resource_defs", key_type=str, value_type=ResourceDefinition
        )
        hook_defs = check.opt_set_param(hook_defs, "hook_defs", HookDefinition)

        transformed_internal_asset_deps: dict[AssetKey, AbstractSet[AssetKey]] = {}
        if internal_asset_deps:
            for output_name, asset_keys in internal_asset_deps.items():
                if output_name not in keys_by_output_name:
                    check.failed(
                        f"output_name {output_name} specified in internal_asset_deps does not exist"
                        f" in the decorated function. Output names: {list(keys_by_output_name.keys())}.",
                    )
                transformed_internal_asset_deps[keys_by_output_name[output_name]] = asset_keys

        _validate_check_specs_target_relevant_asset_keys(
            check_specs, list(keys_by_output_name.values())
        )

        keys_by_output_name_with_prefix: dict[str, AssetKey] = {}
        key_prefix_list = [key_prefix] if isinstance(key_prefix, str) else key_prefix
        for output_name, key in keys_by_output_name.items():
            # add key_prefix to the beginning of each asset key
            key_with_key_prefix = AssetKey(
                list(filter(None, [*(key_prefix_list or []), *key.path]))
            )
            keys_by_output_name_with_prefix[output_name] = key_with_key_prefix

        T = TypeVar("T")

        def _output_dict_to_asset_dict(
            attr_by_output_name: Optional[Mapping[str, Optional[T]]],
        ) -> Optional[Mapping[AssetKey, T]]:
            if not attr_by_output_name:
                return None
            return {
                keys_by_output_name_with_prefix[output_name]: attr
                for output_name, attr in attr_by_output_name.items()
                if attr is not None
            }

        check.param_invariant(
            group_name is None or group_names_by_output_name is None,
            "group_name",
            "Cannot use both group_name and group_names_by_output_name",
        )

        if group_name is not None:
            group_names_by_key = {
                asset_key: group_name for asset_key in keys_by_output_name_with_prefix.values()
            }
        elif group_names_by_output_name:
            group_names_by_key = _output_dict_to_asset_dict(group_names_by_output_name)
        else:
            group_names_by_key = None

        specs = _asset_specs_from_attr_key_params(
            all_asset_keys=set(keys_by_output_name_with_prefix.values()),
            keys_by_input_name=keys_by_input_name,
            deps_by_asset_key=transformed_internal_asset_deps or None,
            partition_mappings=(
                {
                    keys_by_input_name[input_name]: partition_mapping
                    for input_name, partition_mapping in partition_mappings.items()
                }
                if partition_mappings
                else None
            ),
            tags_by_key=_output_dict_to_asset_dict(tags_by_output_name),
            owners_by_key=_output_dict_to_asset_dict(owners_by_output_name),
            group_names_by_key=group_names_by_key,
            legacy_freshness_policies_by_key=_output_dict_to_asset_dict(
                legacy_freshness_policies_by_output_name
            ),
            automation_conditions_by_key=_output_dict_to_asset_dict(
                automation_conditions_by_output_name
            ),
            metadata_by_key=_output_dict_to_asset_dict(metadata_by_output_name),
            descriptions_by_key=_output_dict_to_asset_dict(descriptions_by_output_name),
            code_versions_by_key=_output_dict_to_asset_dict(code_versions_by_output_name),
            partitions_def=partitions_def,
        )

        return AssetsDefinition.dagster_internal_init(
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name=keys_by_output_name_with_prefix,
            node_def=node_def,
            resource_defs=resource_defs,
            hook_defs=hook_defs,
            backfill_policy=check.opt_inst_param(
                backfill_policy, "backfill_policy", BackfillPolicy
            ),
            can_subset=can_subset,
            selected_asset_keys=None,  # node has no subselection info
            check_specs_by_output_name=check_specs_by_output_name,
            selected_asset_check_keys=None,
            is_subset=False,
            specs=specs,
            execution_type=AssetExecutionType.MATERIALIZATION,
        )

    @public
    @property
    def can_subset(self) -> bool:
        """bool: If True, indicates that this AssetsDefinition may materialize any subset of its
        asset keys in a given computation (as opposed to being required to materialize all asset
        keys).
        """
        return self._computation.can_subset if self._computation else False

    @property
    def computation(self) -> Optional[AssetGraphComputation]:
        return self._computation

    @property
    def specs(self) -> Iterable[AssetSpec]:
        return self._specs_by_key.values()

    @property
    def specs_by_key(self) -> Mapping[AssetKey, AssetSpec]:
        return self._specs_by_key

    @public
    @property
    def group_names_by_key(self) -> Mapping[AssetKey, str]:
        """Mapping[AssetKey, str]: Returns a mapping from the asset keys in this AssetsDefinition
        to the group names assigned to them. If there is no assigned group name for a given AssetKey,
        it will not be present in this dictionary.
        """
        return {key: check.not_none(spec.group_name) for key, spec in self._specs_by_key.items()}

    @public
    @property
    def descriptions_by_key(self) -> Mapping[AssetKey, str]:
        """Mapping[AssetKey, str]: Returns a mapping from the asset keys in this AssetsDefinition
        to the descriptions assigned to them. If there is no assigned description for a given AssetKey,
        it will not be present in this dictionary.
        """
        return {
            key: spec.description
            for key, spec in self._specs_by_key.items()
            if spec.description is not None
        }

    @public
    @property
    def op(self) -> OpDefinition:
        """OpDefinition: Returns the OpDefinition that is used to materialize the assets in this
        AssetsDefinition.
        """
        node_def = self.node_def
        check.invariant(
            isinstance(node_def, OpDefinition),
            "The NodeDefinition for this AssetsDefinition is not of type OpDefinition.",
        )
        return cast("OpDefinition", node_def)

    @public
    @property
    def node_def(self) -> NodeDefinition:
        """NodeDefinition: Returns the OpDefinition or GraphDefinition that is used to materialize
        the assets in this AssetsDefinition.
        """
        return check.not_none(self._computation, "This AssetsDefinition has no node_def").node_def

    @public
    @cached_property
    def asset_deps(self) -> Mapping[AssetKey, AbstractSet[AssetKey]]:
        """Maps assets that are produced by this definition to assets that they depend on. The
        dependencies can be either "internal", meaning that they refer to other assets that are
        produced by this definition, or "external", meaning that they refer to assets that aren't
        produced by this definition.
        """
        return {
            key: {dep.asset_key for dep in spec.deps} for key, spec in self._specs_by_key.items()
        }

    @property
    def input_names(self) -> Iterable[str]:
        """Iterable[str]: The set of input names of the underlying NodeDefinition for this
        AssetsDefinition.
        """
        return self.keys_by_input_name.keys()

    @public
    @property
    def key(self) -> AssetKey:
        """AssetKey: The asset key associated with this AssetsDefinition. If this AssetsDefinition
        has more than one asset key, this will produce an error.
        """
        check.invariant(
            len(self.keys) == 1,
            "Tried to retrieve asset key from an assets definition with multiple asset keys: "
            + ", ".join([str(ak.to_string()) for ak in self.keys]),
        )

        return next(iter(self.keys))

    @public
    @property
    def resource_defs(self) -> Mapping[str, ResourceDefinition]:
        """Mapping[str, ResourceDefinition]: A mapping from resource name to ResourceDefinition for
        the resources bound to this AssetsDefinition.
        """
        return dict(self._resource_defs)

    @property
    def hook_defs(self) -> AbstractSet[HookDefinition]:
        """AbstractSet[HookDefinition]: A set of hook definitions that are bound to this
        AssetsDefinition. These hooks will be executed when the assets in this AssetsDefinition
        are materialized.
        """
        return self._hook_defs

    @public
    @property
    def keys(self) -> AbstractSet[AssetKey]:
        """AbstractSet[AssetKey]: The asset keys associated with this AssetsDefinition."""
        if self._computation:
            return self._computation.selected_asset_keys
        else:
            return self._specs_by_key.keys()

    @property
    def has_keys(self) -> bool:
        return len(self.keys) > 0

    @property
    def has_check_keys(self) -> bool:
        return len(self.check_keys) > 0

    @public
    @property
    def dependency_keys(self) -> Iterable[AssetKey]:
        """Iterable[AssetKey]: The asset keys which are upstream of any asset included in this
        AssetsDefinition.
        """
        # the input asset keys that are directly upstream of a selected asset key
        return {dep.asset_key for key in self.keys for dep in self._specs_by_key[key].deps}

    @property
    def node_keys_by_output_name(self) -> Mapping[str, AssetKey]:
        """AssetKey for each output on the underlying NodeDefinition."""
        return self._computation.keys_by_output_name if self._computation else {}

    @property
    def node_keys_by_input_name(self) -> Mapping[str, AssetKey]:
        """AssetKey for each input on the underlying NodeDefinition."""
        return self._computation.keys_by_input_name if self._computation else {}

    @property
    def input_names_by_node_key(self) -> Mapping[AssetKey, str]:
        return {key: input_name for input_name, key in self.node_keys_by_input_name.items()}

    @property
    def node_check_specs_by_output_name(self) -> Mapping[str, AssetCheckSpec]:
        """AssetCheckSpec for each output on the underlying NodeDefinition."""
        return self._check_specs_by_output_name

    @property
    def check_specs_by_output_name(self) -> Mapping[str, AssetCheckSpec]:
        return {
            name: spec
            for name, spec in self._check_specs_by_output_name.items()
            if self._computation is None or spec.key in self._computation.selected_asset_check_keys
        }

    def get_spec_for_check_key(self, asset_check_key: AssetCheckKey) -> AssetCheckSpec:
        return self._check_specs_by_key[asset_check_key]

    @property
    def keys_by_output_name(self) -> Mapping[str, AssetKey]:
        return {
            name: key for name, key in self.node_keys_by_output_name.items() if key in self.keys
        }

    @cached_property
    def entity_keys_by_output_name(self) -> Mapping[str, EntityKey]:
        return merge_dicts(
            self.keys_by_output_name,
            {
                output_name: spec.key
                for output_name, spec in self.check_specs_by_output_name.items()
            },
        )

    @cached_property
    def output_names_by_entity_key(self) -> Mapping[EntityKey, str]:
        return reverse_dict(self.entity_keys_by_output_name)

    @property
    def asset_and_check_keys(self) -> AbstractSet[EntityKey]:
        return set(self.keys).union(self.check_keys)

    @cached_property
    def keys_by_input_name(self) -> Mapping[str, AssetKey]:
        upstream_keys = {
            *(dep.asset_key for key in self.keys for dep in self._specs_by_key[key].deps),
            *(spec.asset_key for spec in self.check_specs if spec.asset_key not in self.keys),
            *(
                dep.asset_key
                for spec in self.check_specs
                for dep in spec.additional_deps
                if dep.asset_key not in self.keys
            ),
        }

        return {
            name: key for name, key in self.node_keys_by_input_name.items() if key in upstream_keys
        }

    @property
    def legacy_freshness_policies_by_key(self) -> Mapping[AssetKey, LegacyFreshnessPolicy]:
        return {
            key: spec.legacy_freshness_policy
            for key, spec in self._specs_by_key.items()
            if spec.legacy_freshness_policy
        }

    @property
    def auto_materialize_policies_by_key(
        self,
    ) -> Mapping[AssetKey, AutoMaterializePolicy]:
        return {
            key: spec.auto_materialize_policy
            for key, spec in self._specs_by_key.items()
            if spec.auto_materialize_policy
        }

    @property
    def automation_conditions_by_key(self) -> Mapping[AssetKey, AutomationCondition]:
        return {
            key: spec.automation_condition
            for key, spec in self._specs_by_key.items()
            if spec.automation_condition
        }

    @cached_method
    def get_upstream_input_keys(self, keys: frozenset[AssetKey]) -> AbstractSet[AssetKey]:
        """Returns keys that are directly upstream of the provided keys and are inputs of this asset."""
        direct_upstreams = {dep.asset_key for key in keys for dep in self._specs_by_key[key].deps}
        return direct_upstreams - set(self.node_keys_by_output_name.values())

    @cached_method
    def get_checks_targeting_keys(self, keys: frozenset[AssetKey]) -> AbstractSet[AssetCheckKey]:
        """Returns checks defined on this AssetsDefinition for the provided keys."""
        check_keys = {
            check_spec.key for check_spec in self.node_check_specs_by_output_name.values()
        }
        return {key for key in check_keys if key.asset_key in keys}

    # Applies only to external observable assets. Can be removed when we fold
    # `auto_observe_interval_minutes` into auto-materialize policies.
    @property
    def auto_observe_interval_minutes(self) -> Optional[float]:
        value = self._get_external_asset_metadata_value(
            SYSTEM_METADATA_KEY_AUTO_OBSERVE_INTERVAL_MINUTES
        )
        if not (value is None or isinstance(value, (int, float))):
            check.failed(
                f"Expected auto_observe_interval_minutes to be a number or None, not {value}"
            )
        return value

    # Applies to AssetsDefinition that were auto-created because some asset referenced a key as a
    # dependency, but no definition was provided for that key.
    @property
    def is_auto_created_stub(self) -> bool:
        return (
            self._get_external_asset_metadata_value(SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET)
            is not None
        )

    def _get_external_asset_metadata_value(self, metadata_key: str) -> object:
        first_key = next(iter(self.keys), None)
        if not first_key:
            return None
        return (self._specs_by_key[first_key].metadata or {}).get(metadata_key)

    @property
    def backfill_policy(self) -> Optional[BackfillPolicy]:
        return self._computation.backfill_policy if self._computation else None

    @public
    @cached_property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        """Optional[PartitionsDefinition]: The PartitionsDefinition for this AssetsDefinition (if any)."""
        partitions_defs = {
            spec.partitions_def for spec in self.specs if spec.partitions_def is not None
        }
        if len(partitions_defs) == 1:
            return next(iter(partitions_defs))
        elif len(partitions_defs) == 0:
            return None
        else:
            check.failed(
                "Different assets within this AssetsDefinition have different PartitionsDefinitions"
            )

    @property
    def metadata_by_key(self) -> Mapping[AssetKey, ArbitraryMetadataMapping]:
        return {
            key: spec.metadata
            for key, spec in self._specs_by_key.items()
            if spec.metadata is not None
        }

    @property
    def tags_by_key(self) -> Mapping[AssetKey, Mapping[str, str]]:
        return {key: spec.tags or {} for key, spec in self._specs_by_key.items()}

    @property
    def code_versions_by_key(self) -> Mapping[AssetKey, Optional[str]]:
        return {key: spec.code_version for key, spec in self._specs_by_key.items()}

    @property
    def owners_by_key(self) -> Mapping[AssetKey, Sequence[str]]:
        return {key: spec.owners or [] for key, spec in self._specs_by_key.items()}

    @public
    def get_partition_mapping(self, in_asset_key: AssetKey) -> Optional[PartitionMapping]:
        """Returns the partition mapping between keys in this AssetsDefinition and a given input
        asset key (if any).
        """
        return self._partition_mappings.get(in_asset_key)

    @public
    @property
    def check_specs(self) -> Iterable[AssetCheckSpec]:
        """Returns the asset check specs defined on this AssetsDefinition, i.e. the checks that can
        be executed while materializing the assets.

        Returns:
            Iterable[AssetsCheckSpec]:
        """
        return self.check_specs_by_output_name.values()

    @property
    def check_keys(self) -> AbstractSet[AssetCheckKey]:
        """Returns the selected asset checks associated by this AssetsDefinition.

        Returns:
            AbstractSet[Tuple[AssetKey, str]]: The selected asset checks. An asset check is
                identified by the asset key and the name of the check.
        """
        if self._computation:
            return self._computation.selected_asset_check_keys
        else:
            check.invariant(not self._check_specs_by_output_name)
            return set()

    @property
    def check_key(self) -> AssetCheckKey:
        check.invariant(
            len(self.check_keys) == 1,
            "Tried to retrieve asset check key from an assets definition with more or less than 1 asset check key: "
            + ", ".join([ak.to_user_string() for ak in self.check_keys]),
        )

        return next(iter(self.check_keys))

    @property
    def execution_type(self) -> AssetExecutionType:
        if self._computation is None:
            return AssetExecutionType.UNEXECUTABLE
        else:
            return self._computation.execution_type

    @property
    def is_external(self) -> bool:
        return self.execution_type != AssetExecutionType.MATERIALIZATION

    @property
    def is_observable(self) -> bool:
        return self.execution_type == AssetExecutionType.OBSERVATION

    @property
    def is_materializable(self) -> bool:
        return self.execution_type == AssetExecutionType.MATERIALIZATION

    @property
    def is_executable(self) -> bool:
        return self.execution_type != AssetExecutionType.UNEXECUTABLE

    def get_partition_mapping_for_dep(self, dep_key: AssetKey) -> Optional[PartitionMapping]:
        return self._partition_mappings.get(dep_key)

    def infer_partition_mapping(
        self,
        asset_key: AssetKey,
        upstream_asset_key: AssetKey,
        upstream_partitions_def: Optional[PartitionsDefinition],
    ) -> PartitionMapping:
        with disable_dagster_warnings():
            partition_mapping = self._partition_mappings.get(upstream_asset_key)
            return infer_partition_mapping(
                partition_mapping,
                self.specs_by_key[asset_key].partitions_def,
                upstream_partitions_def,
            )

    def has_output_for_asset_key(self, key: AssetKey) -> bool:
        return self._computation is not None and key in self._computation.output_names_by_key

    def get_output_name_for_asset_key(self, key: AssetKey) -> str:
        if (
            self._computation is None
            or key not in self._computation.output_names_by_key
            or key not in self.keys
        ):
            raise DagsterInvariantViolationError(
                f"Asset key {key.to_user_string()} not found in AssetsDefinition"
            )
        else:
            return self._computation.output_names_by_key[key]

    def get_output_name_for_asset_check_key(self, key: AssetCheckKey) -> str:
        for output_name, spec in self._check_specs_by_output_name.items():
            if key == spec.key:
                return output_name

        raise DagsterInvariantViolationError(
            f"Asset check key {key.to_user_string()} not found in AssetsDefinition"
        )

    def get_op_def_for_asset_key(self, key: AssetKey) -> Optional[OpDefinition]:
        """If this is an op-backed asset, returns the op def. If it's a graph-backed asset,
        returns the op def within the graph that produces the given asset key.
        """
        if self._computation is None:
            return None

        output_name = self.get_output_name_for_asset_key(key)
        return self.node_def.resolve_output_to_origin_op_def(output_name)

    def coerce_to_checks_def(self) -> "AssetChecksDefinition":
        from dagster._core.definitions.asset_checks.asset_checks_definition import (
            AssetChecksDefinition,
            has_only_asset_checks,
        )

        if not has_only_asset_checks(self):
            raise DagsterInvalidDefinitionError(
                "Cannot coerce an AssetsDefinition to an AssetChecksDefinition if it contains "
                "non-check assets."
            )
        if len(self.check_keys) == 0:
            raise DagsterInvalidDefinitionError(
                "Cannot coerce an AssetsDefinition to an AssetChecksDefinition if it contains no "
                "checks."
            )
        return AssetChecksDefinition.create(
            keys_by_input_name=self.keys_by_input_name,
            node_def=self.op,
            check_specs_by_output_name=self.check_specs_by_output_name,
            resource_defs=self.resource_defs,
            can_subset=self.can_subset,
        )

    def with_attributes(
        self,
        *,
        asset_key_replacements: Mapping[AssetKey, AssetKey] = {},
        group_names_by_key: Mapping[AssetKey, str] = {},
        tags_by_key: Mapping[AssetKey, Mapping[str, str]] = {},
        legacy_freshness_policy: Optional[
            Union[LegacyFreshnessPolicy, Mapping[AssetKey, LegacyFreshnessPolicy]]
        ] = None,
        automation_condition: Optional[
            Union[AutomationCondition, Mapping[AssetKey, AutomationCondition]]
        ] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
        metadata_by_key: Optional[
            Mapping[Union[AssetKey, AssetCheckKey], ArbitraryMetadataMapping]
        ] = None,
    ) -> "AssetsDefinition":
        conflicts_by_attr_name: dict[str, set[AssetKey]] = defaultdict(set)
        replaced_specs = []

        for key, spec in self._specs_by_key.items():
            replace_dict = {}

            def update_replace_dict_and_conflicts(
                new_value: Union[Mapping[AssetKey, object], object],
                attr_name: str,
                default_value: object = None,
            ) -> None:
                if isinstance(new_value, Mapping):
                    if key in new_value:
                        replace_dict[attr_name] = new_value[key]
                elif new_value:
                    replace_dict[attr_name] = new_value

                old_value = getattr(spec, attr_name)
                if old_value and old_value != default_value and attr_name in replace_dict:
                    conflicts_by_attr_name[attr_name].add(key)

            update_replace_dict_and_conflicts(
                new_value=automation_condition, attr_name="automation_condition"
            )
            update_replace_dict_and_conflicts(
                new_value=legacy_freshness_policy, attr_name="legacy_freshness_policy"
            )
            update_replace_dict_and_conflicts(new_value=tags_by_key, attr_name="tags")
            update_replace_dict_and_conflicts(
                new_value=group_names_by_key,
                attr_name="group_name",
                default_value=DEFAULT_GROUP_NAME,
            )

            if metadata_by_key and key in metadata_by_key:
                replace_dict["metadata"] = metadata_by_key[key]

            if key in asset_key_replacements:
                replace_dict["key"] = asset_key_replacements[key]

            if asset_key_replacements:
                new_deps = []
                for dep in spec.deps:
                    replacement_key = asset_key_replacements.get(dep.asset_key, dep.asset_key)
                    if replacement_key is not None:
                        new_deps.append(dep._replace(asset_key=replacement_key))
                    else:
                        new_deps.append(dep)

                replace_dict["deps"] = new_deps

            replaced_specs.append(replace(spec, **replace_dict))

        for attr_name, conflicting_asset_keys in conflicts_by_attr_name.items():
            raise DagsterInvalidDefinitionError(
                f"{attr_name} already exists on assets"
                f" {', '.join(asset_key.to_user_string() for asset_key in conflicting_asset_keys)}"
            )

        check_specs_by_output_name = {}
        for output_name, check_spec in self.node_check_specs_by_output_name.items():
            updated_check_spec = check_spec
            if check_spec.asset_key in asset_key_replacements:
                updated_check_spec = updated_check_spec.replace_key(
                    key=check_spec.key.replace_asset_key(
                        asset_key_replacements[check_spec.asset_key]
                    )
                )
            if metadata_by_key and check_spec.key in metadata_by_key:
                updated_check_spec = updated_check_spec.with_metadata(
                    metadata_by_key[check_spec.key]
                )

            check_specs_by_output_name[output_name] = updated_check_spec

        selected_asset_check_keys = {
            check_key.replace_asset_key(
                asset_key_replacements.get(check_key.asset_key, check_key.asset_key)
            )
            for check_key in self.check_keys
        }

        replaced_attributes = dict(
            keys_by_input_name={
                input_name: asset_key_replacements.get(key, key)
                for input_name, key in self.node_keys_by_input_name.items()
            },
            keys_by_output_name={
                output_name: asset_key_replacements.get(key, key)
                for output_name, key in self.node_keys_by_output_name.items()
            },
            selected_asset_keys={asset_key_replacements.get(key, key) for key in self.keys},
            backfill_policy=backfill_policy if backfill_policy else self.backfill_policy,
            is_subset=self.is_subset,
            check_specs_by_output_name=check_specs_by_output_name,
            selected_asset_check_keys=selected_asset_check_keys,
            specs=replaced_specs,
            hook_defs=hook_defs if hook_defs else self.hook_defs,
        )

        merged_attrs = merge_dicts(self.get_attributes_dict(), replaced_attributes)
        return self.__class__.dagster_internal_init(**merged_attrs)

    def map_asset_specs(self, fn: Callable[[AssetSpec], AssetSpec]) -> "AssetsDefinition":
        mapped_specs = []
        for spec in self.specs:
            mapped_spec = fn(spec)
            if mapped_spec.key != spec.key:
                raise DagsterInvalidDefinitionError(
                    f"Asset key {spec.key.to_user_string()} was changed to "
                    f"{mapped_spec.key.to_user_string()}. Mapping function must not change keys."
                )

            mapped_specs.append(mapped_spec)

        return replace_specs_on_asset(self, mapped_specs)

    def subset_for(
        self,
        selected_asset_keys: AbstractSet[AssetKey],
        selected_asset_check_keys: Optional[AbstractSet[AssetCheckKey]],
    ) -> "AssetsDefinition":
        """Create a subset of this AssetsDefinition that will only materialize the assets and checks
        in the selected set.

        Args:
            selected_asset_keys (AbstractSet[AssetKey]): The total set of asset keys
            selected_asset_check_keys (AbstractSet[AssetCheckKey]): The selected asset checks
        """
        subsetted_computation = check.not_none(self._computation).subset_for(
            selected_asset_keys, selected_asset_check_keys
        )
        return self.__class__.dagster_internal_init(
            **{
                **self.get_attributes_dict(),
                "node_def": subsetted_computation.node_def,
                "selected_asset_keys": subsetted_computation.selected_asset_keys,
                "selected_asset_check_keys": subsetted_computation.selected_asset_check_keys,
                "is_subset": True,
            }
        )

    @property
    def is_subset(self) -> bool:
        return self._computation.is_subset if self._computation else False

    @public
    def to_source_assets(self) -> Sequence[SourceAsset]:
        """Returns a SourceAsset for each asset in this definition.

        Each produced SourceAsset will have the same key, metadata, io_manager_key, etc. as the
        corresponding asset
        """
        return [
            self._output_to_source_asset(output_name)
            for output_name in self.keys_by_output_name.keys()
        ]

    @public
    def to_source_asset(self, key: Optional[CoercibleToAssetKey] = None) -> SourceAsset:
        """Returns a representation of this asset as a :py:class:`SourceAsset`.

        If this is a multi-asset, the "key" argument allows selecting which asset to return a
        SourceAsset representation of.

        Args:
            key (Optional[Union[str, Sequence[str], AssetKey]]]): If this is a multi-asset, select
                which asset to return a SourceAsset representation of. If not a multi-asset, this
                can be left as None.

        Returns:
            SourceAsset
        """
        if len(self.keys) > 1:
            check.invariant(
                key is not None,
                "The 'key' argument is required when there are multiple assets to choose from",
            )

        if key is not None:
            resolved_key = AssetKey.from_coercible(key)
            check.invariant(
                resolved_key in self.keys,
                f"Key {resolved_key} not found in AssetsDefinition",
            )
        else:
            resolved_key = self.key

        output_names = [
            output_name
            for output_name, ak in self.keys_by_output_name.items()
            if ak == resolved_key
        ]
        check.invariant(len(output_names) == 1)
        return self._output_to_source_asset(output_names[0])

    def _output_to_source_asset(self, output_name: str) -> SourceAsset:
        with disable_dagster_warnings():
            output_def = self.node_def.resolve_output_to_origin(
                output_name, NodeHandle(self.node_def.name, parent=None)
            )[0]
            key = self.node_keys_by_output_name[output_name]
            spec = self.specs_by_key[key]

            return SourceAsset.dagster_internal_init(
                key=key,
                metadata=spec.metadata,
                io_manager_key=output_def.io_manager_key,
                description=spec.description,
                resource_defs=self.resource_defs,
                partitions_def=spec.partitions_def,
                group_name=spec.group_name,
                tags=spec.tags,
                io_manager_def=None,
                observe_fn=None,
                op_tags=None,
                automation_condition=None,
                auto_observe_interval_minutes=None,
                legacy_freshness_policy=None,
                _required_resource_keys=None,
            )

    @public
    def get_asset_spec(self, key: Optional[AssetKey] = None) -> AssetSpec:
        """Returns a representation of this asset as an :py:class:`AssetSpec`.

        If this is a multi-asset, the "key" argument allows selecting which asset to return the
        spec for.

        Args:
            key (Optional[AssetKey]): If this is a multi-asset, select which asset to return its
                AssetSpec. If not a multi-asset, this can be left as None.

        Returns:
            AssetSpec
        """
        return self._specs_by_key[key or self.key]

    def get_io_manager_key_for_asset_key(self, key: AssetKey) -> str:
        if self._computation is None:
            return self._specs_by_key[key].metadata.get(
                SYSTEM_METADATA_KEY_IO_MANAGER_KEY, DEFAULT_IO_MANAGER_KEY
            )
        else:
            if SYSTEM_METADATA_KEY_IO_MANAGER_KEY in self._specs_by_key[key].metadata:
                return self._specs_by_key[key].metadata[SYSTEM_METADATA_KEY_IO_MANAGER_KEY]
            check.invariant(
                SYSTEM_METADATA_KEY_IO_MANAGER_KEY not in self._specs_by_key[key].metadata
            )

            output_name = self.get_output_name_for_asset_key(key)
            return self.node_def.resolve_output_to_origin(
                output_name, NodeHandle(self.node_def.name, parent=None)
            )[0].io_manager_key

    def get_resource_requirements(self) -> Iterator[ResourceRequirement]:
        from itertools import chain

        from dagster._core.definitions.graph_definition import GraphDefinition

        if self.is_executable:
            if isinstance(self.node_def, GraphDefinition):
                yield from chain(
                    self.node_def.get_resource_requirements(
                        asset_layer=None,
                    ),
                    (
                        req
                        for hook_def in self._hook_defs
                        for req in hook_def.get_resource_requirements(
                            attached_to=f"asset '{self.node_def.name}'",
                        )
                    ),
                )
            elif isinstance(self.node_def, OpDefinition):
                yield from chain(
                    self.node_def.get_resource_requirements(
                        handle=None,
                        asset_layer=None,
                    ),
                    (
                        req
                        for hook_def in self._hook_defs
                        for req in hook_def.get_resource_requirements(
                            attached_to=f"asset '{self.node_def.name}'",
                        )
                    ),
                )

        else:
            for key in self.keys:
                # This matches how SourceAsset emit requirements except we emit
                # ExternalAssetIOManagerRequirement instead of SourceAssetIOManagerRequirement
                yield ExternalAssetIOManagerRequirement(
                    key=self.get_io_manager_key_for_asset_key(key),
                    asset_key=key.to_string(),
                )
        for source_key, resource_def in self.resource_defs.items():
            yield from resource_def.get_resource_requirements(source_key=source_key)

    @public
    @property
    def required_resource_keys(self) -> set[str]:
        """Set[str]: The set of keys for resources that must be provided to this AssetsDefinition."""
        return {
            requirement.key
            for requirement in self.get_resource_requirements()
            if requirement
            if isinstance(requirement, ResourceKeyRequirement)
        }

    def __str__(self):
        if len(self.keys) == 1:
            return f"AssetsDefinition with key {self.key.to_string()}"
        else:
            asset_keys = ", ".join(sorted([asset_key.to_string() for asset_key in self.keys]))
            return f"AssetsDefinition with keys {asset_keys}"

    @cached_property
    def unique_id(self) -> str:
        return unique_id_from_asset_and_check_keys(itertools.chain(self.keys, self.check_keys))

    def with_resources(self, resource_defs: Mapping[str, ResourceDefinition]) -> "AssetsDefinition":
        attributes_dict = self.get_attributes_dict()
        attributes_dict["resource_defs"] = merge_resource_defs(
            old_resource_defs=self.resource_defs,
            resource_defs_to_merge_in=resource_defs,
            requires_resources=self,
        )
        with disable_dagster_warnings():
            return self.__class__(**attributes_dict)

    @public
    def with_hooks(self, hook_defs: AbstractSet[HookDefinition]) -> "AssetsDefinition":
        """Apply a set of hooks to all op instances within the asset."""
        from dagster._core.definitions.hook_definition import HookDefinition

        hook_defs = check.set_param(hook_defs, "hook_defs", of_type=HookDefinition)
        return self.with_attributes(hook_defs=(hook_defs | self.hook_defs))

    def get_attributes_dict(self) -> dict[str, Any]:
        return dict(
            keys_by_input_name=self.node_keys_by_input_name,
            keys_by_output_name=self.node_keys_by_output_name,
            node_def=self._computation.node_def if self._computation else None,
            selected_asset_keys=self.keys,
            can_subset=self.can_subset,
            resource_defs=self._resource_defs,
            hook_defs=self._hook_defs,
            backfill_policy=self.backfill_policy,
            check_specs_by_output_name=self._check_specs_by_output_name,
            selected_asset_check_keys=self.check_keys,
            specs=self.specs,
            is_subset=self.is_subset,
            execution_type=self._computation.execution_type if self._computation else None,
        )


def _infer_keys_by_input_names(
    node_def: NodeDefinition, keys_by_input_name: Mapping[str, AssetKey]
) -> Mapping[str, AssetKey]:
    all_input_names = [input_def.name for input_def in node_def.input_defs]
    if keys_by_input_name:
        check.invariant(
            set(keys_by_input_name.keys()) == set(all_input_names),
            "The set of input names keys specified in the keys_by_input_name argument must "
            f"equal the set of asset keys inputted by '{node_def.name}'. \n"
            f"keys_by_input_name keys: {set(keys_by_input_name.keys())} \n"
            f"expected keys: {all_input_names}",
        )

    # If asset key is not supplied in keys_by_input_name, create asset key
    # from input name
    inferred_input_names_by_asset_key: dict[str, AssetKey] = {
        input_name: keys_by_input_name.get(input_name, AssetKey([input_name]))
        for input_name in all_input_names
    }

    return inferred_input_names_by_asset_key


def _infer_keys_by_output_names(
    node_def: NodeDefinition,
    keys_by_output_name: Mapping[str, AssetKey],
    check_specs_by_output_name: Mapping[str, AssetCheckSpec],
) -> Mapping[str, AssetKey]:
    output_names = [output_def.name for output_def in node_def.output_defs]
    if keys_by_output_name:
        overlapping_asset_and_check_outputs = set(keys_by_output_name.keys()) & set(
            check_specs_by_output_name.keys()
        )
        check.invariant(
            not overlapping_asset_and_check_outputs,
            "The set of output names associated with asset keys and checks overlap:"
            f" {overlapping_asset_and_check_outputs}",
        )

        union_asset_and_check_outputs = set(keys_by_output_name.keys()) | set(
            check_specs_by_output_name.keys()
        )
        check.invariant(
            union_asset_and_check_outputs == set(output_names),
            "The union of the set of output names keys specified in the keys_by_output_name and"
            " check_specs_by_output_name arguments must equal the set of asset keys outputted by"
            f" {node_def.name}. union keys:"
            f" {union_asset_and_check_outputs} \nexpected keys: {set(output_names)}",
        )

    inferred_keys_by_output_names: dict[str, AssetKey] = {
        output_name: asset_key for output_name, asset_key in keys_by_output_name.items()
    }

    if (
        len(output_names) == 1
        and output_names[0] not in keys_by_output_name
        and output_names[0] not in check_specs_by_output_name
        and output_names[0] == "result"
    ):
        # If there is only one output and the name is the default "result", generate asset key
        # from the name of the node
        inferred_keys_by_output_names[output_names[0]] = AssetKey([node_def.name])

    for output_name in output_names:
        if (
            output_name not in inferred_keys_by_output_names
            and output_name not in check_specs_by_output_name
        ):
            inferred_keys_by_output_names[output_name] = AssetKey([output_name])
    return inferred_keys_by_output_names


def _validate_graph_def(graph_def: "GraphDefinition", prefix: Optional[Sequence[str]] = None):
    """Ensure that all leaf nodes are mapped to graph outputs."""
    from dagster._core.definitions.graph_definition import GraphDefinition, create_adjacency_lists

    prefix = check.opt_sequence_param(prefix, "prefix")

    # recursively validate any sub-graphs
    for inner_node_def in graph_def.node_defs:
        if isinstance(inner_node_def, GraphDefinition):
            _validate_graph_def(inner_node_def, prefix=[*prefix, graph_def.name])

    # leaf nodes have no downstream nodes
    forward_edges, _ = create_adjacency_lists(graph_def.nodes, graph_def.dependency_structure)
    leaf_nodes = {
        node_name for node_name, downstream_nodes in forward_edges.items() if not downstream_nodes
    }

    # set of nodes that have outputs mapped to a graph output
    mapped_output_nodes = {
        output_mapping.maps_from.node_name for output_mapping in graph_def.output_mappings
    }

    # leaf nodes which do not have an associated mapped output
    unmapped_leaf_nodes = {".".join([*prefix, node]) for node in leaf_nodes - mapped_output_nodes}

    check.invariant(
        not unmapped_leaf_nodes,
        f"All leaf nodes within graph '{graph_def.name}' must generate outputs which are mapped"
        " to outputs of the graph, and produce assets. The following leaf node(s) are"
        f" non-asset producing ops: {unmapped_leaf_nodes}. This behavior is not currently"
        " supported because these ops are not required for the creation of the associated"
        " asset(s).",
    )


def _resolve_automation_conditions_by_output_name(
    automation_conditions_by_output_name: Optional[Mapping[str, Optional[AutomationCondition]]],
    auto_materialize_policies_by_output_name: Optional[
        Mapping[str, Optional[AutoMaterializePolicy]]
    ],
) -> Optional[Mapping[str, Optional[AutomationCondition]]]:
    if auto_materialize_policies_by_output_name is not None:
        check.param_invariant(
            automation_conditions_by_output_name is None,
            "automation_conditions_by_output_name",
            "Cannot supply both `automation_conditions_by_output_name` and `auto_materialize_policies_by_output_name`",
        )
        return {
            k: v.to_automation_condition() if v else None
            for k, v in auto_materialize_policies_by_output_name.items()
        }
    else:
        return automation_conditions_by_output_name


def _resolve_selections(
    all_asset_keys: AbstractSet[AssetKey],
    all_check_keys: AbstractSet[AssetCheckKey],
    selected_asset_keys: Optional[AbstractSet[AssetKey]],
    selected_asset_check_keys: Optional[AbstractSet[AssetCheckKey]],
) -> tuple[AbstractSet[AssetKey], AbstractSet[AssetCheckKey]]:
    # NOTE: this logic mirrors subsetting at the asset layer. This is ripe for consolidation.
    if selected_asset_keys is None and selected_asset_check_keys is None:
        # if no selections, include everything
        return all_asset_keys, all_check_keys
    else:
        resolved_selected_asset_keys = selected_asset_keys or set()

        if selected_asset_check_keys is None:
            # if assets were selected but checks are None, then include all checks for selected
            # assets
            resolved_selected_asset_check_keys = {
                key for key in all_check_keys if key.asset_key in resolved_selected_asset_keys
            }
        else:
            # otherwise, use the selected checks
            resolved_selected_asset_check_keys = selected_asset_check_keys

        return resolved_selected_asset_keys, resolved_selected_asset_check_keys


def _validate_partition_mappings(
    partition_mappings: Mapping[AssetKey, PartitionMapping],
    input_asset_keys: AbstractSet[AssetKey],
    all_asset_keys: AbstractSet[AssetKey],
) -> None:
    for asset_key, partition_mapping in partition_mappings.items():
        warn_if_partition_mapping_not_builtin(partition_mapping)

        if asset_key not in input_asset_keys:
            check.failed(
                f"While constructing AssetsDefinition outputting {all_asset_keys}, received a"
                f" partition mapping for {asset_key} that is not defined in the set of upstream"
                f" assets: {input_asset_keys}"
            )


def _asset_specs_from_attr_key_params(
    all_asset_keys: AbstractSet[AssetKey],
    keys_by_input_name: Mapping[str, AssetKey],
    deps_by_asset_key: Optional[Mapping[AssetKey, AbstractSet[AssetKey]]],
    partition_mappings: Optional[Mapping[AssetKey, PartitionMapping]],
    group_names_by_key: Optional[Mapping[AssetKey, str]],
    metadata_by_key: Optional[Mapping[AssetKey, ArbitraryMetadataMapping]],
    tags_by_key: Optional[Mapping[AssetKey, Mapping[str, str]]],
    legacy_freshness_policies_by_key: Optional[Mapping[AssetKey, LegacyFreshnessPolicy]],
    automation_conditions_by_key: Optional[Mapping[AssetKey, AutomationCondition]],
    code_versions_by_key: Optional[Mapping[AssetKey, str]],
    descriptions_by_key: Optional[Mapping[AssetKey, str]],
    owners_by_key: Optional[Mapping[AssetKey, Sequence[str]]],
    partitions_def: Optional[PartitionsDefinition],
) -> Sequence[AssetSpec]:
    validated_group_names_by_key = check.opt_mapping_param(
        group_names_by_key, "group_names_by_key", key_type=AssetKey, value_type=str
    )

    validated_metadata_by_key = check.opt_mapping_param(
        metadata_by_key, "metadata_by_key", key_type=AssetKey, value_type=dict
    )

    for tags in (tags_by_key or {}).values():
        normalize_tags(tags, strict=True)
    validated_tags_by_key = tags_by_key or {}

    validated_descriptions_by_key = check.opt_mapping_param(
        descriptions_by_key, "descriptions_by_key", key_type=AssetKey, value_type=str
    )

    validated_code_versions_by_key = check.opt_mapping_param(
        code_versions_by_key, "code_versions_by_key", key_type=AssetKey, value_type=str
    )

    validated_legacy_freshness_policies_by_key = check.opt_mapping_param(
        legacy_freshness_policies_by_key,
        "legacy_freshness_policies_by_key",
        key_type=AssetKey,
        value_type=LegacyFreshnessPolicy,
    )

    validated_automation_conditions_by_key = check.opt_mapping_param(
        automation_conditions_by_key,
        "automation_conditions_by_key",
        key_type=AssetKey,
        value_type=AutomationCondition,
    )

    validated_owners_by_key = check.opt_mapping_param(
        owners_by_key, "owners_by_key", key_type=AssetKey, value_type=list
    )

    dep_keys_from_keys_by_input_name = set(keys_by_input_name.values())
    dep_objs_from_keys_by_input_name = [
        AssetDep(asset=key, partition_mapping=(partition_mappings or {}).get(key))
        for key in dep_keys_from_keys_by_input_name
    ]

    result: list[AssetSpec] = []
    for key in all_asset_keys:
        if deps_by_asset_key:
            dep_objs = [
                AssetDep(asset=key, partition_mapping=(partition_mappings or {}).get(key))
                for key in deps_by_asset_key.get(key, [])
            ]
        else:
            dep_objs = dep_objs_from_keys_by_input_name

        with disable_dagster_warnings():
            result.append(
                AssetSpec.dagster_internal_init(
                    key=key,
                    description=validated_descriptions_by_key.get(key),
                    metadata=validated_metadata_by_key.get(key),
                    tags=validated_tags_by_key.get(key),
                    legacy_freshness_policy=validated_legacy_freshness_policies_by_key.get(key),
                    automation_condition=validated_automation_conditions_by_key.get(key),
                    owners=validated_owners_by_key.get(key),
                    group_name=validated_group_names_by_key.get(key),
                    code_version=validated_code_versions_by_key.get(key),
                    deps=dep_objs,
                    # Value here is irrelevant, because it will be replaced by value from
                    # NodeDefinition
                    skippable=False,
                    auto_materialize_policy=None,
                    kinds=None,
                    partitions_def=check.opt_inst_param(
                        partitions_def, "partitions_def", PartitionsDefinition
                    ),
                )
            )

    return result


def _validate_self_deps(specs: Iterable[AssetSpec]) -> None:
    for spec in specs:
        for dep in spec.deps:
            if dep.asset_key != spec.key:
                continue
            if dep.partition_mapping:
                time_window_partition_mapping = get_self_dep_time_window_partition_mapping(
                    dep.partition_mapping, spec.partitions_def
                )
                if (
                    time_window_partition_mapping is not None
                    and (time_window_partition_mapping.start_offset or 0) < 0
                    and (time_window_partition_mapping.end_offset or 0) < 0
                ):
                    continue

            raise DagsterInvalidDefinitionError(
                f'Asset "{spec.key.to_user_string()}" depends on itself. Assets can only depend'
                " on themselves if they are:\n(a) time-partitioned and each partition depends on"
                " earlier partitions\n(b) multipartitioned, with one time dimension that depends"
                " on earlier time partitions"
            )


def get_self_dep_time_window_partition_mapping(
    partition_mapping: Optional[PartitionMapping],
    partitions_def: Optional[PartitionsDefinition],
) -> Optional[TimeWindowPartitionMapping]:
    """Returns a time window partition mapping dimension of the provided partition mapping,
    if exists.
    """
    if isinstance(partition_mapping, TimeWindowPartitionMapping):
        return partition_mapping
    elif isinstance(partition_mapping, MultiPartitionMapping):
        if not isinstance(partitions_def, MultiPartitionsDefinition):
            return None

        time_partition_mapping = partition_mapping.downstream_mappings_by_upstream_dimension.get(
            partitions_def.time_window_dimension.name
        )

        if time_partition_mapping is None or not isinstance(
            time_partition_mapping.partition_mapping, TimeWindowPartitionMapping
        ):
            return None

        return time_partition_mapping.partition_mapping
    return None


def get_partition_mappings_from_deps(
    partition_mappings: dict[AssetKey, PartitionMapping],
    deps: Iterable[AssetDep],
    asset_name: str,
) -> Mapping[AssetKey, PartitionMapping]:
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


def unique_id_from_asset_and_check_keys(entity_keys: Iterable["EntityKey"]) -> str:
    """Generate a unique ID from the provided asset keys.

    This is useful for generating op names that don't have collisions.
    """
    sorted_key_strs = sorted(str(key) for key in entity_keys)
    return non_secure_md5_hash_str(json.dumps(sorted_key_strs).encode("utf-8"))[:8]


def replace_specs_on_asset(
    assets_def: AssetsDefinition, replaced_specs: Sequence[AssetSpec]
) -> "AssetsDefinition":
    from dagster._builtins import Nothing
    from dagster._core.definitions.input import In

    new_deps_by_key = {dep.asset_key: dep for spec in replaced_specs for dep in spec.deps}
    previous_deps_by_key = {dep.asset_key: dep for spec in assets_def.specs for dep in spec.deps}
    added_dep_keys = set(new_deps_by_key.keys()) - set(previous_deps_by_key.keys())
    removed_dep_keys = set(previous_deps_by_key.keys()) - set(new_deps_by_key.keys())
    remaining_original_deps_by_key = {
        key: previous_deps_by_key[key]
        for key in set(previous_deps_by_key.keys()) - removed_dep_keys
    }
    original_key_to_input_mapping = reverse_dict(assets_def.node_keys_by_input_name)

    # If there are no changes to the dependency structure, we don't need to make any changes to the underlying node.
    if not assets_def.is_executable or (not added_dep_keys and not removed_dep_keys):
        return assets_def.__class__.dagster_internal_init(
            **{**assets_def.get_attributes_dict(), "specs": replaced_specs}
        )

    # Otherwise, there are changes to the dependency structure. We need to update the node_def.
    # Graph-backed assets do not currently support non-argument-based deps. Every argument to a graph-backed asset
    # must map to an an input on an internal asset node in the graph structure.
    # IMPROVEME BUILD-529
    check.invariant(
        isinstance(assets_def.node_def, OpDefinition),
        "Can only add additional deps to an op-backed asset.",
    )
    # for each deleted dep, we need to make sure it is not an argument-based dep. Argument-based deps cannot be removed.
    for dep_key in removed_dep_keys:
        dep = previous_deps_by_key[dep_key]
        input_name = original_key_to_input_mapping[dep.asset_key]
        input_def = assets_def.node_def.input_def_named(input_name)
        check.invariant(
            input_def.dagster_type.is_nothing,
            f"Attempted to remove argument-backed dependency {dep.asset_key} (mapped to argument {input_name}) from the asset. Only non-argument dependencies can be changed or removed using map_asset_specs.",
        )

    remaining_ins = {
        input_name: the_in
        for input_name, the_in in assets_def.node_def.input_dict.items()
        if assets_def.node_keys_by_input_name[input_name] in remaining_original_deps_by_key
    }
    all_ins = merge_dicts(
        remaining_ins,
        {
            stringify_asset_key_to_input_name(dep.asset_key): In(dagster_type=Nothing)
            for dep in new_deps_by_key.values()
        },
    )

    return assets_def.__class__.dagster_internal_init(
        **{
            **assets_def.get_attributes_dict(),
            "node_def": assets_def.op.with_replaced_properties(
                name=assets_def.op.name, ins=all_ins
            ),
            "specs": replaced_specs,
        }
    )
