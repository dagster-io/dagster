from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.core.execution.config import RunConfig
from dagster.core.types.runtime import construct_runtime_type_dictionary

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
    '''A instance of a PipelineDefinition represents a pipeline in dagster.

    A pipeline is comprised of:

    - Solids:
        Each solid represents a functional unit of data computation.

    - Dependencies:
        Solids within a pipeline are arranged as a DAG (directed, acyclic graph). Dependencies
        determine how the values produced by solids flow through the DAG.

    Args:
        solid_defs (List[SolidDefinition]):
            The set of solid definitions used in this pipeline.
        name (Optional[str])
        description (Optional[str])
        dependencies (Optional[Dict[Union[str, SolidInvocation], Dict[str, DependencyDefinition]]]):
            A structure that declares where each solid gets its inputs. The keys at the top
            level dict are either string names of solids or SolidInvocations. The values
            are dicts that map input names to DependencyDefinitions.
        mode_defs (Optional[List[ModeDefinition]]):
            The set of modes this pipeline can operate in. Modes can be used for example to vary
            resources and logging implementations for local testing and running in production.
        preset_defs (Optional[List[PresetDefinition]]):
            Given the different ways a pipeline may execute, presets give you a way to provide
            specific valid collections of configuration.
    '''

    def __init__(
        self,
        solid_defs,
        name=None,
        description=None,
        dependencies=None,
        mode_defs=None,
        preset_defs=None,
    ):
        self._name = check.opt_str_param(name, 'name', '<<unnamed>>')
        self._description = check.opt_str_param(description, 'description')

        mode_definitions = check.opt_list_param(mode_defs, 'mode_defs', of_type=ModeDefinition)

        if not mode_definitions:
            mode_definitions = [ModeDefinition()]

        self._mode_definitions = mode_definitions

        current_level_solid_defs = check.list_param(
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

        dependency_structure, pipeline_solid_dict = create_execution_structure(
            current_level_solid_defs, self._dependencies, container_definition=None
        )

        self._solid_dict = pipeline_solid_dict
        self._dependency_structure = dependency_structure

        self._runtime_type_dict = construct_runtime_type_dictionary(current_level_solid_defs)

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
        _validate_resource_dependencies(self._mode_definitions, current_level_solid_defs)

        self._all_solid_defs = {}
        for current_level_solid_def in current_level_solid_defs:
            for solid_def in current_level_solid_def.iterate_solid_defs():
                self._all_solid_defs[solid_def.name] = solid_def

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
        '''Name suitable for exception messages, logging etc. If pipeline
        is unnamed the method with return "<<unnamed>>".

        Returns:
            str: Display name of pipeline
        '''
        return self._name if self._name else '<<unnamed>>'

    @property
    def solids(self):
        '''Return the top level solids in the pipeline.

        Returns:
            List[Solid]: List of solids.
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
            handle (SolidHandle):

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

    def has_runtime_type(self, name):
        check.str_param(name, 'name')
        return name in self._runtime_type_dict

    def runtime_type_named(self, name):
        check.str_param(name, 'name')
        return self._runtime_type_dict[name]

    def all_runtime_types(self):
        return self._runtime_type_dict.values()

    @property
    def solid_defs(self):
        return list(self._all_solid_defs.values())

    def solid_def_named(self, name):
        check.str_param(name, 'name')

        check.invariant(name in self._all_solid_defs, '{} not found'.format(name))
        return self._all_solid_defs[name]

    def has_solid_def(self, name):
        check.str_param(name, 'name')
        return name in self._all_solid_defs

    def build_sub_pipeline(self, solid_subset):
        return self if solid_subset is None else _build_sub_pipeline(self, solid_subset)

    def get_presets(self):
        return list(self._preset_dict.values())

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

        preset = self._preset_dict[name]

        pipeline = self
        if preset.solid_subset is not None:
            pipeline = pipeline.build_sub_pipeline(preset.solid_subset)

        return {
            'pipeline': pipeline,
            'environment_dict': preset.get_environment_dict(self._name),
            'run_config': RunConfig(mode=preset.mode),
        }


def _dep_key_of(solid):
    return SolidInvocation(solid.definition.name, solid.name)


def _build_sub_pipeline(pipeline_def, solid_names):
    '''
    Build a pipeline which is a subset of another pipeline.
    Only includes the solids which are in solid_names.
    '''

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

    return PipelineDefinition(
        name=pipeline_def.name,
        solid_defs=list({solid.definition for solid in solids}),
        mode_defs=pipeline_def.mode_definitions,
        dependencies=deps,
    )


def _validate_resource_dependencies(mode_definitions, solid_defs):
    '''This validation ensures that each pipeline context provides the resources that are required
    by each solid.
    '''
    check.list_param(mode_definitions, 'mode_definintions', of_type=ModeDefinition)
    check.list_param(solid_defs, 'solid_defs', of_type=ISolidDefinition)

    for mode_def in mode_definitions:
        mode_resources = set(mode_def.resource_defs.keys())
        for solid in solid_defs:
            for required_resource in solid.required_resource_keys:
                if required_resource not in mode_resources:
                    raise DagsterInvalidDefinitionError(
                        (
                            'Resource "{resource}" is required by solid {solid_name}, but is not '
                            'provided by mode "{mode_name}".'
                        ).format(
                            resource=required_resource,
                            solid_name=solid.name,
                            mode_name=mode_def.name,
                        )
                    )
        for system_storage_def in mode_def.system_storage_defs:
            for required_resource in system_storage_def.required_resource_keys:
                if required_resource not in mode_resources:
                    raise DagsterInvalidDefinitionError(
                        (
                            'Resource "{resource}" is required by system storage'
                            '{storage_name}, but is not provided by mode "{mode_name}".'
                        ).format(
                            resource=required_resource,
                            storage_name=system_storage_def.name,
                            mode_name=mode_def.name,
                        )
                    )
