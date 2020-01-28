import keyword
import re

from dagster import check, seven
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.utils import frozentags

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


def validate_tags(tags):
    valid_tags = {}
    for key, value in check.opt_dict_param(tags, 'tags', key_type=str).items():
        if not check.is_str(value):
            valid = False
            err_reason = 'Could not JSON encode value "{}"'.format(value)
            try:
                str_val = seven.json.dumps(value)
                err_reason = 'JSON encoding "{json}" of value "{val}" is not equivalent to original value'.format(
                    json=str_val, val=value
                )

                valid = seven.json.loads(str_val) == value
            except Exception:  # pylint: disable=broad-except
                pass

            if not valid:
                raise DagsterInvalidDefinitionError(
                    'Invalid value for tag "{key}", {err_reason}. Tag values must be strings '
                    'or meet the constraint that json.loads(json.dumps(value)) == value.'.format(
                        key=key, err_reason=err_reason
                    )
                )

            valid_tags[key] = str_val
        else:
            valid_tags[key] = value

    return frozentags(valid_tags)
