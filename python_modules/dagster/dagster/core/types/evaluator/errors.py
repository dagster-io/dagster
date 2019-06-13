from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.errors import DagsterError

from ..config import ConfigType
from ..field_utils import check_field_param
from ..type_printer import print_config_type_to_string

from .stack import get_friendly_path_info, get_friendly_path_msg, EvaluationStack


class DagsterEvaluationErrorReason(Enum):
    RUNTIME_TYPE_MISMATCH = 'RUNTIME_TYPE_MISMATCH'
    MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD'
    MISSING_REQUIRED_FIELDS = 'MISSING_REQUIRED_FIELDS'
    FIELD_NOT_DEFINED = 'FIELD_NOT_DEFINED'
    FIELDS_NOT_DEFINED = 'FIELDS_NOT_DEFINED'
    SELECTOR_FIELD_ERROR = 'SELECTOR_FIELD_ERROR'


class FieldsNotDefinedErrorData(namedtuple('_FieldsNotDefinedErrorData', 'field_names')):
    def __new__(cls, field_names):
        return super(FieldsNotDefinedErrorData, cls).__new__(
            cls, check.list_param(field_names, 'field_names', of_type=str)
        )


class FieldNotDefinedErrorData(namedtuple('_FieldNotDefinedErrorData', 'field_name')):
    def __new__(cls, field_name):
        return super(FieldNotDefinedErrorData, cls).__new__(
            cls, check.str_param(field_name, 'field_name')
        )


class MissingFieldErrorData(namedtuple('_MissingFieldErrorData', 'field_name field_def')):
    def __new__(cls, field_name, field_def):
        return super(MissingFieldErrorData, cls).__new__(
            cls,
            check.str_param(field_name, 'field_name'),
            check_field_param(field_def, 'field_def'),
        )


class MissingFieldsErrorData(namedtuple('_MissingFieldErrorData', 'field_names field_defs')):
    def __new__(cls, field_names, field_defs):
        return super(MissingFieldsErrorData, cls).__new__(
            cls,
            check.list_param(field_names, 'field_names', of_type=str),
            [check_field_param(field_def, 'field_defs') for field_def in field_defs],
        )


class RuntimeMismatchErrorData(namedtuple('_RuntimeMismatchErrorData', 'config_type value_rep')):
    def __new__(cls, config_type, value_rep):
        return super(RuntimeMismatchErrorData, cls).__new__(
            cls,
            check.inst_param(config_type, 'config_type', ConfigType),
            check.str_param(value_rep, 'value_rep'),
        )


class SelectorTypeErrorData(namedtuple('_SelectorTypeErrorData', 'dagster_type incoming_fields')):
    def __new__(cls, dagster_type, incoming_fields):
        check.param_invariant(dagster_type.is_selector, 'dagster_type')
        return super(SelectorTypeErrorData, cls).__new__(
            cls, dagster_type, check.list_param(incoming_fields, 'incoming_fields', of_type=str)
        )


ERROR_DATA_TYPES = (
    FieldNotDefinedErrorData,
    FieldsNotDefinedErrorData,
    MissingFieldErrorData,
    MissingFieldsErrorData,
    RuntimeMismatchErrorData,
    SelectorTypeErrorData,
)


class EvaluationError(namedtuple('_EvaluationError', 'stack reason message error_data')):
    def __new__(cls, stack, reason, message, error_data):
        return super(EvaluationError, cls).__new__(
            cls,
            check.inst_param(stack, 'stack', EvaluationStack),
            check.inst_param(reason, 'reason', DagsterEvaluationErrorReason),
            check.str_param(message, 'message'),
            check.inst_param(error_data, 'error_data', ERROR_DATA_TYPES),
        )


class DagsterEvaluateConfigValueError(DagsterError):
    '''Indicates invalid value was passed to a type's evaluate_value method'''

    def __init__(self, stack, *args, **kwargs):
        super(DagsterEvaluateConfigValueError, self).__init__(*args, **kwargs)
        self.stack = check.inst_param(stack, 'stack', EvaluationStack)


def friendly_string_for_error(error):
    type_in_context = error.stack.type_in_context

    path_msg, path = get_friendly_path_info(error.stack)

    type_msg = _get_type_msg(error, type_in_context)

    if error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD:
        return error.message
    elif error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELDS:
        return error.message
    elif error.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED:
        return 'Undefined field "{field_name}"{type_msg} {path_msg}'.format(
            field_name=error.error_data.field_name, path_msg=path_msg, type_msg=type_msg
        )
    elif error.reason == DagsterEvaluationErrorReason.FIELDS_NOT_DEFINED:
        return error.message
    elif error.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH:
        return 'Type failure at path "{path}"{type_msg}. {message}.'.format(
            path=path, type_msg=type_msg, message=error.message
        )
    elif error.reason == DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR:
        return error.message
    else:
        check.failed('{} (friendly message for this type not yet provided)'.format(error.reason))


def _get_type_msg(error, type_in_context):
    if error.stack.type_in_context.is_system_config:
        return ''
    else:
        return ' on type "{type_name}"'.format(type_name=type_in_context.name)


def create_fields_not_defined_error(composite_type, stack, undefined_fields):
    check.inst_param(composite_type, 'composite_type', ConfigType)
    check.param_invariant(composite_type.has_fields, 'composite_type')
    check.inst_param(stack, 'stack', EvaluationStack)
    check.list_param(undefined_fields, 'undefined_fields', of_type=str)

    available_fields = sorted(list(composite_type.fields.keys()))
    undefined_fields = sorted(undefined_fields)

    return EvaluationError(
        stack=stack,
        reason=DagsterEvaluationErrorReason.FIELDS_NOT_DEFINED,
        message=(
            'Fields "{undefined_fields}" are not defined {path_msg} Available '
            'fields: "{available_fields}"'
        ).format(
            undefined_fields=undefined_fields,
            path_msg=get_friendly_path_msg(stack),
            available_fields=available_fields,
        ),
        error_data=FieldsNotDefinedErrorData(field_names=undefined_fields),
    )


def create_field_not_defined_error(config_type, stack, received_field):
    check.param_invariant(config_type.has_fields, 'config_type')
    check.inst_param(stack, 'stack', EvaluationStack)
    check.str_param(received_field, 'received_field')

    return EvaluationError(
        stack=stack,
        reason=DagsterEvaluationErrorReason.FIELD_NOT_DEFINED,
        message='Field "{received}" is not defined {path_msg} Expected: "{type_name}"'.format(
            path_msg=get_friendly_path_msg(stack),
            type_name=print_config_type_to_string(config_type, with_lines=False),
            received=received_field,
        ),
        error_data=FieldNotDefinedErrorData(field_name=received_field),
    )


def create_missing_required_field_error(config_type, stack, expected_field):
    check.param_invariant(config_type.has_fields, 'config_type')
    check.inst_param(stack, 'stack', EvaluationStack)
    check.str_param(expected_field, 'expected_field')

    return EvaluationError(
        stack=stack,
        reason=DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD,
        message=(
            'Missing required field "{expected}" {path_msg} Available Fields: '
            '"{available_fields}".'
        ).format(
            expected=expected_field,
            path_msg=get_friendly_path_msg(stack),
            available_fields=sorted(list(config_type.fields.keys())),
        ),
        error_data=MissingFieldErrorData(
            field_name=expected_field, field_def=config_type.fields[expected_field]
        ),
    )


def create_missing_required_fields_error(composite_type, stack, missing_fields):
    check.inst_param(composite_type, 'composite_type', ConfigType)
    check.param_invariant(composite_type.has_fields, 'compositve_type')
    check.inst_param(stack, 'stack', EvaluationStack)
    check.list_param(missing_fields, 'missing_fields', of_type=str)

    missing_fields = sorted(missing_fields)
    missing_field_defs = list(map(lambda mf: composite_type.fields[mf], missing_fields))

    return EvaluationError(
        stack=stack,
        reason=DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELDS,
        message='Missing required fields "{missing_fields}" {path_msg}".'.format(
            missing_fields=missing_fields, path_msg=get_friendly_path_msg(stack)
        ),
        error_data=MissingFieldsErrorData(
            field_names=missing_fields, field_defs=missing_field_defs
        ),
    )
