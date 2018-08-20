from collections import (defaultdict, namedtuple)
import copy
import keyword
import re

from dagster import check
from dagster.core import types
from dagster.utils.logging import (
    level_from_string,
    define_colored_console_logger,
)

from .errors import DagsterInvalidDefinitionError

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


def check_argument_def_dict(argument_def_dict):
    return check.dict_param(
        argument_def_dict,
        'argument_def_dict',
        key_type=str,
        value_type=ArgumentDefinition,
    )


class PipelineContextDefinition:
    def __init__(self, *, argument_def_dict, context_fn, description=None):
        self.argument_def_dict = check_argument_def_dict(argument_def_dict)
        self.context_fn = check.callable_param(context_fn, 'context_fn')
        self.description = description


def _default_pipeline_context_definitions():
    def _default_context_fn(_pipeline, args):
        import dagster.core.execution

        log_level = level_from_string(args['log_level'])
        context = dagster.core.execution.ExecutionContext(
            loggers=[define_colored_console_logger('dagster', level=log_level)]
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


class DependencyDefinition:
    def __init__(self, solid, output=DEFAULT_OUTPUT, description=None):
        self.solid = check.str_param(solid, 'solid')
        self.output = check.str_param(output, 'output')
        self.description = check.opt_str_param(description, 'description')


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
        return list(self.__gen_deps_of_solid(solid_name))

    def __gen_deps_of_solid(self, solid_name):
        for input_handle, output_handle in self._handle_dict.items():
            if input_handle.solid.name == solid_name:
                yield output_handle

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
    def create_pipeline_slice(pipeline, from_solids, through_solids, injected_solids):
        from .graph import ExecutionGraph
        check.inst_param(pipeline, 'pipeline', PipelineDefinition)
        check.list_param(from_solids, 'from_solids', of_type=str)
        check.list_param(through_solids, 'through_solids', of_type=str)
        check_two_dim_str_dict(injected_solids, 'injected_solids', SolidDefinition)

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

        dependencies = check.opt_dict_param(
            dependencies,
            'dependencies',
            key_type=str,
            value_type=dict,
        )

        self.dependency_structure = DependencyStructure.from_definitions(solids, dependencies)

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


class SolidOutputHandle(namedtuple('_SolidOutputHandle', 'solid output')):
    def __new__(cls, solid, output):
        return super(SolidOutputHandle, cls).__new__(
            cls,
            check.inst_param(solid, 'solid', SolidDefinition),
            check.inst_param(output, 'output', OutputDefinition),
        )

    def __str__(self):
        return f'SolidOutputHandle(solid="{self.solid.name}", output.name="{self.output.name}")'

    def __repr__(self):
        return f'SolidOutputHandle(solid="{self.solid.name}", output.name="{self.output.name}")'

    def __hash__(self):
        return hash((self.solid.name, self.output.name))

    def __eq__(self, other):
        return self.solid.name == other.solid.name and self.output.name == other.output.name


class Result(namedtuple('_Result', 'value output_name')):
    def __new__(cls, value, output_name=DEFAULT_OUTPUT):
        return super(Result, cls).__new__(
            cls,
            value,
            check.str_param(output_name, 'output_name'),
        )


class SolidDefinition:
    def __init__(self, *, name, inputs, transform_fn, outputs, config_def, description=None):
        self.name = check_valid_name(name)
        self.inputs = check.list_param(inputs, 'inputs', InputDefinition)
        self.transform_fn = check.callable_param(transform_fn, 'transform_fn')
        self.outputs = check.list_param(outputs, 'outputs', OutputDefinition)
        self.description = check.opt_str_param(description, 'description')
        self.config_dict_def = check_argument_def_dict(config_def)

        input_handles = {}
        for inp in self.inputs:
            input_handles[inp.name] = SolidInputHandle(self, inp)

        self.input_handles = input_handles

        output_handles = {}
        for output in outputs:
            output_handles[output.name] = SolidOutputHandle(self, output)

        self.output_handles = output_handles

    @staticmethod
    def single_output_transform(name, inputs, transform_fn, output, description=None):
        def _new_transform_fn(context, inputs, _config_dict):
            value = transform_fn(context, inputs)
            yield Result(output_name=DEFAULT_OUTPUT, value=value)

        return SolidDefinition(
            name=name,
            inputs=inputs,
            transform_fn=_new_transform_fn,
            outputs=[output],
            config_def={},
            description=description,
        )

    def input_handle(self, name):
        check.str_param(name, 'name')
        return self.input_handles[name]

    def output_handle(self, name):
        check.str_param(name, 'name')
        return self.output_handles[name]

    @property
    def input_names(self):
        return [inp.name for inp in self.inputs]

    def has_input(self, name):
        check.str_param(name, 'name')
        for input_def in self.inputs:
            if input_def.name == name:
                return True
        return False

    def input_def_named(self, name):
        check.str_param(name, 'name')
        for input_def in self.inputs:
            if input_def.name == name:
                return input_def

        check.failed('input {name} not found'.format(name=name))

    def output_def_named(self, name):
        check.str_param(name, 'name')
        for output in self.outputs:
            if output.name == name:
                return output

        check.failed('output {name} not found'.format(name=name))


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
