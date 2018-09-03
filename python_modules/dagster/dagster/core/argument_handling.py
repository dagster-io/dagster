from dagster import check

from .errors import DagsterTypeError
from .types import DagsterType


# We wrap the passed in dictionary of str : ArgumentDefinition to
# 1) enforce typing
# 2) enforce immutability
# 3) make type checks throughout execution cheaper
class ArgumentDefinitionDictionary(dict):
    def __init__(self, ddict):
        super(ArgumentDefinitionDictionary, self).__init__(
            check.dict_param(ddict, 'ddict', key_type=str, value_type=ArgumentDefinition)
        )

    def __setitem__(self, _key, _value):
        check.failed('This dictionary is readonly')


class __ArgumentValueSentinel(object):
    pass


NO_DEFAULT_PROVIDED = __ArgumentValueSentinel


class ArgumentDefinition(object):
    def __init__(
        self, dagster_type, default_value=NO_DEFAULT_PROVIDED, is_optional=False, description=None
    ):
        '''Definition of an argument passed through the config system. Used in a few different
        contexts: to configure a context, to configure a solid, and more to come.

        We have decided to allow arguments to be explictly made *optional* and separate that
        concept from the nullability of the type. That means one could have a *required* argument
        that is nullable, because sometimes an argument set to null has a distinct semantic meaning
        from the lack of an argument. Optional arguments can have default values. Required arguments
        cannot.
        '''
        if not is_optional:
            check.param_invariant(
                default_value == NO_DEFAULT_PROVIDED,
                'default_value',
                'required arguments should not specify default values',
            )

        self.dagster_type = check.inst_param(dagster_type, 'dagster_type', DagsterType)
        self.description = check.opt_str_param(description, 'description')
        self.is_optional = check.bool_param(is_optional, 'is_optional')
        self.default_value = default_value

    @property
    def default_provided(self):
        return self.default_value != NO_DEFAULT_PROVIDED


def validate_args(argument_def_dict, arg_dict, error_context_str):
    check.inst_param(argument_def_dict, 'argument_def_dict', ArgumentDefinitionDictionary)
    check.dict_param(arg_dict, 'arg_dict', key_type=str)
    check.str_param(error_context_str, 'error_context_str')

    defined_args = set(argument_def_dict.keys())
    received_args = set(arg_dict.keys())

    for received_arg in received_args:
        if received_arg not in defined_args:
            raise DagsterTypeError(
                'Argument {received} not found in {error_context_str}. Defined args: {defined}'.
                format(
                    error_context_str=error_context_str,
                    defined=repr(defined_args),
                    received=received_arg,
                )
            )

    for expected_arg, arg_def in argument_def_dict.items():
        if arg_def.is_optional:
            continue

        check.invariant(not arg_def.default_provided)

        if expected_arg not in received_args:
            raise DagsterTypeError(
                'Did not not find {expected} in {error_context_str}. Defined args: {defined}'.
                format(
                    error_context_str=error_context_str,
                    expected=expected_arg,
                    defined=repr(defined_args),
                )
            )

    args_to_pass = {}

    for expected_arg, arg_def in argument_def_dict.items():
        if expected_arg in received_args:
            args_to_pass[expected_arg] = arg_dict[expected_arg]
        elif arg_def.default_provided:
            args_to_pass[expected_arg] = arg_def.default_value
        else:
            check.invariant(arg_def.is_optional and not arg_def.default_provided)

    for arg_name, arg_value in arg_dict.items():
        arg_def = argument_def_dict[arg_name]
        if not arg_def.dagster_type.is_python_valid_value(arg_value):
            format_string = (
                'Expected type {typename} for arg {arg_name} ' +
                'for {error_context_str} but got type "{arg_type}" value {arg_value}'
            )
            raise DagsterTypeError(
                format_string.format(
                    typename=arg_def.dagster_type.name,
                    arg_name=arg_name,
                    error_context_str=error_context_str,
                    arg_type=type(arg_value).__name__,
                    arg_value=repr(arg_value),
                )
            )

    return args_to_pass
