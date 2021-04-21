from functools import update_wrapper
from typing import TYPE_CHECKING, AbstractSet, Any, Dict, FrozenSet, List, Optional, Set, Union

from dagster import check
from dagster.core.definitions.input import InputMapping
from dagster.core.definitions.output import OutputMapping
from dagster.core.definitions.solid import NodeDefinition
from dagster.core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidSubsetError,
    DagsterInvariantViolationError,
)
from dagster.core.storage.root_input_manager import IInputManagerDefinition
from dagster.core.types.dagster_type import DagsterType, DagsterTypeKind
from dagster.core.utils import str_format_set
from dagster.utils.backcompat import experimental_arg_warning

from .config import ConfigMapping
from .dependency import (
    DependencyDefinition,
    DependencyStructure,
    DynamicCollectDependencyDefinition,
    IDependencyDefinition,
    MultiDependencyDefinition,
    Solid,
    SolidHandle,
    SolidInvocation,
)
from .graph import GraphDefinition
from .hook import HookDefinition
from .mode import ModeDefinition
from .preset import PresetDefinition
from .solid import NodeDefinition
from .utils import validate_tags

if TYPE_CHECKING:
    from .run_config_schema import RunConfigSchema
    from dagster.core.snap import PipelineSnapshot, ConfigSchemaSnapshot
    from dagster.core.host_representation import PipelineIndex


class PipelineDefinition(GraphDefinition):
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
        solid_defs (List[SolidDefinition]): The set of solids used in this pipeline.
        name (str): The name of the pipeline. Must be unique within any
            :py:class:`RepositoryDefinition` containing the pipeline.
        description (Optional[str]): A human-readable description of the pipeline.
        dependencies (Optional[Dict[Union[str, SolidInvocation], Dict[str, DependencyDefinition]]]):
            A structure that declares the dependencies of each solid's inputs on the outputs of
            other solids in the pipeline. Keys of the top level dict are either the string names of
            solids in the pipeline or, in the case of aliased solids,
            :py:class:`SolidInvocations <SolidInvocation>`. Values of the top level dict are
            themselves dicts, which map input names belonging to the solid or aliased solid to
            :py:class:`DependencyDefinitions <DependencyDefinition>`.
        mode_defs (Optional[List[ModeDefinition]]): The set of modes in which this pipeline can
            operate. Modes are used to attach resources, custom loggers, custom system storage
            options, and custom executors to a pipeline. Modes can be used, e.g., to vary available
            resource and logging implementations between local test and production runs.
        preset_defs (Optional[List[PresetDefinition]]): A set of preset collections of configuration
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

        _parent_pipeline_def (INTERNAL ONLY): Used for tracking pipelines created using solid subsets.

    Examples:

        .. code-block:: python

            @lambda_solid
            def return_one():
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

    def __init__(
        self,
        solid_defs: List[NodeDefinition],
        name: str,
        description: Optional[str] = None,
        dependencies: Optional[
            Dict[Union[str, SolidInvocation], Dict[str, IDependencyDefinition]]
        ] = None,
        mode_defs: Optional[List[ModeDefinition]] = None,
        preset_defs: Optional[List[PresetDefinition]] = None,
        tags: Dict[str, Any] = None,
        hook_defs: Optional[AbstractSet[HookDefinition]] = None,
        input_mappings: Optional[List[InputMapping]] = None,
        output_mappings: Optional[List[OutputMapping]] = None,
        config_mapping: Optional[ConfigMapping] = None,
        positional_inputs: List[str] = None,
        _parent_pipeline_def: Optional[
            "PipelineDefinition"
        ] = None,  # https://github.com/dagster-io/dagster/issues/2115
    ):
        # For these warnings they check truthiness because they get changed to [] higher
        # in the stack for the decorator case

        if input_mappings:
            experimental_arg_warning("input_mappings", "PipelineDefinition")

        if output_mappings:
            experimental_arg_warning("output_mappings", "PipelineDefinition")

        if config_mapping is not None:
            experimental_arg_warning("config_mapping", "PipelineDefinition")

        if positional_inputs:
            experimental_arg_warning("positional_inputs", "PipelineDefinition")

        super(PipelineDefinition, self).__init__(
            name=name,
            description=description,
            dependencies=dependencies,
            node_defs=solid_defs,
            tags=check.opt_dict_param(tags, "tags", key_type=str),
            positional_inputs=positional_inputs,
            input_mappings=input_mappings,
            output_mappings=output_mappings,
            config_mapping=config_mapping,
        )

        self._current_level_node_defs = solid_defs
        self._tags = validate_tags(tags)

        mode_definitions = check.opt_list_param(mode_defs, "mode_defs", of_type=ModeDefinition)

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
                    ).format(mode_name=mode_def.name, pipeline_name=self._name)
                )
            seen_modes.add(mode_def.name)

        self._hook_defs = check.opt_set_param(hook_defs, "hook_defs", of_type=HookDefinition)

        self._preset_defs = check.opt_list_param(preset_defs, "preset_defs", PresetDefinition)
        self._preset_dict: Dict[str, PresetDefinition] = {}
        for preset in self._preset_defs:
            if preset.name in self._preset_dict:
                raise DagsterInvalidDefinitionError(
                    (
                        'Two PresetDefinitions seen with the name "{name}" in "{pipeline_name}". '
                        "PresetDefinitions must have unique names."
                    ).format(name=preset.name, pipeline_name=self._name)
                )
            if preset.mode not in seen_modes:
                raise DagsterInvalidDefinitionError(
                    (
                        'PresetDefinition "{name}" in "{pipeline_name}" '
                        'references mode "{mode}" which is not defined.'
                    ).format(name=preset.name, pipeline_name=self._name, mode=preset.mode)
                )
            self._preset_dict[preset.name] = preset

        self._resource_requirements = {
            mode_def.name: _checked_resource_reqs_for_mode(
                mode_def,
                self._current_level_node_defs,
                self._dagster_type_dict,
                self._solid_dict,
                self._hook_defs,
            )
            for mode_def in self._mode_definitions
        }

        # Validate unsatisfied inputs can be materialized from config
        _validate_inputs(self._dependency_structure, self._solid_dict, self._mode_definitions)

        # Recursively explore all nodes in the this pipeline
        self._all_node_defs = _build_all_node_defs(self._current_level_node_defs)
        self._parent_pipeline_def = check.opt_inst_param(
            _parent_pipeline_def, "_parent_pipeline_def", PipelineDefinition
        )
        self._cached_run_config_schemas: Dict[str, "RunConfigSchema"] = {}
        self._cached_external_pipeline = None

    def copy_for_configured(
        self,
        name: str,
        description: Optional[str],
        config_schema: Any,
        config_or_config_fn,
    ) -> "PipelineDefinition":
        if not self.has_config_mapping:
            raise DagsterInvalidDefinitionError(
                "Only pipelines utilizing config mapping can be pre-configured. The pipeline "
                '"{graph_name}" does not have a config mapping, and thus has nothing to be '
                "configured.".format(graph_name=self.name)
            )

        return PipelineDefinition(
            solid_defs=self._solid_defs,
            name=name,
            description=description or self.description,
            dependencies=self._dependencies,
            mode_defs=self._mode_definitions,
            preset_defs=self.preset_defs,
            hook_defs=self.hook_defs,
            input_mappings=self._input_mappings,
            output_mappings=self._output_mappings,
            config_mapping=ConfigMapping(
                self._config_mapping.config_fn, config_schema=config_schema
            ),
            positional_inputs=self.positional_inputs,
            _parent_pipeline_def=self._parent_pipeline_def,
        )

    def get_run_config_schema(self, mode: Optional[str] = None) -> "RunConfigSchema":
        check.str_param(mode, "mode")

        mode_def = self.get_mode_definition(mode)

        if mode_def.name in self._cached_run_config_schemas:
            return self._cached_run_config_schemas[mode_def.name]

        self._cached_run_config_schemas[mode_def.name] = _create_run_config_schema(
            self, mode_def, self._resource_requirements[mode_def.name]
        )
        return self._cached_run_config_schemas[mode_def.name]

    @property
    def mode_definitions(self) -> List[ModeDefinition]:
        return self._mode_definitions

    @property
    def preset_defs(self) -> List[PresetDefinition]:
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
                "Could not find mode {mode} in pipeline {name}".format(mode=mode, name=self._name),
            )

        return mode_def

    @property
    def available_modes(self) -> List[str]:
        return [mode_def.name for mode_def in self._mode_definitions]

    @property
    def tags(self) -> Dict[str, Any]:
        return self._tags

    def has_dagster_type(self, name: str) -> bool:
        check.str_param(name, "name")
        return name in self._dagster_type_dict

    def dagster_type_named(self, name: str) -> DagsterType:
        check.str_param(name, "name")
        return self._dagster_type_dict[name]

    @property
    def all_solid_defs(self) -> List[NodeDefinition]:
        return list(self._all_node_defs.values())

    @property
    def top_level_solid_defs(self) -> List[NodeDefinition]:
        return self._current_level_node_defs

    def solid_def_named(self, name: str) -> NodeDefinition:
        check.str_param(name, "name")

        check.invariant(name in self._all_node_defs, "{} not found".format(name))
        return self._all_node_defs[name]

    def has_solid_def(self, name: str) -> bool:
        check.str_param(name, "name")
        return name in self._all_node_defs

    def get_pipeline_subset_def(self, solids_to_execute: AbstractSet[str]) -> "PipelineDefinition":
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
                    name=name, preset_names=list(self._preset_dict.keys()), pipeline_name=self._name
                )
            )

        return self._preset_dict[name]

    def get_pipeline_snapshot(self) -> "PipelineSnapshot":
        return self.get_pipeline_index().pipeline_snapshot

    def get_pipeline_snapshot_id(self) -> str:
        return self.get_pipeline_index().pipeline_snapshot_id

    def get_pipeline_index(self) -> "PipelineIndex":
        from dagster.core.snap import PipelineSnapshot
        from dagster.core.host_representation import PipelineIndex

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

    def get_all_hooks_for_handle(self, handle: SolidHandle) -> FrozenSet[HookDefinition]:
        """Gather all the hooks for the given solid from all places possibly attached with a hook.

        A hook can be attached to any of the following objects
        * Solid (solid invocation)
        * PipelineDefinition

        Args:
            handle (SolidHandle): The solid's handle

        Returns:
            FrozenSet[HookDefinition]
        """
        check.inst_param(handle, "handle", SolidHandle)
        hook_defs: AbstractSet[HookDefinition] = set()

        current = handle
        lineage = []
        while current:
            lineage.append(current.name)
            current = current.parent

        # hooks on top-level solid
        name = lineage.pop()
        solid = self.solid_named(name)
        hook_defs = hook_defs.union(solid.hook_defs)

        # hooks on non-top-level solids
        while lineage:
            name = lineage.pop()
            solid = solid.definition.solid_named(name)
            hook_defs = hook_defs.union(solid.hook_defs)

        # hooks applied to a pipeline definition will run on every solid
        hook_defs = hook_defs.union(self.hook_defs)

        return frozenset(hook_defs)

    def with_hooks(self, hook_defs: AbstractSet[HookDefinition]) -> "PipelineDefinition":
        """Apply a set of hooks to all solid instances within the pipeline."""

        hook_defs = check.set_param(hook_defs, "hook_defs", of_type=HookDefinition)

        pipeline_def = PipelineDefinition(
            solid_defs=self.top_level_solid_defs,
            name=self.name,
            description=self.description,
            dependencies=self.dependencies,
            mode_defs=self.mode_definitions,
            preset_defs=self.preset_defs,
            tags=self.tags,
            hook_defs=hook_defs | self.hook_defs,
            _parent_pipeline_def=self._parent_pipeline_def,
        )

        update_wrapper(pipeline_def, self, updated=())

        return pipeline_def


class PipelineSubsetDefinition(PipelineDefinition):
    @property
    def solids_to_execute(self) -> Optional[FrozenSet[str]]:
        return frozenset(self._solid_dict.keys())

    @property
    def solid_selection(self) -> List[str]:
        # we currently don't pass the real solid_selection (the solid query list) down here.
        # so in the short-term, to make the call sites cleaner, we will convert the solids to execute
        # to a list
        return list(self._solid_dict.keys())

    @property
    def parent_pipeline_def(self) -> Optional["PipelineDefinition"]:
        return self._parent_pipeline_def

    def get_parent_pipeline_snapshot(self) -> Optional["PipelineSnapshot"]:
        return self._parent_pipeline_def.get_pipeline_snapshot()

    @property
    def is_subset_pipeline(self) -> bool:
        return True

    def get_pipeline_subset_def(
        self, solids_to_execute: AbstractSet[str]
    ) -> "PipelineSubsetDefinition":
        raise DagsterInvariantViolationError("Pipeline subsets may not be subset again.")


def _dep_key_of(solid: Solid) -> SolidInvocation:
    return SolidInvocation(solid.definition.name, solid.name)


def _get_pipeline_subset_def(
    pipeline_def, solids_to_execute: AbstractSet[str]
) -> "PipelineSubsetDefinition":
    """
    Build a pipeline which is a subset of another pipeline.
    Only includes the solids which are in solids_to_execute.
    """

    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    check.set_param(solids_to_execute, "solids_to_execute", of_type=str)

    for solid_name in solids_to_execute:
        if not pipeline_def.has_solid_named(solid_name):
            raise DagsterInvalidSubsetError(
                "Pipeline {pipeline_name} has no solid named {name}.".format(
                    pipeline_name=pipeline_def.name, name=solid_name
                ),
            )

    solids = list(map(pipeline_def.solid_named, solids_to_execute))
    deps: Dict[
        Union[str, SolidInvocation],
        Dict[str, IDependencyDefinition],
    ] = {_dep_key_of(solid): {} for solid in solids}

    for solid in solids:
        for input_handle in solid.input_handles():
            if pipeline_def.dependency_structure.has_direct_dep(input_handle):
                output_handle = pipeline_def.dependency_structure.get_direct_dep(input_handle)
                if output_handle.solid.name in solids_to_execute:
                    deps[_dep_key_of(solid)][input_handle.input_def.name] = DependencyDefinition(
                        solid=output_handle.solid.name, output=output_handle.output_def.name
                    )
            if pipeline_def.dependency_structure.has_dynamic_fan_in_dep(input_handle):
                output_handle = pipeline_def.dependency_structure.get_dynamic_fan_in_dep(
                    input_handle
                )
                if output_handle.solid.name in solids_to_execute:
                    deps[_dep_key_of(solid)][
                        input_handle.input_def.name
                    ] = DynamicCollectDependencyDefinition(
                        solid_name=output_handle.solid.name,
                        output_name=output_handle.output_def.name,
                    )
            elif pipeline_def.dependency_structure.has_fan_in_deps(input_handle):
                output_handles = pipeline_def.dependency_structure.get_fan_in_deps(input_handle)
                deps[_dep_key_of(solid)][input_handle.input_def.name] = MultiDependencyDefinition(
                    [
                        DependencyDefinition(
                            solid=output_handle.solid.name, output=output_handle.output_def.name
                        )
                        for output_handle in output_handles
                        if output_handle.solid.name in solids_to_execute
                    ]
                )

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
            f"The attempted subset {str_format_set(solids_to_execute)} for pipeline "
            f"{pipeline_def.name} results in an invalid pipeline"
        ) from exc


def _checked_resource_reqs_for_mode(
    mode_def: ModeDefinition,
    node_defs: List[NodeDefinition],
    dagster_type_dict: Dict[str, DagsterType],
    solid_dict: Dict[str, Solid],
    pipeline_hook_defs: AbstractSet[HookDefinition],
) -> Set[str]:
    """
    Calculate the resource requirements for the pipeline in this mode and ensure they are
    provided by the mode.

    We combine these operations in to one traversal to allow for raising excpetions that provide
    as much context as possible about where the unsatisfied resource requirement came from.
    """
    resource_reqs: Set[str] = set()
    mode_resources = set(mode_def.resource_defs.keys())
    for node_def in node_defs:
        for required_resource in node_def.required_resource_keys:
            resource_reqs.add(required_resource)
            if required_resource not in mode_resources:
                raise DagsterInvalidDefinitionError(
                    (
                        'Resource "{resource}" is required by solid def {node_def_name}, but is not '
                        'provided by mode "{mode_name}".'
                    ).format(
                        resource=required_resource,
                        node_def_name=node_def.name,
                        mode_name=mode_def.name,
                    )
                )

        for output_def in node_def.output_defs:
            resource_reqs.add(output_def.io_manager_key)
            if output_def.io_manager_key not in mode_resources:
                raise DagsterInvalidDefinitionError(
                    f'IO manager "{output_def.io_manager_key}" is required by output '
                    f'"{output_def.name}" of solid def {node_def.name}, but is not '
                    f'provided by mode "{mode_def.name}".'
                )

    resource_reqs.update(
        _checked_type_resource_reqs_for_mode(
            mode_def,
            dagster_type_dict,
        )
    )

    for intermediate_storage in mode_def.intermediate_storage_defs or []:
        for required_resource in intermediate_storage.required_resource_keys:
            resource_reqs.add(required_resource)
            if required_resource not in mode_resources:
                raise DagsterInvalidDefinitionError(
                    (
                        "Resource '{resource}' is required by intermediate storage "
                        "'{storage_name}', but is not provided by mode '{mode_name}'."
                    ).format(
                        resource=required_resource,
                        storage_name=intermediate_storage.name,
                        mode_name=mode_def.name,
                    )
                )
    for solid in solid_dict.values():
        for hook_def in solid.hook_defs:
            for required_resource in hook_def.required_resource_keys:
                resource_reqs.add(required_resource)
                if required_resource not in mode_resources:
                    raise DagsterInvalidDefinitionError(
                        (
                            'Resource "{resource}" is required by hook "{hook_name}", but is not '
                            'provided by mode "{mode_name}".'
                        ).format(
                            resource=required_resource,
                            hook_name=hook_def.name,
                            mode_name=mode_def.name,
                        )
                    )

    for hook_def in pipeline_hook_defs:
        for required_resource in hook_def.required_resource_keys:
            resource_reqs.add(required_resource)
            if required_resource not in mode_resources:
                raise DagsterInvalidDefinitionError(
                    (
                        'Resource "{resource}" is required by hook "{hook_name}", but is not '
                        'provided by mode "{mode_name}".'
                    ).format(
                        resource=required_resource,
                        hook_name=hook_def.name,
                        mode_name=mode_def.name,
                    )
                )

    for resource_key, resource in mode_def.resource_defs.items():
        for required_resource in resource.required_resource_keys:
            resource_reqs.add(required_resource)
            if required_resource not in mode_resources:
                raise DagsterInvalidDefinitionError(
                    f'Resource "{required_resource}" is required by resource at key "{resource_key}", '
                    f'but is not provided by mode "{mode_def.name}"'
                )

    return resource_reqs


def _checked_type_resource_reqs_for_mode(
    mode_def: ModeDefinition,
    dagster_type_dict: Dict[str, DagsterType],
) -> AbstractSet[str]:
    """
    Calculate all the resource requirements related to DagsterTypes for this mode and ensure the
    mode provides those resources.
    """

    resource_reqs = set()
    mode_resources = set(mode_def.resource_defs.keys())
    for dagster_type in dagster_type_dict.values():
        for required_resource in dagster_type.required_resource_keys:
            resource_reqs.add(required_resource)
            if required_resource not in mode_resources:
                raise DagsterInvalidDefinitionError(
                    (
                        'Resource "{resource}" is required by type "{type_name}", but is not '
                        'provided by mode "{mode_name}".'
                    ).format(
                        resource=required_resource,
                        type_name=dagster_type.display_name,
                        mode_name=mode_def.name,
                    )
                )
        if dagster_type.loader:
            for required_resource in dagster_type.loader.required_resource_keys():
                resource_reqs.add(required_resource)
                if required_resource not in mode_resources:
                    raise DagsterInvalidDefinitionError(
                        (
                            'Resource "{resource}" is required by the loader on type '
                            '"{type_name}", but is not provided by mode "{mode_name}".'
                        ).format(
                            resource=required_resource,
                            type_name=dagster_type.display_name,
                            mode_name=mode_def.name,
                        )
                    )
        if dagster_type.materializer:
            for required_resource in dagster_type.materializer.required_resource_keys():
                resource_reqs.add(required_resource)
                if required_resource not in mode_resources:
                    raise DagsterInvalidDefinitionError(
                        (
                            'Resource "{resource}" is required by the materializer on type '
                            '"{type_name}", but is not provided by mode "{mode_name}".'
                        ).format(
                            resource=required_resource,
                            type_name=dagster_type.display_name,
                            mode_name=mode_def.name,
                        )
                    )

        for plugin in dagster_type.auto_plugins:
            used_by_storage = set(
                [
                    intermediate_storage_def.name
                    for intermediate_storage_def in mode_def.intermediate_storage_defs
                    if plugin.compatible_with_storage_def(intermediate_storage_def)
                ]
            )

            if used_by_storage:
                for required_resource in plugin.required_resource_keys():
                    resource_reqs.add(required_resource)
                    if required_resource not in mode_resources:
                        raise DagsterInvalidDefinitionError(
                            (
                                'Resource "{resource}" is required by the plugin "{plugin_name}"'
                                ' on type "{type_name}" (used with storages {storages}), '
                                'but is not provided by mode "{mode_name}".'
                            ).format(
                                resource=required_resource,
                                type_name=dagster_type.display_name,
                                plugin_name=plugin.__name__,
                                mode_name=mode_def.name,
                                storages=used_by_storage,
                            )
                        )
    return resource_reqs


def _validate_inputs(
    dependency_structure: DependencyStructure,
    solid_dict: Dict[str, Solid],
    mode_definitions: List[ModeDefinition],
) -> None:
    for solid in solid_dict.values():
        for handle in solid.input_handles():
            if dependency_structure.has_deps(handle):
                for mode_def in mode_definitions:
                    for source_output_handle in dependency_structure.get_deps_list(handle):
                        output_manager_key = source_output_handle.output_def.io_manager_key
                        output_manager_def = mode_def.resource_defs[output_manager_key]
                        if not isinstance(output_manager_def, IInputManagerDefinition):
                            raise DagsterInvalidDefinitionError(
                                f'Input "{handle.input_def.name}" of solid "{solid.name}" is '
                                f'connected to output "{source_output_handle.output_def.name}" '
                                f'of solid "{source_output_handle.solid.name}". In mode '
                                f'"{mode_def.name}", that output does not have an output '
                                f"manager that knows how to load inputs, so we don't know how "
                                f"to load the input. To address this, assign an IOManager to "
                                f"the upstream output."
                            )
            else:
                input_def = handle.input_def
                if (
                    not input_def.dagster_type.loader
                    and not input_def.dagster_type.kind == DagsterTypeKind.NOTHING
                    and not input_def.root_manager_key
                ):
                    raise DagsterInvalidDefinitionError(
                        'Input "{input_name}" in solid "{solid_name}" is not connected to '
                        "the output of a previous solid and can not be loaded from configuration, "
                        "creating an impossible to execute pipeline. "
                        "Possible solutions are:\n"
                        '  * add a dagster_type_loader for the type "{dagster_type}"\n'
                        '  * connect "{input_name}" to the output of another solid\n'.format(
                            solid_name=solid.name,
                            input_name=input_def.name,
                            dagster_type=input_def.dagster_type.display_name,
                        )
                    )

                for mode_def in mode_definitions:
                    # If a root manager is provided, it's always used. I.e. it has priority over
                    # the other ways of loading unsatisified inputs - dagster type loaders and
                    # default values.
                    if (
                        input_def.root_manager_key
                        and input_def.root_manager_key not in mode_def.resource_defs
                    ):
                        raise DagsterInvalidDefinitionError(
                            f'Root input manager "{input_def.root_manager_key}" is required by '
                            f'unsatisfied input "{input_def.name}" of solid {solid.name}, but is not '
                            f'provided by mode "{mode_def.name}".'
                        )


def _build_all_node_defs(node_defs: List[NodeDefinition]) -> Dict[str, NodeDefinition]:
    all_defs: Dict[str, NodeDefinition] = {}
    for current_level_node_def in node_defs:
        for node_def in current_level_node_def.iterate_node_defs():
            if node_def.name in all_defs:
                if all_defs[node_def.name] != node_def:
                    raise DagsterInvalidDefinitionError(
                        'Detected conflicting solid definitions with the same name "{name}"'.format(
                            name=node_def.name
                        )
                    )
            else:
                all_defs[node_def.name] = node_def

    return all_defs


def _create_run_config_schema(
    pipeline_def: PipelineDefinition,
    mode_definition: ModeDefinition,
    required_resources: Set[str],
) -> "RunConfigSchema":
    from .environment_configs import (
        EnvironmentClassCreationData,
        construct_config_type_dictionary,
        define_environment_cls,
    )
    from .run_config_schema import RunConfigSchema

    # When executing with a subset pipeline, include the missing solids
    # from the original pipeline as ignored to allow execution with
    # run config that is valid for the original
    if pipeline_def.is_subset_pipeline:
        if pipeline_def.parent_pipeline_def is None:
            check.failed("Unexpected subset pipeline state")

        ignored_solids = [
            solid
            for solid in pipeline_def.parent_pipeline_def.solids
            if not pipeline_def.has_solid_named(solid.name)
        ]
    else:
        ignored_solids = []

    environment_type = define_environment_cls(
        EnvironmentClassCreationData(
            pipeline_name=pipeline_def.name,
            solids=pipeline_def.solids,
            dependency_structure=pipeline_def.dependency_structure,
            mode_definition=mode_definition,
            logger_defs=mode_definition.loggers,
            ignored_solids=ignored_solids,
            required_resources=required_resources,
        )
    )

    config_type_dict_by_name, config_type_dict_by_key = construct_config_type_dictionary(
        pipeline_def.all_solid_defs, environment_type
    )

    return RunConfigSchema(
        environment_type=environment_type,
        config_type_dict_by_name=config_type_dict_by_name,
        config_type_dict_by_key=config_type_dict_by_key,
    )
