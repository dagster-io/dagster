import keyword
import re

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError

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
        'type',
    ]
    + keyword.kwlist  # just disallow all python keywords
)

VALID_NAME_REGEX_STR = r'^[A-Za-z0-9_]+$'
VALID_NAME_REGEX = re.compile(VALID_NAME_REGEX_STR)


def has_valid_name_chars(name):
    return bool(VALID_NAME_REGEX.match(name))


def check_valid_name(name):
    check.str_param(name, 'name')
    if name in DISALLOWED_NAMES:
        raise DagsterInvalidDefinitionError('{name} is not allowed.'.format(name=name))

    if not has_valid_name_chars(name):
        raise DagsterInvalidDefinitionError(
            '{name} must be in regex {regex}'.format(name=name, regex=VALID_NAME_REGEX_STR)
        )
    return name


def _kv_str(key, value):
    return '{key}="{value}"'.format(key=key, value=repr(value))


def struct_to_string(name, **kwargs):
    # Sort the kwargs to ensure consistent representations across Python versions
    props_str = ', '.join([_kv_str(key, value) for key, value in sorted(kwargs.items())])
    return '{name}({props_str})'.format(name=name, props_str=props_str)
