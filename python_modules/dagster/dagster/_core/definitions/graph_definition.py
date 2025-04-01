from collections import OrderedDict, defaultdict
from collections.abc import Iterable, Iterator, Mapping, Sequence, Set
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

from toposort import CircularDependencyError
from typing_extensions import Self

import dagster._check as check
from dagster._annotations import deprecated_param, public
from dagster._core.definitions.config import ConfigMapping
from dagster._core.definitions.definition_config_schema import IDefinitionConfigSchema
from dagster._core.definitions.dependency import (
    DependencyMapping,
    DependencyStructure,
    GraphNode,
    Node,
    NodeHandle,
    NodeInput,
    NodeInputHandle,
    NodeInvocation,
    NodeOutput,
    NodeOutputHandle,
)
from dagster._core.definitions.hook_definition import HookDefinition
from dagster._core.definitions.input import (
    FanInInputPointer,
    InputDefinition,
    InputMapping,
    InputPointer,
)
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.metadata import RawMetadataValue
from dagster._core.definitions.node_container import (
    create_execution_structure,
    normalize_dependency_dict,
)
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.output import OutputDefinition, OutputMapping
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_requirement import ResourceRequirement
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster._core.selector.subset_selector import AssetSelectionData
from dagster._core.types.dagster_type import (
    DagsterType,
    DagsterTypeKind,
    construct_dagster_type_dictionary,
)
from dagster._core.utils import toposort_flatten
from dagster._utils.warnings import normalize_renamed_param

if TYPE_CHECKING:
    from dagster._core.definitions.asset_layer import AssetLayer
    from dagster._core.definitions.assets import AssetsDefinition
    from dagster._core.definitions.composition import PendingNodeInvocation
    from dagster._core.definitions.executor_definition import ExecutorDefinition
    from dagster._core.definitions.job_definition import JobDefinition
    from dagster._core.definitions.op_definition import OpDefinition
    from dagster._core.definitions.partition import PartitionedConfig, PartitionsDefinition
    from dagster._core.definitions.run_config import RunConfig
    from dagster._core.definitions.source_asset import SourceAsset
    from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
    from dagster._core.instance import DagsterInstance

T = TypeVar("T")


def _check_node_defs_arg(
    graph_name: str, node_defs: Optional[Sequence[NodeDefinition]]
) -> Sequence[NodeDefinition]:
    node_defs = node_defs or []

    _node_defs = check.opt_sequence_param(node_defs, "node_defs")
    for node_def in _node_defs:
        if isinstance(node_def, NodeDefinition):
            continue
        elif callable(node_def):
            raise DagsterInvalidDefinitionError(
                f"""You have passed a lambda or function {node_def.__name__} into {graph_name} that is
                not a node. You have likely forgetten to annotate this function with
                the @op or @graph decorators.'
                """
            )
        else:
            raise DagsterInvalidDefinitionError(f"Invalid item in node list: {node_def!r}")

    return node_defs


def create_adjacency_lists(
    nodes: Sequence[Node],
    dep_structure: DependencyStructure,
) -> tuple[Mapping[str, set[str]], Mapping[str, set[str]]]:
    visit_dict = {s.name: False for s in nodes}
    forward_edges: dict[str, set[str]] = {s.name: set() for s in nodes}
    backward_edges: dict[str, set[str]] = {s.name: set() for s in nodes}

    def visit(node_name: str) -> None:
        if visit_dict[node_name]:
            return

        visit_dict[node_name] = True

        for node_output in dep_structure.all_upstream_outputs_from_node(node_name):
            forward_node = node_output.node.name
            backward_node = node_name
            if forward_node in forward_edges:
                forward_edges[forward_node].add(backward_node)
                backward_edges[backward_node].add(forward_node)
                visit(forward_node)

    for s in nodes:
        visit(s.name)

    return (forward_edges, backward_edges)


@deprecated_param(
    param="node_input_source_assets",
    breaking_version="2.0",
    additional_warn_text="Use `input_assets` instead.",
)
class GraphDefinition(NodeDefinition):
    """Defines a Dagster op graph.

    An op graph is made up of

    - Nodes, which can either be an op (the functional unit of computation), or another graph.
    - Dependencies, which determine how the values produced by nodes as outputs flow from
      one node to another. This tells Dagster how to arrange nodes into a directed, acyclic graph
      (DAG) of compute.

    End users should prefer the :func:`@graph <graph>` decorator. GraphDefinition is generally
    intended to be used by framework authors or for programatically generated graphs.

    Args:
        name (str): The name of the graph. Must be unique within any :py:class:`GraphDefinition`
            or :py:class:`JobDefinition` containing the graph.
        description (Optional[str]): A human-readable description of the job.
        node_defs (Optional[Sequence[NodeDefinition]]): The set of ops / graphs used in this graph.
        dependencies (Optional[Dict[Union[str, NodeInvocation], Dict[str, DependencyDefinition]]]):
            A structure that declares the dependencies of each op's inputs on the outputs of other
            ops in the graph. Keys of the top level dict are either the string names of ops in the
            graph or, in the case of aliased ops, :py:class:`NodeInvocations <NodeInvocation>`.
            Values of the top level dict are themselves dicts, which map input names belonging to
            the op or aliased op to :py:class:`DependencyDefinitions <DependencyDefinition>`.
        input_mappings (Optional[Sequence[InputMapping]]): Defines the inputs to the nested graph, and
            how they map to the inputs of its constituent ops.
        output_mappings (Optional[Sequence[OutputMapping]]): Defines the outputs of the nested graph,
            and how they map from the outputs of its constituent ops.
        config (Optional[ConfigMapping]): Defines the config of the graph, and how its schema maps
            to the config of its constituent ops.
        tags (Optional[Dict[str, Any]]): Arbitrary metadata for any execution of the graph.
            Values that are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.  These tag values may be overwritten by tag
            values provided at invocation time.
        composition_fn (Optional[Callable]): The function that defines this graph. Used to generate
            code references for this graph.

    Examples:
        .. code-block:: python

            @op
            def return_one():
                return 1

            @op
            def add_one(num):
                return num + 1

            graph_def = GraphDefinition(
                name='basic',
                node_defs=[return_one, add_one],
                dependencies={'add_one': {'num': DependencyDefinition('return_one')}},
            )
    """

    _node_defs: Sequence[NodeDefinition]
    _dagster_type_dict: Mapping[str, DagsterType]
    _dependencies: DependencyMapping[NodeInvocation]
    _dependency_structure: DependencyStructure
    _node_dict: Mapping[str, Node]
    _input_mappings: Sequence[InputMapping]
    _output_mappings: Sequence[OutputMapping]
    _config_mapping: Optional[ConfigMapping]
    _nodes_in_topological_order: Sequence[Node]

    # (node name within the graph -> (input name -> AssetsDefinition to load that input from))
    # Does NOT include keys for:
    # - Inputs to the graph itself
    # - Inputs to nodes within sub-graphs of the graph
    _input_assets: Mapping[str, Mapping[str, "AssetsDefinition"]]

    def __init__(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        node_defs: Optional[Sequence[NodeDefinition]] = None,
        dependencies: Optional[
            Union[DependencyMapping[str], DependencyMapping[NodeInvocation]]
        ] = None,
        input_mappings: Optional[Sequence[InputMapping]] = None,
        output_mappings: Optional[Sequence[OutputMapping]] = None,
        config: Optional[ConfigMapping] = None,
        tags: Optional[Mapping[str, str]] = None,
        node_input_source_assets: Optional[Mapping[str, Mapping[str, "SourceAsset"]]] = None,
        input_assets: Optional[
            Mapping[str, Mapping[str, Union["AssetsDefinition", "SourceAsset"]]]
        ] = None,
        composition_fn: Optional[Callable] = None,
        **kwargs: Any,
    ):
        from dagster._core.definitions.external_asset import create_external_asset_from_source_asset
        from dagster._core.definitions.source_asset import SourceAsset

        self._node_defs = _check_node_defs_arg(name, node_defs)

        # `dependencies` will be converted to `dependency_structure` and `node_dict`, which may
        # alternatively be passed directly (useful when copying)
        self._dependencies = normalize_dependency_dict(dependencies)
        self._dependency_structure, self._node_dict = create_execution_structure(
            self._node_defs, self._dependencies, graph_definition=self
        )

        # Sequence[InputMapping]
        self._input_mappings = check.opt_sequence_param(input_mappings, "input_mappings")
        input_defs = _validate_in_mappings(
            self._input_mappings,
            self._node_dict,
            self._dependency_structure,
            name,
            class_name=type(self).__name__,
        )

        # Sequence[OutputMapping]
        self._output_mappings, output_defs = _validate_out_mappings(
            check.opt_sequence_param(output_mappings, "output_mappings"),
            self._node_dict,
            name,
            class_name=type(self).__name__,
        )

        self._config_mapping = check.opt_inst_param(config, "config", ConfigMapping)

        self._composition_fn = check.opt_callable_param(composition_fn, "composition_fn")

        super().__init__(
            name=name,
            description=description,
            input_defs=input_defs,
            output_defs=output_defs,
            tags=tags,
            **kwargs,
        )

        # must happen after base class construction as properties are assumed to be there
        # eager computation to detect cycles
        self._nodes_in_topological_order = self._get_nodes_in_topological_order()
        self._dagster_type_dict = construct_dagster_type_dictionary([self])

        # Backcompat: the previous  API `node_input_source_assets` with a Dict[str, Dict[str,
        # SourceAsset]]. The new API is `input_assets` and accepts external assets as well as
        # SourceAsset.
        self._input_assets = {}
        input_assets = check.opt_mapping_param(
            normalize_renamed_param(
                new_val=input_assets,
                new_arg="input_assets",
                old_val=node_input_source_assets,
                old_arg="node_input_source_assets",
            ),
            "input_assets",
            key_type=str,
            value_type=dict,
        )
        for node_name, inputs in input_assets.items():
            self._input_assets[node_name] = {
                input_name: (
                    create_external_asset_from_source_asset(asset)
                    if isinstance(asset, SourceAsset)
                    else asset
                )
                for input_name, asset in inputs.items()
            }

    def _get_nodes_in_topological_order(self) -> Sequence[Node]:
        _forward_edges, backward_edges = create_adjacency_lists(
            self.nodes, self.dependency_structure
        )

        try:
            order = toposort_flatten(backward_edges)
        except CircularDependencyError as err:
            raise DagsterInvalidDefinitionError(str(err)) from err

        return [self.node_named(node_name) for node_name in order]

    def get_inputs_must_be_resolved_top_level(
        self, asset_layer: "AssetLayer", handle: Optional[NodeHandle] = None
    ) -> Sequence[InputDefinition]:
        unresolveable_input_defs: list[InputDefinition] = []
        for node in self.node_dict.values():
            cur_handle = NodeHandle(node.name, handle)
            for input_def in node.definition.get_inputs_must_be_resolved_top_level(
                asset_layer, cur_handle
            ):
                if self.dependency_structure.has_deps(NodeInput(node, input_def)):
                    continue
                elif not node.container_maps_input(input_def.name):
                    raise DagsterInvalidDefinitionError(
                        f"Input '{input_def.name}' of {node.describe_node()} "
                        "has no way of being resolved. Must provide a resolution to this "
                        "input via another op/graph, or via a direct input value mapped from the "
                        "top-level graph. To "
                        "learn more, see the docs for unconnected inputs: "
                        "https://legacy-docs.dagster.io/concepts/io-management/unconnected-inputs#unconnected-inputs."
                    )
                else:
                    mapped_input = node.container_mapped_input(input_def.name)
                    unresolveable_input_defs.append(mapped_input.get_definition())
        return unresolveable_input_defs

    @property
    def node_type_str(self) -> str:
        return "graph"

    @property
    def is_graph_job_op_node(self) -> bool:
        return True

    @property
    def nodes(self) -> Sequence[Node]:
        return list(set(self._node_dict.values()))

    @property
    def node_dict(self) -> Mapping[str, Node]:
        return self._node_dict

    @property
    def node_defs(self) -> Sequence[NodeDefinition]:
        return self._node_defs

    @property
    def nodes_in_topological_order(self) -> Sequence[Node]:
        return self._nodes_in_topological_order

    @property
    def input_assets(self) -> Mapping[str, Mapping[str, "AssetsDefinition"]]:
        return self._input_assets

    @property
    def composition_fn(self) -> Optional[Callable]:
        return self._composition_fn

    def has_node_named(self, name: str) -> bool:
        check.str_param(name, "name")
        return name in self._node_dict

    def node_named(self, name: str) -> Node:
        check.str_param(name, "name")
        if name not in self._node_dict:
            raise DagsterInvariantViolationError(f"{self._name} has no op named {name}.")

        return self._node_dict[name]

    def get_node(self, handle: NodeHandle) -> Node:
        check.inst_param(handle, "handle", NodeHandle)
        current = handle
        lineage: list[str] = []
        while current:
            lineage.append(current.name)
            current = current.parent

        name = lineage.pop()
        node = self.node_named(name)
        while lineage:
            name = lineage.pop()
            # We know that this is a current node is a graph while ascending lineage
            definition = cast(GraphDefinition, node.definition)
            node = definition.node_named(name)

        return node

    def iterate_node_defs(self) -> Iterator[NodeDefinition]:
        yield self
        for outer_node_def in self._node_defs:
            yield from outer_node_def.iterate_node_defs()

    def iterate_op_defs(self) -> Iterator["OpDefinition"]:
        for outer_node_def in self._node_defs:
            yield from outer_node_def.iterate_op_defs()

    def iterate_node_handles(
        self, parent_node_handle: Optional[NodeHandle] = None
    ) -> Iterator[NodeHandle]:
        for node in self.node_dict.values():
            cur_node_handle = NodeHandle(node.name, parent_node_handle)
            if isinstance(node, GraphNode):
                yield from node.definition.iterate_node_handles(cur_node_handle)
            yield cur_node_handle

    @public
    @property
    def input_mappings(self) -> Sequence[InputMapping]:
        """Input mappings for the graph.

        An input mapping is a mapping from an input of the graph to an input of a child node.
        """
        return self._input_mappings

    @public
    @property
    def output_mappings(self) -> Sequence[OutputMapping]:
        """Output mappings for the graph.

        An output mapping is a mapping from an output of the graph to an output of a child node.
        """
        return self._output_mappings

    @public
    @property
    def config_mapping(self) -> Optional[ConfigMapping]:
        """The config mapping for the graph, if present.

        By specifying a config mapping function, you can override the configuration for the child nodes contained within a graph.
        """
        return self._config_mapping

    @property
    def has_config_mapping(self) -> bool:
        return self._config_mapping is not None

    def all_dagster_types(self) -> Iterable[DagsterType]:
        return self._dagster_type_dict.values()

    def has_dagster_type(self, name: str) -> bool:
        check.str_param(name, "name")
        return name in self._dagster_type_dict

    def dagster_type_named(self, name: str) -> DagsterType:
        check.str_param(name, "name")
        return self._dagster_type_dict[name]

    def get_input_mapping(self, input_name: str) -> InputMapping:
        check.str_param(input_name, "input_name")
        for mapping in self._input_mappings:
            if mapping.graph_input_name == input_name:
                return mapping
        check.failed(f"Could not find input mapping {input_name}")

    def input_mapping_for_pointer(
        self, pointer: Union[InputPointer, FanInInputPointer]
    ) -> Optional[InputMapping]:
        check.inst_param(pointer, "pointer", (InputPointer, FanInInputPointer))

        for mapping in self._input_mappings:
            if mapping.maps_to == pointer:
                return mapping
        return None

    def get_output_mapping(self, output_name: str) -> OutputMapping:
        check.str_param(output_name, "output_name")
        for mapping in self._output_mappings:
            if mapping.graph_output_name == output_name:
                return mapping
        check.failed(f"Could not find output mapping {output_name}")

    def resolve_output_to_origin(
        self, output_name: str, handle: Optional[NodeHandle]
    ) -> tuple[OutputDefinition, Optional[NodeHandle]]:
        check.str_param(output_name, "output_name")
        check.opt_inst_param(handle, "handle", NodeHandle)

        mapping = self.get_output_mapping(output_name)
        check.invariant(mapping, "Can only resolve outputs for valid output names")
        mapped_node = self.node_named(mapping.maps_from.node_name)
        return mapped_node.definition.resolve_output_to_origin(
            mapping.maps_from.output_name,
            NodeHandle(mapped_node.name, handle),
        )

    def resolve_output_to_origin_op_def(self, output_name: str) -> "OpDefinition":
        mapping = self.get_output_mapping(output_name)
        check.invariant(mapping, "Can only resolve outputs for valid output names")
        return self.node_named(
            mapping.maps_from.node_name
        ).definition.resolve_output_to_origin_op_def(output_name)

    def default_value_for_input(self, input_name: str) -> object:
        check.str_param(input_name, "input_name")

        # base case
        if self.input_def_named(input_name).has_default_value:
            return self.input_def_named(input_name).default_value

        mapping = self.get_input_mapping(input_name)
        check.invariant(mapping, "Can only resolve inputs for valid input names")
        mapped_node = self.node_named(mapping.maps_to.node_name)

        return mapped_node.definition.default_value_for_input(mapping.maps_to.input_name)

    def input_has_default(self, input_name: str) -> bool:
        check.str_param(input_name, "input_name")

        # base case
        if self.input_def_named(input_name).has_default_value:
            return True

        mapping = self.get_input_mapping(input_name)
        check.invariant(mapping, "Can only resolve inputs for valid input names")
        mapped_node = self.node_named(mapping.maps_to.node_name)

        return mapped_node.definition.input_has_default(mapping.maps_to.input_name)

    @property
    def dependencies(self) -> DependencyMapping[NodeInvocation]:
        return self._dependencies

    @property
    def dependency_structure(self) -> DependencyStructure:
        return self._dependency_structure

    @property
    def config_schema(self) -> Optional[IDefinitionConfigSchema]:
        return self.config_mapping.config_schema if self.config_mapping is not None else None

    def input_supports_dynamic_output_dep(self, input_name: str) -> bool:
        mapping = self.get_input_mapping(input_name)
        target_node = mapping.maps_to.node_name
        # check if input mapped to node which is downstream of another dynamic output within
        if self.dependency_structure.is_dynamic_mapped(target_node):
            return False

        # check if input mapped to node which starts new dynamic downstream
        if self.dependency_structure.has_dynamic_downstreams(target_node):
            return False

        return self.node_named(target_node).definition.input_supports_dynamic_output_dep(
            mapping.maps_to.input_name
        )

    def copy(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        input_mappings: Optional[Sequence[InputMapping]] = None,
        output_mappings: Optional[Sequence[OutputMapping]] = None,
        config: Optional[ConfigMapping] = None,
        tags: Optional[Mapping[str, str]] = None,
        input_assets: Optional[Mapping[str, Mapping[str, "AssetsDefinition"]]] = None,
    ) -> Self:
        return self.__class__(
            node_defs=self.node_defs,
            dependencies=self.dependencies,
            name=name or self.name,
            description=description or self.description,
            input_mappings=input_mappings or self._input_mappings,
            output_mappings=output_mappings or self._output_mappings,
            config=config or self.config_mapping,
            tags=tags or self.tags,
            input_assets=input_assets or self._input_assets,
        )

    def copy_for_configured(
        self,
        name: str,
        description: Optional[str],
        config_schema: Any,
    ) -> Self:
        if not self.has_config_mapping:
            raise DagsterInvalidDefinitionError(
                "Only graphs utilizing config mapping can be pre-configured. The graph "
                f'"{self.name}" does not have a config mapping, and thus has nothing to be '
                "configured."
            )
        config_mapping = cast(ConfigMapping, self.config_mapping)
        return self.copy(
            name=name,
            description=check.opt_str_param(description, "description", default=self.description),
            config=ConfigMapping(
                config_mapping.config_fn,
                config_schema=config_schema,
                receive_processed_config_values=config_mapping.receive_processed_config_values,
            ),
        )

    def node_names(self) -> Sequence[str]:
        return list(self._node_dict.keys())

    @public
    def to_job(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        resource_defs: Optional[Mapping[str, object]] = None,
        config: Optional[
            Union["RunConfig", ConfigMapping, Mapping[str, object], "PartitionedConfig"]
        ] = None,
        tags: Optional[Mapping[str, object]] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
        executor_def: Optional["ExecutorDefinition"] = None,
        hooks: Optional[AbstractSet[HookDefinition]] = None,
        op_retry_policy: Optional[RetryPolicy] = None,
        op_selection: Optional[Sequence[str]] = None,
        partitions_def: Optional["PartitionsDefinition"] = None,
        asset_layer: Optional["AssetLayer"] = None,
        input_values: Optional[Mapping[str, object]] = None,
        run_tags: Optional[Mapping[str, object]] = None,
        _asset_selection_data: Optional[AssetSelectionData] = None,
    ) -> "JobDefinition":
        """Make this graph in to an executable Job by providing remaining components required for execution.

        Args:
            name (Optional[str]):
                The name for the Job. Defaults to the name of the this graph.
            resource_defs (Optional[Mapping [str, object]]):
                Resources that are required by this graph for execution.
                If not defined, `io_manager` will default to filesystem.
            config:
                Describes how the job is parameterized at runtime.

                If no value is provided, then the schema for the job's run config is a standard
                format based on its ops and resources.

                If a dictionary is provided, then it must conform to the standard config schema, and
                it will be used as the job's run config for the job whenever the job is executed.
                The values provided will be viewable and editable in the Dagster UI, so be
                careful with secrets.

                If a :py:class:`ConfigMapping` object is provided, then the schema for the job's run config is
                determined by the config mapping, and the ConfigMapping, which should return
                configuration in the standard format to configure the job.

                If a :py:class:`PartitionedConfig` object is provided, then it defines a discrete set of config
                values that can parameterize the job, as well as a function for mapping those
                values to the base config. The values provided will be viewable and editable in the
                Dagster UI, so be careful with secrets.
            tags (Optional[Mapping[str, object]]): A set of key-value tags that annotate the job and can
                be used for searching and filtering in the UI. Values that are not already strings will
                be serialized as JSON. If `run_tags` is not set, then the content of `tags` will also be
                automatically appended to the tags of any runs of this job.
            run_tags (Optional[Mapping[str, object]]):
                A set of key-value tags that will be automatically attached to runs launched by this
                job. Values that are not already strings will be serialized as JSON. These tag values
                may be overwritten by tag values provided at invocation time. If `run_tags` is set, then
                `tags` are not automatically appended to the tags of any runs of this job.
            metadata (Optional[Mapping[str, RawMetadataValue]]):
                Arbitrary information that will be attached to the JobDefinition and be viewable in the Dagster UI.
                Keys must be strings, and values must be python primitive types or one of the provided
                MetadataValue types
            logger_defs (Optional[Mapping[str, LoggerDefinition]]):
                A dictionary of string logger identifiers to their implementations.
            executor_def (Optional[ExecutorDefinition]):
                How this Job will be executed. Defaults to :py:class:`multi_or_in_process_executor`,
                which can be switched between multi-process and in-process modes of execution. The
                default mode of execution is multi-process.
            op_retry_policy (Optional[RetryPolicy]): The default retry policy for all ops in this job.
                Only used if retry policy is not defined on the op definition or op invocation.
            partitions_def (Optional[PartitionsDefinition]): Defines a discrete set of partition
                keys that can parameterize the job. If this argument is supplied, the config
                argument can't also be supplied.
            asset_layer (Optional[AssetLayer]): Top level information about the assets this job
                will produce. Generally should not be set manually.
            input_values (Optional[Mapping[str, Any]]):
                A dictionary that maps python objects to the top-level inputs of a job.

        Returns:
            JobDefinition
        """
        from dagster._core.definitions.job_definition import JobDefinition
        from dagster._core.execution.build_resources import wrap_resources_for_execution

        wrapped_resource_defs = wrap_resources_for_execution(resource_defs)
        return JobDefinition.dagster_internal_init(
            name=name,
            description=description or self.description,
            graph_def=self,
            resource_defs=wrapped_resource_defs,
            logger_defs=logger_defs,
            executor_def=executor_def,
            config=config,
            partitions_def=partitions_def,
            tags=tags,
            run_tags=run_tags,
            metadata=metadata,
            hook_defs=hooks,
            op_retry_policy=op_retry_policy,
            asset_layer=asset_layer,
            input_values=input_values,
            _subset_selection_data=_asset_selection_data,
            _was_explicitly_provided_resources=None,  # None means this is determined by whether resource_defs contains any explicitly provided resources
        ).get_subset(op_selection=op_selection)

    def coerce_to_job(self) -> "JobDefinition":
        # attempt to coerce a Graph in to a Job, raising a useful error if it doesn't work
        try:
            return self.to_job()
        except DagsterInvalidDefinitionError as err:
            raise DagsterInvalidDefinitionError(
                f"Failed attempting to coerce Graph {self.name} in to a Job. "
                "Use to_job instead, passing the required information."
            ) from err

    @public
    def execute_in_process(
        self,
        run_config: Any = None,
        instance: Optional["DagsterInstance"] = None,
        resources: Optional[Mapping[str, object]] = None,
        raise_on_error: bool = True,
        op_selection: Optional[Sequence[str]] = None,
        run_id: Optional[str] = None,
        input_values: Optional[Mapping[str, object]] = None,
    ) -> "ExecuteInProcessResult":
        """Execute this graph in-process, collecting results in-memory.

        Args:
            run_config (Optional[Mapping[str, Any]]):
                Run config to provide to execution. The configuration for the underlying graph
                should exist under the "ops" key.
            instance (Optional[DagsterInstance]):
                The instance to execute against, an ephemeral one will be used if none provided.
            resources (Optional[Mapping[str, Any]]):
                The resources needed if any are required. Can provide resource instances directly,
                or resource definitions.
            raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
                Defaults to ``True``.
            op_selection (Optional[List[str]]): A list of op selection queries (including single op
                names) to execute. For example:
                * ``['some_op']``: selects ``some_op`` itself.
                * ``['*some_op']``: select ``some_op`` and all its ancestors (upstream dependencies).
                * ``['*some_op+++']``: select ``some_op``, all its ancestors, and its descendants
                (downstream dependencies) within 3 levels down.
                * ``['*some_op', 'other_op_a', 'other_op_b+']``: select ``some_op`` and all its
                ancestors, ``other_op_a`` itself, and ``other_op_b`` and its direct child ops.
            input_values (Optional[Mapping[str, Any]]):
                A dictionary that maps python objects to the top-level inputs of the graph.

        Returns:
            :py:class:`~dagster.ExecuteInProcessResult`
        """
        from dagster._core.definitions.executor_definition import execute_in_process_executor
        from dagster._core.definitions.job_definition import JobDefinition
        from dagster._core.execution.build_resources import wrap_resources_for_execution
        from dagster._core.instance import DagsterInstance

        instance = check.opt_inst_param(instance, "instance", DagsterInstance)
        resources = check.opt_mapping_param(resources, "resources", key_type=str)
        input_values = check.opt_mapping_param(input_values, "input_values")

        resource_defs = wrap_resources_for_execution(resources)

        ephemeral_job = JobDefinition(
            name=self._name,
            graph_def=self,
            executor_def=execute_in_process_executor,
            resource_defs=resource_defs,
            input_values=input_values,
        ).get_subset(op_selection=op_selection)

        run_config = run_config if run_config is not None else {}
        op_selection = check.opt_sequence_param(op_selection, "op_selection", str)

        return ephemeral_job.execute_in_process(
            run_config=run_config,
            instance=instance,
            raise_on_error=raise_on_error,
            run_id=run_id,
        )

    @property
    def parent_graph_def(self) -> Optional["GraphDefinition"]:
        return None

    @property
    def is_subselected(self) -> bool:
        return False

    def get_resource_requirements(
        self,
        asset_layer: Optional["AssetLayer"],
    ) -> Iterator[ResourceRequirement]:
        for node in self.node_dict.values():
            yield from node.get_resource_requirements(outer_container=self, asset_layer=asset_layer)

        for dagster_type in self.all_dagster_types():
            yield from dagster_type.get_resource_requirements()

    @public
    @property
    def name(self) -> str:
        """The name of the graph."""
        return super().name

    @public
    @property
    def tags(self) -> Mapping[str, str]:
        """The tags associated with the graph."""
        return super().tags

    @property
    def pools(self) -> Set[str]:
        pools = set()
        for node_def in self.node_defs:
            pools.update(node_def.pools)
        return pools

    @public
    def alias(self, name: str) -> "PendingNodeInvocation":
        """Aliases the graph with a new name.

        Can only be used in the context of a :py:func:`@graph <graph>`, :py:func:`@job <job>`, or :py:func:`@asset_graph <asset_graph>` decorated function.

        **Examples:**
            .. code-block:: python

                @job
                def do_it_all():
                    my_graph.alias("my_graph_alias")
        """
        return super().alias(name)

    @public
    def tag(self, tags: Optional[Mapping[str, str]]) -> "PendingNodeInvocation":
        """Attaches the provided tags to the graph immutably.

        Can only be used in the context of a :py:func:`@graph <graph>`, :py:func:`@job <job>`, or :py:func:`@asset_graph <asset_graph>` decorated function.

        **Examples:**
            .. code-block:: python

                @job
                def do_it_all():
                    my_graph.tag({"my_tag": "my_value"})
        """
        return super().tag(tags)

    @public
    def with_hooks(self, hook_defs: AbstractSet[HookDefinition]) -> "PendingNodeInvocation":
        """Attaches the provided hooks to the graph immutably.

        Can only be used in the context of a :py:func:`@graph <graph>`, :py:func:`@job <job>`, or :py:func:`@asset_graph <asset_graph>` decorated function.

        **Examples:**
            .. code-block:: python

                @job
                def do_it_all():
                    my_graph.with_hooks({my_hook})
        """
        return super().with_hooks(hook_defs)

    @public
    def with_retry_policy(self, retry_policy: RetryPolicy) -> "PendingNodeInvocation":
        """Attaches the provided retry policy to the graph immutably.

        Can only be used in the context of a :py:func:`@graph <graph>`, :py:func:`@job <job>`, or :py:func:`@asset_graph <asset_graph>` decorated function.

        **Examples:**
            .. code-block:: python

                @job
                def do_it_all():
                    my_graph.with_retry_policy(RetryPolicy(max_retries=5))
        """
        return super().with_retry_policy(retry_policy)

    def resolve_input_to_destinations(
        self, input_handle: NodeInputHandle
    ) -> Sequence[NodeInputHandle]:
        all_destinations: list[NodeInputHandle] = []
        for mapping in self.input_mappings:
            if mapping.graph_input_name != input_handle.input_name:
                continue
            # recurse into graph structure
            all_destinations += self.node_named(
                mapping.maps_to.node_name
            ).definition.resolve_input_to_destinations(
                NodeInputHandle(
                    node_handle=NodeHandle(
                        mapping.maps_to.node_name, parent=input_handle.node_handle
                    ),
                    input_name=mapping.maps_to.input_name,
                ),
            )

        return all_destinations

    def resolve_output_to_destinations(
        self, output_name: str, handle: Optional[NodeHandle]
    ) -> Sequence[NodeInputHandle]:
        all_destinations: list[NodeInputHandle] = []
        for mapping in self.output_mappings:
            if mapping.graph_output_name != output_name:
                continue
            output_pointer = mapping.maps_from
            output_node = self.node_named(output_pointer.node_name)

            all_destinations.extend(
                output_node.definition.resolve_output_to_destinations(
                    output_pointer.output_name,
                    NodeHandle(output_pointer.node_name, parent=handle),
                )
            )

            output_def = output_node.definition.output_def_named(output_pointer.output_name)
            downstream_input_handles = (
                self.dependency_structure.output_to_downstream_inputs_for_node(
                    output_pointer.node_name
                ).get(NodeOutput(output_node, output_def), [])
            )
            for input_handle in downstream_input_handles:
                all_destinations.append(
                    NodeInputHandle(
                        node_handle=NodeHandle(input_handle.node_name, parent=handle),
                        input_name=input_handle.input_name,
                    )
                )

        return all_destinations

    def get_op_handles(self, parent: NodeHandle) -> AbstractSet[NodeHandle]:
        return {
            op_handle
            for node in self.nodes
            for op_handle in node.definition.get_op_handles(NodeHandle(node.name, parent=parent))
        }

    def get_op_output_handles(self, parent: Optional[NodeHandle]) -> AbstractSet[NodeOutputHandle]:
        return {
            op_output_handle
            for node in self.nodes
            for op_output_handle in node.definition.get_op_output_handles(
                NodeHandle(node.name, parent=parent)
            )
        }

    def get_op_input_output_handle_pairs(
        self, outer_handle: Optional[NodeHandle]
    ) -> AbstractSet[tuple[NodeOutputHandle, NodeInputHandle]]:
        """Get all pairs of op output handles and their downstream op input handles within the graph."""
        result: set[tuple[NodeOutputHandle, NodeInputHandle]] = set()

        for node in self.nodes:
            node_handle = NodeHandle(node.name, parent=outer_handle)
            if isinstance(node.definition, GraphDefinition):
                result.update(node.definition.get_op_input_output_handle_pairs(node_handle))

            for (
                node_input,
                upstream_outputs,
            ) in self.dependency_structure.input_to_upstream_outputs_for_node(node.name).items():
                op_input_handles = node_input.node.definition.resolve_input_to_destinations(
                    NodeInputHandle(node_handle=node_handle, input_name=node_input.input_def.name)
                )
                for op_input_handle in op_input_handles:
                    for upstream_node_output in upstream_outputs:
                        origin_output_def, origin_node_handle = (
                            upstream_node_output.node.definition.resolve_output_to_origin(
                                upstream_node_output.output_def.name,
                                NodeHandle(upstream_node_output.node.name, parent=outer_handle),
                            )
                        )
                        origin_output_handle = NodeOutputHandle(
                            node_handle=origin_node_handle, output_name=origin_output_def.name
                        )

                        result.add((origin_output_handle, op_input_handle))

        return result


class SubselectedGraphDefinition(GraphDefinition):
    """Defines a subselected graph.

    Args:
        parent_graph_def (GraphDefinition): The parent graph that this current graph is subselected
            from. This is used for tracking where the subselected graph originally comes from.
            Note that we allow subselecting a subselected graph, and this field refers to the direct
            parent graph of the current subselection, rather than the original root graph.
        node_defs (Optional[Sequence[NodeDefinition]]): A list of all top level nodes in the graph. A
            node can be an op or a graph that contains other nodes.
        dependencies (Optional[Mapping[Union[str, NodeInvocation], Mapping[str, IDependencyDefinition]]]):
            A structure that declares the dependencies of each op's inputs on the outputs of other
            ops in the subselected graph. Keys of the top level dict are either the string names of
            ops in the graph or, in the case of aliased ops, :py:class:`NodeInvocations <NodeInvocation>`.
            Values of the top level dict are themselves dicts, which map input names belonging to
            the op or aliased op to :py:class:`DependencyDefinitions <DependencyDefinition>`.
        input_mappings (Optional[Sequence[InputMapping]]): Define the inputs to the nested graph, and
            how they map to the inputs of its constituent ops.
        output_mappings (Optional[Sequence[OutputMapping]]): Define the outputs of the nested graph, and
            how they map from the outputs of its constituent ops.
    """

    def __init__(
        self,
        parent_graph_def: GraphDefinition,
        node_defs: Optional[Sequence[NodeDefinition]],
        dependencies: Optional[
            Union[
                DependencyMapping[str],
                DependencyMapping[NodeInvocation],
            ]
        ],
        input_mappings: Optional[Sequence[InputMapping]],
        output_mappings: Optional[Sequence[OutputMapping]],
    ):
        self._parent_graph_def = check.inst_param(
            parent_graph_def, "parent_graph_def", GraphDefinition
        )
        super().__init__(
            name=parent_graph_def.name,  # should we create special name for subselected graphs
            node_defs=node_defs,
            dependencies=dependencies,
            input_mappings=input_mappings,
            output_mappings=output_mappings,
            config=parent_graph_def.config_mapping,
            tags=parent_graph_def.tags,
        )

    @property
    def parent_graph_def(self) -> GraphDefinition:
        return self._parent_graph_def

    def get_top_level_omitted_nodes(self) -> Sequence[Node]:
        return [node for node in self.parent_graph_def.nodes if not self.has_node_named(node.name)]

    @property
    def is_subselected(self) -> bool:
        return True


def _validate_in_mappings(
    input_mappings: Sequence[InputMapping],
    nodes_by_name: Mapping[str, Node],
    dependency_structure: DependencyStructure,
    name: str,
    class_name: str,
) -> Sequence[InputDefinition]:
    from dagster._core.definitions.composition import MappedInputPlaceholder

    input_defs_by_name: dict[str, InputDefinition] = OrderedDict()
    mapping_keys: Set[str] = set()

    target_input_types_by_graph_input_name: dict[str, set[DagsterType]] = defaultdict(set)

    for mapping in input_mappings:
        # handle incorrect objects passed in as mappings
        if not isinstance(mapping, InputMapping):
            if isinstance(mapping, InputDefinition):
                raise DagsterInvalidDefinitionError(
                    f"In {class_name} '{name}' you passed an InputDefinition "
                    f"named '{mapping.name}' directly in to input_mappings. Return "
                    "an InputMapping by calling mapping_to on the InputDefinition."
                )
            else:
                raise DagsterInvalidDefinitionError(
                    f"In {class_name} '{name}' received unexpected type '{type(mapping)}' in"
                    " input_mappings. Provide an InputMapping using InputMapping(...)"
                )

        input_defs_by_name[mapping.graph_input_name] = mapping.get_definition()

        target_node = nodes_by_name.get(mapping.maps_to.node_name)
        if target_node is None:
            raise DagsterInvalidDefinitionError(
                f"In {class_name} '{name}' input mapping references node "
                f"'{mapping.maps_to.node_name}' which it does not contain."
            )
        if not target_node.has_input(mapping.maps_to.input_name):
            raise DagsterInvalidDefinitionError(
                f"In {class_name} '{name}' input mapping to node '{mapping.maps_to.node_name}' "
                f"which contains no input named '{mapping.maps_to.input_name}'"
            )

        target_input_def = target_node.input_def_named(mapping.maps_to.input_name)
        node_input = NodeInput(target_node, target_input_def)

        if mapping.maps_to_fan_in:
            maps_to = cast(FanInInputPointer, mapping.maps_to)
            if not dependency_structure.has_fan_in_deps(node_input):
                raise DagsterInvalidDefinitionError(
                    f"In {class_name} '{name}' input mapping target"
                    f' "{maps_to.node_name}.{maps_to.input_name}" (index'
                    f" {maps_to.fan_in_index} of fan-in) is not a MultiDependencyDefinition."
                )
            inner_deps = dependency_structure.get_fan_in_deps(node_input)
            if (maps_to.fan_in_index >= len(inner_deps)) or (
                inner_deps[maps_to.fan_in_index] is not MappedInputPlaceholder
            ):
                raise DagsterInvalidDefinitionError(
                    f"In {class_name} '{name}' input mapping target "
                    f'"{maps_to.node_name}.{maps_to.input_name}" index {maps_to.fan_in_index} in '
                    "the MultiDependencyDefinition is not a MappedInputPlaceholder"
                )
            mapping_keys.add(f"{maps_to.node_name}.{maps_to.input_name}.{maps_to.fan_in_index}")
            target_input_types_by_graph_input_name[mapping.graph_input_name].add(
                target_input_def.dagster_type.get_inner_type_for_fan_in()
            )
        else:
            if dependency_structure.has_deps(node_input):
                raise DagsterInvalidDefinitionError(
                    f"In {class_name} '{name}' input mapping target "
                    f'"{mapping.maps_to.node_name}.{mapping.maps_to.input_name}" '
                    "is already satisfied by output"
                )

            mapping_keys.add(f"{mapping.maps_to.node_name}.{mapping.maps_to.input_name}")
            target_input_types_by_graph_input_name[mapping.graph_input_name].add(
                target_input_def.dagster_type
            )

    for node_input in dependency_structure.inputs():
        if dependency_structure.has_fan_in_deps(node_input):
            for idx, dep in enumerate(dependency_structure.get_fan_in_deps(node_input)):
                if dep is MappedInputPlaceholder:
                    mapping_str = f"{node_input.node_name}.{node_input.input_name}.{idx}"
                    if mapping_str not in mapping_keys:
                        raise DagsterInvalidDefinitionError(
                            f"Unsatisfied MappedInputPlaceholder at index {idx} in"
                            " MultiDependencyDefinition for"
                            f" '{node_input.node_name}.{node_input.input_name}'"
                        )

    # if the dagster type on a graph input is Any and all its target inputs have the
    # same dagster type, then use that dagster type for the graph input
    for graph_input_name, graph_input_def in input_defs_by_name.items():
        if graph_input_def.dagster_type.kind == DagsterTypeKind.ANY:
            target_input_types = target_input_types_by_graph_input_name[graph_input_name]
            if len(target_input_types) == 1:
                input_defs_by_name[graph_input_name] = graph_input_def.with_dagster_type(
                    next(iter(target_input_types))
                )

    return list(input_defs_by_name.values())


def _validate_out_mappings(
    output_mappings: Sequence[OutputMapping],
    node_dict: Mapping[str, Node],
    name: str,
    class_name: str,
) -> tuple[Sequence[OutputMapping], Sequence[OutputDefinition]]:
    output_defs: list[OutputDefinition] = []
    for mapping in output_mappings:
        if isinstance(mapping, OutputMapping):
            target_node = node_dict.get(mapping.maps_from.node_name)
            if target_node is None:
                raise DagsterInvalidDefinitionError(
                    f"In {class_name} '{name}', output mapping references node "
                    f"'{mapping.maps_from.node_name}' which it does not contain."
                )
            if not target_node.has_output(mapping.maps_from.output_name):
                raise DagsterInvalidDefinitionError(
                    f"In {class_name} {name}, output mapping from {target_node.describe_node()} "
                    f"references output '{mapping.maps_from.output_name}', which the node does not "
                    "contain."
                )

            target_output = target_node.output_def_named(mapping.maps_from.output_name)
            output_def = mapping.get_definition(is_dynamic=target_output.is_dynamic)
            output_defs.append(output_def)

            if (
                mapping.dagster_type
                and mapping.dagster_type.kind != DagsterTypeKind.ANY
                and (target_output.dagster_type != mapping.dagster_type)
                and class_name != "GraphDefinition"
            ):
                raise DagsterInvalidDefinitionError(
                    f"In {class_name} '{name}' output '{mapping.graph_output_name}' of type"
                    f" {mapping.dagster_type.display_name} maps from"
                    f" {mapping.maps_from.node_name}.{mapping.maps_from.output_name} of different"
                    f" type {target_output.dagster_type.display_name}. OutputMapping source and"
                    " destination must have the same type."
                )

        elif isinstance(mapping, OutputDefinition):
            raise DagsterInvalidDefinitionError(
                f"You passed an OutputDefinition named '{mapping.name}' directly "
                "in to output_mappings. Return an OutputMapping by calling "
                "mapping_from on the OutputDefinition."
            )
        else:
            raise DagsterInvalidDefinitionError(
                f"Received unexpected type '{type(mapping)}' in output_mappings. "
                "Provide an OutputMapping using OutputDefinition(...).mapping_from(...)"
            )
    return output_mappings, output_defs
