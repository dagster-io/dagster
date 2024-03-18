import json
import warnings
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
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Union,
    cast,
)

import dagster._check as check
from dagster._annotations import experimental_param, public
from dagster._core.definitions.asset_check_spec import AssetCheckKey, AssetCheckSpec
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
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
)
from dagster._core.utils import is_valid_email
from dagster._utils import IHasInternalInit
from dagster._utils.merger import merge_dicts
from dagster._utils.security import non_secure_md5_hash_str
from dagster._utils.warnings import (
    disable_dagster_warnings,
)

from .dependency import NodeHandle
from .events import AssetKey, CoercibleToAssetKey, CoercibleToAssetKeyPrefix
from .node_definition import NodeDefinition
from .op_definition import OpDefinition
from .partition import PartitionsDefinition
from .partition_mapping import (
    PartitionMapping,
    get_builtin_partition_mapping_types,
    infer_partition_mapping,
)
from .resource_definition import ResourceDefinition
from .source_asset import SourceAsset
from .utils import DEFAULT_GROUP_NAME, validate_definition_tags, validate_group_name

if TYPE_CHECKING:
    from .base_asset_graph import AssetKeyOrCheckKey
    from .graph_definition import GraphDefinition

ASSET_SUBSET_INPUT_PREFIX = "__subset_input__"


class UserAssetOwner(NamedTuple):
    email: str


class TeamAssetOwner(NamedTuple):
    team: str


AssetOwner = Union[UserAssetOwner, TeamAssetOwner]


def asset_owner_to_str(owner: AssetOwner) -> str:
    if isinstance(owner, UserAssetOwner):
        return owner.email
    elif isinstance(owner, TeamAssetOwner):
        return owner.team
    else:
        check.failed(f"Unexpected owner type {type(owner)}")


class AssetsDefinition(ResourceAddable, RequiresResources, IHasInternalInit):
    """Defines a set of assets that are produced by the same op or graph.

    AssetsDefinitions are typically not instantiated directly, but rather produced using the
    :py:func:`@asset <asset>` or :py:func:`@multi_asset <multi_asset>` decorators.
    """

    _node_def: NodeDefinition
    _keys_by_input_name: Mapping[str, AssetKey]
    _keys_by_output_name: Mapping[str, AssetKey]
    _partitions_def: Optional[PartitionsDefinition]
    _partition_mappings: Mapping[AssetKey, PartitionMapping]
    _asset_deps: Mapping[AssetKey, AbstractSet[AssetKey]]
    _resource_defs: Mapping[str, ResourceDefinition]
    _group_names_by_key: Mapping[AssetKey, str]
    _selected_asset_keys: AbstractSet[AssetKey]
    _can_subset: bool
    _metadata_by_key: Mapping[AssetKey, ArbitraryMetadataMapping]
    _tags_by_key: Mapping[AssetKey, Mapping[str, str]]
    _freshness_policies_by_key: Mapping[AssetKey, FreshnessPolicy]
    _auto_materialize_policies_by_key: Mapping[AssetKey, AutoMaterializePolicy]
    _backfill_policy: Optional[BackfillPolicy]
    _code_versions_by_key: Mapping[AssetKey, Optional[str]]
    _descriptions_by_key: Mapping[AssetKey, str]
    _selected_asset_check_keys: AbstractSet[AssetCheckKey]
    _is_subset: bool
    _owners_by_key: Mapping[AssetKey, Sequence[AssetOwner]]

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
        descriptions_by_key: Optional[Mapping[AssetKey, str]] = None,
        check_specs_by_output_name: Optional[Mapping[str, AssetCheckSpec]] = None,
        selected_asset_check_keys: Optional[AbstractSet[AssetCheckKey]] = None,
        is_subset: bool = False,
        owners_by_key: Optional[Mapping[AssetKey, Sequence[Union[str, AssetOwner]]]] = None,
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

        check.opt_mapping_param(
            check_specs_by_output_name,
            "check_specs_by_output_name",
            key_type=str,
            value_type=AssetCheckSpec,
        )

        # if not specified assume all output assets depend on all input assets
        all_asset_keys = set(keys_by_output_name.values())
        input_asset_keys = set(keys_by_input_name.values())

        self._partitions_def = partitions_def
        self._partition_mappings = partition_mappings or {}
        builtin_partition_mappings = get_builtin_partition_mapping_types()
        for asset_key, partition_mapping in self._partition_mappings.items():
            if not isinstance(partition_mapping, builtin_partition_mappings):
                warnings.warn(
                    f"Non-built-in PartitionMappings, such as {type(partition_mapping).__name__} "
                    "are deprecated and will not work with asset reconciliation. The built-in "
                    "partition mappings are "
                    + ", ".join(
                        builtin_partition_mapping.__name__
                        for builtin_partition_mapping in builtin_partition_mappings
                    )
                    + ".",
                    category=DeprecationWarning,
                )

            if asset_key not in input_asset_keys:
                check.failed(
                    f"While constructing AssetsDefinition outputting {all_asset_keys}, received a"
                    f" partition mapping for {asset_key} that is not defined in the set of upstream"
                    f" assets: {input_asset_keys}"
                )

        self._asset_deps = asset_deps or {
            out_asset_key: set(keys_by_input_name.values()) for out_asset_key in all_asset_keys
        }
        check.invariant(
            set(self._asset_deps.keys()) == all_asset_keys,
            "The set of asset keys with dependencies specified in the asset_deps argument must "
            "equal the set of asset keys produced by this AssetsDefinition. \n"
            f"asset_deps keys: {set(self._asset_deps.keys())} \n"
            f"expected keys: {all_asset_keys}",
        )
        self._resource_defs = wrap_resources_for_execution(
            check.opt_mapping_param(resource_defs, "resource_defs")
        )

        group_names_by_key = (
            check.mapping_param(group_names_by_key, "group_names_by_key")
            if group_names_by_key
            else {}
        )
        self._group_names_by_key = {}
        # assets that don't have a group name get a DEFAULT_GROUP_NAME
        for key in all_asset_keys:
            group_name = group_names_by_key.get(key)
            self._group_names_by_key[key] = validate_group_name(group_name)

        all_check_keys = {spec.key for spec in (check_specs_by_output_name or {}).values()}

        # NOTE: this logic mirrors subsetting at the asset layer. This is ripe for consolidation.
        if selected_asset_keys is None and selected_asset_check_keys is None:
            # if no selections, include everything
            self._selected_asset_keys = all_asset_keys
            self._selected_asset_check_keys = all_check_keys
        else:
            self._selected_asset_keys = selected_asset_keys or set()

            if selected_asset_check_keys is None:
                # if assets were selected but checks are None, then include all checks for selected
                # assets
                self._selected_asset_check_keys = {
                    key for key in all_check_keys if key.asset_key in self._selected_asset_keys
                }
            else:
                # otherwise, use the selected checks
                self._selected_asset_check_keys = selected_asset_check_keys

        self._check_specs_by_output_name = {
            name: spec
            for name, spec in (check_specs_by_output_name or {}).items()
            if spec.key in self._selected_asset_check_keys
        }
        self._check_specs_by_key = {
            spec.key: spec for spec in self._check_specs_by_output_name.values()
        }

        self._can_subset = can_subset

        self._code_versions_by_key = {}
        self._metadata_by_key = dict(
            check.opt_mapping_param(
                metadata_by_key, "metadata_by_key", key_type=AssetKey, value_type=dict
            )
        )

        for tags in (tags_by_key or {}).values():
            validate_definition_tags(tags)
        self._tags_by_key = tags_by_key or {}

        self._descriptions_by_key = dict(
            check.opt_mapping_param(
                descriptions_by_key, "descriptions_by_key", key_type=AssetKey, value_type=str
            )
        )
        for output_name, asset_key in keys_by_output_name.items():
            output_def, _ = node_def.resolve_output_to_origin(output_name, None)
            self._metadata_by_key[asset_key] = {
                **output_def.metadata,
                **self._metadata_by_key.get(asset_key, {}),
            }
            # We construct description from three sources of truth here. This
            # highly unfortunate. See commentary in @multi_asset's call to dagster_internal_init.
            description = (
                self._descriptions_by_key.get(asset_key, output_def.description)
                or node_def.description
            )
            if description:
                self._descriptions_by_key[asset_key] = description
            self._code_versions_by_key[asset_key] = output_def.code_version

        for key, freshness_policy in (freshness_policies_by_key or {}).items():
            check.param_invariant(
                not (
                    freshness_policy
                    and self._partitions_def is not None
                    and not isinstance(self._partitions_def, TimeWindowPartitionsDefinition)
                ),
                "freshness_policies_by_key",
                "FreshnessPolicies are currently unsupported for assets with partitions of type"
                f" {type(self._partitions_def)}.",
            )

        self._freshness_policies_by_key = check.opt_mapping_param(
            freshness_policies_by_key,
            "freshness_policies_by_key",
            key_type=AssetKey,
            value_type=FreshnessPolicy,
        )

        self._auto_materialize_policies_by_key = check.opt_mapping_param(
            auto_materialize_policies_by_key,
            "auto_materialize_policies_by_key",
            key_type=AssetKey,
            value_type=AutoMaterializePolicy,
        )

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

        self._is_subset = check.bool_param(is_subset, "is_subset")

        check.opt_mapping_param(owners_by_key, "owners_by_key", key_type=AssetKey, value_type=list)
        for key, owners in (owners_by_key or {}).items():
            for owner in owners:
                if isinstance(owner, (TeamAssetOwner, UserAssetOwner)):
                    continue
                elif is_valid_email(owner):
                    continue
                elif owner.startswith("team:") and len(owner) > 5:
                    continue
                else:
                    raise DagsterInvalidDefinitionError(
                        f"Invalid owner '{owner}' for asset '{key}'. Owner must be an email address or a team"
                        " name prefixed with 'team:'."
                    )
        self._owners_by_key = {
            key: [
                owner
                if isinstance(owner, (TeamAssetOwner, UserAssetOwner))
                else (
                    UserAssetOwner(email=owner)
                    if is_valid_email(owner)
                    else TeamAssetOwner(team=owner[5:])
                )
                for owner in owners
            ]
            for key, owners in (owners_by_key or {}).items()
        }

    def dagster_internal_init(
        *,
        keys_by_input_name: Mapping[str, AssetKey],
        keys_by_output_name: Mapping[str, AssetKey],
        node_def: NodeDefinition,
        partitions_def: Optional[PartitionsDefinition],
        partition_mappings: Optional[Mapping[AssetKey, PartitionMapping]],
        asset_deps: Optional[Mapping[AssetKey, AbstractSet[AssetKey]]],
        selected_asset_keys: Optional[AbstractSet[AssetKey]],
        can_subset: bool,
        resource_defs: Optional[Mapping[str, object]],
        group_names_by_key: Optional[Mapping[AssetKey, str]],
        metadata_by_key: Optional[Mapping[AssetKey, ArbitraryMetadataMapping]],
        tags_by_key: Optional[Mapping[AssetKey, Mapping[str, str]]],
        freshness_policies_by_key: Optional[Mapping[AssetKey, FreshnessPolicy]],
        auto_materialize_policies_by_key: Optional[Mapping[AssetKey, AutoMaterializePolicy]],
        backfill_policy: Optional[BackfillPolicy],
        descriptions_by_key: Optional[Mapping[AssetKey, str]],
        check_specs_by_output_name: Optional[Mapping[str, AssetCheckSpec]],
        selected_asset_check_keys: Optional[AbstractSet[AssetCheckKey]],
        is_subset: bool,
        owners_by_key: Optional[Mapping[AssetKey, Sequence[Union[str, AssetOwner]]]],
    ) -> "AssetsDefinition":
        return AssetsDefinition(
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name=keys_by_output_name,
            node_def=node_def,
            partitions_def=partitions_def,
            partition_mappings=partition_mappings,
            asset_deps=asset_deps,
            selected_asset_keys=selected_asset_keys,
            can_subset=can_subset,
            resource_defs=resource_defs,
            group_names_by_key=group_names_by_key,
            metadata_by_key=metadata_by_key,
            tags_by_key=tags_by_key,
            freshness_policies_by_key=freshness_policies_by_key,
            auto_materialize_policies_by_key=auto_materialize_policies_by_key,
            backfill_policy=backfill_policy,
            descriptions_by_key=descriptions_by_key,
            check_specs_by_output_name=check_specs_by_output_name,
            selected_asset_check_keys=selected_asset_check_keys,
            is_subset=is_subset,
            owners_by_key=owners_by_key,
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
        node_def: Union[OpDefinition, "GraphDefinition"],
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
        owners_by_key: Optional[Mapping[AssetKey, Sequence[Union[str, AssetOwner]]]] = None,
    ) -> "AssetsDefinition":
        from dagster._core.definitions.decorators.asset_decorator import (
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
            group_names_by_key = {
                keys_by_output_name_with_prefix[output_name]: group_name
                for output_name, group_name in group_names_by_output_name.items()
                if group_name is not None
            }
        else:
            group_names_by_key = None

        return AssetsDefinition.dagster_internal_init(
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name=keys_by_output_name_with_prefix,
            node_def=node_def,
            asset_deps=transformed_internal_asset_deps or None,
            partitions_def=check.opt_inst_param(
                partitions_def,
                "partitions_def",
                PartitionsDefinition,
            ),
            group_names_by_key=group_names_by_key,
            resource_defs=resource_defs,
            partition_mappings=(
                {
                    keys_by_input_name[input_name]: partition_mapping
                    for input_name, partition_mapping in partition_mappings.items()
                }
                if partition_mappings
                else None
            ),
            metadata_by_key=(
                {
                    keys_by_output_name_with_prefix[output_name]: metadata
                    for output_name, metadata in metadata_by_output_name.items()
                    if metadata is not None
                }
                if metadata_by_output_name
                else None
            ),
            tags_by_key=(
                {
                    keys_by_output_name_with_prefix[output_name]: tags
                    for output_name, tags in tags_by_output_name.items()
                    if tags is not None
                }
                if tags_by_output_name
                else None
            ),
            freshness_policies_by_key=(
                {
                    keys_by_output_name_with_prefix[output_name]: freshness_policy
                    for output_name, freshness_policy in freshness_policies_by_output_name.items()
                    if freshness_policy is not None
                }
                if freshness_policies_by_output_name
                else None
            ),
            auto_materialize_policies_by_key=(
                {
                    keys_by_output_name_with_prefix[output_name]: auto_materialize_policy
                    for output_name, auto_materialize_policy in auto_materialize_policies_by_output_name.items()
                    if auto_materialize_policy is not None
                }
                if auto_materialize_policies_by_output_name
                else None
            ),
            backfill_policy=check.opt_inst_param(
                backfill_policy, "backfill_policy", BackfillPolicy
            ),
            descriptions_by_key=(
                {
                    keys_by_output_name_with_prefix[output_name]: description
                    for output_name, description in descriptions_by_output_name.items()
                    if description is not None
                }
                if descriptions_by_output_name
                else None
            ),
            can_subset=can_subset,
            selected_asset_keys=None,  # node has no subselection info
            check_specs_by_output_name=check_specs_by_output_name,
            selected_asset_check_keys=None,
            is_subset=False,
            owners_by_key=owners_by_key,
        )

    @public
    @property
    def can_subset(self) -> bool:
        """bool: If True, indicates that this AssetsDefinition may materialize any subset of its
        asset keys in a given computation (as opposed to being required to materialize all asset
        keys).
        """
        return self._can_subset

    @public
    @property
    def group_names_by_key(self) -> Mapping[AssetKey, str]:
        """Mapping[AssetKey, str]: Returns a mapping from the asset keys in this AssetsDefinition
        to the group names assigned to them. If there is no assigned group name for a given AssetKey,
        it will not be present in this dictionary.
        """
        return self._group_names_by_key

    @public
    @property
    def descriptions_by_key(self) -> Mapping[AssetKey, str]:
        """Mapping[AssetKey, str]: Returns a mapping from the asset keys in this AssetsDefinition
        to the descriptions assigned to them. If there is no assigned description for a given AssetKey,
        it will not be present in this dictionary.
        """
        return self._descriptions_by_key

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
        return self._asset_deps

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
    def check_specs_by_output_name(self) -> Mapping[str, AssetCheckSpec]:
        return self._check_specs_by_output_name

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
        return self._freshness_policies_by_key

    @property
    def auto_materialize_policies_by_key(self) -> Mapping[AssetKey, AutoMaterializePolicy]:
        return self._auto_materialize_policies_by_key

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
        return self.metadata_by_key.get(first_key, {}).get(metadata_key) if first_key else None

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
        return self._metadata_by_key

    @property
    def tags_by_key(self) -> Mapping[AssetKey, Mapping[str, str]]:
        return self._tags_by_key

    @property
    def code_versions_by_key(self) -> Mapping[AssetKey, Optional[str]]:
        return self._code_versions_by_key

    @property
    def partition_mappings(self) -> Mapping[AssetKey, PartitionMapping]:
        return self._partition_mappings

    @property
    def owners_by_key(self) -> Mapping[AssetKey, Sequence[AssetOwner]]:
        return self._owners_by_key

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
        return self._check_specs_by_output_name.values()

    @property
    def check_keys(self) -> AbstractSet[AssetCheckKey]:
        """Returns the selected asset checks associated by this AssetsDefinition.

        Returns:
            AbstractSet[Tuple[AssetKey, str]]: The selected asset checks. An asset check is
                identified by the asset key and the name of the check.
        """
        return self._selected_asset_check_keys

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

    def get_op_def_for_asset_key(self, key: AssetKey) -> OpDefinition:
        """If this is an op-backed asset, returns the op def. If it's a graph-backed asset,
        returns the op def within the graph that produces the given asset key.
        """
        output_name = self.get_output_name_for_asset_key(key)
        return self.node_def.resolve_output_to_origin_op_def(output_name)

    def with_attributes(
        self,
        *,
        output_asset_key_replacements: Optional[Mapping[AssetKey, AssetKey]] = None,
        input_asset_key_replacements: Optional[Mapping[AssetKey, AssetKey]] = None,
        group_names_by_key: Optional[Mapping[AssetKey, str]] = None,
        descriptions_by_key: Optional[Mapping[AssetKey, str]] = None,
        metadata_by_key: Optional[Mapping[AssetKey, ArbitraryMetadataMapping]] = None,
        tags_by_key: Optional[Mapping[AssetKey, Mapping[str, str]]] = None,
        freshness_policy: Optional[
            Union[FreshnessPolicy, Mapping[AssetKey, FreshnessPolicy]]
        ] = None,
        auto_materialize_policy: Optional[
            Union[AutoMaterializePolicy, Mapping[AssetKey, AutoMaterializePolicy]]
        ] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        check_specs_by_output_name: Optional[Mapping[str, AssetCheckSpec]] = None,
        selected_asset_check_keys: Optional[AbstractSet[AssetCheckKey]] = None,
    ) -> "AssetsDefinition":
        output_asset_key_replacements = check.opt_mapping_param(
            output_asset_key_replacements,
            "output_asset_key_replacements",
            key_type=AssetKey,
            value_type=AssetKey,
        )
        input_asset_key_replacements = check.opt_mapping_param(
            input_asset_key_replacements,
            "input_asset_key_replacements",
            key_type=AssetKey,
            value_type=AssetKey,
        )
        group_names_by_key = check.opt_mapping_param(
            group_names_by_key, "group_names_by_key", key_type=AssetKey, value_type=str
        )
        descriptions_by_key = check.opt_mapping_param(
            descriptions_by_key, "descriptions_by_key", key_type=AssetKey, value_type=str
        )
        metadata_by_key = check.opt_mapping_param(
            metadata_by_key, "metadata_by_key", key_type=AssetKey, value_type=dict
        )

        backfill_policy = check.opt_inst_param(backfill_policy, "backfill_policy", BackfillPolicy)

        if group_names_by_key:
            group_name_conflicts = [
                asset_key
                for asset_key in group_names_by_key
                if asset_key in self.group_names_by_key
                and self.group_names_by_key[asset_key] != DEFAULT_GROUP_NAME
            ]
            if group_name_conflicts:
                raise DagsterInvalidDefinitionError(
                    "Group name already exists on assets"
                    f" {', '.join(asset_key.to_user_string() for asset_key in group_name_conflicts)}"
                )

        replaced_group_names_by_key = {
            output_asset_key_replacements.get(key, key): group_name
            for key, group_name in self.group_names_by_key.items()
        }

        if freshness_policy:
            freshness_policy_conflicts = (
                self.freshness_policies_by_key.keys()
                if isinstance(freshness_policy, FreshnessPolicy)
                else (freshness_policy.keys() & self.freshness_policies_by_key.keys())
            )
            if freshness_policy_conflicts:
                raise DagsterInvalidDefinitionError(
                    "FreshnessPolicy already exists on assets"
                    f" {', '.join(key.to_string() for key in freshness_policy_conflicts)}"
                )

        replaced_freshness_policies_by_key = {}
        for key in self.keys:
            if isinstance(freshness_policy, FreshnessPolicy):
                replaced_freshness_policy = freshness_policy
            elif freshness_policy:
                replaced_freshness_policy = freshness_policy.get(key)
            else:
                replaced_freshness_policy = self.freshness_policies_by_key.get(key)

            if replaced_freshness_policy:
                replaced_freshness_policies_by_key[output_asset_key_replacements.get(key, key)] = (
                    replaced_freshness_policy
                )

        if auto_materialize_policy:
            auto_materialize_policy_conflicts = (
                self.auto_materialize_policies_by_key.keys()
                if isinstance(auto_materialize_policy, AutoMaterializePolicy)
                else (auto_materialize_policy.keys() & self.auto_materialize_policies_by_key.keys())
            )
            if auto_materialize_policy_conflicts:
                raise DagsterInvalidDefinitionError(
                    "AutoMaterializePolicy already exists on assets"
                    f" {', '.join(key.to_string() for key in auto_materialize_policy_conflicts)}"
                )

        replaced_auto_materialize_policies_by_key = {}
        for key in self.keys:
            if isinstance(auto_materialize_policy, AutoMaterializePolicy):
                replaced_auto_materialize_policy = auto_materialize_policy
            elif auto_materialize_policy:
                replaced_auto_materialize_policy = auto_materialize_policy.get(key)
            else:
                replaced_auto_materialize_policy = self.auto_materialize_policies_by_key.get(key)

            if replaced_auto_materialize_policy:
                replaced_auto_materialize_policies_by_key[
                    output_asset_key_replacements.get(key, key)
                ] = replaced_auto_materialize_policy

        replaced_descriptions_by_key = {
            output_asset_key_replacements.get(key, key): description
            for key, description in descriptions_by_key.items()
        }

        if not metadata_by_key:
            metadata_by_key = self.metadata_by_key

        replaced_metadata_by_key = {
            output_asset_key_replacements.get(key, key): metadata
            for key, metadata in metadata_by_key.items()
        }

        replaced_tags_by_key = {
            output_asset_key_replacements.get(key, key): tags
            for key, tags in self.tags_by_key.items()
        }

        replaced_owners_by_key = {
            output_asset_key_replacements.get(key, key): owners
            for key, owners in self.owners_by_key.items()
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
            partition_mappings={
                input_asset_key_replacements.get(key, key): partition_mapping
                for key, partition_mapping in self._partition_mappings.items()
            },
            asset_deps={
                # replace both the keys and the values in this mapping
                output_asset_key_replacements.get(key, key): {
                    input_asset_key_replacements.get(
                        upstream_key,
                        output_asset_key_replacements.get(upstream_key, upstream_key),
                    )
                    for upstream_key in value
                }
                for key, value in self.asset_deps.items()
            },
            selected_asset_keys={
                output_asset_key_replacements.get(key, key) for key in self._selected_asset_keys
            },
            group_names_by_key={
                **replaced_group_names_by_key,
                **group_names_by_key,
            },
            metadata_by_key={
                **self._metadata_by_key,
                **replaced_metadata_by_key,
            },
            tags_by_key=replaced_tags_by_key,
            owners_by_key=replaced_owners_by_key,
            freshness_policies_by_key=replaced_freshness_policies_by_key,
            auto_materialize_policies_by_key=replaced_auto_materialize_policies_by_key,
            backfill_policy=backfill_policy if backfill_policy else self.backfill_policy,
            descriptions_by_key={
                **self._descriptions_by_key,
                **replaced_descriptions_by_key,
            },
            is_subset=self.is_subset,
            check_specs_by_output_name=check_specs_by_output_name
            if check_specs_by_output_name
            else self.check_specs_by_output_name,
            selected_asset_check_keys=selected_asset_check_keys
            if selected_asset_check_keys
            else self._selected_asset_check_keys,
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

            # An op within the graph-backed asset that yields multiple assets will be run
            # any time any of its output assets are selected. Thus, if an op yields multiple assets
            # and only one of them is selected, the op will still run and potentially unexpectedly
            # materialize the unselected asset.
            #
            # Thus, we include unselected assets that may be accidentally materialized in
            # keys_by_output_name and asset_deps so that the webserver can populate an warning when
            # this occurs. This is the same behavior as multi-asset subsetting.

            subsetted_asset_deps = {
                out_asset_key: set(self._keys_by_input_name.values())
                for out_asset_key in subsetted_keys_by_output_name.values()
            }
            replaced_attributes = dict(
                keys_by_input_name=subsetted_keys_by_input_name,
                keys_by_output_name=subsetted_keys_by_output_name,
                node_def=subsetted_node,
                asset_deps=subsetted_asset_deps,
                selected_asset_keys=selected_asset_keys & self.keys,
                selected_asset_check_keys=asset_check_subselection,
                is_subset=True,
            )

            return self.__class__(**merge_dicts(self.get_attributes_dict(), replaced_attributes))
        else:
            # multi_asset subsetting
            replaced_attributes = {
                "selected_asset_keys": asset_subselection,
                "selected_asset_check_keys": asset_check_subselection,
                "is_subset": True,
            }
            return self.__class__(**merge_dicts(self.get_attributes_dict(), replaced_attributes))

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

            return SourceAsset(
                key=key,
                metadata=output_def.metadata,
                io_manager_key=output_def.io_manager_key,
                description=output_def.description,
                resource_defs=self.resource_defs,
                partitions_def=self.partitions_def,
                group_name=self.group_names_by_key[key],
                tags=self.tags_by_key.get(key),
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
        """A unique identifier for the AssetsDefinition that's stable across processes."""
        return non_secure_md5_hash_str((json.dumps(sorted(self.keys))).encode("utf-8"))

    def with_resources(self, resource_defs: Mapping[str, ResourceDefinition]) -> "AssetsDefinition":
        attributes_dict = self.get_attributes_dict()
        attributes_dict["resource_defs"] = merge_resource_defs(
            old_resource_defs=self.resource_defs,
            resource_defs_to_merge_in=resource_defs,
            requires_resources=self,
        )
        return self.__class__(**attributes_dict)

    def get_attributes_dict(self) -> Dict[str, Any]:
        return dict(
            keys_by_input_name=self._keys_by_input_name,
            keys_by_output_name=self._keys_by_output_name,
            node_def=self._node_def,
            partitions_def=self._partitions_def,
            partition_mappings=self._partition_mappings,
            asset_deps=self.asset_deps,
            selected_asset_keys=self._selected_asset_keys,
            can_subset=self._can_subset,
            resource_defs=self._resource_defs,
            group_names_by_key=self._group_names_by_key,
            metadata_by_key=self._metadata_by_key,
            freshness_policies_by_key=self._freshness_policies_by_key,
            auto_materialize_policies_by_key=self._auto_materialize_policies_by_key,
            backfill_policy=self._backfill_policy,
            descriptions_by_key=self._descriptions_by_key,
            check_specs_by_output_name=self._check_specs_by_output_name,
            selected_asset_check_keys=self._selected_asset_check_keys,
            owners_by_key=self._owners_by_key,
            tags_by_key=self._tags_by_key,
        )


def _infer_keys_by_input_names(
    node_def: Union["GraphDefinition", OpDefinition], keys_by_input_name: Mapping[str, AssetKey]
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
    node_def: Union["GraphDefinition", OpDefinition],
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
