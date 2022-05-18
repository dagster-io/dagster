from collections import OrderedDict
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
    Set,
    Tuple,
    Union,
    cast,
)

from toposort import CircularDependencyError, toposort_flatten

import dagster._check as check
from dagster.config import Field, Shape
from dagster.config.config_type import ConfigType
from dagster.config.validate import validate_config
from dagster.core.definitions.config import ConfigMapping
from dagster.core.definitions.definition_config_schema import IDefinitionConfigSchema
from dagster.core.definitions.policy import RetryPolicy
from dagster.core.definitions.resource_definition import ResourceDefinition
from dagster.core.definitions.utils import check_valid_name
from dagster.core.errors import DagsterInvalidConfigError, DagsterInvalidDefinitionError
from dagster.core.selector.subset_selector import AssetSelectionData
from dagster.core.storage.io_manager import io_manager
from dagster.core.types.dagster_type import (
    DagsterType,
    DagsterTypeKind,
    construct_dagster_type_dictionary,
)
from dagster.utils import merge_dicts

from .dependency import (
    DependencyStructure,
    IDependencyDefinition,
    Node,
    NodeHandle,
    NodeInvocation,
    SolidInputHandle,
)
from .hook_definition import HookDefinition
from .input import FanInInputPointer, InputDefinition, InputMapping, InputPointer
from .logger_definition import LoggerDefinition
from .node_definition import NodeDefinition
from .output import OutputDefinition, OutputMapping
from .preset import PresetDefinition
from .solid_container import create_execution_structure, validate_dependency_dict
from .version_strategy import VersionStrategy

if TYPE_CHECKING:
    from dagster.core.execution.execute_in_process_result import ExecuteInProcessResult
    from dagster.core.instance import DagsterInstance

    from .asset_layer import AssetLayer
    from .executor_definition import ExecutorDefinition
    from .job_definition import JobDefinition
    from .partition import PartitionedConfig, PartitionsDefinition
    from .solid_definition import SolidDefinition


def _check_node_defs_arg(graph_name: str, node_defs: Optional[List[NodeDefinition]]):
    node_defs = node_defs or []

    if not isinstance(node_defs, list):
        raise DagsterInvalidDefinitionError(
            '"nodes" arg to "{name}" is not a list. Got {val}.'.format(
                name=graph_name, val=repr(node_defs)
            )
        )
    for node_def in node_defs:
        if isinstance(node_def, NodeDefinition):
            continue
        elif callable(node_def):
            raise DagsterInvalidDefinitionError(
                """You have passed a lambda or function {func} into {name} that is
                not a node. You have likely forgetten to annotate this function with
                the @op or @graph decorators.'
                """.format(
                    name=graph_name, func=node_def.__name__
                )
            )
        else:
            raise DagsterInvalidDefinitionError(
                "Invalid item in node list: {item}".format(item=repr(node_def))
            )

    return node_defs


def _create_adjacency_lists(
    solids: List[Node],
    dep_structure: DependencyStructure,
) -> Tuple[Dict[str, Set[Node]], Dict[str, Set[Node]]]:
    visit_dict = {s.name: False for s in solids}
    forward_edges: Dict[str, Set[Node]] = {s.name: set() for s in solids}
    backward_edges: Dict[str, Set[Node]] = {s.name: set() for s in solids}

    def visit(solid_name):
        if visit_dict[solid_name]:
            return

        visit_dict[solid_name] = True

        for output_handle in dep_structure.all_upstream_outputs_from_solid(solid_name):
            forward_node = output_handle.solid.name
            backward_node = solid_name
            if forward_node in forward_edges:
                forward_edges[forward_node].add(backward_node)
                backward_edges[backward_node].add(forward_node)
                visit(forward_node)

    for s in solids:
        visit(s.name)

    return (forward_edges, backward_edges)


class GraphDefinition(NodeDefinition):
    """Defines a Dagster graph.

    A graph is made up of

    - Nodes, which can either be an op (the functional unit of computation), or another graph.
    - Dependencies, which determine how the values produced by nodes as outputs flow from
      one node to another. This tells Dagster how to arrange nodes into a directed, acyclic graph
      (DAG) of compute.

    End users should prefer the :func:`@graph <graph>` decorator. GraphDefinition is generally
    intended to be used by framework authors or for programatically generated graphs.

    Args:
        name (str): The name of the graph. Must be unique within any :py:class:`GraphDefinition`
            or :py:class:`JobDefinition` containing the graph.
        description (Optional[str]): A human-readable description of the pipeline.
        node_defs (Optional[List[NodeDefinition]]): The set of ops / graphs used in this graph.
        dependencies (Optional[Dict[Union[str, NodeInvocation], Dict[str, DependencyDefinition]]]):
            A structure that declares the dependencies of each op's inputs on the outputs of other
            ops in the graph. Keys of the top level dict are either the string names of ops in the
            graph or, in the case of aliased ops, :py:class:`NodeInvocations <NodeInvocation>`.
            Values of the top level dict are themselves dicts, which map input names belonging to
            the op or aliased op to :py:class:`DependencyDefinitions <DependencyDefinition>`.
        input_mappings (Optional[List[InputMapping]]): Defines the inputs to the nested graph, and
            how they map to the inputs of its constituent ops.
        output_mappings (Optional[List[OutputMapping]]): Defines the outputs of the nested graph,
            and how they map from the outputs of its constituent ops.
        config (Optional[ConfigMapping]): Defines the config of the graph, and how its schema maps
            to the config of its constituent ops.
        tags (Optional[Dict[str, Any]]): Arbitrary metadata for any execution of the graph.
            Values that are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.  These tag values may be overwritten by tag
            values provided at invocation time.

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

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        node_defs: Optional[List[NodeDefinition]] = None,
        dependencies: Optional[
            Dict[Union[str, NodeInvocation], Dict[str, IDependencyDefinition]]
        ] = None,
        input_mappings: Optional[List[InputMapping]] = None,
        output_mappings: Optional[List[OutputMapping]] = None,
        config: Optional[ConfigMapping] = None,
        tags: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        self._node_defs = _check_node_defs_arg(name, node_defs)
        self._dagster_type_dict = construct_dagster_type_dictionary(self._node_defs)
        self._dependencies = validate_dependency_dict(dependencies)
        self._dependency_structure, self._node_dict = create_execution_structure(
            self._node_defs, self._dependencies, graph_definition=self
        )

        # List[InputMapping]
        self._input_mappings, input_defs = _validate_in_mappings(
            check.opt_list_param(input_mappings, "input_mappings"),
            self._node_dict,
            self._dependency_structure,
            name,
            class_name=type(self).__name__,
        )
        # List[OutputMapping]
        self._output_mappings = _validate_out_mappings(
            check.opt_list_param(output_mappings, "output_mappings"),
            self._node_dict,
            self._dependency_structure,
            name,
            class_name=type(self).__name__,
        )

        self._config_mapping = check.opt_inst_param(config, "config", ConfigMapping)

        super(GraphDefinition, self).__init__(
            name=name,
            description=description,
            input_defs=input_defs,
            output_defs=[output_mapping.definition for output_mapping in self._output_mappings],
            tags=tags,
            **kwargs,
        )

        # must happen after base class construction as properties are assumed to be there
        # eager computation to detect cycles
        self.solids_in_topological_order = self._solids_in_topological_order()

    def _solids_in_topological_order(self):

        _forward_edges, backward_edges = _create_adjacency_lists(
            self.solids, self.dependency_structure
        )

        try:
            order = toposort_flatten(backward_edges)
        except CircularDependencyError as err:
            raise DagsterInvalidDefinitionError(str(err)) from err

        return [self.solid_named(solid_name) for solid_name in order]

    @property
    def node_type_str(self) -> str:
        return "graph"

    @property
    def is_graph_job_op_node(self) -> bool:
        return True

    @property
    def solids(self) -> List[Node]:
        return list(set(self._node_dict.values()))

    @property
    def node_dict(self) -> Dict[str, Node]:
        return self._node_dict

    @property
    def node_defs(self) -> List[NodeDefinition]:
        return self._node_defs

    def has_solid_named(self, name: str) -> bool:
        check.str_param(name, "name")
        return name in self._node_dict

    def solid_named(self, name: str) -> Node:
        check.str_param(name, "name")
        check.invariant(
            name in self._node_dict,
            "{graph_name} has no solid named {name}.".format(graph_name=self._name, name=name),
        )

        return self._node_dict[name]

    def get_solid(self, handle: NodeHandle) -> Node:
        check.inst_param(handle, "handle", NodeHandle)
        current = handle
        lineage = []
        while current:
            lineage.append(current.name)
            current = current.parent

        name = lineage.pop()
        solid = self.solid_named(name)
        while lineage:
            name = lineage.pop()
            solid = solid.definition.solid_named(name)

        return solid

    def iterate_node_defs(self) -> Iterator[NodeDefinition]:
        yield self
        for outer_node_def in self._node_defs:
            yield from outer_node_def.iterate_node_defs()

    def iterate_solid_defs(self) -> Iterator["SolidDefinition"]:
        for outer_node_def in self._node_defs:
            yield from outer_node_def.iterate_solid_defs()

    @property
    def input_mappings(self) -> List[InputMapping]:
        return self._input_mappings

    @property
    def output_mappings(self) -> List[OutputMapping]:
        return self._output_mappings

    @property
    def config_mapping(self) -> Optional[ConfigMapping]:
        return self._config_mapping

    @property
    def has_config_mapping(self) -> bool:
        return self._config_mapping is not None

    def all_dagster_types(self) -> Iterable[DagsterType]:
        return self._dagster_type_dict.values()

    def has_dagster_type(self, name):
        check.str_param(name, "name")
        return name in self._dagster_type_dict

    def dagster_type_named(self, name):
        check.str_param(name, "name")
        return self._dagster_type_dict[name]

    def get_input_mapping(self, input_name: str) -> InputMapping:

        check.str_param(input_name, "input_name")
        for mapping in self._input_mappings:
            if mapping.definition.name == input_name:
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
            if mapping.definition.name == output_name:
                return mapping
        check.failed(f"Could not find output mapping {output_name}")

    def resolve_output_to_origin(
        self, output_name: str, handle: NodeHandle
    ) -> Tuple[OutputDefinition, NodeHandle]:
        check.str_param(output_name, "output_name")
        check.inst_param(handle, "handle", NodeHandle)

        mapping = self.get_output_mapping(output_name)
        check.invariant(mapping, "Can only resolve outputs for valid output names")
        mapped_solid = self.solid_named(mapping.maps_from.solid_name)
        return mapped_solid.definition.resolve_output_to_origin(
            mapping.maps_from.output_name,
            NodeHandle(mapped_solid.name, handle),
        )

    def default_value_for_input(self, input_name: str) -> Any:
        check.str_param(input_name, "input_name")

        # base case
        if self.input_def_named(input_name).has_default_value:
            return self.input_def_named(input_name).default_value

        mapping = self.get_input_mapping(input_name)
        check.invariant(mapping, "Can only resolve inputs for valid input names")
        mapped_solid = self.solid_named(mapping.maps_to.solid_name)

        return mapped_solid.definition.default_value_for_input(mapping.maps_to.input_name)

    def input_has_default(self, input_name: str) -> bool:
        check.str_param(input_name, "input_name")

        # base case
        if self.input_def_named(input_name).has_default_value:
            return True

        mapping = self.get_input_mapping(input_name)
        check.invariant(mapping, "Can only resolve inputs for valid input names")
        mapped_solid = self.solid_named(mapping.maps_to.solid_name)

        return mapped_solid.definition.input_has_default(mapping.maps_to.input_name)

    @property
    def dependencies(self) -> Dict[Union[str, NodeInvocation], Dict[str, IDependencyDefinition]]:
        return self._dependencies

    @property
    def dependency_structure(self) -> DependencyStructure:
        return self._dependency_structure

    @property
    def config_schema(self) -> Optional[IDefinitionConfigSchema]:
        return self.config_mapping.config_schema if self.config_mapping is not None else None

    def input_supports_dynamic_output_dep(self, input_name: str) -> bool:
        mapping = self.get_input_mapping(input_name)
        target_node = mapping.maps_to.solid_name
        # check if input mapped to solid which is downstream of another dynamic output within
        if self.dependency_structure.is_dynamic_mapped(target_node):
            return False

        # check if input mapped to solid which starts new dynamic downstream
        if self.dependency_structure.has_dynamic_downstreams(target_node):
            return False

        return self.solid_named(target_node).definition.input_supports_dynamic_output_dep(
            mapping.maps_to.input_name
        )

    def copy_for_configured(
        self,
        name: str,
        description: Optional[str],
        config_schema: Any,
        config_or_config_fn: Any,
    ):
        if not self.has_config_mapping:
            raise DagsterInvalidDefinitionError(
                "Only graphs utilizing config mapping can be pre-configured. The graph "
                '"{graph_name}" does not have a config mapping, and thus has nothing to be '
                "configured.".format(graph_name=self.name)
            )
        config_mapping = cast(ConfigMapping, self.config_mapping)
        return GraphDefinition(
            name=name,
            description=check.opt_str_param(description, "description", default=self.description),
            node_defs=self._node_defs,
            dependencies=self._dependencies,
            input_mappings=self._input_mappings,
            output_mappings=self._output_mappings,
            config=ConfigMapping(
                config_mapping.config_fn,
                config_schema=config_schema,
                receive_processed_config_values=config_mapping.receive_processed_config_values,
            ),
        )

    def node_names(self):
        return list(self._node_dict.keys())

    def to_job(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        resource_defs: Optional[Dict[str, ResourceDefinition]] = None,
        config: Optional[Union[ConfigMapping, Dict[str, Any], "PartitionedConfig"]] = None,
        tags: Optional[Dict[str, Any]] = None,
        logger_defs: Optional[Dict[str, LoggerDefinition]] = None,
        executor_def: Optional["ExecutorDefinition"] = None,
        hooks: Optional[AbstractSet[HookDefinition]] = None,
        op_retry_policy: Optional[RetryPolicy] = None,
        version_strategy: Optional[VersionStrategy] = None,
        op_selection: Optional[List[str]] = None,
        partitions_def: Optional["PartitionsDefinition"] = None,
        asset_layer: Optional["AssetLayer"] = None,
        input_values: Optional[Mapping[str, object]] = None,
        _asset_selection_data: Optional[AssetSelectionData] = None,
    ) -> "JobDefinition":
        """
        Make this graph in to an executable Job by providing remaining components required for execution.

        Args:
            name (Optional[str]):
                The name for the Job. Defaults to the name of the this graph.
            resource_defs (Optional[Dict[str, ResourceDefinition]]):
                Resources that are required by this graph for execution.
                If not defined, `io_manager` will default to filesystem.
            config:
                Describes how the job is parameterized at runtime.

                If no value is provided, then the schema for the job's run config is a standard
                format based on its solids and resources.

                If a dictionary is provided, then it must conform to the standard config schema, and
                it will be used as the job's run config for the job whenever the job is executed.
                The values provided will be viewable and editable in the Dagit playground, so be
                careful with secrets.

                If a :py:class:`ConfigMapping` object is provided, then the schema for the job's run config is
                determined by the config mapping, and the ConfigMapping, which should return
                configuration in the standard format to configure the job.

                If a :py:class:`PartitionedConfig` object is provided, then it defines a discrete set of config
                values that can parameterize the job, as well as a function for mapping those
                values to the base config. The values provided will be viewable and editable in the
                Dagit playground, so be careful with secrets.
            tags (Optional[Dict[str, Any]]):
                Arbitrary metadata for any execution of the Job.
                Values that are not strings will be json encoded and must meet the criteria that
                `json.loads(json.dumps(value)) == value`.  These tag values may be overwritten by tag
                values provided at invocation time.
            logger_defs (Optional[Dict[str, LoggerDefinition]]):
                A dictionary of string logger identifiers to their implementations.
            executor_def (Optional[ExecutorDefinition]):
                How this Job will be executed. Defaults to :py:class:`multi_or_in_process_executor`,
                which can be switched between multi-process and in-process modes of execution. The
                default mode of execution is multi-process.
            op_retry_policy (Optional[RetryPolicy]): The default retry policy for all ops in this job.
                Only used if retry policy is not defined on the op definition or op invocation.
            version_strategy (Optional[VersionStrategy]):
                Defines how each solid (and optionally, resource) in the job can be versioned. If
                provided, memoizaton will be enabled for this job.
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
        from .executor_definition import ExecutorDefinition, multi_or_in_process_executor
        from .job_definition import JobDefinition
        from .partition import PartitionedConfig, PartitionsDefinition

        job_name = check_valid_name(name or self.name)

        tags = check.opt_dict_param(tags, "tags", key_type=str)
        executor_def = check.opt_inst_param(
            executor_def, "executor_def", ExecutorDefinition, default=multi_or_in_process_executor
        )
        input_values = check.opt_mapping_param(input_values, "input_values")

        if resource_defs and "io_manager" in resource_defs:
            resource_defs_with_defaults = resource_defs
        else:
            resource_defs_with_defaults = merge_dicts(
                {"io_manager": default_job_io_manager}, resource_defs or {}
            )

        hooks = check.opt_set_param(hooks, "hooks", of_type=HookDefinition)
        op_retry_policy = check.opt_inst_param(op_retry_policy, "op_retry_policy", RetryPolicy)
        op_selection = check.opt_list_param(op_selection, "op_selection", of_type=str)
        presets = []
        config_mapping = None
        partitioned_config = None

        if partitions_def:
            check.inst_param(partitions_def, "partitions_def", PartitionsDefinition)
            check.invariant(
                config is None, "Can't supply both the 'config' and 'partitions_def' arguments"
            )
            partitioned_config = PartitionedConfig(partitions_def, lambda _: {})

        if isinstance(config, ConfigMapping):
            config_mapping = config
        elif isinstance(config, PartitionedConfig):
            partitioned_config = config
        elif isinstance(config, dict):
            presets = [PresetDefinition(name="default", run_config=config)]
            # Using config mapping here is a trick to make it so that the preset will be used even
            # when no config is supplied for the job.
            config_mapping = _config_mapping_with_default_value(
                self._get_config_schema(resource_defs_with_defaults, executor_def, logger_defs),
                config,
                job_name,
                self.name,
            )
        elif config is not None:
            check.failed(
                f"config param must be a ConfigMapping, a PartitionedConfig, or a dictionary, but "
                f"is an object of type {type(config)}"
            )

        return JobDefinition(
            name=job_name,
            description=description or self.description,
            graph_def=self,
            resource_defs=resource_defs_with_defaults,
            logger_defs=logger_defs,
            executor_def=executor_def,
            config_mapping=config_mapping,
            partitioned_config=partitioned_config,
            preset_defs=presets,
            tags=tags,
            hook_defs=hooks,
            version_strategy=version_strategy,
            op_retry_policy=op_retry_policy,
            asset_layer=asset_layer,
            _input_values=input_values,
            _subset_selection_data=_asset_selection_data,
        ).get_job_def_for_subset_selection(op_selection)

    def coerce_to_job(self):
        # attempt to coerce a Graph in to a Job, raising a useful error if it doesn't work
        try:
            return self.to_job()
        except DagsterInvalidDefinitionError as err:
            raise DagsterInvalidDefinitionError(
                f"Failed attempting to coerce Graph {self.name} in to a Job. "
                "Use to_job instead, passing the required information."
            ) from err

    def _get_config_schema(
        self,
        resource_defs: Optional[Dict[str, ResourceDefinition]],
        executor_def: "ExecutorDefinition",
        logger_defs: Optional[Dict[str, LoggerDefinition]],
    ) -> ConfigType:
        from .job_definition import JobDefinition

        return (
            JobDefinition(
                name=self.name,
                graph_def=self,
                resource_defs=resource_defs,
                executor_def=executor_def,
                logger_defs=logger_defs,
            )
            .get_run_config_schema("default")
            .run_config_schema_type
        )

    def execute_in_process(
        self,
        run_config: Any = None,
        instance: Optional["DagsterInstance"] = None,
        resources: Optional[Dict[str, Any]] = None,
        raise_on_error: bool = True,
        op_selection: Optional[List[str]] = None,
        run_id: Optional[str] = None,
        input_values: Optional[Mapping[str, object]] = None,
    ) -> "ExecuteInProcessResult":
        """
        Execute this graph in-process, collecting results in-memory.

        Args:
            run_config (Optional[Dict[str, Any]]):
                Run config to provide to execution. The configuration for the underlying graph
                should exist under the "ops" key.
            instance (Optional[DagsterInstance]):
                The instance to execute against, an ephemeral one will be used if none provided.
            resources (Optional[Dict[str, Any]]):
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
        from dagster.core.execution.build_resources import wrap_resources_for_execution
        from dagster.core.execution.execute_in_process import core_execute_in_process
        from dagster.core.instance import DagsterInstance

        from .executor_definition import execute_in_process_executor
        from .job_definition import JobDefinition

        instance = check.opt_inst_param(instance, "instance", DagsterInstance)
        resources = check.opt_dict_param(resources, "resources", key_type=str)
        input_values = check.opt_mapping_param(input_values, "input_values")

        resource_defs = wrap_resources_for_execution(resources)

        ephemeral_job = JobDefinition(
            name=self._name,
            graph_def=self,
            executor_def=execute_in_process_executor,
            resource_defs=resource_defs,
            _input_values=input_values,
        ).get_job_def_for_subset_selection(op_selection)

        run_config = run_config if run_config is not None else {}
        op_selection = check.opt_list_param(op_selection, "op_selection", str)

        return core_execute_in_process(
            node=self,
            ephemeral_pipeline=ephemeral_job,
            run_config=run_config,
            instance=instance,
            output_capturing_enabled=True,
            raise_on_error=raise_on_error,
            run_id=run_id,
        )

    @property
    def parent_graph_def(self) -> Optional["GraphDefinition"]:
        return None

    @property
    def is_subselected(self) -> bool:
        return False


class SubselectedGraphDefinition(GraphDefinition):
    """Defines a subselected graph.

    Args:
        parent_graph_def (GraphDefinition): The parent graph that this current graph is subselected
            from. This is used for tracking where the subselected graph originally comes from.
            Note that we allow subselecting a subselected graph, and this field refers to the direct
            parent graph of the current subselection, rather than the original root graph.
        node_defs (Optional[List[NodeDefinition]]): A list of all top level nodes in the graph. A
            node can be an op or a graph that contains other nodes.
        dependencies (Optional[Dict[Union[str, NodeInvocation], Dict[str, IDependencyDefinition]]]):
            A structure that declares the dependencies of each op's inputs on the outputs of other
            ops in the subselected graph. Keys of the top level dict are either the string names of
            ops in the graph or, in the case of aliased solids, :py:class:`NodeInvocations <NodeInvocation>`.
            Values of the top level dict are themselves dicts, which map input names belonging to
            the op or aliased op to :py:class:`DependencyDefinitions <DependencyDefinition>`.
        input_mappings (Optional[List[InputMapping]]): Define the inputs to the nested graph, and
            how they map to the inputs of its constituent ops.
        output_mappings (Optional[List[OutputMapping]]): Define the outputs of the nested graph, and
            how they map from the outputs of its constituent ops.
    """

    def __init__(
        self,
        parent_graph_def: GraphDefinition,
        node_defs: Optional[List[NodeDefinition]],
        dependencies: Optional[Dict[Union[str, NodeInvocation], Dict[str, IDependencyDefinition]]],
        input_mappings: Optional[List[InputMapping]],
        output_mappings: Optional[List[OutputMapping]],
    ):
        self._parent_graph_def = check.inst_param(
            parent_graph_def, "parent_graph_def", GraphDefinition
        )
        super(SubselectedGraphDefinition, self).__init__(
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

    def get_top_level_omitted_nodes(self) -> List[Node]:
        return [
            solid for solid in self.parent_graph_def.solids if not self.has_solid_named(solid.name)
        ]

    @property
    def is_subselected(self) -> bool:
        return True


def _validate_in_mappings(
    input_mappings: List[InputMapping],
    solid_dict: Dict[str, Node],
    dependency_structure: DependencyStructure,
    name: str,
    class_name: str,
) -> Tuple[List[InputMapping], Iterable[InputDefinition]]:
    from .composition import MappedInputPlaceholder

    input_def_dict: Dict[str, InputDefinition] = OrderedDict()
    mapping_keys = set()

    for mapping in input_mappings:
        # handle incorrect objects passed in as mappings
        if not isinstance(mapping, InputMapping):
            if isinstance(mapping, InputDefinition):
                raise DagsterInvalidDefinitionError(
                    "In {class_name} '{name}' you passed an InputDefinition "
                    "named '{input_name}' directly in to input_mappings. Return "
                    "an InputMapping by calling mapping_to on the InputDefinition.".format(
                        name=name, input_name=mapping.name, class_name=class_name
                    )
                )
            else:
                raise DagsterInvalidDefinitionError(
                    "In {class_name} '{name}' received unexpected type '{type}' in input_mappings. "
                    "Provide an OutputMapping using InputDefinition(...).mapping_to(...)".format(
                        type=type(mapping), name=name, class_name=class_name
                    )
                )

        if input_def_dict.get(mapping.definition.name):
            if input_def_dict[mapping.definition.name] != mapping.definition:
                raise DagsterInvalidDefinitionError(
                    "In {class_name} '{name}' multiple input mappings with same "
                    "definition name but different definitions".format(
                        name=name, class_name=class_name
                    ),
                )
        else:
            input_def_dict[mapping.definition.name] = mapping.definition

        target_solid = solid_dict.get(mapping.maps_to.solid_name)
        if target_solid is None:
            raise DagsterInvalidDefinitionError(
                "In {class_name} '{name}' input mapping references solid "
                "'{solid_name}' which it does not contain.".format(
                    name=name, solid_name=mapping.maps_to.solid_name, class_name=class_name
                )
            )
        if not target_solid.has_input(mapping.maps_to.input_name):
            raise DagsterInvalidDefinitionError(
                "In {class_name} '{name}' input mapping to solid '{mapping.maps_to.solid_name}' "
                "which contains no input named '{mapping.maps_to.input_name}'".format(
                    name=name, mapping=mapping, class_name=class_name
                )
            )

        target_input = target_solid.input_def_named(mapping.maps_to.input_name)
        solid_input_handle = SolidInputHandle(target_solid, target_input)

        if mapping.maps_to_fan_in:
            maps_to = cast(FanInInputPointer, mapping.maps_to)
            if not dependency_structure.has_fan_in_deps(solid_input_handle):
                raise DagsterInvalidDefinitionError(
                    f"In {class_name} '{name}' input mapping target "
                    f'"{maps_to.solid_name}.{maps_to.input_name}" (index {maps_to.fan_in_index} of fan-in) '
                    f"is not a MultiDependencyDefinition."
                )
            inner_deps = dependency_structure.get_fan_in_deps(solid_input_handle)
            if (maps_to.fan_in_index >= len(inner_deps)) or (
                inner_deps[maps_to.fan_in_index] is not MappedInputPlaceholder
            ):
                raise DagsterInvalidDefinitionError(
                    f"In {class_name} '{name}' input mapping target "
                    f'"{maps_to.solid_name}.{maps_to.input_name}" index {maps_to.fan_in_index} in '
                    f"the MultiDependencyDefinition is not a MappedInputPlaceholder"
                )
            mapping_keys.add(f"{maps_to.solid_name}.{maps_to.input_name}.{maps_to.fan_in_index}")
            target_type = target_input.dagster_type.get_inner_type_for_fan_in()
            fan_in_msg = " (index {} of fan-in)".format(maps_to.fan_in_index)
        else:
            if dependency_structure.has_deps(solid_input_handle):
                raise DagsterInvalidDefinitionError(
                    "In {class_name} '{name}' input mapping target "
                    '"{mapping.maps_to.solid_name}.{mapping.maps_to.input_name}" '
                    "is already satisfied by output".format(
                        name=name, mapping=mapping, class_name=class_name
                    )
                )

            mapping_keys.add(
                "{mapping.maps_to.solid_name}.{mapping.maps_to.input_name}".format(mapping=mapping)
            )
            target_type = target_input.dagster_type
            fan_in_msg = ""

        if (
            # no need to check mapping type for graphs because users can't specify ins/out type on graphs
            class_name not in (GraphDefinition.__name__, SubselectedGraphDefinition.__name__)
            and target_type != mapping.definition.dagster_type
        ):
            raise DagsterInvalidDefinitionError(
                "In {class_name} '{name}' input "
                "'{mapping.definition.name}' of type {mapping.definition.dagster_type.display_name} maps to "
                "{mapping.maps_to.solid_name}.{mapping.maps_to.input_name}{fan_in_msg} of different type "
                "{target_type.display_name}. InputMapping source and "
                "destination must have the same type.".format(
                    mapping=mapping,
                    name=name,
                    target_type=target_type,
                    class_name=class_name,
                    fan_in_msg=fan_in_msg,
                )
            )

    for input_handle in dependency_structure.input_handles():
        if dependency_structure.has_fan_in_deps(input_handle):
            for idx, dep in enumerate(dependency_structure.get_fan_in_deps(input_handle)):
                if dep is MappedInputPlaceholder:
                    mapping_str = (
                        "{input_handle.solid_name}.{input_handle.input_name}.{idx}".format(
                            input_handle=input_handle, idx=idx
                        )
                    )
                    if mapping_str not in mapping_keys:
                        raise DagsterInvalidDefinitionError(
                            "Unsatisfied MappedInputPlaceholder at index {idx} in "
                            "MultiDependencyDefinition for '{input_handle.solid_name}.{input_handle.input_name}'".format(
                                input_handle=input_handle, idx=idx
                            )
                        )

    return input_mappings, input_def_dict.values()


def _validate_out_mappings(
    output_mappings: List[OutputMapping],
    solid_dict: Dict[str, Node],
    dependency_structure: DependencyStructure,
    name: str,
    class_name: str,
) -> List[OutputMapping]:
    for mapping in output_mappings:
        if isinstance(mapping, OutputMapping):

            target_solid = solid_dict.get(mapping.maps_from.solid_name)
            if target_solid is None:
                raise DagsterInvalidDefinitionError(
                    "In {class_name} '{name}' output mapping references node "
                    "'{solid_name}' which it does not contain.".format(
                        name=name, solid_name=mapping.maps_from.solid_name, class_name=class_name
                    )
                )
            if not target_solid.has_output(mapping.maps_from.output_name):
                raise DagsterInvalidDefinitionError(
                    "In {class_name} {name} output mapping from {described_node} "
                    "which contains no output named '{mapping.maps_from.output_name}'".format(
                        described_node=target_solid.describe_node(),
                        name=name,
                        mapping=mapping,
                        class_name=class_name,
                    )
                )

            target_output = target_solid.output_def_named(mapping.maps_from.output_name)

            if (
                mapping.definition.dagster_type.kind != DagsterTypeKind.ANY
                and (target_output.dagster_type != mapping.definition.dagster_type)
                and class_name != "GraphDefinition"
            ):
                raise DagsterInvalidDefinitionError(
                    "In {class_name} '{name}' output "
                    "'{mapping.definition.name}' of type {mapping.definition.dagster_type.display_name} "
                    "maps from {mapping.maps_from.solid_name}.{mapping.maps_from.output_name} of different type "
                    "{target_output.dagster_type.display_name}. OutputMapping source "
                    "and destination must have the same type.".format(
                        class_name=class_name,
                        mapping=mapping,
                        name=name,
                        target_output=target_output,
                    )
                )

            if target_output.is_dynamic and not mapping.definition.is_dynamic:
                raise DagsterInvalidDefinitionError(
                    f'In {class_name} "{name}" can not map from {target_output.__class__.__name__} '
                    f'"{target_output.name}" to {mapping.definition.__class__.__name__} '
                    f'"{mapping.definition.name}". Definition types must align.'
                )

            dynamic_handle = dependency_structure.get_upstream_dynamic_handle_for_solid(
                target_solid.name
            )
            if dynamic_handle and not mapping.definition.is_dynamic:
                raise DagsterInvalidDefinitionError(
                    f'In {class_name} "{name}" output "{mapping.definition.name}" mapping from '
                    f"{target_solid.describe_node()} must be a DynamicOutputDefinition since it is "
                    f'downstream of dynamic output "{dynamic_handle.describe()}".'
                )

        elif isinstance(mapping, OutputDefinition):
            raise DagsterInvalidDefinitionError(
                "You passed an OutputDefinition named '{output_name}' directly "
                "in to output_mappings. Return an OutputMapping by calling "
                "mapping_from on the OutputDefinition.".format(output_name=mapping.name)
            )
        else:
            raise DagsterInvalidDefinitionError(
                "Received unexpected type '{type}' in output_mappings. "
                "Provide an OutputMapping using OutputDefinition(...).mapping_from(...)".format(
                    type=type(mapping)
                )
            )
    return output_mappings


def _config_mapping_with_default_value(
    inner_schema: ConfigType,
    default_config: Dict[str, Any],
    job_name: str,
    graph_name: str,
) -> ConfigMapping:
    if not isinstance(inner_schema, Shape):
        check.failed("Only Shape (dictionary) config_schema allowed on Job ConfigMapping")

    def config_fn(x):
        return x

    updated_fields = {}
    field_aliases = inner_schema.field_aliases
    for name, field in inner_schema.fields.items():
        if name in default_config:
            updated_fields[name] = Field(
                config=field.config_type,
                default_value=default_config[name],
                description=field.description,
            )
        elif name in field_aliases and field_aliases[name] in default_config:
            updated_fields[name] = Field(
                config=field.config_type,
                default_value=default_config[field_aliases[name]],
                description=field.description,
            )
        else:
            updated_fields[name] = field

    config_schema = Shape(
        fields=updated_fields,
        description="run config schema with default values from default_config",
        field_aliases=inner_schema.field_aliases,
    )

    config_evr = validate_config(config_schema, default_config)
    if not config_evr.success:
        raise DagsterInvalidConfigError(
            f"Error in config when building job '{job_name}' from graph '{graph_name}' ",
            config_evr.errors,
            default_config,
        )

    return ConfigMapping(
        config_fn=config_fn, config_schema=config_schema, receive_processed_config_values=False
    )


@io_manager(
    description="The default io manager for Jobs. Uses filesystem but switches to in-memory when invoked through execute_in_process."
)
def default_job_io_manager(init_context):
    from dagster.core.storage.fs_io_manager import PickledObjectFilesystemIOManager

    return PickledObjectFilesystemIOManager(base_dir=init_context.instance.storage_directory())
