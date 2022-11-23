import warnings
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    Set,
    Union,
    cast,
)

import dagster._check as check
from dagster._annotations import public
from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.asset_layer import get_dep_node_handles_of_graph_backed_asset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.metadata import MetadataUserInput
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.utils import DEFAULT_GROUP_NAME, validate_group_name
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._utils import merge_dicts
from dagster._utils.backcompat import (
    ExperimentalWarning,
    deprecation_warning,
    experimental_arg_warning,
)

from .dependency import NodeHandle
from .events import AssetKey, CoercibleToAssetKeyPrefix
from .node_definition import NodeDefinition
from .op_definition import OpDefinition
from .partition import PartitionsDefinition
from .partition_mapping import PartitionMapping, infer_partition_mapping
from .resource_definition import ResourceDefinition
from .resource_requirement import (
    ResourceAddable,
    ResourceRequirement,
    ensure_requirements_satisfied,
    get_resource_key_conflicts,
)
from .source_asset import SourceAsset
from .utils import DEFAULT_GROUP_NAME, validate_group_name

if TYPE_CHECKING:
    from dagster._core.execution.context.compute import OpExecutionContext

    from .graph_definition import GraphDefinition


class AssetsDefinition(ResourceAddable):
    """
    Defines a set of assets that are produced by the same op or graph.

    AssetsDefinitions are typically not instantiated directly, but rather produced using the
    :py:func:`@asset <asset>` or :py:func:`@multi_asset <multi_asset>` decorators.

    Attributes:
        asset_deps (Mapping[AssetKey, AbstractSet[AssetKey]]): Maps assets that are produced by this
            definition to assets that they depend on. The dependencies can be either "internal",
            meaning that they refer to other assets that are produced by this definition, or
            "external", meaning that they refer to assets that aren't produced by this definition.
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
    _metadata_by_key: Mapping[AssetKey, MetadataUserInput]
    _freshness_policies_by_key: Mapping[AssetKey, FreshnessPolicy]
    _code_versions_by_key: Mapping[AssetKey, Optional[str]]

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
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        group_names_by_key: Optional[Mapping[AssetKey, str]] = None,
        metadata_by_key: Optional[Mapping[AssetKey, MetadataUserInput]] = None,
        freshness_policies_by_key: Optional[Mapping[AssetKey, FreshnessPolicy]] = None,
        # if adding new fields, make sure to handle them in the with_prefix_or_group
        # and from_graph methods
    ):
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

        self._partitions_def = partitions_def
        self._partition_mappings = partition_mappings or {}

        # if not specified assume all output assets depend on all input assets
        all_asset_keys = set(keys_by_output_name.values())
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
        self._resource_defs = check.opt_mapping_param(resource_defs, "resource_defs")

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

        if selected_asset_keys is not None:
            self._selected_asset_keys = selected_asset_keys
        else:
            self._selected_asset_keys = all_asset_keys
        self._can_subset = can_subset

        self._code_versions_by_key = {}
        self._metadata_by_key = dict(
            check.opt_mapping_param(
                metadata_by_key, "metadata_by_key", key_type=AssetKey, value_type=dict
            )
        )
        for output_name, asset_key in keys_by_output_name.items():
            output_def, _ = node_def.resolve_output_to_origin(output_name, None)
            self._metadata_by_key[asset_key] = merge_dicts(
                output_def.metadata,
                self._metadata_by_key.get(asset_key, {}),
            )
            self._code_versions_by_key[asset_key] = output_def.code_version
        for key, freshness_policy in (freshness_policies_by_key or {}).items():
            check.param_invariant(
                not (freshness_policy and self._partitions_def),
                "freshness_policies_by_key",
                "FreshnessPolicies are currently unsupported for partitioned assets.",
            )

        self._freshness_policies_by_key = check.opt_mapping_param(
            freshness_policies_by_key,
            "freshness_policies_by_key",
            key_type=AssetKey,
            value_type=FreshnessPolicy,
        )

    def __call__(self, *args: object, **kwargs: object) -> object:
        from dagster._core.definitions.decorators.solid_decorator import DecoratedSolidFunction
        from dagster._core.execution.context.compute import OpExecutionContext

        from .graph_definition import GraphDefinition

        if isinstance(self.node_def, GraphDefinition):
            return self._node_def(*args, **kwargs)
        solid_def = self.op
        provided_context: Optional[OpExecutionContext] = None
        if len(args) > 0 and isinstance(args[0], OpExecutionContext):
            provided_context = _build_invocation_context_with_included_resources(self, args[0])
            new_args = [provided_context, *args[1:]]
            return solid_def(*new_args, **kwargs)
        elif (
            isinstance(solid_def.compute_fn, DecoratedSolidFunction)
            and solid_def.compute_fn.has_context_arg()
        ):
            context_param_name = get_function_params(solid_def.compute_fn.decorated_fn)[0].name
            if context_param_name in kwargs:
                provided_context = _build_invocation_context_with_included_resources(
                    self, cast(OpExecutionContext, kwargs[context_param_name])
                )
                new_kwargs = dict(kwargs)
                new_kwargs[context_param_name] = provided_context
                return solid_def(*args, **new_kwargs)

        return solid_def(*args, **kwargs)

    @public
    @staticmethod
    def from_graph(
        graph_def: "GraphDefinition",
        *,
        keys_by_input_name: Optional[Mapping[str, AssetKey]] = None,
        keys_by_output_name: Optional[Mapping[str, AssetKey]] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        internal_asset_deps: Optional[Mapping[str, Set[AssetKey]]] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        group_name: Optional[str] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        partition_mappings: Optional[Mapping[str, PartitionMapping]] = None,
        metadata_by_output_name: Optional[Mapping[str, MetadataUserInput]] = None,
        can_subset: bool = False,
    ) -> "AssetsDefinition":
        """
        Constructs an AssetsDefinition from a GraphDefinition.

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
            group_name (Optional[str]): A group name for the constructed asset. Assets without a
                group name are assigned to a group called "default".
            resource_defs (Optional[Mapping[str, ResourceDefinition]]):
                (Experimental) A mapping of resource keys to resource definitions. These resources
                will be initialized during execution, and can be accessed from the
                body of ops in the graph during execution.
            partition_mappings (Optional[Mapping[str, PartitionMapping]]): Defines how to map partition
                keys for this asset to partition keys of upstream assets. Each key in the dictionary
                correponds to one of the input assets, and each value is a PartitionMapping.
                If no entry is provided for a particular asset dependency, the partition mapping defaults
                to the default partition mapping for the partitions definition, which is typically maps
                partition keys to the same partition keys in upstream assets.
            metadata_by_output_name (Optional[Mapping[str, MetadataUserInput]]): Defines metadata to
                be associated with each of the output assets for this node. Keys are names of the
                outputs, and values are dictionaries of metadata to be associated with the related
                asset.
        """
        if resource_defs is not None:
            experimental_arg_warning("resource_defs", "AssetsDefinition.from_graph")
        return AssetsDefinition._from_node(
            node_def=graph_def,
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name=keys_by_output_name,
            internal_asset_deps=internal_asset_deps,
            partitions_def=partitions_def,
            group_name=group_name,
            resource_defs=resource_defs,
            partition_mappings=partition_mappings,
            metadata_by_output_name=metadata_by_output_name,
            key_prefix=key_prefix,
            can_subset=can_subset,
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
        group_name: Optional[str] = None,
        partition_mappings: Optional[Mapping[str, PartitionMapping]] = None,
        metadata_by_output_name: Optional[Mapping[str, MetadataUserInput]] = None,
    ) -> "AssetsDefinition":
        """
        Constructs an AssetsDefinition from an OpDefinition.

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
            group_name (Optional[str]): A group name for the constructed asset. Assets without a
                group name are assigned to a group called "default".
            partition_mappings (Optional[Mapping[str, PartitionMapping]]): Defines how to map partition
                keys for this asset to partition keys of upstream assets. Each key in the dictionary
                correponds to one of the input assets, and each value is a PartitionMapping.
                If no entry is provided for a particular asset dependency, the partition mapping defaults
                to the default partition mapping for the partitions definition, which is typically maps
                partition keys to the same partition keys in upstream assets.
            metadata_by_output_name (Optional[Mapping[str, MetadataUserInput]]): Defines metadata to
                be associated with each of the output assets for this node. Keys are names of the
                outputs, and values are dictionaries of metadata to be associated with the related
                asset.
        """
        return AssetsDefinition._from_node(
            node_def=op_def,
            keys_by_input_name=keys_by_input_name,
            keys_by_output_name=keys_by_output_name,
            internal_asset_deps=internal_asset_deps,
            partitions_def=partitions_def,
            group_name=group_name,
            partition_mappings=partition_mappings,
            metadata_by_output_name=metadata_by_output_name,
            key_prefix=key_prefix,
        )

    @staticmethod
    def _from_node(
        node_def: Union[OpDefinition, "GraphDefinition"],
        *,
        keys_by_input_name: Optional[Mapping[str, AssetKey]] = None,
        keys_by_output_name: Optional[Mapping[str, AssetKey]] = None,
        internal_asset_deps: Optional[Mapping[str, Set[AssetKey]]] = None,
        partitions_def: Optional[PartitionsDefinition] = None,
        group_name: Optional[str] = None,
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
        partition_mappings: Optional[Mapping[str, PartitionMapping]] = None,
        metadata_by_output_name: Optional[Mapping[str, MetadataUserInput]] = None,
        key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
        can_subset: bool = False,
    ) -> "AssetsDefinition":
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

        transformed_internal_asset_deps = {}
        if internal_asset_deps:
            for output_name, asset_keys in internal_asset_deps.items():
                check.invariant(
                    output_name in keys_by_output_name,
                    f"output_name {output_name} specified in internal_asset_deps does not exist in the decorated function",
                )
                transformed_internal_asset_deps[keys_by_output_name[output_name]] = asset_keys

        keys_by_output_name = _infer_keys_by_output_names(node_def, keys_by_output_name or {})

        keys_by_output_name_with_prefix: Dict[str, AssetKey] = {}
        key_prefix_list = [key_prefix] if isinstance(key_prefix, str) else key_prefix
        for output_name, key in keys_by_output_name.items():
            # add key_prefix to the beginning of each asset key
            key_with_key_prefix = AssetKey(
                list(filter(None, [*(key_prefix_list or []), *key.path]))
            )
            keys_by_output_name_with_prefix[output_name] = key_with_key_prefix

        # For graph backed assets, we assign all assets to the same group_name, if specified.
        # To assign to different groups, use .with_prefix_or_groups.
        group_names_by_key = (
            {asset_key: group_name for asset_key in keys_by_output_name_with_prefix.values()}
            if group_name
            else None
        )

        return AssetsDefinition(
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
            partition_mappings={
                keys_by_input_name[input_name]: partition_mapping
                for input_name, partition_mapping in partition_mappings.items()
            }
            if partition_mappings
            else None,
            metadata_by_key={
                keys_by_output_name[output_name]: metadata
                for output_name, metadata in metadata_by_output_name.items()
            }
            if metadata_by_output_name
            else None,
            can_subset=can_subset,
        )

    @public  # type: ignore
    @property
    def can_subset(self) -> bool:
        return self._can_subset

    @public  # type: ignore
    @property
    def group_names_by_key(self) -> Mapping[AssetKey, str]:
        return self._group_names_by_key

    @public  # type: ignore
    @property
    def op(self) -> OpDefinition:
        check.invariant(
            isinstance(self._node_def, OpDefinition),
            "The NodeDefinition for this AssetsDefinition is not of type OpDefinition.",
        )
        return cast(OpDefinition, self._node_def)

    @public  # type: ignore
    @property
    def node_def(self) -> NodeDefinition:
        return self._node_def

    @public  # type: ignore
    @property
    def asset_deps(self) -> Mapping[AssetKey, AbstractSet[AssetKey]]:
        return self._asset_deps

    @property
    def input_names(self) -> Iterable[str]:
        return self.keys_by_input_name.keys()

    @public  # type: ignore
    @property
    def key(self) -> AssetKey:
        check.invariant(
            len(self.keys) == 1,
            "Tried to retrieve asset key from an assets definition with multiple asset keys: "
            + ", ".join([str(ak.to_string()) for ak in self._keys_by_output_name.values()]),
        )

        return next(iter(self.keys))

    @property
    def asset_key(self) -> AssetKey:
        deprecation_warning(
            "AssetsDefinition.asset_key", "1.0.0", "Use AssetsDefinition.key instead."
        )
        return self.key

    @public  # type: ignore
    @property
    def resource_defs(self) -> Mapping[str, ResourceDefinition]:
        return dict(self._resource_defs)

    @public  # type: ignore
    @property
    def keys(self) -> AbstractSet[AssetKey]:
        return self._selected_asset_keys

    @property
    def asset_keys(self) -> AbstractSet[AssetKey]:
        deprecation_warning(
            "AssetsDefinition.asset_keys", "1.0.0", "Use AssetsDefinition.keys instead."
        )
        return self.keys

    @public  # type: ignore
    @property
    def dependency_keys(self) -> Iterable[AssetKey]:
        # the input asset keys that are directly upstream of a selected asset key
        upstream_keys = set().union(*(self.asset_deps[key] for key in self.keys))
        input_keys = set(self._keys_by_input_name.values())
        return upstream_keys.intersection(input_keys)

    @property
    def node_keys_by_output_name(self) -> Mapping[str, AssetKey]:
        """AssetKey for each output on the underlying NodeDefinition"""
        return self._keys_by_output_name

    @property
    def node_keys_by_input_name(self) -> Mapping[str, AssetKey]:
        """AssetKey for each input on the underlying NodeDefinition"""
        return self._keys_by_input_name

    @property
    def keys_by_output_name(self) -> Mapping[str, AssetKey]:
        return {
            name: key for name, key in self.node_keys_by_output_name.items() if key in self.keys
        }

    @property
    def keys_by_input_name(self) -> Mapping[str, AssetKey]:
        upstream_keys = set().union(*(self.asset_deps[key] for key in self.keys))
        return {
            name: key for name, key in self.node_keys_by_input_name.items() if key in upstream_keys
        }

    @property
    def freshness_policies_by_key(self) -> Mapping[AssetKey, FreshnessPolicy]:
        return self._freshness_policies_by_key

    @public  # type: ignore
    @property
    def partitions_def(self) -> Optional[PartitionsDefinition]:
        return self._partitions_def

    @property
    def metadata_by_key(self):
        return self._metadata_by_key

    @property
    def code_versions_by_key(self):
        return self._code_versions_by_key

    @public
    def get_partition_mapping(self, in_asset_key: AssetKey) -> PartitionMapping:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)

            partition_mapping = self._partition_mappings.get(in_asset_key)
            return infer_partition_mapping(partition_mapping, self._partitions_def)

    def get_output_name_for_asset_key(self, key: AssetKey) -> str:
        for output_name, asset_key in self.keys_by_output_name.items():
            if key == asset_key:
                return output_name

        check.failed(f"Asset key {key.to_user_string()} not found in AssetsDefinition")

    def get_op_def_for_asset_key(self, key: AssetKey) -> OpDefinition:
        """
        If this is an op-backed asset, returns the op def. If it's a graph-backed asset,
        returns the op def within the graph that produces the given asset key.
        """
        output_name = self.get_output_name_for_asset_key(key)
        return cast(OpDefinition, self.node_def.resolve_output_to_origin_op_def(output_name))

    def with_prefix_or_group(
        self,
        output_asset_key_replacements: Optional[Mapping[AssetKey, AssetKey]] = None,
        input_asset_key_replacements: Optional[Mapping[AssetKey, AssetKey]] = None,
        group_names_by_key: Optional[Mapping[AssetKey, str]] = None,
    ) -> "AssetsDefinition":
        from dagster import DagsterInvalidDefinitionError

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

        defined_group_names = [
            asset_key.to_user_string()
            for asset_key in group_names_by_key
            if asset_key in self.group_names_by_key
            and self.group_names_by_key[asset_key] != DEFAULT_GROUP_NAME
        ]
        if defined_group_names:
            raise DagsterInvalidDefinitionError(
                f"Group name already exists on assets {', '.join(defined_group_names)}"
            )

        replaced_group_names_by_key = {
            output_asset_key_replacements.get(key, key): group_name
            for key, group_name in self.group_names_by_key.items()
        }

        replaced_freshness_policies_by_key = {
            output_asset_key_replacements.get(key, key): policy
            for key, policy in self._freshness_policies_by_key.items()
        }

        return self.__class__(
            keys_by_input_name={
                input_name: input_asset_key_replacements.get(key, key)
                for input_name, key in self._keys_by_input_name.items()
            },
            keys_by_output_name={
                output_name: output_asset_key_replacements.get(key, key)
                for output_name, key in self._keys_by_output_name.items()
            },
            node_def=self.node_def,
            partitions_def=self.partitions_def,
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
            can_subset=self.can_subset,
            selected_asset_keys={
                output_asset_key_replacements.get(key, key) for key in self._selected_asset_keys
            },
            resource_defs=self.resource_defs,
            group_names_by_key={
                **replaced_group_names_by_key,
                **group_names_by_key,
            },
            freshness_policies_by_key=replaced_freshness_policies_by_key,
        )

    def _subset_graph_backed_asset(
        self,
        selected_asset_keys: AbstractSet[AssetKey],
    ):
        from dagster._core.definitions.graph_definition import GraphDefinition
        from dagster._core.selector.subset_selector import convert_dot_seperated_string_to_dict

        from .job_definition import get_subselected_graph_definition

        if not isinstance(self.node_def, GraphDefinition):
            raise DagsterInvalidInvocationError(
                "Method _subset_graph_backed_asset cannot subset an asset that is not a graph"
            )

        # All asset keys in selected_asset_keys are outputted from the same top-level graph backed asset
        dep_node_handles_by_asset_key = get_dep_node_handles_of_graph_backed_asset(
            self.node_def, self
        )
        op_selection = []
        for asset_key in selected_asset_keys:
            dep_node_handles = dep_node_handles_by_asset_key[asset_key]
            for dep_node_handle in dep_node_handles:
                str_op_path = ".".join(dep_node_handle.path[1:])
                op_selection.append(str_op_path)

        # Pass an op selection into the original job containing only the ops necessary to
        # generate the selected assets. The ops should all be nested within a top-level graph
        # node in the original job.

        resolved_op_selection_dict: Dict = {}
        for item in op_selection:
            convert_dot_seperated_string_to_dict(resolved_op_selection_dict, splits=item.split("."))

        return get_subselected_graph_definition(self.node_def, resolved_op_selection_dict)

    def subset_for(
        self,
        selected_asset_keys: AbstractSet[AssetKey],
    ) -> "AssetsDefinition":
        """
        Create a subset of this AssetsDefinition that will only materialize the assets in the
        selected set.

        Args:
            selected_asset_keys (AbstractSet[AssetKey]): The total set of asset keys
        """
        from dagster._core.definitions.graph_definition import GraphDefinition

        check.invariant(
            self.can_subset,
            f"Attempted to subset AssetsDefinition for {self.node_def.name}, but can_subset=False.",
        )

        # Set of assets within selected_asset_keys which are outputted by this AssetDefinition
        asset_subselection = selected_asset_keys & self.keys
        # Early escape if all assets in AssetsDefinition are selected
        if asset_subselection == self.keys:
            return self
        elif isinstance(self.node_def, GraphDefinition):  # Node is graph-backed asset
            subsetted_node = self._subset_graph_backed_asset(
                asset_subselection,
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
            # keys_by_output_name and asset_deps so that Dagit can populate an warning when this
            # occurs. This is the same behavior as multi-asset subsetting.

            subsetted_asset_deps = {
                out_asset_key: set(self._keys_by_input_name.values())
                for out_asset_key in subsetted_keys_by_output_name.values()
            }

            return AssetsDefinition(
                keys_by_input_name=subsetted_keys_by_input_name,
                keys_by_output_name=subsetted_keys_by_output_name,
                node_def=subsetted_node,
                partitions_def=self.partitions_def,
                partition_mappings=self._partition_mappings,
                asset_deps=subsetted_asset_deps,
                can_subset=self.can_subset,
                selected_asset_keys=selected_asset_keys & self.keys,
                resource_defs=self.resource_defs,
                group_names_by_key=self.group_names_by_key,
                freshness_policies_by_key=self.freshness_policies_by_key,
            )
        else:
            # multi_asset subsetting
            return AssetsDefinition(
                # keep track of the original mapping
                keys_by_input_name=self._keys_by_input_name,
                keys_by_output_name=self._keys_by_output_name,
                node_def=self.node_def,
                partitions_def=self.partitions_def,
                partition_mappings=self._partition_mappings,
                asset_deps=self._asset_deps,
                can_subset=self.can_subset,
                selected_asset_keys=asset_subselection,
                resource_defs=self.resource_defs,
                group_names_by_key=self.group_names_by_key,
            )

    def to_source_assets(self) -> Sequence[SourceAsset]:
        result = []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ExperimentalWarning)

            for output_name, asset_key in self.keys_by_output_name.items():
                # This could maybe be sped up by batching
                output_def = self.node_def.resolve_output_to_origin(
                    output_name, NodeHandle(self.node_def.name, parent=None)
                )[0]
                result.append(
                    SourceAsset(
                        key=asset_key,
                        metadata=output_def.metadata,
                        io_manager_key=output_def.io_manager_key,
                        description=output_def.description,
                        resource_defs=self.resource_defs,
                        partitions_def=self.partitions_def,
                        group_name=self.group_names_by_key[asset_key],
                    )
                )

            return result

    def get_io_manager_key_for_asset_key(self, key: AssetKey) -> str:
        output_name = self.get_output_name_for_asset_key(key)
        return self.node_def.resolve_output_to_origin(
            output_name, NodeHandle(self.node_def.name, parent=None)
        )[0].io_manager_key

    def get_resource_requirements(self) -> Iterator[ResourceRequirement]:
        yield from self.node_def.get_resource_requirements()  # type: ignore[attr-defined]
        for source_key, resource_def in self.resource_defs.items():
            yield from resource_def.get_resource_requirements(outer_context=source_key)

    @public  # type: ignore
    @property
    def required_resource_keys(self) -> Set[str]:
        return {requirement.key for requirement in self.get_resource_requirements()}

    def __str__(self):
        if len(self.asset_keys) == 1:
            return f"AssetsDefinition with key {self.asset_key.to_string()}"
        else:
            asset_keys = ", ".join(
                sorted(list([asset_key.to_string() for asset_key in self.asset_keys]))
            )
            return f"AssetsDefinition with keys {asset_keys}"

    def with_resources(self, resource_defs: Mapping[str, ResourceDefinition]) -> "AssetsDefinition":
        from dagster._core.execution.resources_init import get_transitive_required_resource_keys

        overlapping_keys = get_resource_key_conflicts(self.resource_defs, resource_defs)
        if overlapping_keys:
            overlapping_keys_str = ", ".join(sorted(list(overlapping_keys)))
            raise DagsterInvalidInvocationError(
                f"{str(self)} has conflicting resource "
                "definitions with provided resources for the following keys: "
                f"{overlapping_keys_str}. Either remove the existing "
                "resources from the asset or change the resource keys so that "
                "they don't overlap."
            )

        merged_resource_defs = merge_dicts(resource_defs, self.resource_defs)

        # Ensure top-level resource requirements are met - except for
        # io_manager, since that is a default it can be resolved later.
        ensure_requirements_satisfied(merged_resource_defs, list(self.get_resource_requirements()))

        # Get all transitive resource dependencies from other resources.
        relevant_keys = get_transitive_required_resource_keys(
            self.required_resource_keys, merged_resource_defs
        )
        relevant_resource_defs = {
            key: resource_def
            for key, resource_def in merged_resource_defs.items()
            if key in relevant_keys
        }

        return AssetsDefinition(
            keys_by_input_name=self._keys_by_input_name,
            keys_by_output_name=self._keys_by_output_name,
            node_def=self.node_def,
            partitions_def=self._partitions_def,
            partition_mappings=self._partition_mappings,
            asset_deps=self._asset_deps,
            selected_asset_keys=self._selected_asset_keys,
            can_subset=self._can_subset,
            resource_defs=relevant_resource_defs,
            group_names_by_key=self.group_names_by_key,
            freshness_policies_by_key=self.freshness_policies_by_key,
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
    node_def: Union["GraphDefinition", OpDefinition], keys_by_output_name: Mapping[str, AssetKey]
) -> Mapping[str, AssetKey]:
    output_names = [output_def.name for output_def in node_def.output_defs]
    if keys_by_output_name:
        check.invariant(
            set(keys_by_output_name.keys()) == set(output_names),
            "The set of output names keys specified in the keys_by_output_name argument must "
            f"equal the set of asset keys outputted by {node_def.name}. \n"
            f"keys_by_input_name keys: {set(keys_by_output_name.keys())} \n"
            f"expected keys: {set(output_names)}",
        )

    inferred_keys_by_output_names: Dict[str, AssetKey] = {
        output_name: asset_key for output_name, asset_key in keys_by_output_name.items()
    }

    if (
        len(output_names) == 1
        and output_names[0] not in keys_by_output_name
        and output_names[0] == "result"
    ):
        # If there is only one output and the name is the default "result", generate asset key
        # from the name of the node
        inferred_keys_by_output_names[output_names[0]] = AssetKey([node_def.name])

    for output_name in output_names:
        if output_name not in inferred_keys_by_output_names:
            inferred_keys_by_output_names[output_name] = AssetKey([output_name])
    return inferred_keys_by_output_names


def _build_invocation_context_with_included_resources(
    assets_def: AssetsDefinition,
    context: "OpExecutionContext",
) -> "OpExecutionContext":
    from dagster._core.execution.context.invocation import (
        UnboundSolidExecutionContext,
        build_op_context,
    )

    resource_defs = assets_def.resource_defs
    invocation_resources = context.resources._asdict()
    for resource_key in sorted(list(invocation_resources.keys())):
        if resource_key in resource_defs:
            raise DagsterInvalidInvocationError(
                f"Error when invoking {str(assets_def)}: resource '{resource_key}' "
                "provided on both the definition and invocation context. Please "
                "provide on only one or the other."
            )
    all_resources = merge_dicts(resource_defs, invocation_resources)

    if isinstance(context, UnboundSolidExecutionContext):
        context = cast(UnboundSolidExecutionContext, context)
        # pylint: disable=protected-access
        return build_op_context(
            resources=all_resources,
            config=context.solid_config,
            resources_config=context._resources_config,
            instance=context._instance,
            partition_key=context._partition_key,
            mapping_key=context._mapping_key,
        )
    else:
        # If user is mocking OpExecutionContext, send it through (we don't know
        # what modifications they might be making, and we don't want to override)
        return context


def _validate_graph_def(graph_def: "GraphDefinition", prefix: Optional[Sequence[str]] = None):
    """Ensure that all leaf nodes are mapped to graph outputs."""
    from dagster._core.definitions.graph_definition import GraphDefinition, _create_adjacency_lists

    prefix = check.opt_sequence_param(prefix, "prefix")

    # recursively validate any sub-graphs
    for inner_node_def in graph_def.node_defs:
        if isinstance(inner_node_def, GraphDefinition):
            _validate_graph_def(inner_node_def, prefix=[*prefix, graph_def.name])

    # leaf nodes have no downstream nodes
    forward_edges, _ = _create_adjacency_lists(graph_def.solids, graph_def.dependency_structure)
    leaf_nodes = {
        node_name for node_name, downstream_nodes in forward_edges.items() if not downstream_nodes
    }

    # set of nodes that have outputs mapped to a graph output
    mapped_output_nodes = {
        output_mapping.maps_from.solid_name for output_mapping in graph_def.output_mappings
    }

    # leaf nodes which do not have an associated mapped output
    unmapped_leaf_nodes = {".".join([*prefix, node]) for node in leaf_nodes - mapped_output_nodes}

    check.invariant(
        not unmapped_leaf_nodes,
        f"All leaf nodes within graph '{graph_def.name}' must generate outputs which are mapped to "
        "outputs of the graph, and produce assets. The following leaf node(s) are non-asset producing "
        f"ops: {unmapped_leaf_nodes}. This behavior is not currently supported because these ops "
        "are not required for the creation of the associated asset(s).",
    )
