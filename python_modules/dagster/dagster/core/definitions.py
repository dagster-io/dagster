from collections import (defaultdict, namedtuple)
import copy
import keyword
import re

from dagster import check
from dagster.core import types
from dagster.utils.logging import define_logger

from .errors import DagsterInvalidDefinitionError
from .execution_context import ExecutionContext

DEFAULT_OUTPUT = 'result'

DISALLOWED_NAMES = set(
    [
        'context',
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


# We wrap the passed in dictionary of str : ArgumentDefinition to
# 1) enforce typing
# 2) enforce immutability
# 3) make type checks throughout execution cheaper
class ArgumentDefinitionDictionary(dict):
    def __init__(self, ddict):
        super().__init__(
            check.dict_param(ddict, 'ddict', key_type=str, value_type=ArgumentDefinition)
        )

    def __setitem__(self, _key, _value):
        check.failed('This dictionary is readonly')


class PipelineContextDefinition:
    def __init__(self, *, argument_def_dict, context_fn, description=None):
        self.argument_def_dict = ArgumentDefinitionDictionary(argument_def_dict)
        self.context_fn = check.callable_param(context_fn, 'context_fn')
        self.description = description


def _default_pipeline_context_definitions():
    def _default_context_fn(_pipeline, args):

        log_level = args['log_level']
        context = ExecutionContext(
            log_level=log_level, loggers=[define_logger('dagster', level=log_level)]
        )
        return context

    default_context_def = PipelineContextDefinition(
        argument_def_dict={
            'log_level':
            ArgumentDefinition(dagster_type=types.String, is_optional=True, default_value='ERROR')
        },
        context_fn=_default_context_fn,
    )
    return {'default': default_context_def}


class DependencyDefinition(namedtuple('_DependencyDefinition', 'solid output description')):
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


def check_two_dim_str_dict(ddict, param_name, value_type):
    check.dict_param(ddict, param_name, key_type=str, value_type=dict)
    for sub_dict in ddict.values():
        check.dict_param(sub_dict, 'sub_dict', key_type=str, value_type=value_type)
    return ddict


def check_opt_two_dim_str_dict(ddict, param_name, value_type):
    ddict = check.opt_dict_param(ddict, param_name, key_type=str, value_type=dict)
    for sub_dict in ddict.values():
        check.dict_param(sub_dict, 'sub_dict', key_type=str, value_type=value_type)
    return ddict


def create_handle_dict(solid_dict, dep_dict):
    check.dict_param(solid_dict, 'solid_dict', key_type=str, value_type=SolidDefinition)
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


class DependencyStructure:
    @staticmethod
    def from_definitions(solids, dep_dict):
        return DependencyStructure(create_handle_dict(_build_named_dict(solids), dep_dict))

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
                result[output_handle].extend(input_handle)
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


class PipelineDefinition:
    @staticmethod
    def create_single_solid_pipeline(pipeline, solid_name, injected_solids=None):
        return PipelineDefinition.create_sub_pipeline(
            pipeline,
            [solid_name],
            [solid_name],
            injected_solids,
        )

    @staticmethod
    def create_sub_pipeline(pipeline, from_solids, through_solids, injected_solids=None):
        from .graph import ExecutionGraph
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        check.list_param(from_solids, 'from_solids', of_type=str)
        check.list_param(through_solids, 'through_solids', of_type=str)
        injected_solids = check_opt_two_dim_str_dict(
            injected_solids, 'injected_solids', SolidDefinition
        )

        subgraph = ExecutionGraph.from_pipeline_subset(
            pipeline,
            from_solids,
            through_solids,
            injected_solids,
        )

        return subgraph.to_pipeline()

    def __init__(
        self, solids, name=None, description=None, context_definitions=None, dependencies=None
    ):
        self.description = check.opt_str_param(description, 'description')
        self.name = check.opt_str_param(name, 'name')

        if context_definitions is None:
            context_definitions = _default_pipeline_context_definitions()

        self.context_definitions = check.dict_param(
            context_definitions,
            'context_definitions',
            key_type=str,
            value_type=PipelineContextDefinition,
        )

        for solid in solids:
            if not isinstance(solid, SolidDefinition) and callable(solid):
                raise DagsterInvalidDefinitionError(
                    '''You have passed a lambda or function {solid} into
                a pipeline that is not a solid. You have likely forgetten to annotate this function
                with an @solid decorator located in dagster.core.decorators
                '''.format(solid=solid.__name__)
                )

        self._solid_dict = _build_named_dict(solids)

        dependencies = check_two_dim_str_dict(
            dependencies,
            'dependencies',
            DependencyDefinition,
        ) if dependencies else {}

        for from_solid, dep_by_input in dependencies.items():
            for from_input, dep in dep_by_input.items():
                if from_solid == dep.solid:
                    raise DagsterInvalidDefinitionError(
                        f'Circular reference detected in solid {from_solid} input {from_input}.'
                    )
                if not from_solid in self._solid_dict:
                    raise DagsterInvalidDefinitionError(
                        f'Solid {from_solid} in dependency dictionary not found in solid list',
                    )

                if not self._solid_dict[from_solid].has_input(from_input):
                    input_list = [
                        input_def.name for input_def in self._solid_dict[from_solid].input_defs
                    ]
                    raise DagsterInvalidDefinitionError(
                        f'Solid {from_solid} does not have input {from_input}. ' + \
                        f'Input list: {input_list}'
                    )

                if not dep.solid in self._solid_dict:
                    raise DagsterInvalidDefinitionError(
                        f'Solid {dep.solid} in DependencyDefinition not found in solid list',
                    )

                if not self._solid_dict[dep.solid].has_output(dep.output):
                    raise DagsterInvalidDefinitionError(
                        f'Solid {dep.solid} does not have output {dep.output}',
                    )

        self.dependency_structure = DependencyStructure.from_definitions(solids, dependencies)

        for solid in solids:
            for input_def in solid.input_defs:
                if not self.dependency_structure.has_dep(solid.input_handle(input_def.name)):
                    if name:
                        raise DagsterInvalidDefinitionError(
                            f'Dependency must be specified for solid {solid.name} input ' + \
                            f'{input_def.name} in pipeline {name}'
                        )
                    else:
                        raise DagsterInvalidDefinitionError(
                            f'Dependency must be specified for solid {solid.name} input ' + \
                            f'{input_def.name}'
                        )

    @property
    def solids(self):
        return list(self._solid_dict.values())

    def has_solid(self, name):
        check.str_param(name, 'name')
        return name in self._solid_dict

    def solid_named(self, name):
        check.str_param(name, 'name')
        return self._solid_dict[name]


class ExpectationResult:
    def __init__(self, success, solid=None, message=None, result_context=None):
        self.success = check.bool_param(success, 'success')
        self.solid = check.opt_inst_param(solid, SolidDefinition, 'solid')
        self.message = check.opt_str_param(message, 'message')
        self.result_context = check.opt_dict_param(result_context, 'result_context')

    def copy(self):
        return copy.deepcopy(self)


class ExpectationDefinition:
    def __init__(self, name, expectation_fn, description=None):
        self.name = check_valid_name(name)
        self.expectation_fn = check.callable_param(expectation_fn, 'expectation_fn')
        self.description = check.opt_str_param(description, 'description')


class InputDefinition:
    '''
    An InputDefinition instances represents an argument to a transform defined within a solid.

    - name: Name of input

    - sources: A list of possible sources for the input. For example, an input which is passed
    to the transform as a pandas dataframe could have any number of different source types
    (CSV, Parquet etc). Some inputs have zero sources, and can only be created by
    execute a dependant solid.

    - depends_on: (Optional). This input depends on another solid in the context of a
    a pipeline.

    - input_callback: (Optional) Called on the source result. Gets execution context and result.
    Can be used to validate the result, log stats etc.
    '''

    def __init__(
        self, name, dagster_type=None, expectations=None, input_callback=None, description=None
    ):
        self.name = check_valid_name(name)

        self.dagster_type = check.opt_inst_param(
            dagster_type, 'dagster_type', types.DagsterType, types.Any
        )

        self.expectations = check.opt_list_param(
            expectations, 'expectations', of_type=ExpectationDefinition
        )
        self.input_callback = check.opt_callable_param(input_callback, 'input_callback')
        self.description = check.opt_str_param(description, 'description')


class OutputDefinition:
    # runtime type info
    def __init__(
        self,
        name=None,
        dagster_type=None,
        expectations=None,
        output_callback=None,
        description=None
    ):
        self.name = check.opt_str_param(name, 'name', DEFAULT_OUTPUT)

        self.dagster_type = check.opt_inst_param(
            dagster_type, 'dagster_type', types.DagsterType, types.Any
        )

        self.expectations = check.opt_list_param(
            expectations, 'expectations', of_type=ExpectationDefinition
        )
        self.output_callback = check.opt_callable_param(output_callback, 'output_callback')
        self.description = check.opt_str_param(description, 'description')


class SolidInputHandle(namedtuple('_SolidInputHandle', 'solid input_def')):
    def __new__(cls, solid, input_def):
        return super(SolidInputHandle, cls).__new__(
            cls,
            check.inst_param(solid, 'solid', SolidDefinition),
            check.inst_param(input_def, 'input_def', InputDefinition),
        )

    def __str__(self):
        return f'SolidInputHandle(solid="{self.solid.name}", input_name="{self.input_def.name}")'

    def __repr__(self):
        return f'SolidInputHandle(solid="{self.solid.name}", input_name="{self.input_def.name}")'

    def __hash__(self):
        return hash((self.solid.name, self.input_def.name))

    def __eq__(self, other):
        return self.solid.name == other.solid.name and self.input_def.name == other.input_def.name


class SolidOutputHandle(namedtuple('_SolidOutputHandle', 'solid output_def')):
    def __new__(cls, solid, output_def):
        return super(SolidOutputHandle, cls).__new__(
            cls,
            check.inst_param(solid, 'solid', SolidDefinition),
            check.inst_param(output_def, 'output_def', OutputDefinition),
        )

    def __str__(self):
        return f'SolidOutputHandle(solid="{self.solid.name}", output.name="{self.output_def.name}")'

    def __repr__(self):
        return f'SolidOutputHandle(solid="{self.solid.name}", output.name="{self.output_def.name}")'

    def __hash__(self):
        return hash((self.solid.name, self.output_def.name))

    def __eq__(self, other):
        return self.solid.name == other.solid.name and self.output_def.name == other.output_def.name


class Result(namedtuple('_Result', 'value output_name')):
    def __new__(cls, value, output_name=DEFAULT_OUTPUT):
        return super(Result, cls).__new__(
            cls,
            value,
            check.str_param(output_name, 'output_name'),
        )


class ConfigDefinition:
    def __init__(self, argument_def_dict):
        self.argument_def_dict = ArgumentDefinitionDictionary(argument_def_dict)


class SolidDefinition:
    def __init__(self, *, name, inputs, transform_fn, outputs, config_def=None, description=None):
        self.name = check_valid_name(name)
        self.input_defs = check.list_param(inputs, 'inputs', InputDefinition)
        self.transform_fn = check.callable_param(transform_fn, 'transform_fn')
        self.output_defs = check.list_param(outputs, 'outputs', OutputDefinition)
        self.description = check.opt_str_param(description, 'description')
        self.config_def = check.opt_inst_param(
            config_def,
            'config_def',
            ConfigDefinition,
            ConfigDefinition({}),
        )

        input_handles = {}
        for input_def in self.input_defs:
            input_handles[input_def.name] = SolidInputHandle(self, input_def)

        self._input_handles = input_handles

        output_handles = {}
        for output_def in self.output_defs:
            output_handles[output_def.name] = SolidOutputHandle(self, output_def)

        self._output_handles = output_handles
        self._input_dict = _build_named_dict(inputs)
        self._output_dict = _build_named_dict(outputs)

    @property
    def outputs(self):
        return self.output_defs

    @staticmethod
    def single_output_transform(
        name, inputs, transform_fn, output, config_def=None, description=None
    ):
        def _new_transform_fn(context, inputs, _config_dict):
            value = transform_fn(context, inputs)
            yield Result(output_name=DEFAULT_OUTPUT, value=value)

        return SolidDefinition(
            name=name,
            inputs=inputs,
            transform_fn=_new_transform_fn,
            outputs=[output],
            config_def=config_def,
            description=description,
        )

    def input_handle(self, name):
        check.str_param(name, 'name')
        return self._input_handles[name]

    def output_handle(self, name):
        check.str_param(name, 'name')
        return self._output_handles[name]

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


class __ArgumentValueSentinel:
    pass


NO_DEFAULT_PROVIDED = __ArgumentValueSentinel


class ArgumentDefinition:
    def __init__(
        self, dagster_type, default_value=NO_DEFAULT_PROVIDED, is_optional=False, description=None
    ):
        if not is_optional:
            check.param_invariant(
                default_value == NO_DEFAULT_PROVIDED,
                'default_value',
                'required arguments should not specify default values',
            )

        self.dagster_type = check.inst_param(dagster_type, 'dagster_type', types.DagsterType)
        self.description = check.opt_str_param(description, 'description')
        self.is_optional = check.bool_param(is_optional, 'is_optional')
        self.default_value = default_value

    @property
    def default_provided(self):
        return self.default_value != NO_DEFAULT_PROVIDED
