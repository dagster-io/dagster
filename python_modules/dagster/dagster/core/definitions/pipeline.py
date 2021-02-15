import uuid
import warnings

from dagster import check
from dagster.core.definitions.solid import NodeDefinition
from dagster.core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidSubsetError,
    DagsterInvariantViolationError,
)
from dagster.core.storage.output_manager import IOutputManagerDefinition
from dagster.core.storage.root_input_manager import IInputManagerDefinition
from dagster.core.types.dagster_type import DagsterTypeKind
from dagster.core.utils import str_format_set
from dagster.utils.backcompat import experimental_arg_warning

from .config import ConfigMapping
from .dependency import (
    DependencyDefinition,
    MultiDependencyDefinition,
    SolidHandle,
    SolidInvocation,
)
from .graph import GraphDefinition
from .hook import HookDefinition
from .mode import ModeDefinition
from .preset import PresetDefinition
from .solid import NodeDefinition
from .utils import validate_tags


def _anonymous_pipeline_name():
    return "__pipeline__" + str(uuid.uuid4()).replace("-", "")


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
        name (Optional[str]): The name of the pipeline. Must be unique within any
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
        hook_defs (Optional[Set[HookDefinition]]): A set of hook definitions applied to the
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
        solid_defs,
        name=None,
        description=None,
        dependencies=None,
        mode_defs=None,
        preset_defs=None,
        tags=None,
        hook_defs=None,
        input_mappings=None,
        output_mappings=None,
        config_mapping=None,
        positional_inputs=None,
        _parent_pipeline_def=None,  # https://github.com/dagster-io/dagster/issues/2115
    ):
        if not name:
            warnings.warn(
                "Pipeline must have a name. Names will be required starting in 0.10.0 or later."
            )
            name = _anonymous_pipeline_name()

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
        self._preset_dict = {}
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

        # Validate solid resource dependencies
        _validate_resource_dependencies(
            self._mode_definitions,
            self._current_level_node_defs,
            self._dagster_type_dict,
            self._solid_dict,
            self._hook_defs,
        )

        # Validate unsatisfied inputs can be materialized from config
        _validate_inputs(self._dependency_structure, self._solid_dict, self._mode_definitions)

        # Recursively explore all nodes in the this pipeline
        self._all_node_defs = _build_all_node_defs(self._current_level_node_defs)
        self._parent_pipeline_def = check.opt_inst_param(
            _parent_pipeline_def, "_parent_pipeline_def", PipelineDefinition
        )
        self._cached_run_config_schemas = {}
        self._cached_external_pipeline = None

    def copy_for_configured(self, name, description, config_schema, config_or_config_fn):
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

    def get_run_config_schema(self, mode=None):
        check.str_param(mode, "mode")

        mode_def = self.get_mode_definition(mode)

        if mode_def.name in self._cached_run_config_schemas:
            return self._cached_run_config_schemas[mode_def.name]

        self._cached_run_config_schemas[mode_def.name] = _create_run_config_schema(self, mode_def)
        return self._cached_run_config_schemas[mode_def.name]

    @property
    def mode_definitions(self):
        return self._mode_definitions

    @property
    def preset_defs(self):
        return self._preset_defs

    def _get_mode_definition(self, mode):
        check.str_param(mode, "mode")
        for mode_definition in self._mode_definitions:
            if mode_definition.name == mode:
                return mode_definition

        return None

    def get_default_mode(self):
        return self._mode_definitions[0]

    @property
    def is_single_mode(self):
        return len(self._mode_definitions) == 1

    @property
    def is_multi_mode(self):
        return len(self._mode_definitions) > 1

    def has_mode_definition(self, mode):
        check.str_param(mode, "mode")
        return bool(self._get_mode_definition(mode))

    def get_default_mode_name(self):
        return self._mode_definitions[0].name

    def get_mode_definition(self, mode=None):
        check.opt_str_param(mode, "mode")
        if mode is None:
            check.invariant(self.is_single_mode)
            return self.get_default_mode()

        mode_def = self._get_mode_definition(mode)

        check.invariant(
            mode_def is not None,
            "Could not find mode {mode} in pipeline {name}".format(mode=mode, name=self._name),
        )

        return mode_def

    @property
    def available_modes(self):
        return [mode_def.name for mode_def in self._mode_definitions]

    @property
    def display_name(self):
        """str: Display name of pipeline.

        Name suitable for exception messages, logging etc. If pipeline
        is unnamed the method will return "<<unnamed>>".
        """
        return self._name if self._name else "<<unnamed>>"

    @property
    def tags(self):
        return self._tags

    def has_dagster_type(self, name):
        check.str_param(name, "name")
        return name in self._dagster_type_dict

    def dagster_type_named(self, name):
        check.str_param(name, "name")
        return self._dagster_type_dict[name]

    @property
    def all_solid_defs(self):
        return list(self._all_node_defs.values())

    @property
    def top_level_solid_defs(self):
        return self._current_level_node_defs

    def solid_def_named(self, name):
        check.str_param(name, "name")

        check.invariant(name in self._all_node_defs, "{} not found".format(name))
        return self._all_node_defs[name]

    def has_solid_def(self, name):
        check.str_param(name, "name")
        return name in self._all_node_defs

    def get_pipeline_subset_def(self, solids_to_execute):
        return (
            self if solids_to_execute is None else _get_pipeline_subset_def(self, solids_to_execute)
        )

    def get_presets(self):
        return list(self._preset_dict.values())

    def has_preset(self, name):
        check.str_param(name, "name")
        return name in self._preset_dict

    def get_preset(self, name):
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

    def get_pipeline_snapshot(self):
        return self.get_pipeline_index().pipeline_snapshot

    def get_pipeline_snapshot_id(self):
        return self.get_pipeline_index().pipeline_snapshot_id

    def get_pipeline_index(self):
        from dagster.core.snap import PipelineSnapshot
        from dagster.core.host_representation import PipelineIndex

        return PipelineIndex(
            PipelineSnapshot.from_pipeline_def(self), self.get_parent_pipeline_snapshot()
        )

    def get_config_schema_snapshot(self):
        return self.get_pipeline_snapshot().config_schema_snapshot

    @property
    def is_subset_pipeline(self):
        return False

    @property
    def parent_pipeline_def(self):
        return None

    def get_parent_pipeline_snapshot(self):
        return None

    @property
    def solids_to_execute(self):
        return None

    @property
    def hook_defs(self):
        return self._hook_defs

    def get_all_hooks_for_handle(self, handle):
        """Gather all the hooks for the given solid from all places possibly attached with a hook.

        A hook can be attached to any of the following objects
        * Solid (solid invocation)
        * PipelineDefinition

        Args:
            handle (SolidHandle): The solid's handle

        Returns:
            FrozeSet[HookDefinition]
        """
        check.inst_param(handle, "handle", SolidHandle)
        hook_defs = set()

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

    def with_hooks(self, hook_defs):
        """Apply a set of hooks to all solid instances within the pipeline."""

        hook_defs = check.set_param(hook_defs, "hook_defs", of_type=HookDefinition)

        return PipelineDefinition(
            solid_defs=self.top_level_solid_defs,
            name=self.name,
            description=self.description,
            dependencies=self.dependencies,
            mode_defs=self.mode_definitions,
            preset_defs=self.preset_defs,
            tags=self.tags,
            hook_defs=hook_defs.union(self.hook_defs),
            _parent_pipeline_def=self._parent_pipeline_def,
        )


class PipelineSubsetDefinition(PipelineDefinition):
    @property
    def solids_to_execute(self):
        return frozenset(self._solid_dict.keys())

    @property
    def solid_selection(self):
        # we currently don't pass the real solid_selection (the solid query list) down here.
        # so in the short-term, to make the call sites cleaner, we will convert the solids to execute
        # to a list
        return list(self._solid_dict.keys())

    @property
    def parent_pipeline_def(self):
        return self._parent_pipeline_def

    def get_parent_pipeline_snapshot(self):
        return self._parent_pipeline_def.get_pipeline_snapshot()

    @property
    def is_subset_pipeline(self):
        return True

    def get_pipeline_subset_def(self, solids_to_execute):
        raise DagsterInvariantViolationError("Pipeline subsets may not be subset again.")


def _dep_key_of(solid):
    return SolidInvocation(solid.definition.name, solid.name)


def _get_pipeline_subset_def(pipeline_def, solids_to_execute):
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
    deps = {_dep_key_of(solid): {} for solid in solids}

    for solid in solids:
        for input_handle in solid.input_handles():
            if pipeline_def.dependency_structure.has_singular_dep(input_handle):
                output_handle = pipeline_def.dependency_structure.get_singular_dep(input_handle)
                if output_handle.solid.name in solids_to_execute:
                    deps[_dep_key_of(solid)][input_handle.input_def.name] = DependencyDefinition(
                        solid=output_handle.solid.name, output=output_handle.output_def.name
                    )
            elif pipeline_def.dependency_structure.has_multi_deps(input_handle):
                output_handles = pipeline_def.dependency_structure.get_multi_deps(input_handle)
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


def _validate_resource_dependencies(
    mode_definitions, node_defs, dagster_type_dict, solid_dict, pipeline_hook_defs
):
    """This validation ensures that each pipeline context provides the resources that are required
    by each solid.
    """
    check.list_param(mode_definitions, "mode_definitions", of_type=ModeDefinition)
    check.list_param(node_defs, "node_defs", of_type=NodeDefinition)
    check.dict_param(dagster_type_dict, "dagster_type_dict")
    check.dict_param(solid_dict, "solid_dict")
    check.set_param(pipeline_hook_defs, "pipeline_hook_defs", of_type=HookDefinition)

    for mode_def in mode_definitions:
        mode_resources = set(mode_def.resource_defs.keys())
        for node_def in node_defs:
            for required_resource in node_def.required_resource_keys:
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
                if output_def.io_manager_key not in mode_resources:
                    raise DagsterInvalidDefinitionError(
                        f'IO manager "{output_def.io_manager_key}" is required by output '
                        f'"{output_def.name}" of solid def {node_def.name}, but is not '
                        f'provided by mode "{mode_def.name}".'
                    )

            for input_def in node_def.input_defs:
                if input_def.root_manager_key and input_def.root_manager_key not in mode_resources:
                    raise DagsterInvalidDefinitionError(
                        f'Root input manager "{input_def.root_manager_key}" is required by input '
                        f'"{input_def.name}" of solid def {node_def.name}, but is not '
                        f'provided by mode "{mode_def.name}".'
                    )

        _validate_type_resource_deps_for_mode(mode_def, mode_resources, dagster_type_dict)

        for intermediate_storage in mode_def.intermediate_storage_defs or []:
            for required_resource in intermediate_storage.required_resource_keys:
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


def _validate_type_resource_deps_for_mode(mode_def, mode_resources, dagster_type_dict):
    for dagster_type in dagster_type_dict.values():
        for required_resource in dagster_type.required_resource_keys:
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


def _validate_inputs(dependency_structure, solid_dict, mode_definitions):
    for solid in solid_dict.values():
        for handle in solid.input_handles():
            if dependency_structure.has_deps(handle):
                for mode_def in mode_definitions:
                    for source_output_handle in dependency_structure.get_deps_list(handle):
                        output_manager_key = source_output_handle.output_def.io_manager_key
                        output_manager_def = mode_def.resource_defs[output_manager_key]
                        # TODO: remove the IOutputManagerDefinition check when asset store
                        # API is removed.
                        if isinstance(
                            output_manager_def, IOutputManagerDefinition
                        ) and not isinstance(output_manager_def, IInputManagerDefinition):
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
                if (
                    not handle.input_def.dagster_type.loader
                    and not handle.input_def.dagster_type.kind == DagsterTypeKind.NOTHING
                    and not handle.input_def.root_manager_key
                ):
                    raise DagsterInvalidDefinitionError(
                        'Input "{input_name}" in solid "{solid_name}" is not connected to '
                        "the output of a previous solid and can not be loaded from configuration, "
                        "creating an impossible to execute pipeline. "
                        "Possible solutions are:\n"
                        '  * add a dagster_type_loader for the type "{dagster_type}"\n'
                        '  * connect "{input_name}" to the output of another solid\n'.format(
                            solid_name=solid.name,
                            input_name=handle.input_def.name,
                            dagster_type=handle.input_def.dagster_type.display_name,
                        )
                    )


def _build_all_node_defs(node_defs):
    all_defs = {}
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


def _create_run_config_schema(pipeline_def, mode_definition):
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
