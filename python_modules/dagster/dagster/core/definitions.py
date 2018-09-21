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

from dagster.config import DEFAULT_CONTEXT_NAME

from .errors import DagsterInvalidDefinitionError

from .execution_context import ExecutionContext

from .types import (
    DagsterType,
    Field,
)

DEFAULT_OUTPUT = 'result'

DISALLOWED_NAMES = set(
    [
        'context',
        'conf',
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
        config_def (ConfigurationDefinition): The configuration for the pipeline context.

        context_fn (callable):
            Signature is (pipeline: PipelineDefintion, config_value: Any) => ExecutionContext

            A callable that either returns *or* yields an ExecutionContext.

        description (str): A description of what this context represents
    '''

    @staticmethod
    def passthrough_context_definition(context):
        '''Create a context definition from a pre-existing context. This can be useful
        in testing contexts where you may want to create a context manually and then
        pass it into a one-off PipelineDefinition

        Args:
            context (ExecutionContext): The context that will provided to the pipeline.
        Returns:
            PipelineContextDefinition: The passthrough context definition.
        '''

        check.inst_param(context, 'context', ExecutionContext)
        context_definition = PipelineContextDefinition(context_fn=lambda *_args: context)
        return {DEFAULT_CONTEXT_NAME: context_definition}

    def __init__(self, context_fn, config_def=None, description=None):
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

            config_def (ConfigDefinition):
                Define the configuration for the context

            description (str): Description of the context definition.
        '''
        self.config_def = check.opt_inst_param(
            config_def,
            'config_def',
            ConfigDefinition,
            ConfigDefinition(),
        )
        self.context_fn = check.callable_param(context_fn, 'context_fn')
        self.description = description


def _default_pipeline_context_definitions():
    def _default_context_fn(info):
        log_level = level_from_string(info.config['log_level'])
        context = ExecutionContext(
            loggers=[define_colored_console_logger('dagster', level=log_level)]
        )
        return context

    default_context_def = PipelineContextDefinition(
        config_def=ConfigDefinition.config_dict(
            {
                'log_level': Field(
                    dagster_type=types.String,
                    is_optional=True,
                    default_value='INFO',
                )
            }
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
        return DependencyStructure(_create_handle_dict(_build_named_dict(solids), dep_dict))

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


def _build_named_dict(things):
    ddict = {}
    for thing in things:
        ddict[thing.name] = thing
    return ddict


class SolidInstance(namedtuple('Solid', 'name alias')):
    '''
    A solid identifier in a dependency structure. Allows supplying parameters to the solid, like the alias.

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

    @property
    def config_def(self):
        return self.definition.config_def


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
        self, solids, name=None, description=None, context_definitions=None, dependencies=None
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

        if context_definitions is None:
            context_definitions = _default_pipeline_context_definitions()

        self.context_definitions = check.dict_param(
            context_definitions,
            'context_definitions',
            key_type=str,
            value_type=PipelineContextDefinition,
        )
        dependencies = check_opt_two_dim_dict(
            dependencies,
            'dependencies',
            value_type=DependencyDefinition,
        )

        processed_dependencies = {}
        solid_uses = defaultdict(set)

        for solid_key, definition in dependencies.items():
            if not isinstance(solid_key, SolidInstance):
                solid_key = SolidInstance(solid_key)

            if solid_key.alias:
                key = solid_key.name
                alias = solid_key.alias
            else:
                key = solid_key.name
                alias = solid_key.name

            solid_uses[key].add(alias)
            processed_dependencies[alias] = definition

            for dependency in definition.values():
                solid_uses[dependency.solid].add(dependency.solid)

        pipeline_solids = []
        for solid_def in solids:
            if isinstance(solid_def, SolidDefinition):
                # For the case when solids are passed, but no dependency structure.
                if not processed_dependencies:
                    pipeline_solids.append(Solid(name=solid_def.name, definition=solid_def))
                elif not solid_uses[solid_def.name]:
                    raise DagsterInvalidDefinitionError(
                        'Solid {name} is passed to list of pipeline solids, but is not used'.format(
                            name=solid_def.name
                        )
                    )
                else:
                    for alias in solid_uses[solid_def.name]:
                        pipeline_solids.append(Solid(name=alias, definition=solid_def))
            elif callable(solid_def):
                raise DagsterInvalidDefinitionError(
                    '''You have passed a lambda or function {func} into a pipeline that is 
                    not a solid. You have likely forgetten to annotate this function with
                    an @solid or @lambda_solid decorator located in dagster.core.decorators
                    '''.format(func=solid_def.__name__)
                )
            else:
                check.list_param(solids, 'solids', SolidDefinition)

        self._solid_dict = _build_named_dict(pipeline_solids)

        self.__validate_dependences(processed_dependencies)
        dependency_structure = DependencyStructure.from_definitions(
            pipeline_solids, processed_dependencies
        )
        self.__validate_dependency_structure(name, pipeline_solids, dependency_structure)
        self.dependency_structure = dependency_structure

    @staticmethod
    def create_single_solid_pipeline(pipeline, solid_name, injected_solids=None):
        '''
        Return a new pipeline which is a single solid of the passed-in pipeline.

        Frequently (especially in test contexts) one wants to isolate a single solid for
        independent testing.

        See PipelineDefinition.create_sub_pipeline.

        Args:
            pipeline (PipelineDefinition): PipelineDefinition that we will subset
            solid_name (str): Name of the solid to isolate
            injected_solids (Dict[str, Dict[str, SolidDefinition]]):
                When you create a subpipeline, you possible left with solids within that pipeline
                who have unmet dependencies. To fulfill these dependencies new solids must be
                provided.

        Returns:
            PipelineDefinition: The new pipeline with only the passed-in solid and the injected
            solids.

        Example:

        .. code-block:: python

            new_pipeline = PipelineDefinition.create_single_solid_pipeline(
                existing_pipeline,
                'A', # name of solid within existing_pipeline
                {
                    'A': {
                        # new_solid_instance is a solid that outputs something
                        # that is compatible with A_input
                        'A_input': new_solid_instance,
                    },
                },
            )

        '''
        return PipelineDefinition.create_sub_pipeline(
            pipeline,
            [solid_name],
            [solid_name],
            injected_solids,
        )

    @staticmethod
    def create_sub_pipeline(pipeline, from_solids, through_solids, injected_solids=None):
        '''
        Return a new pipeline which is a subset of the passed-in pipeline.

        In addition to making sub-pipelines out of a single solid, one can also create a
        pipeline using an arbitrary subset of the dag. In this case, we start "from" a set
        of solids and then proceed forward through the dependency graph until all the
        "through" solids are reached.

        See PipelineDefinition.create_single_solid_pipeline

        Args:
            pipeline (PipelineDefinition): PipelineDefinition that we will subset
            from_solids (List[str]):
                List solids to "start" from. Inputs into these solids will have to satisfied
                via the injected solids parameter.
            through_solids (List[str]):
                List of solids to execute "through". Solids depending on these solids
                transitively will not be included in the returned PipelineDefinition.
            injected_solids (Dict[str, Dict[str, SolidDefinition]]):
                When you create a subpipeline, you possible left with solids within that pipeline
                who have unmet dependencies. To fulfill these dependencies new solids must be
                provided.

        Returns:
            PipelineDefinition:
                The new pipeline definition that contains all the solids from the "from_solids"
                through the "through_solids", plus the injected solids.
        '''
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        check.list_param(from_solids, 'from_solids', of_type=str)
        check.list_param(through_solids, 'through_solids', of_type=str)
        injected_solids = check_opt_two_dim_str_dict(
            injected_solids, 'injected_solids', SolidDefinition
        )

        # FIXME: fix circular reference
        subgraph = ExecutionGraph.from_pipeline_subset(
            pipeline,
            from_solids,
            through_solids,
            injected_solids,
        )

        return subgraph.to_pipeline()

    def __validate_dependences(self, dependencies):
        for from_solid, dep_by_input in dependencies.items():
            for from_input, dep in dep_by_input.items():
                if from_solid == dep.solid:
                    raise DagsterInvalidDefinitionError(
                        'Circular reference detected in solid {from_solid} input {from_input}.'.
                        format(from_solid=from_solid, from_input=from_input)
                    )

                if not from_solid in self._solid_dict:
                    raise DagsterInvalidDefinitionError(
                        'Solid {from_solid} in dependency dictionary not found in solid list'.
                        format(from_solid=from_solid),
                    )

                if not self._solid_dict[from_solid].definition.has_input(from_input):
                    input_list = [
                        input_def.name
                        for input_def in self._solid_dict[from_solid].definition.input_defs
                    ]
                    raise DagsterInvalidDefinitionError(
                        'Solid {from_solid} does not have input {from_input}. '.format(
                            from_solid=from_solid,
                            from_input=from_input,
                        ) + \
                        'Input list: {input_list}'.format(input_list=input_list)
                    )

                if not dep.solid in self._solid_dict:
                    raise DagsterInvalidDefinitionError(
                        'Solid {dep.solid} in DependencyDefinition not found in solid list'.format(
                            dep=dep
                        ),
                    )

                if not self._solid_dict[dep.solid].definition.has_output(dep.output):
                    raise DagsterInvalidDefinitionError(
                        'Solid {dep.solid} does not have output {dep.output}'.format(dep=dep),
                    )

    def __validate_dependency_structure(self, name, solids, dependency_structure):
        for pipeline_solid in solids:
            solid = pipeline_solid.definition
            for input_def in solid.input_defs:
                if not dependency_structure.has_dep(pipeline_solid.input_handle(input_def.name)):
                    if name:
                        raise DagsterInvalidDefinitionError(
                            'Dependency must be specified for solid {pipeline_solid.name} input '.format(
                                pipeline_solid=pipeline_solid
                            ) + \
                            '{input_def.name} in pipeline {name}'.format(
                                input_def=input_def,
                                name=name,
                            )
                        )
                    else:
                        raise DagsterInvalidDefinitionError(
                            'Dependency must be specified for solid {pipeline_solid.name} input '.format(
                                pipeline_solid=pipeline_solid,
                             ) + \
                            '{input_def.name}'.format(input_def=input_def)
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


class SolidInputHandle(namedtuple('_SolidInputHandle', 'solid input_def')):
    def __new__(cls, solid, input_def):
        return super(SolidInputHandle, cls).__new__(
            cls,
            check.inst_param(solid, 'solid', Solid),
            check.inst_param(input_def, 'input_def', InputDefinition),
        )

    def _inner_str(self):
        return 'SolidInputHandle(name="{solid_name}", solid="{definition_name}", input_name="{input_name}")'.format(
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
        return 'SolidOutputHandle(name="{solid_name}", solid="{definition_name}", output_name="{output_name}")'.format(
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


class ConfigDefinition(object):
    '''Represents the configuration of an entity in Dagster

    Broadly defined, configs determine how computations within dagster interact with
    the external world. Example values that would end up in configs would be file paths,
    database table names, and so forth.

    Attributes:

        config_type (DagsterType): Type of the config.
    '''

    @staticmethod
    def config_dict(field_dict):
        '''Shortcut to create a dictionary based config definition.


        Args:
            field_dict (dict): dictionary of `Field` objects keyed by their names.

        Example:

        .. code-block:: python

            ConfigDefinition.config_dict({
                'int_field': Field(types.Int),
                'string_field': Field(types.String),
             })

        '''
        return ConfigDefinition(types.ConfigDictionary(field_dict))

    def __init__(self, config_type=types.Any, description=None):
        '''Construct a ConfigDefinition

        Args:
            config_type (DagsterType): Type the determines shape and values of config'''
        self.config_type = check.inst_param(config_type, 'config_type', DagsterType)
        self.description = check.opt_str_param(description, 'description')


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
                config_def=ConfigDefinition(types.ConfigDictionary({'path' => types.Path})),
                outputs=[OutputDefinition()] # default name ('result') and any typed
                transform_fn
            )

    Attributes:
        name (str): Name of the solid.
        inputs (List[InputDefiniton]): Inputs of the solid.
        transform_fn (callable):
            Callable with the signature
            (
                info: TransformExecutionInfo,
                inputs: Dict[str, Any],
            ) : Iterable<Result>
        outputs (List[OutputDefinition]): Outputs of the solid.
        config_def (ConfigDefinition): How the solid configured.
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
        config_def=None,
        description=None,
        metadata=None,
    ):
        self.name = check_valid_name(name)
        self.input_defs = check.list_param(inputs, 'inputs', InputDefinition)
        self.transform_fn = check.callable_param(transform_fn, 'transform_fn')
        self.output_defs = check.list_param(outputs, 'outputs', OutputDefinition)
        self.description = check.opt_str_param(description, 'description')
        self.config_def = check.opt_inst_param(
            config_def,
            'config_def',
            ConfigDefinition,
            ConfigDefinition(types.Any),
        )
        self.metadata = check.opt_dict_param(metadata, 'metadata', key_type=str)
        self._input_dict = _build_named_dict(inputs)
        self._output_dict = _build_named_dict(outputs)

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


def _dependency_structure_to_dep_dict(dependency_structure):
    dep_dict = defaultdict(dict)
    for input_handle, output_handle in dependency_structure.items():
        solid_instance = SolidInstance(input_handle.solid.definition.name, input_handle.solid.name)
        dep_dict[solid_instance][input_handle.input_def.name] = DependencyDefinition(
            solid=output_handle.solid.name,
            output=output_handle.output_def.name,
        )
    return dep_dict


class ExecutionGraph(object):
    @staticmethod
    def from_pipeline(pipeline):
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        return ExecutionGraph(pipeline, pipeline.solids, pipeline.dependency_structure)

    @staticmethod
    def from_pipeline_subset(pipeline, from_solids, through_solids, injected_solids):
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        check.list_param(from_solids, 'from_solids', of_type=str)
        check.list_param(through_solids, 'through_solids', of_type=str)
        graph = ExecutionGraph.from_pipeline(pipeline)
        return _create_subgraph(graph, from_solids, through_solids).augment(injected_solids)

    def to_pipeline(self):
        return PipelineDefinition(
            solids=[solid.definition for solid in self.solids],
            dependencies=_dependency_structure_to_dep_dict(self.dependency_structure),
            context_definitions=self.pipeline.context_definitions
        )

    def augment(self, injected_solids):

        new_deps = defaultdict(dict)
        new_solids = []

        for from_solid_name, targets_by_input in injected_solids.items():
            for from_input_name, target_solid in targets_by_input.items():
                new_solids.append(Solid(name=target_solid.name, definition=target_solid))
                new_deps[from_solid_name][from_input_name] = DependencyDefinition(
                    solid=target_solid.name
                )

        check.list_param(new_solids, 'new_solids', of_type=Solid)

        solids = self.solids + new_solids

        solid_dict = _build_named_dict(solids)

        handle_dict = InputToOutputHandleDict()
        for input_handle, output_handle in self.dependency_structure.items():
            handle_dict[input_handle] = output_handle

        for input_handle, output_handle in _create_handle_dict(solid_dict, new_deps).items():
            handle_dict[input_handle] = output_handle

        return ExecutionGraph(self.pipeline, solids, DependencyStructure(handle_dict))

    def __init__(self, pipeline, solids, dependency_structure):
        self.pipeline = pipeline
        solids = check.list_param(solids, 'solids', of_type=Solid)
        self.dependency_structure = check.inst_param(
            dependency_structure, 'dependency_structure', DependencyStructure
        )

        self._solid_dict = _build_named_dict(solids)

        for input_handle in dependency_structure.input_handles():
            check.invariant(input_handle.solid.name in self._solid_dict)

        self.forward_edges, self.backward_edges = _create_adjacency_lists(
            solids, self.dependency_structure
        )
        self.topological_order = toposort_flatten(self.backward_edges, sort=True)

        self._transitive_deps = {}

    @property
    def topological_solids(self):
        return [self._solid_dict[name] for name in self.topological_order]

    @property
    def solids(self):
        return list(self._solid_dict.values())

    def solid_named(self, name):
        check.str_param(name, 'name')
        return self._solid_dict[name]

    def transitive_dependencies_of(self, solid_name):
        check.str_param(solid_name, 'solid_name')

        if solid_name in self._transitive_deps:
            return self._transitive_deps[solid_name]

        trans_deps = set()
        pipeline_solid = self._solid_dict[solid_name]
        solid = pipeline_solid.definition
        for input_def in solid.input_defs:
            input_handle = pipeline_solid.input_handle(input_def.name)
            if self.dependency_structure.has_dep(input_handle):
                output_handle = self.dependency_structure.get_dep(input_handle)
                trans_deps.add(output_handle.solid.name)
                trans_deps.union(self.transitive_dependencies_of(output_handle.solid.name))

        self._transitive_deps[solid_name] = trans_deps
        return self._transitive_deps[solid_name]

    def _check_solid_name(self, solid_name):
        check.str_param(solid_name, 'output_name')
        check.param_invariant(
            solid_name in self._solid_dict, 'output_name',
            'Solid {solid_name} must exist in {solid_names}'.format(
                solid_name=solid_name, solid_names=list(self._solid_dict.keys())
            )
        )

    def create_execution_subgraph(self, from_solids, to_solids):
        check.list_param(from_solids, 'from_solids', of_type=str)
        check.list_param(to_solids, 'to_solids', of_type=str)

        involved_solid_set = self._compute_involved_solid_set(from_solids, to_solids)

        involved_solids = [self._solid_dict[name] for name in involved_solid_set]

        handle_dict = InputToOutputHandleDict()

        for pipeline_solid in involved_solids:
            solid = pipeline_solid.definition
            for input_def in solid.input_defs:
                input_handle = pipeline_solid.input_handle(input_def.name)
                if self.dependency_structure.has_dep(input_handle):
                    handle_dict[input_handle] = self.dependency_structure.get_dep(input_handle)

        return ExecutionGraph(self.pipeline, involved_solids, DependencyStructure(handle_dict))

    def _compute_involved_solid_set(self, from_solids, to_solids):
        from_solid_set = set(from_solids)
        involved_solid_set = from_solid_set

        def visit(solid):
            if solid.name in involved_solid_set:
                return

            involved_solid_set.add(solid.name)

            for input_def in solid.definition.input_defs:
                input_handle = solid.input_handle(input_def.name)
                if not self.dependency_structure.has_dep(input_handle):
                    continue

                output_handle = self.dependency_structure.get_dep(input_handle)

                next_solid = output_handle.solid.name
                if next_solid in from_solid_set:
                    continue

                visit(self._solid_dict[next_solid])

        for to_solid in to_solids:
            visit(self._solid_dict[to_solid])

        return involved_solid_set


def _build_named_dict(things):
    ddict = {}
    for thing in things:
        ddict[thing.name] = thing
    return ddict


def _all_depended_on_solids(execution_graph):
    check.inst_param(execution_graph, 'execution_graph', ExecutionGraph)

    dependency_structure = execution_graph.dependency_structure

    for solid in execution_graph.solids:
        for input_def in solid.input_defs:
            input_handle = solid.input_handle(input_def.name)
            if dependency_structure.has_dep(input_handle):
                output_handle = dependency_structure.get_dep(input_handle)
                yield execution_graph.solid_named(output_handle.solid.name)


def _all_sink_solids(execution_graph):
    check.inst_param(execution_graph, 'execution_graph', ExecutionGraph)
    all_names = set([solid.name for solid in execution_graph.solids])
    all_depended_on_names = set([solid.name for solid in _all_depended_on_solids(execution_graph)])
    return all_names.difference(all_depended_on_names)


def _create_subgraph(execution_graph, from_solids, through_solids):
    check.inst_param(execution_graph, 'execution_graph', ExecutionGraph)
    check.opt_list_param(from_solids, 'from_solids', of_type=str)
    check.opt_list_param(through_solids, 'through_solids', of_type=str)

    if not through_solids:
        through_solids = list(_all_sink_solids(execution_graph))

    if not from_solids:
        all_deps = set()
        for through_solid in through_solids:
            all_deps.union(execution_graph.transitive_dependencies_of(through_solid))

        from_solids = list(all_deps)

    return execution_graph.create_execution_subgraph(from_solids, through_solids)


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

    def __init__(self, name, pipeline_dict):
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

    def get_pipeline(self, name):
        '''Get a pipeline by name. Only constructs that pipeline and caches it.

        Args:
            name (str): Name of the pipeline to retriever

        Returns:
            PipelineDefinition: Instance of PipelineDefinition with that name.
'''
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
        return list(self.iterate_over_pipelines())


class ContextCreationExecutionInfo(
    namedtuple('_ContextCreationExecutionInfo', 'config pipeline_def')
):
    def __new__(cls, config, pipeline_def):
        return super(ContextCreationExecutionInfo, cls).__new__(
            cls,
            config,
            check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
        )


ExpectationExecutionInfo = namedtuple(
    'ExpectationExecutionInfo',
    'context inout_def solid_def expectation_def',
)


class TransformExecutionInfo(namedtuple('_TransformExecutionInfo', 'context config solid_def')):
    '''An instance of TransformExecutionInfo is passed every solid transform function.

    Attributes:

        context (ExecutionContext): Context instance for this pipeline invocation
        config (Any): Config object for current solid
    '''

    def __new__(cls, context, config, solid_def):
        return super(TransformExecutionInfo, cls).__new__(
            cls,
            check.inst_param(context, 'context', ExecutionContext),
            config,
            check.inst_param(solid_def, 'solid_def', SolidDefinition),
        )
