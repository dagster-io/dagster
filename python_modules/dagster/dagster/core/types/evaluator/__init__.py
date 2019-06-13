from collections import namedtuple

import six

from dagster import check

from dagster.utils import single_item, make_readonly_value

from ..config import ConfigType
from ..default_applier import apply_default_values
from ..type_printer import print_config_type_to_string

from .errors import (
    create_field_not_defined_error,
    create_fields_not_defined_error,
    create_missing_required_field_error,
    create_missing_required_fields_error,
    DagsterEvaluationErrorReason,
    EvaluationError,
    RuntimeMismatchErrorData,
    SelectorTypeErrorData,
)
from .stack import get_friendly_path_msg, get_friendly_path_info, EvaluationStack


class EvaluateValueResult(namedtuple('_EvaluateValueResult', 'success value errors')):
    def __new__(cls, success, value, errors):
        return super(EvaluateValueResult, cls).__new__(
            cls,
            check.bool_param(success, 'success'),
            value,
            check.list_param(errors, 'errors', of_type=EvaluationError),
        )

    def errors_at_level(self, *levels):
        return list(self._iterate_errors_at_level(list(levels)))

    def _iterate_errors_at_level(self, levels):
        check.list_param(levels, 'levels', of_type=str)
        for error in self.errors:
            if error.stack.levels == levels:
                yield error


def hard_create_config_value(config_type, config_value):
    check.inst_param(config_type, 'config_type', ConfigType)
    result = evaluate_config_value(config_type, config_value)
    check.invariant(result.success)
    return result.value


def evaluate_config_value(config_type, config_value):
    check.inst_param(config_type, 'config_type', ConfigType)

    errors = validate_config(config_type, config_value)
    if errors:
        return EvaluateValueResult(success=False, value=None, errors=errors)

    value = apply_default_values(config_type, config_value)

    return EvaluateValueResult(success=True, value=make_readonly_value(value), errors=[])


def validate_config(config_type, config_value):
    check.inst_param(config_type, 'config_type', ConfigType)

    return list(
        _validate_config(
            config_type, config_value, EvaluationStack(config_type=config_type, entries=[])
        )
    )


def _validate_config(config_type, config_value, stack):
    check.inst_param(config_type, 'config_type', ConfigType)
    check.inst_param(stack, 'stack', EvaluationStack)

    if config_type.is_scalar:
        if not config_type.is_config_scalar_valid(config_value):
            yield EvaluationError(
                stack=stack,
                reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
                message='Value {path_msg} is not valid. Expected "{type_name}"'.format(
                    path_msg=get_friendly_path_msg(stack), type_name=config_type.name
                ),
                error_data=RuntimeMismatchErrorData(
                    config_type=config_type, value_rep=repr(config_value)
                ),
            )
        return

    errors = []

    if config_type.is_any:
        # no-op: we're safe
        return
    elif config_type.is_selector:
        errors = validate_selector_config_value(config_type, config_value, stack)
    elif config_type.is_composite:
        errors = validate_composite_config_value(config_type, config_value, stack)
    elif config_type.is_list:
        errors = validate_list_value(config_type, config_value, stack)
    elif config_type.is_nullable:
        errors = (
            []
            if config_value is None
            else _validate_config(config_type.inner_type, config_value, stack)
        )
    elif config_type.is_enum:
        errors = validate_enum_value(config_type, config_value, stack)
    else:
        check.failed('Unsupported type {name}'.format(name=config_type.name))

    for error in errors:
        yield error


def validate_enum_value(enum_type, config_value, stack):
    check.param_invariant(enum_type.is_enum, 'enum_type')
    check.inst_param(stack, 'stack', EvaluationStack)

    if not isinstance(config_value, six.string_types):
        yield EvaluationError(
            stack=stack,
            reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
            message='Value for enum type {type_name} must be a string'.format(
                type_name=enum_type.name
            ),
            error_data=RuntimeMismatchErrorData(
                config_type=enum_type, value_rep=repr(config_value)
            ),
        )
        return

    if not enum_type.is_valid_config_enum_value(config_value):
        yield EvaluationError(
            stack=stack,
            reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
            message='Value not in enum type {type_name}'.format(type_name=enum_type.name),
            error_data=RuntimeMismatchErrorData(
                config_type=enum_type, value_rep=repr(config_value)
            ),
        )
        return


## Selectors


def validate_selector_config_value(selector_type, config_value, stack):
    check.param_invariant(selector_type.is_selector, 'selector_type')
    check.inst_param(stack, 'stack', EvaluationStack)

    if config_value and not isinstance(config_value, dict):
        yield EvaluationError(
            stack=stack,
            reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
            message='Value for selector type {type_name} must be a dict'.format(
                type_name=selector_type.name
            ),
            error_data=RuntimeMismatchErrorData(
                config_type=selector_type, value_rep=repr(config_value)
            ),
        )
        return

    if config_value and len(config_value) > 1:
        incoming_fields = sorted(list(config_value.keys()))
        defined_fields = sorted(list(selector_type.fields.keys()))
        yield EvaluationError(
            stack=stack,
            reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
            message=(
                'You can only specify a single field {path_msg}. You specified {incoming_fields}. '
                'The available fields are {defined_fields}'
            ).format(
                incoming_fields=incoming_fields,
                defined_fields=defined_fields,
                path_msg=get_friendly_path_msg(stack),
            ),
            error_data=SelectorTypeErrorData(
                dagster_type=selector_type, incoming_fields=incoming_fields
            ),
        )
        return

    elif not config_value:
        defined_fields = sorted(list(selector_type.fields.keys()))
        if len(selector_type.fields) > 1:
            yield EvaluationError(
                stack=stack,
                reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
                message=(
                    'Must specify a field {path_msg} if more than one field is defined. '
                    'Defined fields: {defined_fields}'
                ).format(defined_fields=defined_fields, path_msg=get_friendly_path_msg(stack)),
                error_data=SelectorTypeErrorData(dagster_type=selector_type, incoming_fields=[]),
            )
            return

        field_name, field_def = single_item(selector_type.fields)

        if not field_def.is_optional:
            yield EvaluationError(
                stack=stack,
                reason=DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR,
                message=(
                    'Must specify the required field {path_msg}. Defined fields: {defined_fields}'
                ).format(defined_fields=defined_fields, path_msg=get_friendly_path_msg(stack)),
                error_data=SelectorTypeErrorData(dagster_type=selector_type, incoming_fields=[]),
            )
            return

        incoming_field_value = field_def.default_value if field_def.default_provided else None

    else:
        check.invariant(config_value and len(config_value) == 1)

        field_name, incoming_field_value = single_item(config_value)
        if field_name not in selector_type.fields:
            yield create_field_not_defined_error(selector_type, stack, field_name)
            return

    parent_field = selector_type.fields[field_name]
    for error in _validate_config(
        parent_field.config_type, incoming_field_value, stack.with_field(field_name, parent_field)
    ):
        yield error


## Composites


def validate_composite_config_value(composite_type, config_value, stack):
    check.inst_param(composite_type, 'composite_type', ConfigType)
    check.param_invariant(composite_type.is_composite, 'composite_type')
    check.inst_param(stack, 'stack', EvaluationStack)

    path_msg, _path = get_friendly_path_info(stack)

    if config_value and not isinstance(config_value, dict):
        yield EvaluationError(
            stack=stack,
            reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
            message='Value {path_msg} must be dict. Expected: "{type_name}".'.format(
                path_msg=path_msg,
                type_name=print_config_type_to_string(composite_type, with_lines=False),
            ),
            error_data=RuntimeMismatchErrorData(
                config_type=composite_type, value_rep=repr(config_value)
            ),
        )
        return

    # ASK: this can crash on user error
    config_value = check.opt_dict_param(config_value, 'incoming_value', key_type=str)

    fields = composite_type.fields

    defined_fields = set(fields.keys())
    incoming_fields = set(config_value.keys())

    # Here, we support permissive composites. In cases where we know the set of permissible keys a
    # priori, we validate against the config. For permissive composites, we give the user an escape
    # hatch where they can specify arbitrary fields...
    if not composite_type.is_permissive_composite:
        undefined_fields = []
        for received_field in incoming_fields:
            if received_field not in defined_fields:
                undefined_fields.append(received_field)

        if undefined_fields:
            if len(undefined_fields) == 1:
                yield create_field_not_defined_error(composite_type, stack, undefined_fields[0])
            else:
                yield create_fields_not_defined_error(composite_type, stack, undefined_fields)

    # ...However, for any fields the user *has* told us about, we validate against their config
    # specifications
    missing_fields = []
    for expected_field, field_def in fields.items():
        if expected_field in incoming_fields:
            for error in _validate_config(
                field_def.config_type,
                config_value[expected_field],
                stack.with_field(expected_field, field_def),
            ):
                yield error

        elif field_def.is_optional:
            pass

        else:
            check.invariant(not field_def.default_provided)
            missing_fields.append(expected_field)

    if missing_fields:
        if len(missing_fields) == 1:
            yield create_missing_required_field_error(composite_type, stack, missing_fields[0])
        else:
            yield create_missing_required_fields_error(composite_type, stack, missing_fields)


## Lists


def validate_list_value(list_type, config_value, stack):
    check.param_invariant(list_type.is_list, 'list_type')
    check.inst_param(stack, 'stack', EvaluationStack)

    if not isinstance(config_value, list):
        yield EvaluationError(
            stack=stack,
            reason=DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH,
            message='Value {path_msg} must be list. Expected: {type_name}'.format(
                path_msg=get_friendly_path_msg(stack),
                type_name=print_config_type_to_string(list_type, with_lines=False),
            ),
            error_data=RuntimeMismatchErrorData(
                config_type=list_type, value_rep=repr(config_value)
            ),
        )
        return

    for index, item in enumerate(config_value):
        for error in _validate_config(list_type.inner_type, item, stack.with_list_index(index)):
            yield error
