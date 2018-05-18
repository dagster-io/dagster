import inspect
import keyword
import re

import check

from .errors import SolidInvalidDefinition
from .types import (SolidType, SolidPath)

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


def has_context_argument(fn):
    check.callable_param(fn, 'fn')

    argspec = inspect.getfullargspec(fn)
    return 'context' in argspec[0]


def check_valid_name(name):
    check.str_param(name, 'name')
    if name in DISALLOWED_NAMES:
        raise SolidInvalidDefinition('{name} is not allowed'.format(name=name))

    regex = r'^[A-Za-z0-9_]+$'
    if not re.match(regex, name):
        raise SolidInvalidDefinition(
            '{name} must be in regex {regex}'.format(name=name, regex=regex)
        )
    return name


class SolidExpectationResult:
    def __init__(self, success, message=None, result_context=None):
        self.success = check.bool_param(success, 'success')
        self.message = check.opt_str_param(message, 'message')
        self.result_context = check.opt_dict_param(result_context, 'result_context')


class SolidExpectationDefinition:
    def __init__(self, name, expectation_fn):
        self.name = check_valid_name(name)
        self.expectation_fn = check.callable_param(expectation_fn, 'expectation_fn')


def _contextify_fn(fn):
    check.callable_param(fn, 'fn')

    if not has_context_argument(fn):

        def wrapper_with_context(*args, context, **kwargs):
            check.not_none_param(context, 'context')
            return fn(*args, **kwargs)

        return wrapper_with_context
    else:
        return fn


class SolidInputDefinition:
    '''
    An input is a computation that takes a set of arguments (key-value pairs) and produces
    an in-memory object to be used in a core transform function.

    This should class should be used by library authors only. End users should have most
    of these details abstracted away fromr them.

    For example, pandas csv input would take single argument "path" and a produce a pandas
    dataframe.

    Parameters
    ----------

    name: str
    input_fn: callable
        The input function defines exactly what happens when the input is invoked. This
        function can be one of two signatures:

        def simplified_read_csv_example_no_context(arg_dict):
            return pd.read_csv(arg_dict['path'])

        OR

        def simplified_read_csv_example_no_context(context, arg_dict):
            context.info('I am in an input.') # use context for logging
            return pd.read_csv(arg_dict['path'])

    argument_def_dict: { str: SolidType }
        Define the arguments expected by this input. A dictionary that maps a string
        (argument name) to an argument type (defined in solidic.types) Continuing
        the above example, the csv signature would be:

        argument_def_dict = { 'path' : SolidPath }

    expectations:
        Define the list of expectations for this input (TODO)

    depends_on:
        Optionally specify that this input is in fact a dependency on another solid
    '''

    def __init__(self, name, input_fn, argument_def_dict, expectations=None, depends_on=None):
        self.name = check_valid_name(name)
        self.input_fn = _contextify_fn(check.callable_param(input_fn, 'input_fn'))
        self.argument_def_dict = check.dict_param(
            argument_def_dict, 'argument_def_dict', key_type=str, value_type=SolidType
        )
        self.expectations = check.opt_list_param(
            expectations, 'expectations', of_type=SolidExpectationDefinition
        )
        self.depends_on = check.opt_inst_param(depends_on, 'depends_on', Solid)

    @property
    def is_external(self):
        return self.depends_on is None


def create_solidic_single_file_input(name, single_file_fn):
    check.str_param(name, 'name')
    return SolidInputDefinition(
        name=name,
        input_fn=lambda context, arg_dict: single_file_fn(
            context=context,
            path=check.str_elem(arg_dict, 'path')
        ),
        argument_def_dict={'path': SolidPath}
    )


class SolidOutputDefinition:
    '''
    An output defines a way the result of a transform can be externalized. This can mean
    writing a file, or moving a file to a well-known location, renaming a database table,
    and so on.

    Parameters
    ----------

    name: str

    output_fn: callable

        This function defines the actual output.

        The first function argument is the output of the transform function. It can be
        named anything.

        You must specify an argument with the name "arg_dict". It will be the dictionary
        of arguments specified by the caller of the solid

        You can optionally specify a context argument. If it is specified a SolidExecutionContext
        will be passed.

        e.g.

        def output_fn(the_actual_output, arg_dict):
            pass

        OR

        def output_fn(actual_output, context, arg_dict):
            pass

    argument_def_dict: { str: SolidType }
        Define the arguments expected by this output . A dictionary that maps a string
        (argument name) to an argument type (defined in solidic.types).

        e.g.:

        argument_def_dict = { 'path' : SolidPath }
    '''

    def __init__(self, name, output_fn, argument_def_dict):
        self.name = check_valid_name(name)
        self.output_fn = _contextify_fn(check.callable_param(output_fn, 'output_fn'))
        self.argument_def_dict = check.dict_param(
            argument_def_dict, 'argument_def_dict', key_type=str, value_type=SolidType
        )


# One or more inputs
# The core computation in the native kernel abstraction
# The output
class Solid:
    def __init__(self, name, inputs, transform_fn, outputs, output_expectations=None):
        self.name = check_valid_name(name)
        self.inputs = check.list_param(inputs, 'inputs', of_type=SolidInputDefinition)
        self.transform_fn = _contextify_fn(check.callable_param(transform_fn, 'transform'))
        self.outputs = check.list_param(outputs, 'supported_outputs', of_type=SolidOutputDefinition)
        self.output_expectations = check.opt_list_param(
            output_expectations, 'output_expectations', of_type=SolidExpectationDefinition
        )

    @property
    def input_names(self):
        return [inp.name for inp in self.inputs]

    def input_def_named(self, name):
        check.str_param(name, 'name')
        for input_ in self.inputs:
            if input_.name == name:
                return input_

        check.failed('Input {name} not found'.format(name=name))

    def output_def_named(self, name):
        check.str_param(name, 'name')
        for output_def in self.outputs:
            if output_def.name == name:
                return output_def

        check.failed('Output {name} not found'.format(name=name))
