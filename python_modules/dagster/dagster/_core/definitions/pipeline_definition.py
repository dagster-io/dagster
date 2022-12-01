from functools import update_wrapper
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    FrozenSet,
    Iterator,
    Mapping,
    Optional,
    Sequence,
    Set,
    Union,
    cast,
)

import dagster._check as check
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.solid_definition import NodeDefinition
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidSubsetError,
    DagsterInvariantViolationError,
)
from dagster._core.storage.tags import MEMOIZED_RUN_TAG
from dagster._core.utils import str_format_set
from dagster._utils import frozentags, merge_dicts
from dagster._utils.backcompat import experimental_class_warning

from .asset_layer import AssetLayer
from .dependency import (
    DependencyDefinition,
    DependencyStructure,
    DynamicCollectDependencyDefinition,
    IDependencyDefinition,
    MultiDependencyDefinition,
    Node,
    NodeHandle,
    NodeInvocation,
    NodeOutput,
)
from .graph_definition import GraphDefinition, SubselectedGraphDefinition
from .hook_definition import HookDefinition
from .metadata import MetadataEntry, PartitionMetadataEntry, RawMetadataValue, normalize_metadata
from .mode import ModeDefinition
from .node_definition import NodeDefinition
from .preset import PresetDefinition
from .resource_requirement import ensure_requirements_satisfied
from .solid_definition import SolidDefinition
from .utils import validate_tags
from .version_strategy import VersionStrategy

if TYPE_CHECKING:
    from dagster._core.host_representation import PipelineIndex
    from dagster._core.snap import ConfigSchemaSnapshot, PipelineSnapshot

    from .run_config_schema import RunConfigSchema


class PipelineDefinition:
    """Defines a Dagster pipeline.

    A pipeline is made up of

    - Solids, each of which is a single functional unit of data computation.
    - Dependencies, which determine how the values produced by solids as their outputs flow from
      one solid to another. This tells Dagster how to arrange solids, and potentially multiple
      aliased instances of solids, into a directed, acyclic graph (DAG) of compute.
    - Modes, which can be used to attach resources, custom loggers, custom system storage
      options, and custom executors to a pipeline, and to switch between them.
    - Presets, which can be used to ship common combinations of pipeline config options in Python
      code, and to switch between them.

    Args:
        solid_defs (Sequence[SolidDefinition]): The set of solids used in this pipeline.
        name (str): The name of the pipeline. Must be unique within any
            :py:class:`RepositoryDefinition` containing the pipeline.
        description (Optional[str]): A human-readable description of the pipeline.
        dependencies (Optional[Dict[Union[str, NodeInvocation], Dict[str, DependencyDefinition]]]):
            A structure that declares the dependencies of each solid's inputs on the outputs of
            other solids in the pipeline. Keys of the top level dict are either the string names of
            solids in the pipeline or, in the case of aliased solids,
            :py:class:`NodeInvocations <NodeInvocation>`. Values of the top level dict are
            themselves dicts, which map input names belonging to the solid or aliased solid to
            :py:class:`DependencyDefinitions <DependencyDefinition>`.
        mode_defs (Optional[Sequence[ModeDefinition]]): The set of modes in which this pipeline can
            operate. Modes are used to attach resources, custom loggers, custom system storage
            options, and custom executors to a pipeline. Modes can be used, e.g., to vary available
            resource and logging implementations between local test and production runs.
        preset_defs (Optional[Sequence[PresetDefinition]]): A set of preset collections of configuration
            options that may be used to execute a pipeline. A preset consists of an environment
            dict, an optional subset of solids to execute, and a mode selection. Presets can be used
            to ship common combinations of options to pipeline end users in Python code, and can
            be selected by tools like Dagit.
        tags (Optional[Dict[str, Any]]): Arbitrary metadata for any execution run of the pipeline.
            Values that are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.  These tag values may be overwritten by tag
            values provided at invocation time.
        hook_defs (Optional[AbstractSet[HookDefinition]]): A set of hook definitions applied to the
            pipeline. When a hook is applied to a pipeline, it will be attached to all solid
            instances within the pipeline.
        solid_retry_policy (Optional[RetryPolicy]): The default retry policy for all solids in
            this pipeline. Only used if retry policy is not defined on the solid definition or
            solid invocation.
        asset_layer (Optional[AssetLayer]): Structured object containing all definition-time asset
            information for this pipeline.


        _parent_pipeline_def (INTERNAL ONLY): Used for tracking pipelines created using solid subsets.

    Examples:

        .. code-block:: python

            @solid
            def return_one(_):
                return 1


            @solid(input_defs=[InputDefinition('num')], required_resource_keys={'op'})
            def apply_op(context, num):
                return context.resources.op(num)

            @resource(config_schema=Int)
            def adder_resource(init_context):
                return lambda x: x + init_context.resource_config


            add_mode = ModeDefinition(
                name='add_mode',
                resource_defs={'op': adder_resource},
                description='Mode that adds things',
            )


            add_three_preset = PresetDefinition(
                name='add_three_preset',
                run_config={'resources': {'op': {'config': 3}}},
                mode='add_mode',
            )


            pipeline_def = PipelineDefinition(
                name='basic',
                solid_defs=[return_one, apply_op],
                dependencies={'apply_op': {'num': DependencyDefinition('return_one')}},
                mode_defs=[add_mode],
                preset_defs=[add_three_preset],
            )
    """

    _name: str
    _graph_def: GraphDefinition
    _description: Optional[str]
    _tags: Mapping[str, str]
    _metadata: Sequence[Union[MetadataEntry, PartitionMetadataEntry]]
    _current_level_node_defs: Sequence[NodeDefinition]
    _mode_definitions: Sequence[ModeDefinition]
    _hook_defs: AbstractSet[HookDefinition]
    _solid_retry_policy: Optional[RetryPolicy]
    _preset_defs: Sequence[PresetDefinition]
    _preset_dict: Dict[str, PresetDefinition]
    _asset_layer: AssetLayer
    _resource_requirements: Mapping[str, AbstractSet[str]]
    _all_node_defs: Mapping[str, NodeDefinition]
    _parent_pipeline_def: Optional["PipelineDefinition"]
    _cached_run_config_schemas: Dict[str, "RunConfigSchema"]
    _cached_external_pipeline: Any
    _version_strategy: VersionStrategy

    def __init__(
        self,
        solid_defs: Optional[Sequence[NodeDefinition]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        dependencies: Optional[
            Mapping[Union[str, NodeInvocation], Mapping[str, IDependencyDefinition]]
        ] = None,
        mode_defs: Optional[Sequence[ModeDefinition]] = None,
        preset_defs: Optional[Sequence[PresetDefinition]] = None,
        tags: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, RawMetadataValue]] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
        solid_retry_policy: Optional[RetryPolicy] = None,
        graph_def: Optional[GraphDefinition] = None,
        _parent_pipeline_def: Optional[
            "PipelineDefinition"
        ] = None,  # https://github.com/dagster-io/dagster/issues/2115
        version_strategy: Optional[VersionStrategy] = None,
        asset_layer: Optional[AssetLayer] = None,
        metadata_entries: Optional[Sequence[Union[MetadataEntry, PartitionMetadataEntry]]] = None,
    ):
        # If a graph is specified directly use it
        if isinstance(graph_def, GraphDefinition):
            self._graph_def = graph_def
            self._name = name or graph_def.name

        # Otherwise fallback to legacy construction
        else:
            if name is None:
                check.failed("name must be set provided")
            self._name = name

            if solid_defs is None:
                check.failed("solid_defs must be provided")

            self._graph_def = GraphDefinition(
                name=name,
                dependencies=dependencies,
                node_defs=solid_defs,
                input_mappings=None,
                output_mappings=None,
                config=None,
                description=None,
            )

        # tags and description can exist on graph as well, but since
        # same graph may be in multiple pipelines/jobs, keep separate layer
        self._description = check.opt_str_param(description, "description")
        self._tags = validate_tags(tags)

        metadata_entries = check.opt_sequence_param(metadata_entries, "metadata_entries")
        metadata = check.opt_mapping_param(metadata, "metadata")
        self._metadata_entries = normalize_metadata(metadata, metadata_entries)

        self._current_level_node_defs = self._graph_def.node_defs

        mode_definitions = check.opt_sequence_param(mode_defs, "mode_defs", of_type=ModeDefinition)

        if not mode_definitions:
            mode_definitions = [ModeDefinition()]

        self._mode_definitions = mode_definitions

        seen_modes = set()
        for mode_def in mode_definitions:
            if mode_def.name in seen_modes:
                raise DagsterInvalidDefinitionError(
                    (
                        'Two modes seen with the name "{mode_name}" in "{pipeline_name}". '
                        "Modes must have unique names."
                    ).format(mode_name=mode_def.name, pipeline_name=self.name)
                )
            seen_modes.add(mode_def.name)

        self._hook_defs = check.opt_set_param(hook_defs, "hook_defs", of_type=HookDefinition)
        self._solid_retry_policy = check.opt_inst_param(
            solid_retry_policy, "solid_retry_policy", RetryPolicy
        )

        self._preset_defs = check.opt_sequence_param(preset_defs, "preset_defs", PresetDefinition)
        self._preset_dict: Dict[str, PresetDefinition] = {}
        for preset in self._preset_defs:
            if preset.name in self._preset_dict:
                raise DagsterInvalidDefinitionError(
                    (
                        'Two PresetDefinitions seen with the name "{name}" in "{pipeline_name}". '
                        "PresetDefinitions must have unique names."
                    ).format(name=preset.name, pipeline_name=self.name)
                )
            if preset.mode not in seen_modes:
                raise DagsterInvalidDefinitionError(
                    (
                        'PresetDefinition "{name}" in "{pipeline_name}" '
                        'references mode "{mode}" which is not defined.'
                    ).format(name=preset.name, pipeline_name=self.name, mode=preset.mode)
                )
            self._preset_dict[preset.name] = preset

        self._asset_layer = check.opt_inst_param(
            asset_layer, "asset_layer", AssetLayer, default=AssetLayer.from_graph(self.graph)
        )

        resource_requirements = {}
        for mode_def in self._mode_definitions:
            resource_requirements[mode_def.name] = self._get_resource_requirements_for_mode(
                mode_def
            )
        self._resource_requirements = resource_requirements

        # Recursively explore all nodes in the this pipeline
        self._all_node_defs = _build_all_node_defs(self._current_level_node_defs)
        self._parent_pipeline_def = check.opt_inst_param(
            _parent_pipeline_def, "_parent_pipeline_def", PipelineDefinition
        )
        self._cached_run_config_schemas = {}
        self._cached_external_pipeline = None

        self.version_strategy = check.opt_inst_param(
            version_strategy, "version_strategy", VersionStrategy
        )

        if self.version_strategy is not None:
            experimental_class_warning("VersionStrategy")

        self._graph_def.get_inputs_must_be_resolved_top_level(self._asset_layer)

    def _get_resource_requirements_for_mode(self, mode_def: ModeDefinition) -> Set[str]:
        from ..execution.resources_init import get_transitive_required_resource_keys

        requirements = list(self._graph_def.get_resource_requirements(self.asset_layer))
        for hook_def in self._hook_defs:
            requirements += list(
                hook_def.get_resource_requirements(
                    outer_context=f"{self.target_type} '{self._name}'"
                )
            )
        ensure_requirements_satisfied(mode_def.resource_defs, requirements, mode_def.name)
        required_keys = {requirement.key for requirement in requirements}
        return required_keys.union(
            get_transitive_required_resource_keys(required_keys, mode_def.resource_defs)
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def target_type(self) -> str:
        return "pipeline"

    @property
    def is_job(self) -> bool:
        return False

    def describe_target(self) -> str:
        return f"{self.target_type} '{self.name}'"

    @property
    def tags(self) -> Mapping[str, str]:
        return frozentags(**merge_dicts(self._graph_def.tags, self._tags))

    @property
    def metadata(self) -> Sequence[Union[MetadataEntry, PartitionMetadataEntry]]:
        return self._metadata_entries

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def graph(self) -> GraphDefinition:
        return self._graph_def

    @property
    def dependency_structure(self) -> DependencyStructure:
        return self._graph_def.dependency_structure

    @property
    def dependencies(
        self,
    ) -> Mapping[Union[str, NodeInvocation], Mapping[str, IDependencyDefinition]]:
        return self._graph_def.dependencies

    def get_run_config_schema(self, mode: Optional[str] = None) -> "RunConfigSchema":
        check.str_param(mode, "mode")

        mode_def = self.get_mode_definition(mode)

        if mode_def.name in self._cached_run_config_schemas:
            return self._cached_run_config_schemas[mode_def.name]

        self._cached_run_config_schemas[mode_def.name] = _create_run_config_schema(
            self,
            mode_def,
            self._resource_requirements[mode_def.name],
        )
        return self._cached_run_config_schemas[mode_def.name]

    @property
    def mode_definitions(self) -> Sequence[ModeDefinition]:
        return self._mode_definitions

    @property
    def preset_defs(self) -> Sequence[PresetDefinition]:
        return self._preset_defs

    def _get_mode_definition(self, mode: str) -> Optional[ModeDefinition]:
        check.str_param(mode, "mode")
        for mode_definition in self._mode_definitions:
            if mode_definition.name == mode:
                return mode_definition

        return None

    def get_default_mode(self) -> ModeDefinition:
        return self._mode_definitions[0]

    @property
    def is_single_mode(self) -> bool:
        return len(self._mode_definitions) == 1

    @property
    def is_multi_mode(self) -> bool:
        return len(self._mode_definitions) > 1

    def is_using_memoization(self, run_tags: Mapping[str, str]) -> bool:
        tags = merge_dicts(self.tags, run_tags)
        # If someone provides a false value for memoized run tag, then they are intentionally
        # switching off memoization.
        if tags.get(MEMOIZED_RUN_TAG) == "false":
            return False
        return (
            MEMOIZED_RUN_TAG in tags and tags.get(MEMOIZED_RUN_TAG) == "true"
        ) or self.version_strategy is not None

    def has_mode_definition(self, mode: str) -> bool:
        check.str_param(mode, "mode")
        return bool(self._get_mode_definition(mode))

    def get_default_mode_name(self) -> str:
        return self._mode_definitions[0].name

    def get_mode_definition(self, mode: Optional[str] = None) -> ModeDefinition:
        check.opt_str_param(mode, "mode")
        if mode is None:
            check.invariant(self.is_single_mode)
            return self.get_default_mode()

        mode_def = self._get_mode_definition(mode)

        if mode_def is None:
            check.failed(
                "Could not find mode {mode} in pipeline {name}".format(mode=mode, name=self.name),
            )

        return mode_def

    @property
    def available_modes(self) -> Sequence[str]:
        return [mode_def.name for mode_def in self._mode_definitions]

    def get_required_resource_defs_for_mode(self, mode: str) -> Mapping[str, ResourceDefinition]:
        return {
            resource_key: resource
            for resource_key, resource in self.get_mode_definition(mode).resource_defs.items()
            if resource_key in self._resource_requirements[mode]
        }

    @property
    def all_node_defs(self) -> Sequence[NodeDefinition]:
        return list(self._all_node_defs.values())

    @property
    def top_level_solid_defs(self) -> Sequence[NodeDefinition]:
        return self._current_level_node_defs

    def solid_def_named(self, name: str) -> NodeDefinition:
        check.str_param(name, "name")

        check.invariant(name in self._all_node_defs, "{} not found".format(name))
        return self._all_node_defs[name]

    def has_solid_def(self, name: str) -> bool:
        check.str_param(name, "name")
        return name in self._all_node_defs

    def get_solid(self, handle):
        return self._graph_def.get_solid(handle)

    def has_solid_named(self, name):
        return self._graph_def.has_solid_named(name)

    def solid_named(self, name):
        return self._graph_def.solid_named(name)

    @property
    def solids(self):
        return self._graph_def.solids

    @property
    def solids_in_topological_order(self):
        return self._graph_def.solids_in_topological_order

    def all_dagster_types(self):
        return self._graph_def.all_dagster_types()

    def has_dagster_type(self, name):
        return self._graph_def.has_dagster_type(name)

    def dagster_type_named(self, name):
        return self._graph_def.dagster_type_named(name)

    def get_pipeline_subset_def(
        self, solids_to_execute: Optional[AbstractSet[str]]
    ) -> "PipelineDefinition":
        return (
            self if solids_to_execute is None else _get_pipeline_subset_def(self, solids_to_execute)
        )

    def has_preset(self, name: str) -> bool:
        check.str_param(name, "name")
        return name in self._preset_dict

    def get_preset(self, name: str) -> PresetDefinition:
        check.str_param(name, "name")
        if name not in self._preset_dict:
            raise DagsterInvariantViolationError(
                (
                    'Could not find preset for "{name}". Available presets '
                    'for pipeline "{pipeline_name}" are {preset_names}.'
                ).format(
                    name=name,
                    preset_names=list(self._preset_dict.keys()),
                    pipeline_name=self.name,
                )
            )

        return self._preset_dict[name]

    def get_pipeline_snapshot(self) -> "PipelineSnapshot":
        return self.get_pipeline_index().pipeline_snapshot

    def get_pipeline_snapshot_id(self) -> str:
        return self.get_pipeline_index().pipeline_snapshot_id

    def get_pipeline_index(self) -> "PipelineIndex":
        from dagster._core.host_representation import PipelineIndex
        from dagster._core.snap import PipelineSnapshot

        return PipelineIndex(
            PipelineSnapshot.from_pipeline_def(self), self.get_parent_pipeline_snapshot()
        )

    def get_config_schema_snapshot(self) -> "ConfigSchemaSnapshot":
        return self.get_pipeline_snapshot().config_schema_snapshot

    @property
    def is_subset_pipeline(self) -> bool:
        return False

    @property
    def parent_pipeline_def(self) -> Optional["PipelineDefinition"]:
        return None

    def get_parent_pipeline_snapshot(self) -> Optional["PipelineSnapshot"]:
        return None

    @property
    def solids_to_execute(self) -> Optional[FrozenSet[str]]:
        return None

    @property
    def hook_defs(self) -> AbstractSet[HookDefinition]:
        return self._hook_defs

    @property
    def asset_layer(self) -> AssetLayer:
        return self._asset_layer

    def get_all_hooks_for_handle(self, handle: NodeHandle) -> FrozenSet[HookDefinition]:
        """Gather all the hooks for the given solid from all places possibly attached with a hook.

        A hook can be attached to any of the following objects
        * Solid (solid invocation)
        * PipelineDefinition

        Args:
            handle (NodeHandle): The solid's handle

        Returns:
            FrozenSet[HookDefinition]
        """
        check.inst_param(handle, "handle", NodeHandle)
        hook_defs: Set[HookDefinition] = set()

        current = handle
        lineage = []
        while current:
            lineage.append(current.name)
            current = current.parent

        # hooks on top-level solid
        name = lineage.pop()
        solid = self._graph_def.solid_named(name)
        hook_defs = hook_defs.union(solid.hook_defs)

        # hooks on non-top-level solids
        while lineage:
            name = lineage.pop()
            # While lineage is non-empty, definition is guaranteed to be a graph
            definition = cast(GraphDefinition, solid.definition)
            solid = definition.solid_named(name)
            hook_defs = hook_defs.union(solid.hook_defs)

        # hooks applied to a pipeline definition will run on every solid
        hook_defs = hook_defs.union(self.hook_defs)

        return frozenset(hook_defs)

    def get_retry_policy_for_handle(self, handle: NodeHandle) -> Optional[RetryPolicy]:
        solid = self.get_solid(handle)
        definition = solid.definition

        if solid.retry_policy:
            return solid.retry_policy
        elif isinstance(definition, SolidDefinition) and definition.retry_policy:
            return definition.retry_policy

        # could be expanded to look in composite_solid / graph containers
        else:
            return self._solid_retry_policy

    def with_hooks(self, hook_defs: AbstractSet[HookDefinition]) -> "PipelineDefinition":
        """Apply a set of hooks to all solid instances within the pipeline."""

        hook_defs = check.set_param(hook_defs, "hook_defs", of_type=HookDefinition)

        pipeline_def = PipelineDefinition(
            name=self.name,
            graph_def=self._graph_def,
            mode_defs=self.mode_definitions,
            preset_defs=self.preset_defs,
            tags=self.tags,
            hook_defs=hook_defs | self.hook_defs,
            description=self._description,
            solid_retry_policy=self._solid_retry_policy,
            _parent_pipeline_def=self._parent_pipeline_def,
        )

        update_wrapper(pipeline_def, self, updated=())

        return pipeline_def

    # make Callable for decorator reference updates
    def __call__(self, *args, **kwargs):
        if self.is_job:
            msg = (
                f"Attempted to call job '{self.name}' directly. Jobs should be invoked by "
                "using an execution API function (e.g. `job.execute_in_process`)."
            )
        else:
            msg = (
                f"Attempted to call pipeline '{self.name}' directly. Pipelines should be invoked by "
                "using an execution API function (e.g. `execute_pipeline`)."
            )
        raise DagsterInvariantViolationError(msg)


class PipelineSubsetDefinition(PipelineDefinition):
    @property
    def solids_to_execute(self) -> FrozenSet[str]:
        return frozenset(self._graph_def.node_names())

    @property
    def solid_selection(self) -> Sequence[str]:
        # we currently don't pass the real solid_selection (the solid query list) down here.
        # so in the short-term, to make the call sites cleaner, we will convert the solids to execute
        # to a list
        return self._graph_def.node_names()

    @property
    def parent_pipeline_def(self) -> PipelineDefinition:
        return check.not_none(self._parent_pipeline_def)

    def get_parent_pipeline_snapshot(self) -> Optional["PipelineSnapshot"]:
        parent_pipeline = check.not_none(self.parent_pipeline_def)
        return parent_pipeline.get_pipeline_snapshot()

    @property
    def is_subset_pipeline(self) -> bool:
        return True

    def get_pipeline_subset_def(
        self, _solids_to_execute: Optional[AbstractSet[str]]
    ) -> "PipelineSubsetDefinition":
        raise DagsterInvariantViolationError("Pipeline subsets may not be subset again.")


def _dep_key_of(solid: Node) -> NodeInvocation:
    return NodeInvocation(
        name=solid.definition.name,
        alias=solid.name,
        tags=solid.tags,
        hook_defs=solid.hook_defs,
        retry_policy=solid.retry_policy,
    )


def _get_pipeline_subset_def(
    pipeline_def: PipelineDefinition,
    solids_to_execute: AbstractSet[str],
) -> "PipelineSubsetDefinition":
    """
    Build a pipeline which is a subset of another pipeline.
    Only includes the solids which are in solids_to_execute.
    """

    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    check.set_param(solids_to_execute, "solids_to_execute", of_type=str)
    graph = pipeline_def.graph
    for solid_name in solids_to_execute:
        if not graph.has_solid_named(solid_name):
            raise DagsterInvalidSubsetError(
                "{target_type} {pipeline_name} has no {node_type} named {name}.".format(
                    target_type=pipeline_def.target_type,
                    pipeline_name=pipeline_def.name,
                    name=solid_name,
                    node_type="ops" if pipeline_def.is_job else "solids",
                ),
            )

    # go in topo order to ensure deps dict is ordered
    solids = list(
        filter(lambda solid: solid.name in solids_to_execute, graph.solids_in_topological_order)
    )

    deps: Dict[
        Union[str, NodeInvocation],
        Dict[str, IDependencyDefinition],
    ] = {_dep_key_of(solid): {} for solid in solids}

    for node in solids:
        for node_input in node.inputs():
            if graph.dependency_structure.has_direct_dep(node_input):
                node_output = pipeline_def.dependency_structure.get_direct_dep(node_input)
                if node_output.node.name in solids_to_execute:
                    deps[_dep_key_of(node)][node_input.input_def.name] = DependencyDefinition(
                        node=node_output.node.name, output=node_output.output_def.name
                    )
            elif graph.dependency_structure.has_dynamic_fan_in_dep(node_input):
                node_output = graph.dependency_structure.get_dynamic_fan_in_dep(node_input)
                if node_output.node.name in solids_to_execute:
                    deps[_dep_key_of(node)][
                        node_input.input_def.name
                    ] = DynamicCollectDependencyDefinition(
                        solid_name=node_output.node.name,
                        output_name=node_output.output_def.name,
                    )
            elif graph.dependency_structure.has_fan_in_deps(node_input):
                outputs = cast(
                    Sequence[NodeOutput],
                    graph.dependency_structure.get_fan_in_deps(node_input),
                )
                deps[_dep_key_of(node)][node_input.input_def.name] = MultiDependencyDefinition(
                    [
                        DependencyDefinition(
                            node=node_output.node.name, output=node_output.output_def.name
                        )
                        for node_output in outputs
                        if node_output.node.name in solids_to_execute
                    ]
                )
            # else input is unconnected

    try:
        sub_pipeline_def = PipelineSubsetDefinition(
            name=pipeline_def.name,  # should we change the name for subsetted pipeline?
            solid_defs=list({solid.definition for solid in solids}),
            mode_defs=pipeline_def.mode_definitions,
            dependencies=deps,
            _parent_pipeline_def=pipeline_def,
            tags=pipeline_def.tags,
            hook_defs=pipeline_def.hook_defs,
        )

        return sub_pipeline_def
    except DagsterInvalidDefinitionError as exc:
        # This handles the case when you construct a subset such that an unsatisfied
        # input cannot be loaded from config. Instead of throwing a DagsterInvalidDefinitionError,
        # we re-raise a DagsterInvalidSubsetError.
        raise DagsterInvalidSubsetError(
            f"The attempted subset {str_format_set(solids_to_execute)} for {pipeline_def.target_type} "
            f"{pipeline_def.name} results in an invalid {pipeline_def.target_type}"
        ) from exc


def _iterate_all_nodes(root_node_dict: Mapping[str, Node]) -> Iterator[Node]:
    for node in root_node_dict.values():
        yield node
        if node.is_graph:
            yield from _iterate_all_nodes(node.definition.ensure_graph_def().node_dict)


def _build_all_node_defs(node_defs: Sequence[NodeDefinition]) -> Mapping[str, NodeDefinition]:
    all_defs: Dict[str, NodeDefinition] = {}
    for current_level_node_def in node_defs:
        for node_def in current_level_node_def.iterate_node_defs():
            if node_def.name in all_defs:
                if all_defs[node_def.name] != node_def:
                    raise DagsterInvalidDefinitionError(
                        'Detected conflicting node definitions with the same name "{name}"'.format(
                            name=node_def.name
                        )
                    )
            else:
                all_defs[node_def.name] = node_def

    return all_defs


def _create_run_config_schema(
    pipeline_def: PipelineDefinition,
    mode_definition: ModeDefinition,
    required_resources: AbstractSet[str],
) -> "RunConfigSchema":
    from .job_definition import JobDefinition, get_direct_input_values_from_job
    from .run_config import (
        RunConfigSchemaCreationData,
        construct_config_type_dictionary,
        define_run_config_schema_type,
    )
    from .run_config_schema import RunConfigSchema

    # When executing with a subset pipeline, include the missing solids
    # from the original pipeline as ignored to allow execution with
    # run config that is valid for the original
    if isinstance(pipeline_def, JobDefinition) and pipeline_def.is_subset_pipeline:
        if isinstance(pipeline_def.graph, SubselectedGraphDefinition):  # op selection provided
            ignored_solids = pipeline_def.graph.get_top_level_omitted_nodes()
        elif pipeline_def.asset_selection_data:
            parent_job = pipeline_def
            while parent_job.asset_selection_data:
                parent_job = parent_job.asset_selection_data.parent_job_def

            ignored_solids = [
                solid
                for solid in parent_job.graph.solids
                if not pipeline_def.has_solid_named(solid.name)
            ]
    elif pipeline_def.is_subset_pipeline:
        if pipeline_def.parent_pipeline_def is None:
            check.failed("Unexpected subset pipeline state")

        ignored_solids = [
            solid
            for solid in pipeline_def.parent_pipeline_def.graph.solids
            if not pipeline_def.has_solid_named(solid.name)
        ]
    else:
        ignored_solids = []

    run_config_schema_type = define_run_config_schema_type(
        RunConfigSchemaCreationData(
            pipeline_name=pipeline_def.name,
            solids=pipeline_def.graph.solids,
            graph_def=pipeline_def.graph,
            dependency_structure=pipeline_def.graph.dependency_structure,
            mode_definition=mode_definition,
            logger_defs=mode_definition.loggers,
            ignored_solids=ignored_solids,
            required_resources=required_resources,
            is_using_graph_job_op_apis=pipeline_def.is_job,
            direct_inputs=get_direct_input_values_from_job(pipeline_def),
            asset_layer=pipeline_def.asset_layer,
        )
    )

    if mode_definition.config_mapping:
        outer_config_type = mode_definition.config_mapping.config_schema.config_type
    else:
        outer_config_type = run_config_schema_type

    if outer_config_type is None:
        check.failed("Unexpected outer_config_type value of None")

    config_type_dict_by_name, config_type_dict_by_key = construct_config_type_dictionary(
        pipeline_def.all_node_defs,
        outer_config_type,
    )

    return RunConfigSchema(
        run_config_schema_type=run_config_schema_type,
        config_type_dict_by_name=config_type_dict_by_name,
        config_type_dict_by_key=config_type_dict_by_key,
        config_mapping=mode_definition.config_mapping,
    )
