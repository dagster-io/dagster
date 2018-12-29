from collections import (
    defaultdict,
    namedtuple,
)
import keyword
import re
from toposort import toposort_flatten

from dagster import check
from dagster.core import types
from dagster.utils.logging import (
    level_from_string,
    define_colored_console_logger,
)

from .config import DEFAULT_CONTEXT_NAME

from .errors import (
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
)

from .execution_context import (
    RuntimeExecutionContext,
    ExecutionContext,
)

from .types import (
    Field,
)

DEFAULT_OUTPUT = 'result'

DISALLOWED_NAMES = set(
    [
        'context',
        'conf',
        'config',
        'meta',
        'arg_dict',
        'dict',
        'input_arg_dict',
        'output_arg_dict',
        'int',
        'str',
        'float',
        'bool',
        'input',
        'output',
        'result',
        'type',
    ] + keyword.kwlist  # just disallow all python keywords
)


def check_valid_name(name):
    check.str_param(name, 'name')
    if name in DISALLOWED_NAMES:
        raise DagsterInvalidDefinitionError('{name} is not allowed'.format(name=name))

    regex = r'^[A-Za-z0-9_]+$'
    if not re.match(regex, name):
        raise DagsterInvalidDefinitionError(
            '{name} must be in regex {regex}'.format(name=name, regex=regex)
        )
    return name


class ResourceDefinition(object):
    def __init__(self, resource_fn, config_field=None, description=None):
        self.resource_fn = check.callable_param(resource_fn, 'resource_fn')
        self.config_field = check.opt_inst_param(config_field, 'config_field', Field)
        self.description = check.opt_str_param(description, 'description')

    @staticmethod
    def null_resource():
        return ResourceDefinition(resource_fn=lambda _info: None)

    @staticmethod
    def string_resource(description=None):
        return ResourceDefinition(
            resource_fn=lambda info: info.config,
            config_field=Field(types.String),
            description=description,
        )


class PipelineContextDefinition(object):
    '''Pipelines declare the different context types they support, in the form
    of PipelineContextDefinitions. For example a pipeline could declare a context
    definition for different operating environments: unittest, integration tests,
    production and so forth. The use provides context function that returns an
    ExecutionContext that is passed to every solid. One can hang resources
    (such as db connections) off of that context. Thus the pipeline author
    has complete control over how the author of each individual solid within
    the pipeline interacts with its operating environment.

    The PipelineContextDefinition is passed to the PipelineDefinition in
    a dictionary key'ed by its name so the name is not present in this object.

    Attributes:
        config_field (Field): The configuration for the pipeline context.

context_fn (callable):
            Signature is (pipeline: PipelineDefintion, config_value: Any) => ExecutionContext

            A callable that either returns *or* yields an ExecutionContext.

        description (str): A description of what this context represents
    '''

    @staticmethod
    def passthrough_context_definition(context_params):
        '''Create a context definition from a pre-existing context. This can be useful
        in testing contexts where you may want to create a context manually and then
        pass it into a one-off PipelineDefinition

        Args:
            context (ExecutionContext): The context that will provided to the pipeline.
        Returns:
            PipelineContextDefinition: The passthrough context definition.
        '''

        check.inst_param(context_params, 'context', ExecutionContext)
        context_definition = PipelineContextDefinition(context_fn=lambda *_args: context_params)
        return {DEFAULT_CONTEXT_NAME: context_definition}

    def __init__(self, context_fn=None, config_field=None, resources=None, description=None):
        '''
        Args:
            context_fn (callable):
                Signature of context_fn:
                (pipeline: PipelineDefintion, config_value: Any) => ExecutionContext

                Returns *or* yields an ExecutionContext.

                If it yields a context, the code after the yield executes after pipeline
                completion, just like a python context manager.

                Environment-specific resources should be placed in the "resources" argument
                to an execution context. This argument can be *anything* and it is made
                avaiable to every solid in the pipeline. A typical pattern is to have this
                resources object be a namedtuple, where each property is an object that
                manages a particular resource, e.g. aws, a local filesystem manager, etc.

            config_field (Field):
                Define the configuration for the context

            description (str): Description of the context definition.
        '''
        self.config_field = check.opt_inst_param(config_field, 'config_field', Field)
        self.context_fn = check.opt_callable_param(
            context_fn,
            'context_fn',
            lambda *args, **kwargs: ExecutionContext(),
        )
        self.resources = check.opt_dict_param(
            resources,
            'resources',
            key_type=str,
            value_type=ResourceDefinition,
        )
        self.description = description
        self.resources_type = namedtuple(
            'Resources',
            list(resources.keys()),
        ) if resources else None


def _default_pipeline_context_definitions():
    def _default_context_fn(info):
        log_level = level_from_string(info.config['log_level'])
        context = ExecutionContext(
            loggers=[define_colored_console_logger('dagster', level=log_level)]
        )
        return context

    default_context_def = PipelineContextDefinition(
        config_field=Field(
            types.Dict(
                {
                    'log_level':
                    Field(
                        dagster_type=types.String,
                        is_optional=True,
                        default_value='INFO',
                    ),
                }
            ),
        ),
        context_fn=_default_context_fn,
    )
    return {DEFAULT_CONTEXT_NAME: default_context_def}


class DependencyDefinition(namedtuple('_DependencyDefinition', 'solid output description')):
    '''Dependency definitions represent an edge in the DAG of solids. This object is
    used with a dictionary structure (whose keys represent solid/input where the dependency
    comes from) so this object only contains the target dependency information.

    Attributes:
        solid (str):
            The name of the solid that is the target of the dependency.
            This is the solid where the value passed between the solids
            comes from.
        output (str):
            The name of the output that is the target of the dependency.
            Defaults to "result", the default output name of solids with a single output.
        description (str):
            Description of this dependency. Optional.
    '''

    def __new__(cls, solid, output=DEFAULT_OUTPUT, description=None):
        return super(DependencyDefinition, cls).__new__(
            cls,
            check.str_param(solid, 'solid'),
            check.str_param(output, 'output'),
            check.opt_str_param(description, 'description'),
        )


class InputToOutputHandleDict(dict):
    def __getitem__(self, key):
        check.inst_param(key, 'key', SolidInputHandle)
        return dict.__getitem__(self, key)

    def __setitem__(self, key, val):
        check.inst_param(key, 'key', SolidInputHandle)
        check.inst_param(val, 'val', SolidOutputHandle)
        return dict.__setitem__(self, key, val)


def check_two_dim_dict(ddict, param_name, key_type=None, value_type=None):
    check.dict_param(ddict, param_name, key_type=key_type, value_type=dict)
    for sub_dict in ddict.values():
        check.dict_param(sub_dict, 'sub_dict', key_type=key_type, value_type=value_type)
    return ddict


def check_opt_two_dim_dict(ddict, param_name, key_type=None, value_type=None):
    ddict = check.opt_dict_param(ddict, param_name, key_type=key_type, value_type=dict)
    for sub_dict in ddict.values():
        check.dict_param(sub_dict, 'sub_dict', key_type=key_type, value_type=value_type)
    return ddict


def check_two_dim_str_dict(ddict, param_name, value_type):
    return check_two_dim_dict(ddict, param_name, key_type=str, value_type=value_type)


def check_opt_two_dim_str_dict(ddict, param_name, value_type):
    return check_opt_two_dim_dict(ddict, param_name, key_type=str, value_type=value_type)


def _create_handle_dict(solid_dict, dep_dict):
    check.dict_param(solid_dict, 'solid_dict', key_type=str, value_type=Solid)
    check_two_dim_str_dict(dep_dict, 'dep_dict', DependencyDefinition)

    handle_dict = InputToOutputHandleDict()

    for solid_name, input_dict in dep_dict.items():
        for input_name, dep_def in input_dict.items():
            from_solid = solid_dict[solid_name]
            to_solid = solid_dict[dep_def.solid]
            handle_dict[from_solid.input_handle(input_name)] = to_solid.output_handle(
                dep_def.output
            )

    return handle_dict


class DependencyStructure(object):
    @staticmethod
    def from_definitions(solids, dep_dict):
        return DependencyStructure(_create_handle_dict(solids, dep_dict))

    def __init__(self, handle_dict):
        self._handle_dict = check.inst_param(handle_dict, 'handle_dict', InputToOutputHandleDict)

    def has_dep(self, solid_input_handle):
        check.inst_param(solid_input_handle, 'solid_input_handle', SolidInputHandle)
        return solid_input_handle in self._handle_dict

    def deps_of_solid(self, solid_name):
        check.str_param(solid_name, 'solid_name')
        return list(handles[1] for handles in self.__gen_deps_of_solid(solid_name))

    def deps_of_solid_with_input(self, solid_name):
        check.str_param(solid_name, 'solid_name')
        return dict(self.__gen_deps_of_solid(solid_name))

    def __gen_deps_of_solid(self, solid_name):
        for input_handle, output_handle in self._handle_dict.items():
            if input_handle.solid.name == solid_name:
                yield (input_handle, output_handle)

    def depended_by_of_solid(self, solid_name):
        check.str_param(solid_name, 'solid_name')
        result = defaultdict(list)
        for input_handle, output_handle in self._handle_dict.items():
            if output_handle.solid.name == solid_name:
                result[output_handle].append(input_handle)
        return result

    def get_dep(self, solid_input_handle):
        check.inst_param(solid_input_handle, 'solid_input_handle', SolidInputHandle)
        return self._handle_dict[solid_input_handle]

    def input_handles(self):
        return list(self._handle_dict.keys())

    def items(self):
        return self._handle_dict.items()


class SolidInstance(namedtuple('Solid', 'name alias')):
    '''
    A solid identifier in a dependency structure. Allows supplying parameters to the solid,
    like the alias.

    Example:

        .. code-block:: python

            pipeline = Pipeline(
                solids=[solid_1, solid_2]
                dependencies={
                    SolidInstance('solid_2', alias='other_name') : {
                        'input_name' : DependencyDefinition('solid_2'),
                    },
                    'solid_1' : {
                        'input_name': DependencyDefinition('other_name'),
                    },
                }
            )
    '''

    def __new__(cls, name, alias=None):
        name = check.str_param(name, 'name')
        alias = check.opt_str_param(alias, 'alias')
        return super(cls, SolidInstance).__new__(cls, name, alias)


class Solid(object):
    '''
    Solid instance within a pipeline. Defined by it's name inside the pipeline.

    Attributes:
        name (str):
            Name of the solid inside the pipeline. Must be unique per-pipeline.
        definition (SolidDefinition):
            Definition of the solid.
    '''

    def __init__(self, name, definition):
        self.name = name
        self.definition = definition

        input_handles = {}
        for input_def in self.definition.input_defs:
            input_handles[input_def.name] = SolidInputHandle(self, input_def)

        self._input_handles = input_handles

        output_handles = {}
        for output_def in self.definition.output_defs:
            output_handles[output_def.name] = SolidOutputHandle(self, output_def)

        self._output_handles = output_handles

    def input_handles(self):
        return self._input_handles.values()

    def output_handles(self):
        return self._output_handles.values()

    def input_handle(self, name):
        check.str_param(name, 'name')
        return self._input_handles[name]

    def output_handle(self, name):
        check.str_param(name, 'name')
        return self._output_handles[name]

    def has_input(self, name):
        return self.definition.has_input(name)

    def input_def_named(self, name):
        return self.definition.input_def_named(name)

    def has_output(self, name):
        return self.definition.has_output(name)

    def output_def_named(self, name):
        return self.definition.output_def_named(name)

    @property
    def input_defs(self):
        return self.definition.input_defs

    @property
    def output_defs(self):
        return self.definition.output_defs


class SolidAliasMapper:
    def __init__(self, dependencies_dict):
        aliased_dependencies_dict = {}
        solid_uses = defaultdict(set)
        alias_lookup = {}

        for solid_key, input_dep_dict in dependencies_dict.items():
            if not isinstance(solid_key, SolidInstance):
                solid_key = SolidInstance(solid_key)

            if solid_key.alias:
                key = solid_key.name
                alias = solid_key.alias
            else:
                key = solid_key.name
                alias = solid_key.name

            solid_uses[key].add(alias)
            aliased_dependencies_dict[alias] = input_dep_dict
            alias_lookup[alias] = key

            for dependency in input_dep_dict.values():
                solid_uses[dependency.solid].add(dependency.solid)

        self.solid_uses = solid_uses
        self.aliased_dependencies_dict = aliased_dependencies_dict
        self.alias_lookup = alias_lookup

    def get_uses_of_solid(self, solid_def_name):
        return self.solid_uses.get(solid_def_name)


def _create_execution_structure(solids, dependencies_dict):
    mapper = SolidAliasMapper(dependencies_dict)

    pipeline_solids = []
    for solid_def in solids:
        if isinstance(solid_def, SolidDefinition):
            uses_of_solid = mapper.get_uses_of_solid(solid_def.name) or set([solid_def.name])

            for alias in uses_of_solid:
                pipeline_solids.append(Solid(name=alias, definition=solid_def))

        elif callable(solid_def):
            raise DagsterInvalidDefinitionError(
                '''You have passed a lambda or function {func} into a pipeline that is
                not a solid. You have likely forgetten to annotate this function with
                an @solid or @lambda_solid decorator located in dagster.core.decorators
                '''.format(func=solid_def.__name__)
            )
        else:
            raise DagsterInvalidDefinitionError(
                'Invalid item in solid list: {item}'.format(item=repr(solid_def))
            )

    pipeline_solid_dict = {ps.name: ps for ps in pipeline_solids}

    _validate_dependencies(
        mapper.aliased_dependencies_dict,
        pipeline_solid_dict,
        mapper.alias_lookup,
    )

    dependency_structure = DependencyStructure.from_definitions(
        pipeline_solid_dict,
        mapper.aliased_dependencies_dict,
    )

    return dependency_structure, pipeline_solid_dict


def _validate_dependencies(dependencies, solid_dict, alias_lookup):
    for from_solid, dep_by_input in dependencies.items():
        for from_input, dep in dep_by_input.items():
            if from_solid == dep.solid:
                raise DagsterInvalidDefinitionError(
                    'Circular reference detected in solid {from_solid} input {from_input}.'.format(
                        from_solid=from_solid, from_input=from_input
                    )
                )

            if not from_solid in solid_dict:
                aliased_solid = alias_lookup.get(from_solid)
                if aliased_solid == from_solid:
                    raise DagsterInvalidDefinitionError(
                        'Solid {from_solid} in dependency dictionary not found in solid list'.
                        format(from_solid=from_solid),
                    )
                else:
                    raise DagsterInvalidDefinitionError(
                        (
                            'Solid {aliased_solid} (aliased by {from_solid} in dependency '
                            'dictionary) not found in solid list'
                        ).format(
                            aliased_solid=aliased_solid,
                            from_solid=from_solid,
                        ),
                    )
            if not solid_dict[from_solid].definition.has_input(from_input):
                input_list = [
                    input_def.name for input_def in solid_dict[from_solid].definition.input_defs
                ]
                raise DagsterInvalidDefinitionError(
                    'Solid "{from_solid}" does not have input "{from_input}". '.format(
                        from_solid=from_solid,
                        from_input=from_input,
                    ) + \
                    'Input list: {input_list}'.format(input_list=input_list)
                )

            if not dep.solid in solid_dict:
                raise DagsterInvalidDefinitionError(
                    'Solid {dep.solid} in DependencyDefinition not found in solid list'.format(
                        dep=dep
                    ),
                )

            if not solid_dict[dep.solid].definition.has_output(dep.output):
                raise DagsterInvalidDefinitionError(
                    'Solid {dep.solid} does not have output {dep.output}'.format(dep=dep),
                )


def _gather_all_types(solids, context_definitions, environment_type):
    check.list_param(solids, 'solids', SolidDefinition)
    check.dict_param(
        context_definitions,
        'context_definitions',
        key_type=str,
        value_type=PipelineContextDefinition,
    )

    check.inst_param(environment_type, 'environment_type', types.DagsterType)

    for solid in solids:
        for dagster_type in solid.iterate_types():
            yield dagster_type

    for context_definition in context_definitions.values():
        if context_definition.config_field:
            for dagster_type in context_definition.config_field.dagster_type.iterate_types():
                yield dagster_type

    for dagster_type in environment_type.iterate_types():
        yield dagster_type


def construct_type_dictionary(solids, context_definitions, environment_type):
    type_dict = {}
    all_types = list(_gather_all_types(solids, context_definitions, environment_type))
    for dagster_type in all_types:
        name = dagster_type.name
        if name in type_dict:
            if dagster_type is not type_dict[name]:
                raise DagsterInvalidDefinitionError(
                    (
                        'Type names must be unique. You have construct two instances of types '
                        'with the same name {name} but have different instances'.format(name=name)
                    )
                )
        else:
            type_dict[dagster_type.name] = dagster_type

    return type_dict


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
            context_definitions = _default_pipeline_context_definitions()

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

        dependency_structure, pipeline_solid_dict = _create_execution_structure(
            solids,
            self.dependencies,
        )

        self._solid_dict = pipeline_solid_dict
        self.dependency_structure = dependency_structure

        from .config_types import EnvironmentConfigType

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


class ExpectationResult(object):
    '''
    When Expectations are evaluated in the callback passed to ExpectationDefinitions,
    the user must return an ExpectationResult object from the callback.

    Attributes:

        success (bool): Whether the expectation passed or not.
        message (str): Information about the computation. Typically only used in the failure case.
        result_context (Any): Arbitrary information about the expectation result.
    '''

    def __init__(self, success, message=None, result_context=None):
        self.success = check.bool_param(success, 'success')
        self.message = check.opt_str_param(message, 'message')
        self.result_context = check.opt_dict_param(result_context, 'result_context')


class ExpectationDefinition(object):
    '''
    Expectations represent a data quality test. It performs an arbitrary computation
    to see if a given input or output satisfies the expectation.

    Attributes:

        name (str): The name of the expectation. Names should be unique per-solid.
        expectation_fn (callable):
            This is the implementation of expectation computation. It should be a callback
            of the form.

            (context: ExecutionContext, info: ExpectationExecutionInfo, value: Any)
            : ExpectationResult

            "value" conforms to the type check performed within the Dagster type system.

            e.g. If the expectation is declare on an input of type dagster_pd.DataFrame, you can
            assume that value is a pandas.DataFrame

        description (str): Description of expectation. Optional.

    Example:

    .. code-block:: python

        InputDefinition('some_input', types.Int, expectations=[
            ExpectationDefinition(
                name='is_positive',
                expectation_fn=lambda(
                    _info,
                    value,
                ): ExpectationResult(success=value > 0),
            )
        ])
    '''

    def __init__(self, name, expectation_fn, description=None):
        self.name = check_valid_name(name)
        self.expectation_fn = check.callable_param(expectation_fn, 'expectation_fn')
        self.description = check.opt_str_param(description, 'description')


class InputDefinition(object):
    '''An InputDefinition instance represents an argument to a transform defined within a solid.
    Inputs are values within the dagster type system that are created from previous solids.

    Attributes:
        name (str): Name of the input.
        dagster_type (DagsterType): Type of the input. Defaults to types.Any
        expectations (List[ExpectationDefinition]):
            List of expectations that applies to the value passed to the solid.
        description (str): Description of the input. Optional.
    '''

    def __init__(self, name, dagster_type=types.Any, expectations=None, description=None):
        ''
        self.name = check_valid_name(name)

        self.dagster_type = check.inst_param(dagster_type, 'dagster_type', types.DagsterType)

        self.expectations = check.opt_list_param(
            expectations, 'expectations', of_type=ExpectationDefinition
        )
        self.description = check.opt_str_param(description, 'description')

    @property
    def descriptive_key(self):
        return 'output'


class OutputDefinition(object):
    '''An OutputDefinition represents an output from a solid. Solids can have multiple
    outputs. In those cases the outputs must be named. Frequently solids have only one
    output, and so the user can construct a single OutputDefinition that will have
    the default name of "result".

    Attributes:
        dagster_type (DagsterType): Type of the output. Defaults to types.Any.
        name (str): Name of the output. Defaults to "result".
        expectations List[ExpectationDefinition]: Expectations for this output.
        description (str): Description of the output. Optional.
    '''

    def __init__(self, dagster_type=None, name=None, expectations=None, description=None):
        self.name = check.opt_str_param(name, 'name', DEFAULT_OUTPUT)

        self.dagster_type = check.opt_inst_param(
            dagster_type, 'dagster_type', types.DagsterType, types.Any
        )

        self.expectations = check.opt_list_param(
            expectations, 'expectations', of_type=ExpectationDefinition
        )
        self.description = check.opt_str_param(description, 'description')

    @property
    def descriptive_key(self):
        return 'output'


def _kv_str(key, value):
    return '{key}="{value}"'.format(key=key, value=repr(value))


def struct_to_string(name, **kwargs):
    props_str = ', '.join([_kv_str(key, value) for key, value in kwargs.items()])
    return '{name}({props_str})'.format(name=name, props_str=props_str)


class SolidInputHandle(namedtuple('_SolidInputHandle', 'solid input_def')):
    def __new__(cls, solid, input_def):
        return super(SolidInputHandle, cls).__new__(
            cls,
            check.inst_param(solid, 'solid', Solid),
            check.inst_param(input_def, 'input_def', InputDefinition),
        )

    def _inner_str(self):
        return struct_to_string(
            'SolidInputHandle',
            solid_name=self.solid.name,
            definition_name=self.solid.definition.name,
            input_name=self.input_def.name,
        )

    def __str__(self):
        return self._inner_str()

    def __repr__(self):
        return self._inner_str()

    def __hash__(self):
        return hash((self.solid.name, self.input_def.name))

    def __eq__(self, other):
        return self.solid.name == other.solid.name and self.input_def.name == other.input_def.name


class SolidOutputHandle(namedtuple('_SolidOutputHandle', 'solid output_def')):
    def __new__(cls, solid, output_def):
        return super(SolidOutputHandle, cls).__new__(
            cls,
            check.inst_param(solid, 'solid', Solid),
            check.inst_param(output_def, 'output_def', OutputDefinition),
        )

    def _inner_str(self):
        return struct_to_string(
            'SolidOutputHandle',
            solid_name=self.solid.name,
            definition_name=self.solid.definition.name,
            output_name=self.output_def.name,
        )

    def __str__(self):
        return self._inner_str()

    def __repr__(self):
        return self._inner_str()

    def __hash__(self):
        return hash((self.solid.name, self.output_def.name))

    def __eq__(self, other):
        return self.solid.name == other.solid.name and self.output_def.name == other.output_def.name


class Result(namedtuple('_Result', 'value output_name')):
    '''A solid transform function return a stream of Result objects.
    An implementator of a SolidDefinition must provide a transform that
    yields objects of this type.

    Attributes:
        value (Any): Value returned by the transform.
        output_name (str): Name of the output returns. defaults to "result"
'''

    def __new__(cls, value, output_name=DEFAULT_OUTPUT):
        return super(Result, cls).__new__(
            cls,
            value,
            check.str_param(output_name, 'output_name'),
        )


def all_fields_optional(field_dict):
    for field in field_dict.values():
        if not field.is_optional:
            return False
    return True


class SolidDefinition(object):
    '''A solid (a name extracted from the acronym of "software-structured data" (SSD)) represents
    a unit of computation within a data pipeline.

    As its core, a solid is a function. It accepts inputs (which are values produced from
    other solids) and configuration, and produces outputs. These solids are composed as a
    directed, acyclic graph (DAG) within a pipeline to form a computation that produces
    data assets.

    Solids should be implemented as idempotent, parameterizable, non-destructive functions.
    Data computations with these properties are much easier to test, reason about, and operate.

    The inputs and outputs are gradually, optionally typed by the dagster type system. Types
    can be user-defined and can represent entites as varied as scalars, dataframe, database
    tables, and so forth. They can represent pure in-memory objects, or handles to assets
    on disk or in external resources.

    A solid is a generalized abstraction that could take many forms.

    Example:

        .. code-block:: python

            def _read_csv(info, inputs):
                yield Result(pandas.read_csv(info.config['path']))

            SolidDefinition(
                name='read_csv',
                inputs=[],
                config_field=Field(types.Dict({'path' => types.Path})),
                outputs=[OutputDefinition()] # default name ('result') and any typed
                transform_fn
            )

    Attributes:
        name (str): Name of the solid.
        input_defs (List[InputDefinition]): Inputs of the solid.
        transform_fn (callable):
            Callable with the signature
            (
                info: TransformExecutionInfo,
                inputs: Dict[str, Any],
            ) : Iterable<Result>
        outputs_defs (List[OutputDefinition]): Outputs of the solid.
        config_field (Field): How the solid configured.
        description (str): Description of the solid.
        metadata (dict):
            Arbitrary metadata for the solid. Some frameworks expect and require
            certain metadata to be attached to a solid.
    '''

    def __init__(
        self,
        name,
        inputs,
        transform_fn,
        outputs,
        config_field=None,
        description=None,
        metadata=None,
    ):
        self.name = check_valid_name(name)
        self.input_defs = check.list_param(inputs, 'inputs', InputDefinition)
        self.transform_fn = check.callable_param(transform_fn, 'transform_fn')
        self.output_defs = check.list_param(outputs, 'outputs', OutputDefinition)
        self.description = check.opt_str_param(description, 'description')
        self.config_field = check.opt_inst_param(config_field, 'config_field', Field)
        self.metadata = check.opt_dict_param(metadata, 'metadata', key_type=str)
        self._input_dict = {inp.name: inp for inp in inputs}
        self._output_dict = {output.name: output for output in outputs}

    def has_input(self, name):
        check.str_param(name, 'name')
        return name in self._input_dict

    def input_def_named(self, name):
        check.str_param(name, 'name')
        return self._input_dict[name]

    def has_output(self, name):
        check.str_param(name, 'name')
        return name in self._output_dict

    def output_def_named(self, name):
        check.str_param(name, 'name')
        return self._output_dict[name]

    def iterate_types(self):
        for input_def in self.input_defs:
            for dagster_type in input_def.dagster_type.iterate_types():
                yield dagster_type

        for output_def in self.output_defs:
            for dagster_type in output_def.dagster_type.iterate_types():
                yield dagster_type

        if self.config_field:
            for dagster_type in self.config_field.dagster_type.iterate_types():
                yield dagster_type


class RepositoryDefinition(object):
    '''Define a repository that contains a collection of pipelines.

    Attributes:
        name (str): The name of the pipeline.
        pipeline_dict (Dict[str, callable]):
            An dictionary of pipelines. The value of the dictionary is a function that takes
            no parameters and returns a PipelineDefiniton.

            We pass callables instead of the PipelineDefinitions itself so that they can be
            created on demand when accessed by name.

            As the pipelines are retrieved it ensures that the keys of the dictionary and the
            name of the pipeline are the same.

    '''

    def __init__(self, name, pipeline_dict, enforce_uniqueness=True):
        '''
        Args:
            name (str): Name of pipeline.
            pipeline_dict (Dict[str, callable]): See top-level class documentation
        '''
        self.name = check.str_param(name, 'name')

        check.dict_param(
            pipeline_dict,
            'pipeline_dict',
            key_type=str,
        )

        for val in pipeline_dict.values():
            check.is_callable(val, 'Value in pipeline_dict must be function')

        self.pipeline_dict = pipeline_dict

        self._pipeline_cache = {}

        self.enforce_uniqueness = enforce_uniqueness

    def has_pipeline(self, name):
        check.str_param(name, 'name')
        return name in self.pipeline_dict

    def get_pipeline(self, name):
        '''Get a pipeline by name. Only constructs that pipeline and caches it.

        Args:
            name (str): Name of the pipeline to retriever

        Returns:
            PipelineDefinition: Instance of PipelineDefinition with that name.
'''
        check.str_param(name, 'name')

        if name in self._pipeline_cache:
            return self._pipeline_cache[name]

        pipeline = self.pipeline_dict[name]()
        check.invariant(
            pipeline.name == name,
            'Name does not match. Name in dict {name}. Name in pipeline {pipeline.name}'.format(
                name=name, pipeline=pipeline
            )
        )

        self._pipeline_cache[name] = check.inst(
            pipeline,
            PipelineDefinition,
            'Function passed into pipeline_dict with key {key} must return a PipelineDefinition'.
            format(key=name),
        )

        return pipeline

    def iterate_over_pipelines(self):
        '''Yield all pipelines one at a time

        Returns:
            Iterable[PipelineDefinition]:
        '''
        for name in self.pipeline_dict.keys():
            yield self.get_pipeline(name)

    def get_all_pipelines(self):
        '''Return all pipelines as a list

        Returns:
            List[PipelineDefinition]:

        '''
        pipelines = list(self.iterate_over_pipelines())

        self._construct_solid_defs(pipelines)

        return pipelines

    def _construct_solid_defs(self, pipelines):
        solid_defs = {}
        solid_to_pipeline = {}
        for pipeline in pipelines:
            for solid_def in pipeline.solid_defs:
                if solid_def.name not in solid_defs:
                    solid_defs[solid_def.name] = solid_def
                    solid_to_pipeline[solid_def.name] = pipeline.name
                elif self.enforce_uniqueness:
                    if not solid_defs[solid_def.name] is solid_def:
                        raise DagsterInvalidDefinitionError(
                            'Trying to add duplicate solid def {} in {}, Already saw in {}'.format(
                                solid_def.name,
                                pipeline.name,
                                solid_to_pipeline[solid_def.name],
                            )
                        )
        return solid_defs

    def get_solid_def(self, name):
        check.str_param(name, 'name')

        if not self.enforce_uniqueness:
            raise DagsterInvariantViolationError(
                (
                    'In order fo get_solid_def to have reliable semantics '
                    'you must construct the repo with ensure_uniqueness=True'
                )
            )

        solid_defs = self._construct_solid_defs(self.get_all_pipelines())

        if name not in solid_defs:
            check.failed('could not find solid_def {}'.format(name))

        return solid_defs[name]

    def solid_def_named(self, name):
        check.str_param(name, 'name')
        for pipeline in self.get_all_pipelines():
            for solid in pipeline.solids:
                if solid.definition.name == name:
                    return solid.definition

        check.failed('Did not find ' + name)


class ContextCreationExecutionInfo(
    namedtuple('_ContextCreationExecutionInfo', 'config pipeline_def run_id')
):
    def __new__(cls, config, pipeline_def, run_id):
        return super(ContextCreationExecutionInfo, cls).__new__(
            cls,
            config,
            check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            check.str_param(run_id, 'run_id'),
        )


class ExpectationExecutionInfo(
    namedtuple(
        '_ExpectationExecutionInfo',
        'context inout_def solid expectation_def',
    )
):
    def __new__(cls, context, inout_def, solid, expectation_def):
        return super(ExpectationExecutionInfo, cls).__new__(
            cls,
            check.inst_param(context, 'context', RuntimeExecutionContext),
            check.inst_param(inout_def, 'inout_def', (InputDefinition, OutputDefinition)),
            check.inst_param(solid, 'solid', Solid),
            check.inst_param(expectation_def, 'expectation_def', ExpectationDefinition),
        )


class TransformExecutionInfo(
    namedtuple('_TransformExecutionInfo', 'context config solid pipeline_def')
):
    '''An instance of TransformExecutionInfo is passed every solid transform function.

    Attributes:

        context (ExecutionContext): Context instance for this pipeline invocation
        config (Any): Config object for current solid
    '''

    def __new__(cls, context, config, solid, pipeline_def):
        return super(TransformExecutionInfo, cls).__new__(
            cls, check.inst_param(context, 'context', RuntimeExecutionContext), config,
            check.inst_param(solid, 'solid', Solid),
            check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
        )

    @property
    def solid_def(self):
        return self.solid.definition


def _create_adjacency_lists(solids, dep_structure):
    check.list_param(solids, 'solids', Solid)
    check.inst_param(dep_structure, 'dep_structure', DependencyStructure)

    visit_dict = {s.name: False for s in solids}
    forward_edges = {s.name: set() for s in solids}
    backward_edges = {s.name: set() for s in solids}

    def visit(solid_name):
        if visit_dict[solid_name]:
            return

        visit_dict[solid_name] = True

        for output_handle in dep_structure.deps_of_solid(solid_name):
            forward_node = output_handle.solid.name
            backward_node = solid_name
            if forward_node in forward_edges:
                forward_edges[forward_node].add(backward_node)
                backward_edges[backward_node].add(forward_node)
                visit(forward_node)

    for s in solids:
        visit(s.name)

    return (forward_edges, backward_edges)


def solids_in_topological_order(pipeline):
    check.inst_param(pipeline, 'pipeline', PipelineDefinition)

    _forward_edges, backward_edges = _create_adjacency_lists(
        pipeline.solids,
        pipeline.dependency_structure,
    )

    order = toposort_flatten(backward_edges, sort=True)
    return [pipeline.solid_named(solid_name) for solid_name in order]
