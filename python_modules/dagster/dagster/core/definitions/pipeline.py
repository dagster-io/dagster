import six

from dagster import check
from dagster.core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidSubsetError,
    DagsterInvariantViolationError,
)
from dagster.core.types.dagster_type import DagsterTypeKind, construct_dagster_type_dictionary
from dagster.core.utils import str_format_set

from .dependency import (
    DependencyDefinition,
    MultiDependencyDefinition,
    SolidHandle,
    SolidInvocation,
)
from .hook import HookDefinition
from .mode import ModeDefinition
from .preset import PresetDefinition
from .solid import ISolidDefinition
from .solid_container import IContainSolids, create_execution_structure, validate_dependency_dict
from .utils import validate_tags


def _check_solids_arg(pipeline_name, solid_defs):
    if not isinstance(solid_defs, list):
        raise DagsterInvalidDefinitionError(
            '"solids" arg to pipeline "{name}" is not a list. Got {val}.'.format(
                name=pipeline_name, val=repr(solid_defs)
            )
        )
    for solid_def in solid_defs:
        if isinstance(solid_def, ISolidDefinition):
            continue
        elif callable(solid_def):
            raise DagsterInvalidDefinitionError(
                """You have passed a lambda or function {func} into pipeline {name} that is
                not a solid. You have likely forgetten to annotate this function with
                an @solid or @lambda_solid decorator.'
                """.format(
                    name=pipeline_name, func=solid_def.__name__
                )
            )
        else:
            raise DagsterInvalidDefinitionError(
                "Invalid item in solid list: {item}".format(item=repr(solid_def))
            )

    return solid_defs


class PipelineDefinition(IContainSolids):
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
        _parent_pipeline_def=None,  # https://github.com/dagster-io/dagster/issues/2115
        _hook_defs=None,
    ):
        self._name = check.opt_str_param(name, "name", "<<unnamed>>")
        self._description = check.opt_str_param(description, "description")

        mode_definitions = check.opt_list_param(mode_defs, "mode_defs", of_type=ModeDefinition)

        if not mode_definitions:
            mode_definitions = [ModeDefinition()]

        self._mode_definitions = mode_definitions

        self._current_level_solid_defs = check.list_param(
            _check_solids_arg(self._name, solid_defs), "solid_defs", of_type=ISolidDefinition
        )
        self._tags = validate_tags(tags)

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

        self._dependencies = validate_dependency_dict(dependencies)

        dependency_structure, solid_dict = create_execution_structure(
            self._current_level_solid_defs, self._dependencies, container_definition=None
        )

        self._solid_dict = solid_dict
        self._dependency_structure = dependency_structure

        # eager toposort solids to detect cycles
        self.solids_in_topological_order = self._solids_in_topological_order()

        self._dagster_type_dict = construct_dagster_type_dictionary(self._current_level_solid_defs)

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
            self._mode_definitions, self._current_level_solid_defs, self._solid_dict
        )

        # Validate unsatisfied inputs can be materialized from config
        _validate_inputs(self._dependency_structure, self._solid_dict)

        self._all_solid_defs = _build_all_solid_defs(self._current_level_solid_defs)
        self._parent_pipeline_def = check.opt_inst_param(
            _parent_pipeline_def, "_parent_pipeline_def", PipelineDefinition
        )
        self._cached_run_config_schemas = {}
        self._cached_external_pipeline = None

        self._hook_defs = check.opt_set_param(_hook_defs, "_hook_defs", of_type=HookDefinition)

    def get_run_config_schema(self, mode=None):
        check.str_param(mode, "mode")

        mode_def = self.get_mode_definition(mode)

        if mode_def.name in self._cached_run_config_schemas:
            return self._cached_run_config_schemas[mode_def.name]

        self._cached_run_config_schemas[mode_def.name] = _create_run_config_schema(self, mode_def)
        return self._cached_run_config_schemas[mode_def.name]

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def mode_definitions(self):
        return self._mode_definitions

    @property
    def dependencies(self):
        return self._dependencies

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

    @property
    def solids(self):
        """List[Solid]: Top-level solids in the pipeline.
        """
        return list(set(self._solid_dict.values()))

    def has_solid_named(self, name):
        """Return whether or not there is a top level solid with this name in the pipeline

        Args:
            name (str): Name of solid

        Returns:
            bool: True if the solid is in the pipeline
        """
        check.str_param(name, "name")
        return name in self._solid_dict

    def solid_named(self, name):
        """Return the top level solid named "name". Throws if it does not exist.

        Args:
            name (str): Name of solid

        Returns:
            Solid:
        """
        check.str_param(name, "name")
        check.invariant(
            name in self._solid_dict,
            "Pipeline {pipeline_name} has no solid named {name}.".format(
                pipeline_name=self._name, name=name
            ),
        )

        return self._solid_dict[name]

    def get_solid(self, handle):
        """Return the solid contained anywhere within the pipeline via its handle.

        Args:
            handle (SolidHandle): The solid's handle

        Returns:
            Solid:

        """
        check.inst_param(handle, "handle", SolidHandle)
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

    @property
    def dependency_structure(self):
        return self._dependency_structure

    def has_dagster_type(self, name):
        check.str_param(name, "name")
        return name in self._dagster_type_dict

    def dagster_type_named(self, name):
        check.str_param(name, "name")
        return self._dagster_type_dict[name]

    def all_dagster_types(self):
        return self._dagster_type_dict.values()

    @property
    def all_solid_defs(self):
        return list(self._all_solid_defs.values())

    @property
    def top_level_solid_defs(self):
        return self._current_level_solid_defs

    def solid_def_named(self, name):
        check.str_param(name, "name")

        check.invariant(name in self._all_solid_defs, "{} not found".format(name))
        return self._all_solid_defs[name]

    def has_solid_def(self, name):
        check.str_param(name, "name")
        return name in self._all_solid_defs

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
            _parent_pipeline_def=self._parent_pipeline_def,
            _hook_defs=hook_defs.union(self.hook_defs),
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
        )

        return sub_pipeline_def
    except DagsterInvalidDefinitionError as exc:
        # This handles the case when you construct a subset such that an unsatisfied
        # input cannot be loaded from config. Instead of throwing a DagsterInvalidDefinitionError,
        # we re-raise a DagsterInvalidSubsetError.
        six.raise_from(
            DagsterInvalidSubsetError(
                "The attempted subset {solids_to_execute} for pipeline {pipeline_name} results in an invalid pipeline".format(
                    solids_to_execute=str_format_set(solids_to_execute),
                    pipeline_name=pipeline_def.name,
                )
            ),
            exc,
        )


def _validate_resource_dependencies(mode_definitions, solid_defs, solid_dict):
    """This validation ensures that each pipeline context provides the resources that are required
    by each solid.
    """
    check.list_param(mode_definitions, "mode_definitions", of_type=ModeDefinition)
    check.list_param(solid_defs, "solid_defs", of_type=ISolidDefinition)

    for mode_def in mode_definitions:
        mode_resources = set(mode_def.resource_defs.keys())
        for solid_def in solid_defs:
            for required_resource in solid_def.required_resource_keys:
                if required_resource not in mode_resources:
                    raise DagsterInvalidDefinitionError(
                        (
                            'Resource "{resource}" is required by solid def {solid_def_name}, but is not '
                            'provided by mode "{mode_name}".'
                        ).format(
                            resource=required_resource,
                            solid_def_name=solid_def.name,
                            mode_name=mode_def.name,
                        )
                    )
        for system_storage_def in mode_def.system_storage_defs:
            for required_resource in system_storage_def.required_resource_keys:
                if required_resource not in mode_resources:
                    raise DagsterInvalidDefinitionError(
                        (
                            "Resource '{resource}' is required by system storage "
                            "'{storage_name}', but is not provided by mode '{mode_name}'."
                        ).format(
                            resource=required_resource,
                            storage_name=system_storage_def.name,
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


def _validate_inputs(dependency_structure, solid_dict):
    for solid in solid_dict.values():
        for handle in solid.input_handles():
            if not dependency_structure.has_deps(handle):
                if (
                    not handle.input_def.dagster_type.loader
                    and not handle.input_def.dagster_type.kind == DagsterTypeKind.NOTHING
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


def _build_all_solid_defs(solid_defs):
    all_defs = {}
    for current_level_solid_def in solid_defs:
        for solid_def in current_level_solid_def.iterate_solid_defs():
            if solid_def.name in all_defs:
                if all_defs[solid_def.name] != solid_def:
                    raise DagsterInvalidDefinitionError(
                        'Detected conflicting solid definitions with the same name "{name}"'.format(
                            name=solid_def.name
                        )
                    )
            else:
                all_defs[solid_def.name] = solid_def

    return all_defs


def _create_run_config_schema(pipeline_def, mode_definition):
    from .environment_configs import (
        EnvironmentClassCreationData,
        construct_config_type_dictionary,
        define_environment_cls,
    )
    from .run_config_schema import RunConfigSchema

    environment_type = define_environment_cls(
        EnvironmentClassCreationData(
            pipeline_name=pipeline_def.name,
            solids=pipeline_def.solids,
            dependency_structure=pipeline_def.dependency_structure,
            mode_definition=mode_definition,
            logger_defs=mode_definition.loggers,
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
