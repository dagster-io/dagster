from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.errors import DagsterError
from dagster.utils.error import SerializableErrorInfo

from .config_type import ConfigType, ConfigTypeKind
from .field import check_field_param
from .stack import EvaluationStack, get_friendly_path_info, get_friendly_path_msg
from .type_printer import print_config_type_to_string
from .validation_context import ValidationContext


class DagsterEvaluationErrorReason(Enum):
    RUNTIME_TYPE_MISMATCH = 'RUNTIME_TYPE_MISMATCH'
    MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD'
    MISSING_REQUIRED_FIELDS = 'MISSING_REQUIRED_FIELDS'
    FIELD_NOT_DEFINED = 'FIELD_NOT_DEFINED'
    FIELDS_NOT_DEFINED = 'FIELDS_NOT_DEFINED'
    SELECTOR_FIELD_ERROR = 'SELECTOR_FIELD_ERROR'
    FAILED_POST_PROCESSING = 'FAILED_POST_PROCESSING'


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
        check.param_invariant(dagster_type.kind == ConfigTypeKind.SELECTOR, 'dagster_type')
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
    SerializableErrorInfo,
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

    type_msg = _get_type_msg(type_in_context)

    if error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD:
        return error.message
    elif error.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELDS:
        return error.message
    elif error.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED:
        return ('Undefined field "{field_name}" {path_msg}.').format(
            field_name=error.error_data.field_name, path_msg=path_msg,
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


def _get_type_msg(type_in_context):
    if type_in_context.given_name is None:
        return ''
    else:
        return ' on type "{type_name}"'.format(type_name=type_in_context.given_name)


def create_dict_type_mismatch_error(context, config_value):
    check.inst_param(context, 'context', ValidationContext)

    path_msg, _path = get_friendly_path_info(context.stack)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message='Value {path_msg} must be dict. Expected: "{type_name}".'.format(
            path_msg=path_msg,
            type_name=print_config_type_to_string(context.config_type, with_lines=False),
        ),
        error_data=RuntimeMismatchErrorData(
            config_type=context.config_type, value_rep=repr(config_value)
        ),
    )


def create_fields_not_defined_error(context, undefined_fields):
    check.inst_param(context, 'context', ValidationContext)
    check_config_type_in_context_has_fields(context, 'context')
    check.list_param(undefined_fields, 'undefined_fields', of_type=str)

    available_fields = sorted(list(context.config_type.fields.keys()))
    undefined_fields = sorted(undefined_fields)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.FIELDS_NOT_DEFINED,
        message=(
            'Fields "{undefined_fields}" are not defined {path_msg} Available '
            'fields: "{available_fields}"'
        ).format(
            undefined_fields=undefined_fields,
            path_msg=get_friendly_path_msg(context.stack),
            available_fields=available_fields,
        ),
        error_data=FieldsNotDefinedErrorData(field_names=undefined_fields),
    )


def create_enum_type_mismatch_error(context, config_value):
    check.inst_param(context, 'context', ValidationContext)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message='Value for enum type {type_name} must be a string'.format(
            type_name=context.config_type.given_name
        ),
        error_data=RuntimeMismatchErrorData(context.config_type, repr(config_value)),
    )


def create_enum_value_missing_error(context, config_value):
    check.inst_param(context, 'context', ValidationContext)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message='Value not in enum type {type_name}'.format(
            type_name=context.config_type.given_name
        ),
        error_data=RuntimeMismatchErrorData(context.config_type, repr(config_value)),
    )


def check_config_type_in_context_has_fields(context, param_name):
    check.param_invariant(ConfigTypeKind.has_fields(context.config_type.kind), param_name)


def create_field_not_defined_error(context, received_field):
    check.inst_param(context, 'context', ValidationContext)
    check_config_type_in_context_has_fields(context, 'context')
    check.str_param(received_field, 'received_field')

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.FIELD_NOT_DEFINED,
        message='Field "{received}" is not defined {path_msg} Expected: "{type_name}"'.format(
            path_msg=get_friendly_path_msg(context.stack),
            type_name=print_config_type_to_string(context.config_type, with_lines=False),
            received=received_field,
        ),
        error_data=FieldNotDefinedErrorData(field_name=received_field),
    )


def create_array_error(context, config_value):
    check.inst_param(context, 'context', ValidationContext)
    check.param_invariant(context.config_type.kind == ConfigTypeKind.ARRAY, 'config_type')

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message='Value {path_msg} must be list. Expected: {type_name}'.format(
            path_msg=get_friendly_path_msg(context.stack),
            type_name=print_config_type_to_string(context.config_type, with_lines=False),
        ),
        error_data=RuntimeMismatchErrorData(context.config_type, repr(config_value)),
    )


def create_missing_required_field_error(context, expected_field):
    check.inst_param(context, 'context', ValidationContext)
    check_config_type_in_context_has_fields(context, 'context')

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD,
        message=(
            'Missing required field "{expected}" {path_msg} Available Fields: '
            '"{available_fields}".'
        ).format(
            expected=expected_field,
            path_msg=get_friendly_path_msg(context.stack),
            available_fields=sorted(list(context.config_type.fields.keys())),
        ),
        error_data=MissingFieldErrorData(
            field_name=expected_field, field_def=context.config_type.fields[expected_field]
        ),
    )


def create_missing_required_fields_error(context, missing_fields):
    check.inst_param(context, 'context', ValidationContext)
    check_config_type_in_context_has_fields(context, 'context')

    missing_fields = sorted(missing_fields)
    missing_field_defs = list(map(lambda mf: context.config_type.fields[mf], missing_fields))

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELDS,
        message='Missing required fields "{missing_fields}" {path_msg}".'.format(
            missing_fields=missing_fields, path_msg=get_friendly_path_msg(context.stack)
        ),
        error_data=MissingFieldsErrorData(
            field_names=missing_fields, field_defs=missing_field_defs
        ),
    )


def create_scalar_error(context, config_value):
    check.inst_param(context, 'context', ValidationContext)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message='Invalid scalar {path_msg} value "{config_value}" of type '
        '"{type}" is not valid for expected type "{type_name}"'.format(
            path_msg=get_friendly_path_msg(context.stack),
            type_name=context.config_type.given_name,
            config_value=config_value,
            type=type(config_value),
        ),
        error_data=RuntimeMismatchErrorData(context.config_type, repr(config_value)),
    )


def create_selector_multiple_fields_error(context, config_value):
    check.inst_param(context, 'context', ValidationContext)

    defined_fields = sorted(list(context.config_type.fields.keys()))
    incoming_fields = sorted(list(config_value.keys()))

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
        message=(
            'You can only specify a single field {path_msg}. You specified {incoming_fields}. '
            'The available fields are {defined_fields}'
        ).format(
            incoming_fields=incoming_fields,
            defined_fields=defined_fields,
            path_msg=get_friendly_path_msg(context.stack),
        ),
        error_data=SelectorTypeErrorData(
            dagster_type=context.config_type, incoming_fields=incoming_fields
        ),
    )


def create_selector_multiple_fields_no_field_selected_error(context):
    check.inst_param(context, 'context', ValidationContext)

    defined_fields = sorted(list(context.config_type.fields.keys()))

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
        message=(
            'Must specify a field {path_msg} if more than one field is defined. '
            'Defined fields: {defined_fields}'
        ).format(defined_fields=defined_fields, path_msg=get_friendly_path_msg(context.stack)),
        error_data=SelectorTypeErrorData(dagster_type=context.config_type, incoming_fields=[]),
    )


def create_selector_type_error(context, config_value):
    check.inst_param(context, 'context', ValidationContext)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message='Value for selector type {path_msg} must be a dict'.format(
            path_msg=get_friendly_path_msg(context.stack)
        ),
        error_data=RuntimeMismatchErrorData(
            config_type=context.config_type, value_rep=repr(config_value)
        ),
    )


def create_selector_unspecified_value_error(context):
    check.inst_param(context, 'context', ValidationContext)

    defined_fields = sorted(list(context.config_type.fields.keys()))

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
        message=(
            'Must specify the required field {path_msg}. Defined fields: {defined_fields}'
        ).format(defined_fields=defined_fields, path_msg=get_friendly_path_msg(context.stack)),
        error_data=SelectorTypeErrorData(dagster_type=context.config_type, incoming_fields=[]),
    )


def create_none_not_allowed_error(context):
    check.inst_param(context, 'context', ValidationContext)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message='Value {path_msg} must be not be None.'.format(
            path_msg=get_friendly_path_msg(context.stack),
        ),
        error_data=RuntimeMismatchErrorData(context.config_type, repr(None)),
    )


def create_failed_post_processing_error(context, original_value, error_data):
    check.inst_param(context, 'context', ValidationContext)
    check.inst_param(error_data, 'error_data', SerializableErrorInfo)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.FAILED_POST_PROCESSING,
        message='Post processing {path_msg} of original value {original_value} failed:\n{error}'.format(
            path_msg=get_friendly_path_msg(context.stack),
            original_value=original_value,
            error=error_data.to_string(),
        ),
        error_data=error_data,
    )
