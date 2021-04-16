from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.utils.error import SerializableErrorInfo

from .config_type import ConfigTypeKind
from .snap import ConfigFieldSnap, ConfigTypeSnap, minimal_config_for_type_snap
from .stack import EvaluationStack, get_friendly_path_info, get_friendly_path_msg
from .traversal_context import ContextData
from .type_printer import print_config_type_key_to_string


class DagsterEvaluationErrorReason(Enum):
    RUNTIME_TYPE_MISMATCH = "RUNTIME_TYPE_MISMATCH"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    MISSING_REQUIRED_FIELDS = "MISSING_REQUIRED_FIELDS"
    FIELD_NOT_DEFINED = "FIELD_NOT_DEFINED"
    FIELDS_NOT_DEFINED = "FIELDS_NOT_DEFINED"
    SELECTOR_FIELD_ERROR = "SELECTOR_FIELD_ERROR"
    FAILED_POST_PROCESSING = "FAILED_POST_PROCESSING"


class FieldsNotDefinedErrorData(namedtuple("_FieldsNotDefinedErrorData", "field_names")):
    def __new__(cls, field_names):
        return super(FieldsNotDefinedErrorData, cls).__new__(
            cls, check.list_param(field_names, "field_names", of_type=str)
        )


class FieldNotDefinedErrorData(namedtuple("_FieldNotDefinedErrorData", "field_name")):
    def __new__(cls, field_name):
        return super(FieldNotDefinedErrorData, cls).__new__(
            cls, check.str_param(field_name, "field_name")
        )


class MissingFieldErrorData(namedtuple("_MissingFieldErrorData", "field_name field_snap")):
    def __new__(cls, field_name, field_snap):
        return super(MissingFieldErrorData, cls).__new__(
            cls,
            check.str_param(field_name, "field_name"),
            check.inst_param(field_snap, "field_snap", ConfigFieldSnap),
        )


class MissingFieldsErrorData(namedtuple("_MissingFieldErrorData", "field_names field_snaps")):
    def __new__(cls, field_names, field_snaps):
        return super(MissingFieldsErrorData, cls).__new__(
            cls,
            check.list_param(field_names, "field_names", of_type=str),
            check.list_param(field_snaps, "field_snaps", of_type=ConfigFieldSnap),
        )


class RuntimeMismatchErrorData(
    namedtuple("_RuntimeMismatchErrorData", "config_type_snap value_rep")
):
    def __new__(cls, config_type_snap, value_rep):
        check.inst_param(config_type_snap, "config_type", ConfigTypeSnap)
        return super(RuntimeMismatchErrorData, cls).__new__(
            cls,
            config_type_snap,
            check.str_param(value_rep, "value_rep"),
        )


class SelectorTypeErrorData(
    namedtuple("_SelectorTypeErrorData", "config_type_snap incoming_fields")
):
    def __new__(cls, config_type_snap, incoming_fields):
        check.inst_param(config_type_snap, "config_type_snap", ConfigTypeSnap)
        check.param_invariant(config_type_snap.kind == ConfigTypeKind.SELECTOR, "config_type")
        return super(SelectorTypeErrorData, cls).__new__(
            cls,
            config_type_snap,
            check.list_param(incoming_fields, "incoming_fields", of_type=str),
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


class EvaluationError(namedtuple("_EvaluationError", "stack reason message error_data")):
    def __new__(cls, stack, reason, message, error_data):
        return super(EvaluationError, cls).__new__(
            cls,
            check.inst_param(stack, "stack", EvaluationStack),
            check.inst_param(reason, "reason", DagsterEvaluationErrorReason),
            check.str_param(message, "message"),
            check.inst_param(error_data, "error_data", ERROR_DATA_TYPES),
        )


def _get_type_msg(type_in_context):
    if type_in_context.given_name is None:
        return ""
    else:
        return ' on type "{type_name}"'.format(type_name=type_in_context.given_name)


def create_dict_type_mismatch_error(context, config_value):
    check.inst_param(context, "context", ContextData)

    path_msg, _path = get_friendly_path_info(context.stack)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message='Value {path_msg} must be dict. Expected: "{type_name}".'.format(
            path_msg=path_msg,
            type_name=print_config_type_key_to_string(
                context.config_schema_snapshot, context.config_type_key, with_lines=False
            ),
        ),
        error_data=RuntimeMismatchErrorData(
            config_type_snap=context.config_type_snap, value_rep=repr(config_value)
        ),
    )


def create_fields_not_defined_error(context, undefined_fields):
    check.inst_param(context, "context", ContextData)
    check_config_type_in_context_has_fields(context, "context")
    check.list_param(undefined_fields, "undefined_fields", of_type=str)

    available_fields = sorted(context.config_type_snap.field_names)
    undefined_fields = sorted(undefined_fields)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.FIELDS_NOT_DEFINED,
        message=(
            'Received unexpected config entries "{undefined_fields}" {path_msg}. '
            'Expected: "{available_fields}."'
        ).format(
            undefined_fields=undefined_fields,
            path_msg=get_friendly_path_msg(context.stack),
            available_fields=available_fields,
        ),
        error_data=FieldsNotDefinedErrorData(field_names=undefined_fields),
    )


def create_enum_type_mismatch_error(context, config_value):
    check.inst_param(context, "context", ContextData)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message="Value {path_msg} for enum type {type_name} must be a string".format(
            type_name=context.config_type_snap.given_name,
            path_msg=get_friendly_path_msg(context.stack),
        ),
        error_data=RuntimeMismatchErrorData(context.config_type_snap, repr(config_value)),
    )


def create_enum_value_missing_error(context, config_value):
    check.inst_param(context, "context", ContextData)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message="Value {path_msg} not in enum type {type_name} got {config_value}".format(
            config_value=config_value,
            type_name=context.config_type_snap.given_name,
            path_msg=get_friendly_path_msg(context.stack),
        ),
        error_data=RuntimeMismatchErrorData(context.config_type_snap, repr(config_value)),
    )


def check_config_type_in_context_has_fields(context, param_name):
    check.param_invariant(ConfigTypeKind.has_fields(context.config_type_snap.kind), param_name)


def create_field_not_defined_error(context, received_field):
    check.inst_param(context, "context", ContextData)
    check_config_type_in_context_has_fields(context, "context")
    check.str_param(received_field, "received_field")

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.FIELD_NOT_DEFINED,
        message='Received unexpected config entry "{received}" {path_msg}. Expected: "{type_name}".'.format(
            path_msg=get_friendly_path_msg(context.stack),
            type_name=print_config_type_key_to_string(
                context.config_schema_snapshot, context.config_type_key, with_lines=False
            ),
            received=received_field,
        ),
        error_data=FieldNotDefinedErrorData(field_name=received_field),
    )


def create_array_error(context, config_value):
    check.inst_param(context, "context", ContextData)
    check.param_invariant(context.config_type_snap.kind == ConfigTypeKind.ARRAY, "config_type")

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message='Value {path_msg} must be list. Expected: "{type_name}"'.format(
            path_msg=get_friendly_path_msg(context.stack),
            type_name=print_config_type_key_to_string(
                context.config_schema_snapshot, context.config_type_key, with_lines=False
            ),
        ),
        error_data=RuntimeMismatchErrorData(context.config_type_snap, repr(config_value)),
    )


def create_missing_required_field_error(context, expected_field):
    check.inst_param(context, "context", ContextData)
    check_config_type_in_context_has_fields(context, "context")

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD,
        message=(
            'Missing required config entry "{expected}" {path_msg}. Minimal acceptable config for this path: {minimal_config}'
        ).format(
            expected=expected_field,
            path_msg=get_friendly_path_msg(context.stack),
            minimal_config=minimal_config_for_type_snap(
                context.config_schema_snapshot, context.config_type_snap
            ),
        ),
        error_data=MissingFieldErrorData(
            field_name=expected_field, field_snap=context.config_type_snap.get_field(expected_field)
        ),
    )


def create_missing_required_fields_error(context, missing_fields):
    check.inst_param(context, "context", ContextData)
    check_config_type_in_context_has_fields(context, "context")

    missing_fields = sorted(missing_fields)
    missing_field_snaps = list(map(context.config_type_snap.get_field, missing_fields))

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELDS,
        message='Missing required config entries "{missing_fields}" {path_msg}". Minimum acceptable config for this path: {minimal_config}'.format(
            missing_fields=missing_fields,
            path_msg=get_friendly_path_msg(context.stack),
            minimal_config=minimal_config_for_type_snap(
                context.config_schema_snapshot, context.config_type_snap
            ),
        ),
        error_data=MissingFieldsErrorData(
            field_names=missing_fields, field_snaps=missing_field_snaps
        ),
    )


def create_scalar_error(context, config_value):
    check.inst_param(context, "context", ContextData)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message='Invalid scalar {path_msg}. Value "{config_value}" of type '
        '"{type}" is not valid for expected type "{type_name}".'.format(
            path_msg=get_friendly_path_msg(context.stack),
            type_name=context.config_type_snap.given_name,
            config_value=config_value,
            type=type(config_value),
        ),
        error_data=RuntimeMismatchErrorData(context.config_type_snap, repr(config_value)),
    )


def create_selector_multiple_fields_error(context, config_value):
    check.inst_param(context, "context", ContextData)

    defined_fields = sorted(context.config_type_snap.field_names)
    incoming_fields = sorted(list(config_value.keys()))

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
        message=(
            "You can only specify a single field {path_msg}. You specified {incoming_fields}. "
            "The available fields are {defined_fields}"
        ).format(
            incoming_fields=incoming_fields,
            defined_fields=defined_fields,
            path_msg=get_friendly_path_msg(context.stack),
        ),
        error_data=SelectorTypeErrorData(
            config_type_snap=context.config_type_snap, incoming_fields=incoming_fields
        ),
    )


def create_selector_multiple_fields_no_field_selected_error(context):
    check.inst_param(context, "context", ContextData)

    defined_fields = sorted(context.config_type_snap.field_names)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
        message=(
            "Must specify a field {path_msg} if more than one field is defined. "
            "Defined fields: {defined_fields}"
        ).format(defined_fields=defined_fields, path_msg=get_friendly_path_msg(context.stack)),
        error_data=SelectorTypeErrorData(
            config_type_snap=context.config_type_snap, incoming_fields=[]
        ),
    )


def create_selector_type_error(context, config_value):
    check.inst_param(context, "context", ContextData)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message="Value for selector type {path_msg} must be a dict".format(
            path_msg=get_friendly_path_msg(context.stack)
        ),
        error_data=RuntimeMismatchErrorData(
            config_type_snap=context.config_type_snap, value_rep=repr(config_value)
        ),
    )


def create_selector_unspecified_value_error(context):
    check.inst_param(context, "context", ContextData)

    defined_fields = sorted(list(context.config_type.fields.keys()))

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
        message=(
            "Must specify the required field {path_msg}. Defined fields: {defined_fields}"
        ).format(defined_fields=defined_fields, path_msg=get_friendly_path_msg(context.stack)),
        error_data=SelectorTypeErrorData(
            config_type_snap=context.config_type_snap, incoming_fields=[]
        ),
    )


def create_none_not_allowed_error(context):
    check.inst_param(context, "context", ContextData)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message='Value {path_msg} must not be None. Expected "{type_name}"'.format(
            path_msg=get_friendly_path_msg(context.stack),
            type_name=print_config_type_key_to_string(
                context.config_schema_snapshot, context.config_type_key, with_lines=False
            ),
        ),
        error_data=RuntimeMismatchErrorData(context.config_type_snap, repr(None)),
    )


def create_failed_post_processing_error(context, original_value, error_data):
    check.inst_param(context, "context", ContextData)
    check.inst_param(error_data, "error_data", SerializableErrorInfo)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.FAILED_POST_PROCESSING,
        message="Post processing {path_msg} of original value {original_value} failed:\n{error}".format(
            path_msg=get_friendly_path_msg(context.stack),
            original_value=original_value,
            error=error_data.to_string(),
        ),
        error_data=error_data,
    )


class PostProcessingError(Exception):
    """
    This is part of the formal API for implementing post_process
    methods on config types. Throw this error to indicate a
    that post processing cannot happen, and that the user
    must make a configuration and environment change in
    order resolve.
    """
