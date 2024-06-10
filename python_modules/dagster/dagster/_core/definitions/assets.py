import json
import warnings
from collections import defaultdict
from functools import cached_property
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import dagster._check as check
from dagster._annotations import experimental_param, public
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSpec
from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_layer import get_dep_node_handles_of_graph_backed_asset
from dagster._core.definitions.asset_spec import (
    SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE,
    SYSTEM_METADATA_KEY_AUTO_CREATED_STUB_ASSET,
    SYSTEM_METADATA_KEY_AUTO_OBSERVE_INTERVAL_MINUTES,
    AssetExecutionType,
)
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy, BackfillPolicyType
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.graph_definition import SubselectedGraphDefinition
from dagster._core.definitions.metadata import ArbitraryMetadataMapping
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.op_invocation import direct_invocation_result
from dagster._core.definitions.op_selection import get_graph_subset
from dagster._core.definitions.partition_mapping import MultiPartitionMapping
from dagster._core.definitions.resource_requirement import (
    ExternalAssetIOManagerRequirement,
    RequiresResources,
    ResourceAddable,
    ResourceRequirement,
    merge_resource_defs,
)
from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._core.definitions.utils import normalize_group_name, validate_asset_owner
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
)
from dagster._utils import IHasInternalInit
from dagster._utils.merger import merge_dicts
from dagster._utils.security import non_secure_md5_hash_str
from dagster._utils.warnings import ExperimentalWarning, disable_dagster_warnings

from .asset_spec import AssetSpec
from .dependency import NodeHandle
from .events import AssetKey, CoercibleToAssetKey, CoercibleToAssetKeyPrefix
from .node_definition import NodeDefinition
from .op_definition import OpDefinition
from .partition import PartitionsDefinition
from .partition_mapping import (
    PartitionMapping,
    infer_partition_mapping,
    warn_if_partition_mapping_not_builtin,
)
from .resource_definition import ResourceDefinition
from .source_asset import SourceAsset
from .utils import DEFAULT_GROUP_NAME, validate_tags_strict

if TYPE_CHECKING:
    from .base_asset_graph import AssetKeyOrCheckKey
    from .graph_definition import GraphDefinition

ASSET_SUBSET_INPUT_PREFIX = "__subset_input__"


class AssetsDefinition(ResourceAddable, RequiresResources, IHasInternalInit):
    """Defines a set of assets that are produced by the same op or graph.

    AssetsDefinitions are typically not instantiated directly, but rather produced using the
    :py:func:`@asset <asset>` or :py:func:`@multi_asset <multi_asset>` decorators.
    """

    # Constructor arguments that are redundant with the specs argument
    _dagster_internal_init_excluded_args = {
        "group_names_by_key",
        "metadata_by_key",
        "tags_by_key",
        "freshness_policies_by_key",
        "auto_materialize_policies_by_key",
        "partition_mappings",
        "descriptions_by_key",
        "asset_deps",
        "owners_by_key",
    }

    _node_def: NodeDefinition
    _keys_by_input_name: Mapping[str, AssetKey]
    _keys_by_output_name: Mapping[str, AssetKey]
    _partitions_def: Optional[PartitionsDefinition]
    # partition mappings are also tracked inside the AssetSpecs, but this enables faster access by
    # upstream asset key
    _partition_mappings: Mapping[AssetKey, PartitionMapping]
    _resource_defs: Mapping[str, ResourceDefinition]
    _selected_asset_keys: AbstractSet[AssetKey]
    _can_subset: bool
    _backfill_policy: Optional[BackfillPolicy]
    _selected_asset_check_keys: AbstractSet[AssetCheckKey]
    _is_subset: bool

    _specs_by_key: Mapping[AssetKey, AssetSpec]

    @experimental_param(param="specs")
    def __init__(
        self,
        *,
        keys_by_input_name: Mapping[str, AssetKey],
        keys_by_output_name: Mapping[str, AssetKey],
        node_def: NodeDefinition,
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_mappings: Optional[Mapping[AssetKey, PartitionMapping]] = None,
        asset_deps: Optional[Mapping[AssetKey, AbstractSet[AssetKey]]] = None,
        selected_asset_keys: Optional[AbstractSet[AssetKey]] = None,
        can_subset: bool = False,
        resource_defs: Optional[Mapping[str, object]] = None,
        group_names_by_key: Optional[Mapping[AssetKey, str]] = None,
        metadata_by_key: Optional[Mapping[AssetKey, ArbitraryMetadataMapping]] = None,
        tags_by_key: Optional[Mapping[AssetKey, Mapping[str, str]]] = None,
        freshness_policies_by_key: Optional[Mapping[AssetKey, FreshnessPolicy]] = None,
        auto_materialize_policies_by_key: Optional[Mapping[AssetKey, AutoMaterializePolicy]] = None,
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
        # if adding new fields, make sure to handle them in the with_attributes, from_graph,
        # from_op, and get_attributes_dict methods
    ):
        from dagster._core.execution.build_resources import wrap_resources_for_execution

        from .graph_definition import GraphDefinition

        if isinstance(node_def, GraphDefinition):
            _validate_graph_def(node_def)

        self._node_def = node_def
        self._keys_by_input_name = check.mapping_param(
            keys_by_input_name,
            "keys_by_input_name",
            key_type=str,
            value_type=AssetKey,
        )
        self._keys_by_output_name = check.mapping_param(
            keys_by_output_name,
            "keys_by_output_name",
            key_type=str,
            value_type=AssetKey,
        )

        self._check_specs_by_output_name = check.opt_mapping_param(
            check_specs_by_output_name,
            "check_specs_by_output_name",
            key_type=str,
            value_type=AssetCheckSpec,
        )

        self._partitions_def = partitions_def

        self._resource_defs = wrap_resources_for_execution(
            check.opt_mapping_param(resource_defs, "resource_defs")
        )

        self._can_subset = can_subset

        self._backfill_policy = check.opt_inst_param(
            backfill_policy, "backfill_policy", BackfillPolicy
        )

        if self._partitions_def is None:
            # check if backfill policy is BackfillPolicyType.SINGLE_RUN if asset is not partitioned
            check.param_invariant(
                (
                    backfill_policy.policy_type is BackfillPolicyType.SINGLE_RUN
                    if backfill_policy
                    else True
                ),
                "backfill_policy",
                "Non partitioned asset can only have single run backfill policy",
            )

        self._is_subset = check.bool_param(is_subset, "is_subset")

        if specs is not None:
            check.invariant(group_names_by_key is None)
            check.invariant(metadata_by_key is None)
            check.invariant(tags_by_key is None)
            check.invariant(freshness_policies_by_key is None)
            check.invariant(auto_materialize_policies_by_key is None)
            check.invariant(descriptions_by_key is None)
            check.invariant(owners_by_key is None)
            check.invariant(partition_mappings is None)
            check.invariant(asset_deps is None)
            resolved_specs = specs

        else:
            all_asset_keys = set(keys_by_output_name.values())

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
                    input_asset_keys=set(keys_by_input_name.values()),
                    all_asset_keys=all_asset_keys,
                )

            resolved_specs = _asset_specs_from_attr_key_params(
                all_asset_keys=all_asset_keys,
                keys_by_input_name=keys_by_input_name,
                deps_by_asset_key=asset_deps,
                partition_mappings=partition_mappings,
                tags_by_key=tags_by_key,
                owners_by_key=owners_by_key,
                group_names_by_key=group_names_by_key,
                freshness_policies_by_key=freshness_policies_by_key,
                auto_materialize_policies_by_key=auto_materialize_policies_by_key,
                metadata_by_key=metadata_by_key,
                descriptions_by_key=descriptions_by_key,
                code_versions_by_key=None,
            )

        normalized_specs: List[AssetSpec] = []
        output_names_by_key = {key: name for name, key in keys_by_output_name.items()}

        for spec in resolved_specs:
            if spec.owners:
                for owner in spec.owners:
                    validate_asset_owner(owner, spec.key)

            group_name = normalize_group_name(spec.group_name)

            output_def, _ = node_def.resolve_output_to_origin(output_names_by_key[spec.key], None)
            metadata = {**output_def.metadata, **(spec.metadata or {})}
            # We construct description from three sources of truth here. This
            # highly unfortunate. See commentary in @multi_asset's call to dagster_internal_init.
            description = spec.description or output_def.description or node_def.description
            code_version = spec.code_version or output_def.code_version
            skippable = not output_def.is_required

            check.invariant(
                not (
                    spec.freshness_policy
                    and self._partitions_def is not None
                    and not isinstance(self._partitions_def, TimeWindowPartitionsDefinition)
                ),
                "FreshnessPolicies are currently unsupported for assets with partitions of type"
                f" {type(self._partitions_def)}.",
            )

            normalized_specs.append(
                spec._replace(
                    group_name=group_name,
                    code_version=code_version,
                    metadata=metadata,
                    description=description,
                    skippable=skippable,
                )
            )

        self._specs_by_key = {spec.key: spec for spec in normalized_specs}

        self._partition_mappings = get_partition_mappings_from_deps(
            {}, [dep for spec in normalized_specs for dep in spec.deps], node_def.name
        )
        self._selected_asset_keys, self._selected_asset_check_keys = _resolve_selections(
            all_asset_keys=self._specs_by_key.keys(),
            all_check_keys={spec.key for spec in (check_specs_by_output_name or {}).values()},
            selected_asset_keys=selected_asset_keys,
            selected_asset_check_keys=selected_asset_check_keys,
        )

        self._check_specs_by_key = {
            spec.key: spec
            for spec in self._check_specs_by_output_name.values()
            if spec.key in self._selected_asset_check_keys
        }

        _validate_self_deps(
            input_keys=[
                key
                # filter out the special inputs which are used for cases when a multi-asset is
                # subsetted, as these are not the same as self-dependencies and are never loaded
                # in the same step that their corresponding output is produced
                for input_name, key in self._keys_by_input_name.items()
                if not input_name.startswith(ASSET_SUBSET_INPUT_PREFIX)
            ],
            output_keys=self._selected_asset_keys,
            partition_mappings=self._partition_mappings,
            partitions_def=self._partitions_def,
        )

    def dagster_internal_init(
        *,
        keys_by_input_name: Mapping[str, AssetKey],
        keys_by_output_name: Mapping[str, AssetKey],
        node_def: NodeDefinition,
        partitions_def: Optional[PartitionsDefinition],
        selected_asset_keys: Optional[AbstractSet[AssetKey]],
        can_subset: bool,
        resource_defs: Optional[Mapping[str, object]],
        backfill_policy: Optional[BackfillPolicy],
        check_specs_by_output_name: Optional[Mapping[str, AssetCheckSpec]],
        selected_asset_check_keys: Optional[AbstractSet[AssetCheckKey]],
        is_subset: bool,
        specs: Optional[Sequence[AssetSpec]],
    ) -> "AssetsDefinition":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)
            return AssetsDefinition(
                keys_by_input_name=keys_by_input_name,
                keys_by_output_name=keys_by_output_name,
                node_def=node_def,
                partitions_def=partitions_def,
                selected_asset_keys=selected_asset_keys,
                can_subset=can_subset,
                resource_defs=resource_defs,
                backfill_policy=backfill_policy,
                check_specs_by_output_name=check_specs_by_output_name,
                selected_asset_check_keys=selected_asset_check_keys,
                is_subset=is_subset,
                specs=specs,
            )

    def __call__(self, *args: object, **kwargs: object) -> object:
        from .composition import is_in_composition
        from .graph_definition import GraphDefinition

        # defer to GraphDefinition.__call__ for graph backed assets, or if invoked in composition
        if isinstance(self.node_def, GraphDefinition) or is_in_composition():
            return self._node_def(*args, **kwargs)

        # invoke against self to allow assets def information to be used
        return direct_invocation_result(self, *args, **kwargs)

    @public
    @experimental_param(param="resource_defs")
    @staticmethod
    def from_graph(
        graph_def: "GraphDefinition",
        *,
        keys_by_input_name: Optional[Mapping[str, AssetKey]] = None,
        keys_by_output_name: Optional[Mapping[str, AssetKey]] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        internal_asset_deps: Optional[Mapping[str, Set[AssetKey]]] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_mappings: Optional[Mapping[str, PartitionMapping]] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        group_name: Optional[str] = None,
        group_names_by_output_name: Optional[Mapping[str, Optional[str]]] = None,
        descriptions_by_output_name: Optional[Mapping[str, str]] = None,
        metadata_by_output_name: Optional[Mapping[str, Optional[ArbitraryMetadataMapping]]] = None,
        tags_by_output_name: Optional[Mapping[str, Optional[Mapping[str, str]]]] = None,
        freshness_policies_by_output_name: Optional[Mapping[str, Optional[FreshnessPolicy]]] = None,
        auto_materialize_policies_by_output_name: Optional[
            Mapping[str, Optional[AutoMaterializePolicy]]
        ] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        can_subset: bool = False,
        check_specs: Optional[Sequence[AssetCheckSpec]] = None,
        owners_by_output_name: Optional[Mapping[str, Sequence[str]]] = None,
        code_versions_by_output_name: Optional[Mapping[str, Optional[str]]] = None,
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
                (Experimental) A mapping of resource keys to resource definitions. These resources
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
            freshness_policies_by_output_name (Optional[Mapping[str, Optional[FreshnessPolicy]]]): Defines a
                FreshnessPolicy to be associated with some or all of the output assets for this node.
                Keys are the names of the outputs, and values are the FreshnessPolicies to be attached
                to the associated asset.
            auto_materialize_policies_by_output_name (Optional[Mapping[str, Optional[AutoMaterializePolicy]]]): Defines an
                AutoMaterializePolicy to be associated with some or all of the output assets for this node.
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
            group_name=group_name,
            group_names_by_output_name=group_names_by_output_name,
            descriptions_by_output_name=descriptions_by_output_name,
            metadata_by_output_name=metadata_by_output_name,
            tags_by_output_name=tags_by_output_name,
            freshness_policies_by_output_name=freshness_policies_by_output_name,
            auto_materialize_policies_by_output_name=auto_materialize_policies_by_output_name,
            backfill_policy=backfill_policy,
            can_subset=can_subset,
            check_specs=check_specs,
            owners_by_output_name=owners_by_output_name,
            code_versions_by_output_name=code_versions_by_output_name,
        )

    @public
    @staticmethod
    def from_op(
        op_def: OpDefinition,
        *,
        keys_by_input_name: Optional[Mapping[str, AssetKey]] = None,
        keys_by_output_name: Optional[Mapping[str, AssetKey]] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        internal_asset_deps: Optional[Mapping[str, Set[AssetKey]]] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_mappings: Optional[Mapping[str, PartitionMapping]] = None,
        group_name: Optional[str] = None,
        group_names_by_output_name: Optional[Mapping[str, Optional[str]]] = None,
        descriptions_by_output_name: Optional[Mapping[str, str]] = None,
        metadata_by_output_name: Optional[Mapping[str, Optional[ArbitraryMetadataMapping]]] = None,
        tags_by_output_name: Optional[Mapping[str, Optional[Mapping[str, str]]]] = None,
        freshness_policies_by_output_name: Optional[Mapping[str, Optional[FreshnessPolicy]]] = None,
        auto_materialize_policies_by_output_name: Optional[
            Mapping[str, Optional[AutoMaterializePolicy]]
        ] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        can_subset: bool = False,
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
            freshness_policies_by_output_name (Optional[Mapping[str, Optional[FreshnessPolicy]]]): Defines a
                FreshnessPolicy to be associated with some or all of the output assets for this node.
                Keys are the names of the outputs, and values are the FreshnessPolicies to be attached
                to the associated asset.
            auto_materialize_policies_by_output_name (Optional[Mapping[str, Optional[AutoMaterializePolicy]]]): Defines an
                AutoMaterializePolicy to be associated with some or all of the output assets for this node.
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
            freshness_policies_by_output_name=freshness_policies_by_output_name,
            auto_materialize_policies_by_output_name=auto_materialize_policies_by_output_name,
            backfill_policy=backfill_policy,
            can_subset=can_subset,
        )

    @staticmethod
    def _from_node(
        node_def: NodeDefinition,
        *,
        keys_by_input_name: Optional[Mapping[str, AssetKey]] = None,
        keys_by_output_name: Optional[Mapping[str, AssetKey]] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        internal_asset_deps: Optional[Mapping[str, Set[AssetKey]]] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        partition_mappings: Optional[Mapping[str, PartitionMapping]] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        group_name: Optional[str] = None,
        group_names_by_output_name: Optional[Mapping[str, Optional[str]]] = None,
        descriptions_by_output_name: Optional[Mapping[str, str]] = None,
        metadata_by_output_name: Optional[Mapping[str, Optional[ArbitraryMetadataMapping]]] = None,
        tags_by_output_name: Optional[Mapping[str, Optional[Mapping[str, str]]]] = None,
        freshness_policies_by_output_name: Optional[Mapping[str, Optional[FreshnessPolicy]]] = None,
        code_versions_by_output_name: Optional[Mapping[str, Optional[str]]] = None,
        auto_materialize_policies_by_output_name: Optional[
            Mapping[str, Optional[AutoMaterializePolicy]]
        ] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        can_subset: bool = False,
        check_specs: Optional[Sequence[AssetCheckSpec]] = None,
        owners_by_output_name: Optional[Mapping[str, Sequence[str]]] = None,
    ) -> "AssetsDefinition":
        from dagster._core.definitions.decorators.decorator_assets_definition_builder import (
            _assign_output_names_to_check_specs,
            _validate_check_specs_target_relevant_asset_keys,
        )

        node_def = check.inst_param(node_def, "node_def", NodeDefinition)
        keys_by_input_name = _infer_keys_by_input_names(
            node_def,
            check.opt_mapping_param(
                keys_by_input_name, "keys_by_input_name", key_type=str, value_type=AssetKey
            ),
        )
        keys_by_output_name = check.opt_mapping_param(
            keys_by_output_name,
            "keys_by_output_name",
            key_type=str,
            value_type=AssetKey,
        )
        internal_asset_deps = check.opt_mapping_param(
            internal_asset_deps, "internal_asset_deps", key_type=str, value_type=set
        )
        resource_defs = check.opt_mapping_param(
            resource_defs, "resource_defs", key_type=str, value_type=ResourceDefinition
        )
        transformed_internal_asset_deps: Dict[AssetKey, AbstractSet[AssetKey]] = {}
        if internal_asset_deps:
            for output_name, asset_keys in internal_asset_deps.items():
                check.invariant(
                    output_name in keys_by_output_name,
                    f"output_name {output_name} specified in internal_asset_deps does not exist"
                    " in the decorated function",
                )
                transformed_internal_asset_deps[keys_by_output_name[output_name]] = asset_keys

        check_specs_by_output_name = _assign_output_names_to_check_specs(check_specs)

        keys_by_output_name = _infer_keys_by_output_names(
            node_def, keys_by_output_name or {}, check_specs_by_output_name
        )

        _validate_check_specs_target_relevant_asset_keys(
            check_specs, list(keys_by_output_name.values())
        )

        keys_by_output_name_with_prefix: Dict[str, AssetKey] = {}
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
            freshness_policies_by_key=_output_dict_to_asset_dict(freshness_policies_by_output_name),
            auto_materialize_policies_by_key=_output_dict_to_asset_dict(
                auto_materialize_policies_by_output_name
            ),
            metadata_by_key=_output_dict_to_asset_dict(metadata_by_output_name),
            descriptions_by_key=_output_dict_to_asset_dict(descriptions_by_output_name),
            code_versions_by_key=_output_dict_to_asset_dict(code_versions_by_output_name),
        )

        return AssetsDefinition.dagster_internal_init(
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name=keys_by_output_name_with_prefix,
            node_def=node_def,
            partitions_def=check.opt_inst_param(
                partitions_def,
                "partitions_def",
                PartitionsDefinition,
            ),
            resource_defs=resource_defs,
            backfill_policy=check.opt_inst_param(
                backfill_policy, "backfill_policy", BackfillPolicy
            ),
            can_subset=can_subset,
            selected_asset_keys=None,  # node has no subselection info
            check_specs_by_output_name=check_specs_by_output_name,
            selected_asset_check_keys=None,
            is_subset=False,
            specs=specs,
        )

    @public
    @property
    def can_subset(self) -> bool:
        """bool: If True, indicates that this AssetsDefinition may materialize any subset of its
        asset keys in a given computation (as opposed to being required to materialize all asset
        keys).
        """
        return self._can_subset

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
        check.invariant(
            isinstance(self._node_def, OpDefinition),
            "The NodeDefinition for this AssetsDefinition is not of type OpDefinition.",
        )
        return cast(OpDefinition, self._node_def)

    @public
    @property
    def node_def(self) -> NodeDefinition:
        """NodeDefinition: Returns the OpDefinition or GraphDefinition that is used to materialize
        the assets in this AssetsDefinition.
        """
        return self._node_def

    @public
    @property
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
            + ", ".join([str(ak.to_string()) for ak in self._keys_by_output_name.values()]),
        )

        return next(iter(self.keys))

    @public
    @property
    def resource_defs(self) -> Mapping[str, ResourceDefinition]:
        """Mapping[str, ResourceDefinition]: A mapping from resource name to ResourceDefinition for
        the resources bound to this AssetsDefinition.
        """
        return dict(self._resource_defs)

    @public
    @property
    def keys(self) -> AbstractSet[AssetKey]:
        """AbstractSet[AssetKey]: The asset keys associated with this AssetsDefinition."""
        return self._selected_asset_keys

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
        upstream_keys = {dep_key for key in self.keys for dep_key in self.asset_deps[key]}
        input_keys = set(self._keys_by_input_name.values())
        return upstream_keys.intersection(input_keys)

    @property
    def node_keys_by_output_name(self) -> Mapping[str, AssetKey]:
        """AssetKey for each output on the underlying NodeDefinition."""
        return self._keys_by_output_name

    @property
    def node_keys_by_input_name(self) -> Mapping[str, AssetKey]:
        """AssetKey for each input on the underlying NodeDefinition."""
        return self._keys_by_input_name

    @property
    def node_check_specs_by_output_name(self) -> Mapping[str, AssetCheckSpec]:
        """AssetCheckSpec for each output on the underlying NodeDefinition."""
        return self._check_specs_by_output_name

    @property
    def check_specs_by_output_name(self) -> Mapping[str, AssetCheckSpec]:
        return {
            name: spec
            for name, spec in self._check_specs_by_output_name.items()
            if spec.key in self._selected_asset_check_keys
        }

    def get_spec_for_check_key(self, asset_check_key: AssetCheckKey) -> AssetCheckSpec:
        return self._check_specs_by_key[asset_check_key]

    @property
    def keys_by_output_name(self) -> Mapping[str, AssetKey]:
        return {
            name: key for name, key in self.node_keys_by_output_name.items() if key in self.keys
        }

    @property
    def asset_and_check_keys_by_output_name(self) -> Mapping[str, "AssetKeyOrCheckKey"]:
        return merge_dicts(
            self.keys_by_output_name,
            {
                output_name: spec.key
                for output_name, spec in self.check_specs_by_output_name.items()
            },
        )

    @property
    def asset_and_check_keys(self) -> AbstractSet["AssetKeyOrCheckKey"]:
        return set(self.keys).union(self.check_keys)

    @property
    def keys_by_input_name(self) -> Mapping[str, AssetKey]:
        upstream_keys = {
            *(dep_key for key in self.keys for dep_key in self.asset_deps[key]),
            *(spec.asset_key for spec in self.check_specs if spec.asset_key not in self.keys),
        }

        return {
            name: key for name, key in self.node_keys_by_input_name.items() if key in upstream_keys
        }

    @property
    def freshness_policies_by_key(self) -> Mapping[AssetKey, FreshnessPolicy]:
        return {
            key: spec.freshness_policy
            for key, spec in self._specs_by_key.items()
            if spec.freshness_policy
        }

    @property
    def auto_materialize_policies_by_key(self) -> Mapping[AssetKey, AutoMaterializePolicy]:
        return {
            key: spec.auto_materialize_policy
            for key, spec in self._specs_by_key.items()
            if spec.auto_materialize_policy
        }

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
        return self._backfill_policy

    @public
    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        """Optional[PartitionsDefinition]: The PartitionsDefinition for this AssetsDefinition (if any)."""
        return self._partitions_def

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
    def partition_mappings(self) -> Mapping[AssetKey, PartitionMapping]:
        return self._partition_mappings

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
        return self._selected_asset_check_keys

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
        value = self._get_external_asset_metadata_value(SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE)
        if value is None:
            return AssetExecutionType.MATERIALIZATION
        elif isinstance(value, str):
            return AssetExecutionType[value]
        else:
            check.failed(f"Expected execution type metadata to be a string or None, not {value}")

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

    def get_partition_mapping_for_input(self, input_name: str) -> Optional[PartitionMapping]:
        return self._partition_mappings.get(self._keys_by_input_name[input_name])

    def infer_partition_mapping(
        self, upstream_asset_key: AssetKey, upstream_partitions_def: Optional[PartitionsDefinition]
    ) -> PartitionMapping:
        with disable_dagster_warnings():
            partition_mapping = self._partition_mappings.get(upstream_asset_key)
            return infer_partition_mapping(
                partition_mapping, self._partitions_def, upstream_partitions_def
            )

    def get_output_name_for_asset_key(self, key: AssetKey) -> str:
        for output_name, asset_key in self.keys_by_output_name.items():
            if key == asset_key:
                return output_name

        raise DagsterInvariantViolationError(
            f"Asset key {key.to_user_string()} not found in AssetsDefinition"
        )

    def get_output_name_for_asset_check_key(self, key: AssetCheckKey) -> str:
        for output_name, spec in self._check_specs_by_output_name.items():
            if key == spec.key:
                return output_name

        raise DagsterInvariantViolationError(
            f"Asset check key {key.to_user_string()} not found in AssetsDefinition"
        )

    def get_op_def_for_asset_key(self, key: AssetKey) -> OpDefinition:
        """If this is an op-backed asset, returns the op def. If it's a graph-backed asset,
        returns the op def within the graph that produces the given asset key.
        """
        output_name = self.get_output_name_for_asset_key(key)
        return self.node_def.resolve_output_to_origin_op_def(output_name)

    def with_attributes(
        self,
        *,
        output_asset_key_replacements: Mapping[AssetKey, AssetKey] = {},
        input_asset_key_replacements: Mapping[AssetKey, AssetKey] = {},
        group_names_by_key: Mapping[AssetKey, str] = {},
        tags_by_key: Mapping[AssetKey, Mapping[str, str]] = {},
        freshness_policy: Optional[
            Union[FreshnessPolicy, Mapping[AssetKey, FreshnessPolicy]]
        ] = None,
        auto_materialize_policy: Optional[
            Union[AutoMaterializePolicy, Mapping[AssetKey, AutoMaterializePolicy]]
        ] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
    ) -> "AssetsDefinition":
        conflicts_by_attr_name: Dict[str, Set[AssetKey]] = defaultdict(set)
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
                new_value=auto_materialize_policy, attr_name="auto_materialize_policy"
            )
            update_replace_dict_and_conflicts(
                new_value=freshness_policy, attr_name="freshness_policy"
            )
            update_replace_dict_and_conflicts(new_value=tags_by_key, attr_name="tags")
            update_replace_dict_and_conflicts(
                new_value=group_names_by_key,
                attr_name="group_name",
                default_value=DEFAULT_GROUP_NAME,
            )

            if key in output_asset_key_replacements:
                replace_dict["key"] = output_asset_key_replacements[key]

            if input_asset_key_replacements or output_asset_key_replacements:
                new_deps = []
                for dep in spec.deps:
                    replacement_key = input_asset_key_replacements.get(
                        dep.asset_key,
                        output_asset_key_replacements.get(dep.asset_key),
                    )
                    if replacement_key is not None:
                        new_deps.append(dep._replace(asset_key=replacement_key))
                    else:
                        new_deps.append(dep)

                replace_dict["deps"] = new_deps

            replaced_specs.append(spec._replace(**replace_dict))

        for attr_name, conflicting_asset_keys in conflicts_by_attr_name.items():
            raise DagsterInvalidDefinitionError(
                f"{attr_name} already exists on assets"
                f" {', '.join(asset_key.to_user_string() for asset_key in conflicting_asset_keys)}"
            )

        check_specs_by_output_name = {
            output_name: check_spec._replace(
                asset_key=output_asset_key_replacements.get(
                    check_spec.asset_key, check_spec.asset_key
                )
            )
            for output_name, check_spec in self.node_check_specs_by_output_name.items()
        }

        selected_asset_check_keys = {
            check_key._replace(
                asset_key=output_asset_key_replacements.get(
                    check_key.asset_key, check_key.asset_key
                )
            )
            for check_key in self.check_keys
        }

        replaced_attributes = dict(
            keys_by_input_name={
                input_name: input_asset_key_replacements.get(key, key)
                for input_name, key in self._keys_by_input_name.items()
            },
            keys_by_output_name={
                output_name: output_asset_key_replacements.get(key, key)
                for output_name, key in self._keys_by_output_name.items()
            },
            selected_asset_keys={
                output_asset_key_replacements.get(key, key) for key in self._selected_asset_keys
            },
            backfill_policy=backfill_policy if backfill_policy else self.backfill_policy,
            is_subset=self.is_subset,
            check_specs_by_output_name=check_specs_by_output_name,
            selected_asset_check_keys=selected_asset_check_keys,
            specs=replaced_specs,
        )

        merged_attrs = merge_dicts(self.get_attributes_dict(), replaced_attributes)
        return self.__class__.dagster_internal_init(**merged_attrs)

    def _subset_graph_backed_asset(
        self,
        selected_asset_keys: AbstractSet[AssetKey],
        selected_asset_check_keys: AbstractSet[AssetCheckKey],
    ) -> SubselectedGraphDefinition:
        from dagster._core.definitions.graph_definition import GraphDefinition

        if not isinstance(self.node_def, GraphDefinition):
            raise DagsterInvalidInvocationError(
                "Method _subset_graph_backed_asset cannot subset an asset that is not a graph"
            )

        # All asset keys in selected_asset_keys are outputted from the same top-level graph backed asset
        dep_node_handles_by_asset_key = get_dep_node_handles_of_graph_backed_asset(
            self.node_def, self
        )
        op_selection: List[str] = []
        for asset_key in selected_asset_keys:
            dep_node_handles = dep_node_handles_by_asset_key[asset_key]
            for dep_node_handle in dep_node_handles:
                op_selection.append(".".join(dep_node_handle.path[1:]))
        for asset_check_key in selected_asset_check_keys:
            dep_node_handles = dep_node_handles_by_asset_key[asset_check_key]
            for dep_node_handle in dep_node_handles:
                op_selection.append(".".join(dep_node_handle.path[1:]))

        return get_graph_subset(self.node_def, op_selection)

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
        from dagster._core.definitions.graph_definition import GraphDefinition

        check.invariant(
            self.can_subset,
            f"Attempted to subset AssetsDefinition for {self.node_def.name}, but can_subset=False.",
        )

        # Set of assets within selected_asset_keys which are outputted by this AssetDefinition
        asset_subselection = selected_asset_keys & self.keys
        if selected_asset_check_keys is None:
            # filter to checks that target selected asset keys
            asset_check_subselection = {
                key for key in self.check_keys if key.asset_key in asset_subselection
            }
        else:
            asset_check_subselection = selected_asset_check_keys & self.check_keys

        # Early escape if all assets and checks in AssetsDefinition are selected
        if asset_subselection == self.keys and asset_check_subselection == self.check_keys:
            return self
        elif isinstance(self.node_def, GraphDefinition):  # Node is graph-backed asset
            subsetted_node = self._subset_graph_backed_asset(
                asset_subselection, asset_check_subselection
            )

            # The subsetted node should only include asset inputs that are dependencies of the
            # selected set of assets.
            subsetted_input_names = [input_def.name for input_def in subsetted_node.input_defs]
            subsetted_keys_by_input_name = {
                key: value
                for key, value in self.node_keys_by_input_name.items()
                if key in subsetted_input_names
            }

            subsetted_output_names = [output_def.name for output_def in subsetted_node.output_defs]
            subsetted_keys_by_output_name = {
                key: value
                for key, value in self.node_keys_by_output_name.items()
                if key in subsetted_output_names
            }
            selected_node_asset_keys = set(subsetted_keys_by_output_name.values())

            # An op within the graph-backed asset that yields multiple assets will be run
            # any time any of its output assets are selected. Thus, if an op yields multiple assets
            # and only one of them is selected, the op will still run and potentially unexpectedly
            # materialize the unselected asset.
            #
            # Thus, we include unselected assets that may be accidentally materialized in
            # keys_by_output_name and asset_deps so that the webserver can populate an warning when
            # this occurs. This is the same behavior as multi-asset subsetting.

            replaced_attributes = dict(
                keys_by_input_name=subsetted_keys_by_input_name,
                keys_by_output_name=subsetted_keys_by_output_name,
                node_def=subsetted_node,
                selected_asset_keys=selected_asset_keys & self.keys,
                selected_asset_check_keys=asset_check_subselection,
                specs=[spec for spec in self.specs if spec.key in selected_node_asset_keys],
                is_subset=True,
            )

            return self.__class__.dagster_internal_init(
                **merge_dicts(self.get_attributes_dict(), replaced_attributes)
            )
        else:
            # multi_asset subsetting
            replaced_attributes = {
                "selected_asset_keys": asset_subselection,
                "selected_asset_check_keys": asset_check_subselection,
                "is_subset": True,
            }
            return self.__class__.dagster_internal_init(
                **merge_dicts(self.get_attributes_dict(), replaced_attributes)
            )

    @property
    def is_subset(self) -> bool:
        return self._is_subset

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
                resolved_key in self.keys, f"Key {resolved_key} not found in AssetsDefinition"
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
            key = self._keys_by_output_name[output_name]
            spec = self.specs_by_key[key]

            return SourceAsset(
                key=key,
                metadata=output_def.metadata,
                io_manager_key=output_def.io_manager_key,
                description=output_def.description,
                resource_defs=self.resource_defs,
                partitions_def=self.partitions_def,
                group_name=spec.group_name,
                tags=spec.tags,
            )

    def get_io_manager_key_for_asset_key(self, key: AssetKey) -> str:
        output_name = self.get_output_name_for_asset_key(key)
        return self.node_def.resolve_output_to_origin(
            output_name, NodeHandle(self.node_def.name, parent=None)
        )[0].io_manager_key

    def get_resource_requirements(self) -> Iterator[ResourceRequirement]:
        if self.is_executable:
            yield from self.node_def.get_resource_requirements()  # type: ignore[attr-defined]
        else:
            for key in self.keys:
                # This matches how SourceAsset emit requirements except we emit
                # ExternalAssetIOManagerRequirement instead of SourceAssetIOManagerRequirement
                yield ExternalAssetIOManagerRequirement(
                    key=self.get_io_manager_key_for_asset_key(key),
                    asset_key=key.to_string(),
                )
        for source_key, resource_def in self.resource_defs.items():
            yield from resource_def.get_resource_requirements(outer_context=source_key)

    @public
    @property
    def required_resource_keys(self) -> Set[str]:
        """Set[str]: The set of keys for resources that must be provided to this AssetsDefinition."""
        return {requirement.key for requirement in self.get_resource_requirements()}

    def __str__(self):
        if len(self.keys) == 1:
            return f"AssetsDefinition with key {self.key.to_string()}"
        else:
            asset_keys = ", ".join(sorted(([asset_key.to_string() for asset_key in self.keys])))
            return f"AssetsDefinition with keys {asset_keys}"

    @cached_property
    def unique_id(self) -> str:
        return unique_id_from_asset_and_check_keys(self.keys, self.check_keys)

    def with_resources(self, resource_defs: Mapping[str, ResourceDefinition]) -> "AssetsDefinition":
        attributes_dict = self.get_attributes_dict()
        attributes_dict["resource_defs"] = merge_resource_defs(
            old_resource_defs=self.resource_defs,
            resource_defs_to_merge_in=resource_defs,
            requires_resources=self,
        )
        with disable_dagster_warnings():
            return self.__class__(**attributes_dict)

    def get_attributes_dict(self) -> Dict[str, Any]:
        return dict(
            keys_by_input_name=self._keys_by_input_name,
            keys_by_output_name=self._keys_by_output_name,
            node_def=self._node_def,
            partitions_def=self._partitions_def,
            selected_asset_keys=self._selected_asset_keys,
            can_subset=self._can_subset,
            resource_defs=self._resource_defs,
            backfill_policy=self._backfill_policy,
            check_specs_by_output_name=self._check_specs_by_output_name,
            selected_asset_check_keys=self._selected_asset_check_keys,
            specs=self.specs,
            is_subset=self.is_subset,
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
    inferred_input_names_by_asset_key: Dict[str, AssetKey] = {
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

    inferred_keys_by_output_names: Dict[str, AssetKey] = {
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


def _resolve_selections(
    all_asset_keys: AbstractSet[AssetKey],
    all_check_keys: AbstractSet[AssetCheckKey],
    selected_asset_keys: Optional[AbstractSet[AssetKey]],
    selected_asset_check_keys: Optional[AbstractSet[AssetCheckKey]],
) -> Tuple[AbstractSet[AssetKey], AbstractSet[AssetCheckKey]]:
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
    freshness_policies_by_key: Optional[Mapping[AssetKey, FreshnessPolicy]],
    auto_materialize_policies_by_key: Optional[Mapping[AssetKey, AutoMaterializePolicy]],
    code_versions_by_key: Optional[Mapping[AssetKey, str]],
    descriptions_by_key: Optional[Mapping[AssetKey, str]],
    owners_by_key: Optional[Mapping[AssetKey, Sequence[str]]],
) -> Sequence[AssetSpec]:
    validated_group_names_by_key = check.opt_mapping_param(
        group_names_by_key, "group_names_by_key", key_type=AssetKey, value_type=str
    )

    validated_metadata_by_key = check.opt_mapping_param(
        metadata_by_key, "metadata_by_key", key_type=AssetKey, value_type=dict
    )

    for tags in (tags_by_key or {}).values():
        validate_tags_strict(tags)
    validated_tags_by_key = tags_by_key or {}

    validated_descriptions_by_key = check.opt_mapping_param(
        descriptions_by_key, "descriptions_by_key", key_type=AssetKey, value_type=str
    )

    validated_code_versions_by_key = check.opt_mapping_param(
        code_versions_by_key, "code_versions_by_key", key_type=AssetKey, value_type=str
    )

    validated_freshness_policies_by_key = check.opt_mapping_param(
        freshness_policies_by_key,
        "freshness_policies_by_key",
        key_type=AssetKey,
        value_type=FreshnessPolicy,
    )

    validated_auto_materialize_policies_by_key = check.opt_mapping_param(
        auto_materialize_policies_by_key,
        "auto_materialize_policies_by_key",
        key_type=AssetKey,
        value_type=AutoMaterializePolicy,
    )

    validated_owners_by_key = check.opt_mapping_param(
        owners_by_key, "owners_by_key", key_type=AssetKey, value_type=list
    )

    dep_keys_from_keys_by_input_name = set(keys_by_input_name.values())
    dep_objs_from_keys_by_input_name = [
        AssetDep(asset=key, partition_mapping=(partition_mappings or {}).get(key))
        for key in dep_keys_from_keys_by_input_name
    ]

    result: List[AssetSpec] = []
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
                    freshness_policy=validated_freshness_policies_by_key.get(key),
                    auto_materialize_policy=validated_auto_materialize_policies_by_key.get(key),
                    owners=validated_owners_by_key.get(key),
                    group_name=validated_group_names_by_key.get(key),
                    code_version=validated_code_versions_by_key.get(key),
                    deps=dep_objs,
                    # Value here is irrelevant, because it will be replaced by value from
                    # NodeDefinition
                    skippable=False,
                )
            )

    return result


def _validate_self_deps(
    input_keys: Iterable[AssetKey],
    output_keys: Iterable[AssetKey],
    partition_mappings: Mapping[AssetKey, PartitionMapping],
    partitions_def: Optional[PartitionsDefinition],
) -> None:
    output_keys_set = set(output_keys)
    for input_key in input_keys:
        if input_key in output_keys_set:
            if input_key in partition_mappings:
                partition_mapping = partition_mappings[input_key]
                time_window_partition_mapping = get_self_dep_time_window_partition_mapping(
                    partition_mapping, partitions_def
                )
                if (
                    time_window_partition_mapping is not None
                    and (time_window_partition_mapping.start_offset or 0) < 0
                    and (time_window_partition_mapping.end_offset or 0) < 0
                ):
                    continue

            raise DagsterInvalidDefinitionError(
                f'Asset "{input_key.to_user_string()}" depends on itself. Assets can only depend'
                " on themselves if they are:\n(a) time-partitioned and each partition depends on"
                " earlier partitions\n(b) multipartitioned, with one time dimension that depends"
                " on earlier time partitions"
            )


def get_self_dep_time_window_partition_mapping(
    partition_mapping: Optional[PartitionMapping], partitions_def: Optional[PartitionsDefinition]
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
    partition_mappings: Dict[AssetKey, PartitionMapping], deps: Iterable[AssetDep], asset_name: str
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


def unique_id_from_asset_and_check_keys(
    asset_keys: Iterable[AssetKey], check_keys: Iterable[AssetCheckKey]
) -> str:
    """Generate a unique ID from the provided asset keys.

    This is useful for generating op names that don't have collisions.
    """
    sorted_asset_key_strs = sorted(asset_key.to_string() for asset_key in asset_keys)
    sorted_check_key_strs = sorted(str(check_key) for check_key in check_keys)
    return non_secure_md5_hash_str(
        json.dumps(sorted_asset_key_strs + sorted_check_key_strs).encode("utf-8")
    )[:8]
