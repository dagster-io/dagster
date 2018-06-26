import keyword
import re
import inspect

from dagster import check
from dagster.core import types
from dagster.utils import make_context_arg_optional

from .errors import DagsterInvalidDefinitionError

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


class ExpectationResult:
    def __init__(self, success, solid=None, message=None, result_context=None):
        self.success = check.bool_param(success, 'success')
        self.solid = check.opt_inst_param(solid, SolidDefinition, 'solid')
        self.message = check.opt_str_param(message, 'message')
        self.result_context = check.opt_dict_param(result_context, 'result_context')


class ExpectationDefinition:
    def __init__(self, name, expectation_fn):
        self.name = check_valid_name(name)
        self.expectation_fn = check.callable_param(expectation_fn, 'expectation_fn')


def create_dagster_single_file_input(name, single_file_fn, source_type='UNNAMED'):
    check.str_param(name, 'name')
    return create_single_source_input(
        name=name,
        source_fn=lambda context, arg_dict: single_file_fn(
            context=context,
            path=check.str_elem(arg_dict, 'path')
        ),
        argument_def_dict={'path': types.PATH},
        source_type=source_type,
    )


class SourceDefinition:
    '''
    name: name of the source

    source_fn: callable
         The input function defines exactly what happens when the source is invoked.

         def simplified_read_csv_example(context, arg_dict):
             context.info('I am in an input.') # use context for logging
             return pd.read_csv(arg_dict['path'])

    argument_def_dict: { str: DagsterType }
         Define the arguments expected by this source . A dictionary that maps a string
         (argument name) to an argument type (defined in dagster.core.types) Continuing
         the above example, the csv signature would be:

         argument_def_dict = {'path' : dagster.core.types.PATH }

    '''

    def __init__(self, source_type, source_fn, argument_def_dict):
        check.callable_param(source_fn, 'source_fn')
        self.source_type = check_valid_name(source_type)
        self.source_fn = check.callable_param(source_fn, 'source_fn')
        self.argument_def_dict = check.dict_param(
            argument_def_dict, 'argument_def_dict', key_type=str, value_type=types.DagsterType
        )


def create_single_source_input(
    name, source_fn, argument_def_dict, depends_on=None, expectations=None, source_type='UNNAMED'
):
    '''
    This function exist and is used a lot because separation of inputs and sources used to not
    exist so most of the unit tests in the systems were written without tha abstraction. So
    this exists as a bridge from the old api to the new api.
    '''
    return InputDefinition(
        name=name,
        sources=[
            SourceDefinition(
                source_type=source_type,
                source_fn=source_fn,
                argument_def_dict=argument_def_dict,
            )
        ],
        depends_on=depends_on,
        expectations=check.opt_list_param(
            expectations, 'expectations', of_type=ExpectationDefinition
        )
    )


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

    - input_callback: (Optional) Called on the source result. Gets execution context and result. Can be used to validate the result, log stats etc.
    '''

    def __init__(self, name, sources, depends_on=None, expectations=None, input_callback=None):
        self.name = check_valid_name(name)
        self.sources = check.list_param(sources, 'sources', of_type=SourceDefinition)
        self.depends_on = check.opt_inst_param(depends_on, 'depends_on', SolidDefinition)
        self.expectations = check.opt_list_param(
            expectations, 'expectations', of_type=ExpectationDefinition
        )
        self.input_callback = check.opt_callable_param(input_callback, 'input_callback')

    @property
    def is_external(self):
        return self.depends_on is None

    def source_of_type(self, source_type):
        check.str_param(source_type, 'source_type')
        for source in self.sources:
            if source.source_type == source_type:
                return source

        check.failed(
            'Source {source_type} not found in input {input_name}.'.format(
                source_type=source_type,
                input_name=self.name,
            )
        )


# class TransformDefinition:
#     def __init__(self, transform_fn):
#         self.transform_fn = make_context_arg_optional(
#             check.callable_param(transform_fn, 'transform_fn')
#         )


class MaterializationDefinition:
    '''
    materialization_fn: callable

        This function defines the actual output.

        The first function argument is the result of the transform function. It can be
        named anything.

        You must specify an argument with the name "arg_dict". It will be the dictionary
        of arguments specified by the caller of the solid

        def materialization_fn(context, args, value):
            pass

    argument_def_dict: { str: DagsterType }
        Define the arguments expected by this materialization. A dictionary that maps a string
        (argument name) to an argument type (defined in dagster.core.types).

        e.g.:

        argument_def_dict = { 'path' : dagster.core.types.PATH}
    '''

    def __init__(self, materialization_type, materialization_fn, argument_def_dict):
        self.materialization_type = check_valid_name(materialization_type)
        self.materialization_fn = check.callable_param(materialization_fn, 'materialization_fn')
        self.argument_def_dict = check.dict_param(
            argument_def_dict, 'argument_def_dict', key_type=str, value_type=types.DagsterType
        )


def create_no_materialization_output(expectations=None):
    return OutputDefinition(expectations=expectations)


def create_single_materialization_output(
    materialization_type, materialization_fn, argument_def_dict, expectations=None
):
    '''
    Similar to create_single_source_input this exists because a move in the primitive APIs.
    Materializations and outputs used to not be separate concepts so this is a compatability
    layer with the old api. Once the *new* api stabilizes this should be removed but it stays
    for now.
    '''
    return OutputDefinition(
        materializations=[
            MaterializationDefinition(
                materialization_type=materialization_type,
                materialization_fn=materialization_fn,
                argument_def_dict=argument_def_dict
            )
        ],
        expectations=expectations
    )


class OutputDefinition:
    # runtime type info
    def __init__(self, materializations=None, expectations=None, output_callback=None):
        self.materializations = check.opt_list_param(
            materializations, 'materializations', of_type=MaterializationDefinition
        )
        self.expectations = check.opt_list_param(
            expectations, 'expectations', of_type=ExpectationDefinition
        )
        self.output_callback = check.opt_callable_param(output_callback, 'output_callback')

    def materialization_of_type(self, materialization_type):
        for materialization in self.materializations:
            if materialization.materialization_type == materialization_type:
                return materialization

        check.failed('Did not find materialization {type}'.format(type=materialization_type))


# One or more inputs
# The core computation in the native kernel abstraction
# The output
class SolidDefinition:
    def __init__(self, name, inputs, transform_fn, output):
        self.name = check_valid_name(name)
        self.inputs = check.list_param(inputs, 'inputs', InputDefinition)
        self.output = check.inst_param(output, 'output', OutputDefinition)
        # validate_transform_fn(self.name, transform_fn, self.inputs)
        self.transform_fn = check.callable_param(transform_fn, 'transform')

    # Notes to self

    # Input Definitions
    #   - DematerializationDefinitions
    #       - Arguments
    #       - Compute (args) => Value
    #   - Expectations
    #   - Dependency

    # Transform Definition
    #   - Function (inputs) => Value
    #   - Runtime Types (Inputs and Outputs)

    # Output Definition
    #   - MaterializationDefinitions
    #       - Arguments
    #       - Compute (value, args) => Result
    #   - Expectations

    @property
    def input_names(self):
        return [inp.name for inp in self.inputs]

    def input_def_named(self, name):
        check.str_param(name, 'name')
        for input_def in self.inputs:
            if input_def.name == name:
                return input_def

        check.failed('input {name} not found'.format(name=name))
