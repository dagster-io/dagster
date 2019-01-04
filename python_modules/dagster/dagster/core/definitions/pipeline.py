from dagster import check

from .context import (
    PipelineContextDefinition,
    default_pipeline_context_definitions,
)

from .dependency import DependencyDefinition

from .pipeline_creation import (
    create_execution_structure,
    construct_type_dictionary,
)

from .utils import check_opt_two_dim_dict


class PipelineDefinition(object):
    '''A instance of a PipelineDefinition represents a pipeline in dagster.

    A pipeline is comprised of:

    - Solids:
        Each solid represents a functional unit of data computation.

    - Context Definitions:
        Pipelines can be designed to execute in a number of different operating environments
        (e.g. prod, dev, unittest) that require different configuration and setup. A context
        definition defines how a context (of type ExecutionContext) is created and what
        configuration is necessary to create it.

    - Dependencies:
        Solids within a pipeline are arranged as a DAG (directed, acyclic graph). Dependencies
        determine how the values produced by solids flow through the DAG.

    Attributes:
        name (str):
            Name of the pipeline. Must be unique per-repository.
        description (str):
            Description of the pipeline. Optional.
        solids (List[SolidDefinition]):
            List of the solids in this pipeline.
        dependencies (Dict[str, Dict[str, DependencyDefinition]]) :
            Dependencies that constitute the structure of the pipeline. This is a two-dimensional
            array that maps solid_name => input_name => DependencyDefiniion instance
        context_definitions (Dict[str, PipelineContextDefinition]):
            The context definitions available for consumers of this pipelines. For example, a
            unit-testing environment and a production environment probably have very different
            configuration and requirements. There would be one context definition per
            environment.
        dependency_structure (DependencyStructure):
            Used mostly internally. This has the same information as the dependencies data
            structure, but indexed for fast usage.
    '''

    def __init__(
        self,
        solids,
        name=None,
        description=None,
        context_definitions=None,
        dependencies=None,
    ):
        '''
        Args:
            solids (List[SolidDefinition]): Solids in the pipeline
            name (str): Name. This is optional, mostly for situations that require ephemeral
                pipeline definitions for fast scaffolding or testing.
            description (str): Description of the pipline.
            context_definitions (Dict[str, PipelineContextDefinition]): See class description.
            dependencies: (Dict[str, Dict[str, DependencyDefinition]]): See class description.
        '''
        self.name = check.opt_str_param(name, 'name', '<<unnamed>>')
        self.description = check.opt_str_param(description, 'description')

        check.list_param(solids, 'solids')

        if context_definitions is None:
            context_definitions = default_pipeline_context_definitions()

        self.context_definitions = check.dict_param(
            context_definitions,
            'context_definitions',
            key_type=str,
            value_type=PipelineContextDefinition,
        )

        self.dependencies = check_opt_two_dim_dict(
            dependencies,
            'dependencies',
            value_type=DependencyDefinition,
        )

        dependency_structure, pipeline_solid_dict = create_execution_structure(
            solids,
            self.dependencies,
        )

        self._solid_dict = pipeline_solid_dict
        self.dependency_structure = dependency_structure

        from dagster.core.system_config.types import EnvironmentConfigType

        self.environment_type = EnvironmentConfigType(self)

        self._type_dict = construct_type_dictionary(
            solids,
            self.context_definitions,
            self.environment_type,
        )

    @property
    def display_name(self):
        '''Name suitable for exception messages, logging etc. If pipeline
        is unnamed the method with return "<<unnamed>>".

        Returns:
            str: Display name of pipeline
        '''
        return self.name if self.name else '<<unnamed>>'

    @property
    def solids(self):
        '''Return the solids in the pipeline.

        Returns:
            List[SolidDefinition]: List of solids.
        '''
        return list(set(self._solid_dict.values()))

    def has_solid(self, name):
        '''Return whether or not the solid is in the piepline

        Args:
            name (str): Name of solid

        Returns:
            bool: True if the solid is in the pipeline
        '''
        check.str_param(name, 'name')
        return name in self._solid_dict

    def solid_named(self, name):
        '''Return the solid named "name". Throws if it does not exist.

        Args:
            name (str): Name of solid

        Returns:
            SolidDefinition: SolidDefinition with correct name.
        '''
        check.str_param(name, 'name')
        return self._solid_dict[name]

    def has_type(self, name):
        check.str_param(name, 'name')
        return name in self._type_dict

    def type_named(self, name):
        check.str_param(name, 'name')
        return self._type_dict[name]

    def all_types(self):
        return self._type_dict.values()

    def has_context(self, name):
        check.str_param(name, 'name')
        return name in self.context_definitions

    @property
    def solid_defs(self):
        return list(set([solid.definition for solid in self.solids]))

    def solid_def_named(self, name):
        check.str_param(name, 'name')

        for solid in self.solids:
            if solid.definition.name == name:
                return solid.definition

        check.failed('{} not found'.format(name))

    def has_solid_def(self, name):
        check.str_param(name, 'name')

        for solid in self.solids:
            if solid.definition.name == name:
                return True

        return False
