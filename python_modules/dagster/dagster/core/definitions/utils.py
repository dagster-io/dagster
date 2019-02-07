import keyword
import re

from dagster import check

from dagster.core.errors import DagsterInvalidDefinitionError

from dagster.core.types.builtin_enum import BuiltinEnum
from dagster.core.types.runtime import RuntimeType, Any

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


def _kv_str(key, value):
    return '{key}="{value}"'.format(key=key, value=repr(value))


def struct_to_string(name, **kwargs):
    props_str = ', '.join([_kv_str(key, value) for key, value in kwargs.items()])
    return '{name}({props_str})'.format(name=name, props_str=props_str)


def check_runtime_cls_arg(runtime_cls, arg_name):
    if isinstance(runtime_cls, BuiltinEnum):
        return RuntimeType.from_builtin_enum(runtime_cls)
    if runtime_cls is None:
        return Any.inst()
    check.param_invariant(issubclass(runtime_cls, RuntimeType), arg_name)
    return runtime_cls.inst()
