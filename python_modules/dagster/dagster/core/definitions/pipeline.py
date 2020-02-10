from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.core.serdes import whitelist_for_serdes
from dagster.core.types.dagster_type import construct_dagster_type_dictionary

from .container import IContainSolids, create_execution_structure, validate_dependency_dict
from .dependency import (
    DependencyDefinition,
    MultiDependencyDefinition,
    SolidHandle,
    SolidInvocation,
)
from .mode import ModeDefinition
from .preset import PresetDefinition
from .solid import ISolidDefinition


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
                '''You have passed a lambda or function {func} into pipeline {name} that is
                not a solid. You have likely forgetten to annotate this function with
                an @solid or @lambda_solid decorator.'
                '''.format(
                    name=pipeline_name, func=solid_def.__name__
                )
            )
        else:
            raise DagsterInvalidDefinitionError(
                'Invalid item in solid list: {item}'.format(item=repr(solid_def))
            )

    return solid_defs


class PipelineDefinition(IContainSolids, object):
    '''Defines a Dagster pipeline.

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

        _parent_pipeline_def (INTERNAL ONLY): Used for tracking pipelines created using solid subsets.

    Examples:

        .. code-block:: python

            @lambda_solid
            def return_one():
                return 1


            @solid(input_defs=[InputDefinition('num')], required_resource_keys={'op'})
            def apply_op(context, num):
                return context.resources.op(num)

            @resource(config=Int)
            def adder_resource(init_context):
                return lambda x: x + init_context.resource_config


            add_mode = ModeDefinition(
                name='add_mode',
                resource_defs={'op': adder_resource},
                description='Mode that adds things',
            )


            add_three_preset = PresetDefinition(
                name='add_three_preset',
                environment_dict={'resources': {'op': {'config': 3}}},
                mode='add_mode',
            )


            pipeline_def = PipelineDefinition(
                name='basic',
                solid_defs=[return_one, apply_op],
                dependencies={'apply_op': {'num': DependencyDefinition('return_one')}},
                mode_defs=[add_mode],
                preset_defs=[add_three_preset],
            )
    '''

    def __init__(
        self,
        solid_defs,
        name=None,
        description=None,
        dependencies=None,
        mode_defs=None,
        preset_defs=None,
        _parent_pipeline_def=None,  # https://github.com/dagster-io/dagster/issues/2115
    ):
        self._name = check.opt_str_param(name, 'name', '<<unnamed>>')
        self._description = check.opt_str_param(description, 'description')

        mode_definitions = check.opt_list_param(mode_defs, 'mode_defs', of_type=ModeDefinition)

        if not mode_definitions:
            mode_definitions = [ModeDefinition()]

        self._mode_definitions = mode_definitions

        self._current_level_solid_defs = check.list_param(
            _check_solids_arg(self._name, solid_defs), 'solid_defs', of_type=ISolidDefinition
        )

        seen_modes = set()
        for mode_def in mode_definitions:
            if mode_def.name in seen_modes:
                raise DagsterInvalidDefinitionError(
                    (
                        'Two modes seen with the name "{mode_name}" in "{pipeline_name}". '
                        'Modes must have unique names.'
                    ).format(mode_name=mode_def.name, pipeline_name=self._name)
                )
            seen_modes.add(mode_def.name)

        self._dependencies = validate_dependency_dict(dependencies)

        dependency_structure, solid_dict = create_execution_structure(
            self._current_level_solid_defs, self._dependencies, container_definition=None
        )

        self._solid_dict = solid_dict
        self._dependency_structure = dependency_structure

        self._runtime_type_dict = construct_dagster_type_dictionary(self._current_level_solid_defs)

        self._preset_defs = check.opt_list_param(preset_defs, 'preset_defs', PresetDefinition)
        self._preset_dict = {}
        for preset in self._preset_defs:
            if preset.name in self._preset_dict:
                raise DagsterInvalidDefinitionError(
                    (
                        'Two PresetDefinitions seen with the name "{name}" in "{pipeline_name}". '
                        'PresetDefinitions must have unique names.'
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
        _validate_resource_dependencies(self._mode_definitions, self._current_level_solid_defs)

        # Validate unsatisfied inputs can be materialized from config
        _validate_inputs(self._dependency_structure, self._solid_dict)

        self._all_solid_defs = _build_all_solid_defs(self._current_level_solid_defs)
        self._parent_pipeline_def = check.opt_inst_param(
            _parent_pipeline_def, '_parent_pipeline_def', PipelineDefinition
        )
        self._cached_enviroment_schemas = {}

    def get_environment_schema(self, mode=None):
        check.str_param(mode, 'mode')

        mode_def = self.get_mode_definition(mode)

        if mode_def.name in self._cached_enviroment_schemas:
            return self._cached_enviroment_schemas[mode_def.name]

        self._cached_enviroment_schemas[mode_def.name] = _create_environment_schema(self, mode_def)
        return self._cached_enviroment_schemas[mode_def.name]

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
        check.str_param(mode, 'mode')
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
        check.str_param(mode, 'mode')
        return bool(self._get_mode_definition(mode))

    def get_default_mode_name(self):
        return self._mode_definitions[0].name

    def get_mode_definition(self, mode=None):
        check.opt_str_param(mode, 'mode')
        if mode is None:
            check.invariant(self.is_single_mode)
            return self.get_default_mode()

        mode_def = self._get_mode_definition(mode)

        if mode_def is None:
            check.failed(
                'Could not find mode {mode} in pipeline {name}'.format(mode=mode, name=self._name)
            )

        return mode_def

    @property
    def available_modes(self):
        return [mode_def.name for mode_def in self._mode_definitions]

    @property
    def display_name(self):
        '''str: Display name of pipeline.

        Name suitable for exception messages, logging etc. If pipeline
        is unnamed the method will return "<<unnamed>>".
        '''
        return self._name if self._name else '<<unnamed>>'

    @property
    def solids(self):
        '''List[Solid]: Top-level solids in the pipeline.
        '''
        return list(set(self._solid_dict.values()))

    def has_solid_named(self, name):
        '''Return whether or not there is a top level solid with this name in the piepline

        Args:
            name (str): Name of solid

        Returns:
            bool: True if the solid is in the pipeline
        '''
        check.str_param(name, 'name')
        return name in self._solid_dict

    def solid_named(self, name):
        '''Return the top level solid named "name". Throws if it does not exist.

        Args:
            name (str): Name of solid

        Returns:
            Solid:
        '''
        check.str_param(name, 'name')
        if name not in self._solid_dict:
            raise DagsterInvariantViolationError(
                'Pipeline {pipeline_name} has no solid named {name}.'.format(
                    pipeline_name=self._name, name=name
                )
            )
        return self._solid_dict[name]

    def get_solid(self, handle):
        '''Return the solid contained anywhere within the pipeline via its handle.

        Args:
            handle (Union[SolidHandle, str]):

        Returns:
            Solid:

        '''
        check.inst_param(handle, 'handle', SolidHandle)
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

    @property
    def selector(self):
        if self._parent_pipeline_def is None:
            return ExecutionSelector(self.name)

        return ExecutionSelector(self.name, list(self._solid_dict.keys()))

    def has_runtime_type(self, name):
        check.str_param(name, 'name')
        return name in self._runtime_type_dict

    def runtime_type_named(self, name):
        check.str_param(name, 'name')
        return self._runtime_type_dict[name]

    def all_runtime_types(self):
        return self._runtime_type_dict.values()

    @property
    def all_solid_defs(self):
        return list(self._all_solid_defs.values())

    @property
    def top_level_solid_defs(self):
        return self._current_level_solid_defs

    def solid_def_named(self, name):
        check.str_param(name, 'name')

        check.invariant(name in self._all_solid_defs, '{} not found'.format(name))
        return self._all_solid_defs[name]

    def has_solid_def(self, name):
        check.str_param(name, 'name')
        return name in self._all_solid_defs

    def build_sub_pipeline(self, solid_subset):
        check.opt_list_param(solid_subset, 'solid_subset', of_type=str)
        return self if solid_subset is None else _build_sub_pipeline(self, solid_subset)

    def get_presets(self):
        return list(self._preset_dict.values())

    def has_preset(self, name):
        check.str_param(name, 'name')
        return name in self._preset_dict

    def get_preset(self, name):
        check.str_param(name, 'name')
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

    def new_with(self, name=None, mode_defs=None, preset_defs=None):
        return PipelineDefinition(
            solid_defs=self._current_level_solid_defs,
            name=name if name is not None else self._name,
            description=self._description,
            dependencies=self._dependencies,
            mode_defs=mode_defs if mode_defs is not None else self._mode_definitions,
            preset_defs=preset_defs if preset_defs is not None else self._preset_defs,
        )


def _dep_key_of(solid):
    return SolidInvocation(solid.definition.name, solid.name)


def _build_sub_pipeline(pipeline_def, solid_names):
    '''
    Build a pipeline which is a subset of another pipeline.
    Only includes the solids which are in solid_names.
    '''

    from dagster.core.definitions.handle import ExecutionTargetHandle

    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.list_param(solid_names, 'solid_names', of_type=str)

    solid_name_set = set(solid_names)
    solids = list(map(pipeline_def.solid_named, solid_names))
    deps = {_dep_key_of(solid): {} for solid in solids}

    for solid in solids:
        for input_handle in solid.input_handles():
            if pipeline_def.dependency_structure.has_singular_dep(input_handle):
                output_handle = pipeline_def.dependency_structure.get_singular_dep(input_handle)
                if output_handle.solid.name in solid_name_set:
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
                        if output_handle.solid.name in solid_name_set
                    ]
                )

    sub_pipeline_def = PipelineDefinition(
        name=pipeline_def.name,  # should we change the name for subsetted pipeline?
        solid_defs=list({solid.definition for solid in solids}),
        mode_defs=pipeline_def.mode_definitions,
        dependencies=deps,
        _parent_pipeline_def=pipeline_def,
    )
    handle, _ = ExecutionTargetHandle.get_handle(pipeline_def)
    if handle:
        ExecutionTargetHandle.cache_handle(sub_pipeline_def, handle, solid_names=solid_names)

    return sub_pipeline_def


def _validate_resource_dependencies(mode_definitions, solid_defs):
    '''This validation ensures that each pipeline context provides the resources that are required
    by each solid.
    '''
    check.list_param(mode_definitions, 'mode_definintions', of_type=ModeDefinition)
    check.list_param(solid_defs, 'solid_defs', of_type=ISolidDefinition)

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
                            'Resource \'{resource}\' is required by system storage '
                            '\'{storage_name}\', but is not provided by mode \'{mode_name}\'.'
                        ).format(
                            resource=required_resource,
                            storage_name=system_storage_def.name,
                            mode_name=mode_def.name,
                        )
                    )


def _validate_inputs(dependency_structure, solid_dict):
    for solid in solid_dict.values():
        for handle in solid.input_handles():
            if not dependency_structure.has_deps(handle):
                if (
                    not handle.input_def.runtime_type.input_hydration_config
                    and not handle.input_def.runtime_type.is_nothing
                ):
                    raise DagsterInvalidDefinitionError(
                        'Input "{input_name}" in solid "{solid_name}" is not connected to '
                        'the output of a previous solid and can not be hydrated from configuration, '
                        'creating an impossible to execute pipeline. '
                        'Possible solutions are:\n'
                        '  * add a input_hydration_config for the type "{runtime_type}"\n'
                        '  * connect "{input_name}" to the output of another solid\n'.format(
                            solid_name=solid.name,
                            input_name=handle.input_def.name,
                            runtime_type=handle.input_def.runtime_type.display_name,
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


@whitelist_for_serdes
class ExecutionSelector(namedtuple('_ExecutionSelector', 'name solid_subset')):
    def __new__(cls, name, solid_subset=None):
        return super(ExecutionSelector, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            solid_subset=None
            if solid_subset is None
            else check.list_param(solid_subset, 'solid_subset', of_type=str),
        )

    def to_graphql_input(self):
        return {'name': self.name, 'solidSubset': self.solid_subset}


@whitelist_for_serdes
class PipelineRunsFilter(namedtuple('_PipelineRunsFilter', 'run_id tags pipeline_name status')):
    def __new__(cls, run_id=None, pipeline_name=None, status=None, tags=None):
        return super(PipelineRunsFilter, cls).__new__(
            cls,
            run_id=check.opt_str_param(run_id, 'run_id'),
            tags=check.opt_dict_param(tags, 'tags', key_type=str, value_type=str),
            pipeline_name=check.opt_str_param(pipeline_name, 'pipeline_name'),
            status=status,
        )

    def to_graphql_input(self):
        return {
            'runId': self.run_id,
            'tags': [{'key': k, 'value': v} for k, v in self.tags.items()],
            'pipelineName': self.pipeline_name,
            'status': self.status,
        }


def _create_environment_schema(pipeline_def, mode_definition):
    from .environment_configs import (
        EnvironmentClassCreationData,
        construct_config_type_dictionary,
        define_environment_cls,
    )
    from .environment_schema import EnvironmentSchema

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

    return EnvironmentSchema(
        environment_type=environment_type,
        config_type_dict_by_name=config_type_dict_by_name,
        config_type_dict_by_key=config_type_dict_by_key,
    )
