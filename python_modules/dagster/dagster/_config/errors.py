from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Union

import dagster._check as check
from dagster._config.config_type import ConfigTypeKind
from dagster._config.field_utils import EnvVar, IntEnvVar
from dagster._config.snap import ConfigFieldSnap, ConfigTypeSnap, minimal_config_for_type_snap
from dagster._config.stack import (
    EvaluationStackEntry,
    get_friendly_path_info,
    get_friendly_path_msg,
)
from dagster._config.traversal_context import ContextData
from dagster._config.type_printer import print_config_type_key_to_string
from dagster._record import IHaveNew, record, record_custom
from dagster._utils.error import SerializableErrorInfo


class DagsterEvaluationErrorReason(Enum):
    RUNTIME_TYPE_MISMATCH = "RUNTIME_TYPE_MISMATCH"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    MISSING_REQUIRED_FIELDS = "MISSING_REQUIRED_FIELDS"
    FIELD_NOT_DEFINED = "FIELD_NOT_DEFINED"
    FIELDS_NOT_DEFINED = "FIELDS_NOT_DEFINED"
    SELECTOR_FIELD_ERROR = "SELECTOR_FIELD_ERROR"
    FAILED_POST_PROCESSING = "FAILED_POST_PROCESSING"
    FIELD_ALIAS_COLLISION = "FIELD_ALIAS_COLLISION"


@record
class FieldsNotDefinedErrorData:
    field_names: Sequence[str]


@record
class FieldAliasCollisionErrorData:
    field_name: str
    aliased_field_name: str


@record
class FieldNotDefinedErrorData:
    field_name: str


@record
class MissingFieldErrorData:
    field_name: str
    field_snap: ConfigFieldSnap


@record
class MissingFieldsErrorData:
    field_names: Sequence[str]
    field_snaps: Sequence[ConfigFieldSnap]


@record
class RuntimeMismatchErrorData:
    config_type_snap: ConfigTypeSnap
    value_rep: str


@record_custom
class SelectorTypeErrorData(IHaveNew):
    config_type_snap: ConfigTypeSnap
    incoming_fields: Sequence[str]

    def __new__(
        cls,
        *,
        config_type_snap: ConfigTypeSnap,
        incoming_fields: Sequence[str],
    ):
        check.inst_param(config_type_snap, "config_type_snap", ConfigTypeSnap)
        check.param_invariant(config_type_snap.kind == ConfigTypeKind.SELECTOR, "config_type")
        return super().__new__(
            cls,
            config_type_snap=config_type_snap,
            incoming_fields=incoming_fields,
        )


ERROR_DATA_UNION = Union[
    FieldNotDefinedErrorData,
    FieldsNotDefinedErrorData,
    MissingFieldErrorData,
    MissingFieldsErrorData,
    RuntimeMismatchErrorData,
    SelectorTypeErrorData,
    SerializableErrorInfo,
    FieldAliasCollisionErrorData,
]

ERROR_DATA_TYPES = ERROR_DATA_UNION.__args__  # type: ignore


@record
class EvaluationError:
    stack: EvaluationStackEntry
    reason: DagsterEvaluationErrorReason
    message: str
    error_data: ERROR_DATA_UNION


def _get_type_msg(type_in_context):
    if type_in_context.given_name is None:
        return ""
    else:
        return f' on type "{type_in_context.given_name}"'


def create_dict_type_mismatch_error(context: ContextData, config_value: object) -> EvaluationError:
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


def create_field_substitution_collision_error(
    context: ContextData, name: str, aliased_name: str
) -> EvaluationError:
    check.inst_param(context, "context", ContextData)
    check_config_type_in_context_has_fields(context, "context")
    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.FIELD_ALIAS_COLLISION,
        message=(
            f"Received both field '{name}' and field '{aliased_name}' in config. Please use one or"
            " the other."
        ),
        error_data=FieldAliasCollisionErrorData(field_name=name, aliased_field_name=aliased_name),
    )


def create_fields_not_defined_error(
    context: ContextData, undefined_fields: Sequence[str]
) -> EvaluationError:
    check.inst_param(context, "context", ContextData)
    check_config_type_in_context_has_fields(context, "context")
    check.list_param(undefined_fields, "undefined_fields", of_type=str)

    available_fields = sorted(context.config_type_snap.field_names)
    undefined_fields = sorted(undefined_fields)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.FIELDS_NOT_DEFINED,
        message=(
            f'Received unexpected config entries "{undefined_fields}" {get_friendly_path_msg(context.stack)}. '
            f'Expected: "{available_fields}."'
        ),
        error_data=FieldsNotDefinedErrorData(field_names=undefined_fields),
    )


def create_enum_type_mismatch_error(context: ContextData, config_value: object) -> EvaluationError:
    check.inst_param(context, "context", ContextData)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message=f"Value {get_friendly_path_msg(context.stack)} for enum type {context.config_type_snap.given_name} must be a string",
        error_data=RuntimeMismatchErrorData(
            config_type_snap=context.config_type_snap,
            value_rep=repr(config_value),
        ),
    )


def create_enum_value_missing_error(context: ContextData, config_value: object) -> EvaluationError:
    check.inst_param(context, "context", ContextData)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message=f"Value {get_friendly_path_msg(context.stack)} not in enum type {context.config_type_snap.given_name} got {config_value}",
        error_data=RuntimeMismatchErrorData(
            config_type_snap=context.config_type_snap,
            value_rep=repr(config_value),
        ),
    )


def check_config_type_in_context_has_fields(context: ContextData, param_name: str) -> None:
    check.param_invariant(ConfigTypeKind.has_fields(context.config_type_snap.kind), param_name)


def create_field_not_defined_error(context: ContextData, received_field: str) -> EvaluationError:
    check.inst_param(context, "context", ContextData)
    check_config_type_in_context_has_fields(context, "context")
    check.str_param(received_field, "received_field")

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.FIELD_NOT_DEFINED,
        message=(
            'Received unexpected config entry "{received}" {path_msg}. Expected: "{type_name}".'.format(
                path_msg=get_friendly_path_msg(context.stack),
                type_name=print_config_type_key_to_string(
                    context.config_schema_snapshot, context.config_type_key, with_lines=False
                ),
                received=received_field,
            )
        ),
        error_data=FieldNotDefinedErrorData(field_name=received_field),
    )


def create_array_error(context: ContextData, config_value: object) -> EvaluationError:
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
        error_data=RuntimeMismatchErrorData(
            config_type_snap=context.config_type_snap,
            value_rep=repr(config_value),
        ),
    )


def create_map_error(context: ContextData, config_value: object) -> EvaluationError:
    check.inst_param(context, "context", ContextData)
    check.param_invariant(context.config_type_snap.kind == ConfigTypeKind.MAP, "config_type")

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message='Value {path_msg} must be dict. Expected: "{type_name}"'.format(
            path_msg=get_friendly_path_msg(context.stack),
            type_name=print_config_type_key_to_string(
                context.config_schema_snapshot, context.config_type_key, with_lines=False
            ),
        ),
        error_data=RuntimeMismatchErrorData(
            config_type_snap=context.config_type_snap,
            value_rep=repr(config_value),
        ),
    )


def create_missing_required_field_error(
    context: ContextData, expected_field: str
) -> EvaluationError:
    check.inst_param(context, "context", ContextData)
    check_config_type_in_context_has_fields(context, "context")

    missing_field_type = context.config_schema_snapshot.get_config_snap(
        context.config_type_snap.get_field(expected_field).type_key
    )

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD,
        message=(
            'Missing required config entry "{expected}" {path_msg}. Sample config for missing'
            " entry: {minimal_config}"
        ).format(
            expected=expected_field,
            path_msg=get_friendly_path_msg(context.stack),
            minimal_config={
                expected_field: minimal_config_for_type_snap(
                    context.config_schema_snapshot, missing_field_type
                )
            },
        ),
        error_data=MissingFieldErrorData(
            field_name=expected_field, field_snap=context.config_type_snap.get_field(expected_field)
        ),
    )


def create_missing_required_fields_error(
    context: ContextData, missing_fields: Sequence[str]
) -> EvaluationError:
    check.inst_param(context, "context", ContextData)
    check_config_type_in_context_has_fields(context, "context")

    missing_fields = sorted(missing_fields)
    missing_field_snaps = list(map(context.config_type_snap.get_field, missing_fields))

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELDS,
        message=(
            "Missing required config entries {missing_fields} {path_msg}. Sample config for missing"
            " entries: {minimal_config}".format(
                missing_fields=missing_fields,
                path_msg=get_friendly_path_msg(context.stack),
                minimal_config={
                    field_snap.name: minimal_config_for_type_snap(
                        context.config_schema_snapshot,
                        context.config_schema_snapshot.get_config_snap(field_snap.type_key),
                    )
                    for field_snap in missing_field_snaps
                },
            )
        ),
        error_data=MissingFieldsErrorData(
            field_names=missing_fields, field_snaps=missing_field_snaps
        ),
    )


def create_scalar_error(context: ContextData, config_value: object) -> EvaluationError:
    check.inst_param(context, "context", ContextData)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message=(
            f'Invalid scalar {get_friendly_path_msg(context.stack)}. Value "{config_value}" of type '
            f'"{type(config_value)}" is not valid for expected type "{context.config_type_snap.given_name}".'
        ),
        error_data=RuntimeMismatchErrorData(
            config_type_snap=context.config_type_snap,
            value_rep=repr(config_value),
        ),
    )


def create_pydantic_env_var_error(
    context: ContextData, config_value: Union[EnvVar, IntEnvVar]
) -> EvaluationError:
    env_var_name = config_value.env_var_name

    correct_env_var = str({"env": env_var_name})
    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message=(
            f'Invalid use of environment variable wrapper. Value "{env_var_name}" is wrapped with'
            " EnvVar(), which is reserved for passing to structured pydantic config objects only."
            " To provide an environment variable to a run config dictionary, replace"
            f' EnvVar("{env_var_name}") with {correct_env_var}, or pass a structured RunConfig'
            " object."
        ),
        error_data=RuntimeMismatchErrorData(
            config_type_snap=context.config_type_snap,
            value_rep=repr(env_var_name),
        ),
    )


def create_selector_multiple_fields_error(
    context: ContextData, config_value: Mapping[str, object]
) -> EvaluationError:
    check.inst_param(context, "context", ContextData)

    defined_fields = sorted(context.config_type_snap.field_names)
    incoming_fields = sorted(list(config_value.keys()))

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
        message=(
            f"You can only specify a single field {get_friendly_path_msg(context.stack)}. You specified {incoming_fields}. "
            f"The available fields are {defined_fields}"
        ),
        error_data=SelectorTypeErrorData(
            config_type_snap=context.config_type_snap, incoming_fields=incoming_fields
        ),
    )


def create_selector_multiple_fields_no_field_selected_error(
    context: ContextData,
) -> EvaluationError:
    check.inst_param(context, "context", ContextData)

    defined_fields = sorted(context.config_type_snap.field_names)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
        message=(
            f"Must specify a field {get_friendly_path_msg(context.stack)} if more than one field is defined. "
            f"Defined fields: {defined_fields}"
        ),
        error_data=SelectorTypeErrorData(
            config_type_snap=context.config_type_snap, incoming_fields=[]
        ),
    )


def create_selector_type_error(context: ContextData, config_value: object) -> EvaluationError:
    check.inst_param(context, "context", ContextData)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
        message=f"Value for selector type {get_friendly_path_msg(context.stack)} must be a dict",
        error_data=RuntimeMismatchErrorData(
            config_type_snap=context.config_type_snap, value_rep=repr(config_value)
        ),
    )


def create_selector_unspecified_value_error(context: ContextData) -> EvaluationError:
    check.inst_param(context, "context", ContextData)

    defined_fields = sorted(context.config_type_snap.field_names)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
        message=(
            f"Must specify the required field {get_friendly_path_msg(context.stack)}. Defined fields: {defined_fields}"
        ),
        error_data=SelectorTypeErrorData(
            config_type_snap=context.config_type_snap, incoming_fields=[]
        ),
    )


def create_none_not_allowed_error(context: ContextData) -> EvaluationError:
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
        error_data=RuntimeMismatchErrorData(
            config_type_snap=context.config_type_snap,
            value_rep=repr(None),
        ),
    )


def create_failed_post_processing_error(
    context: ContextData, original_value: object, error_data: SerializableErrorInfo
) -> EvaluationError:
    check.inst_param(context, "context", ContextData)
    check.inst_param(error_data, "error_data", SerializableErrorInfo)

    return EvaluationError(
        stack=context.stack,
        reason=DagsterEvaluationErrorReason.FAILED_POST_PROCESSING,
        message=(
            f"Post processing {get_friendly_path_msg(context.stack)} of original value {original_value} failed:\n{error_data.to_string()}"
        ),
        error_data=error_data,
    )


class PostProcessingError(Exception):
    """This is part of the formal API for implementing post_process
    methods on config types. Throw this error to indicate a
    that post processing cannot happen, and that the user
    must make a configuration and environment change in
    order resolve.
    """
