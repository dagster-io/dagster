import copy

import six

from dagster import check
from dagster.core.types.config.config_type import (
    Bool,
    ConfigScalar,
    ConfigType,
    ConfigTypeKind,
    Float,
    Int,
    Path,
    String,
)
from dagster.utils import ensure_single_item, frozendict, merge_dicts

from .errors import (
    create_dict_type_mismatch_error,
    create_enum_type_mismatch_error,
    create_enum_value_missing_error,
    create_field_not_defined_error,
    create_fields_not_defined_error,
    create_list_error,
    create_missing_required_field_error,
    create_missing_required_fields_error,
    create_scalar_error,
    create_selector_multiple_fields_error,
    create_selector_multiple_fields_no_field_selected_error,
    create_selector_type_error,
    create_selector_unspecified_value_error,
)
from .evaluate_value_result import EvaluateValueResult
from .stack import EvaluationStack
from .validation_context import ValidationContext


def is_config_scalar_valid(config_type, config_value):
    check.inst_param(config_type, 'config_type', ConfigType)
    if isinstance(config_type, Int):
        return not isinstance(config_value, bool) and isinstance(config_value, six.integer_types)
    elif isinstance(config_type, String) or isinstance(config_type, Path):
        return isinstance(config_value, six.string_types)
    elif isinstance(config_type, Bool):
        return isinstance(config_value, bool)
    elif isinstance(config_type, Float):
        return isinstance(config_value, float)
    elif isinstance(config_type, ConfigScalar):
        # TODO: remove (disallow custom scalars)
        # https://github.com/dagster-io/dagster/issues/1991
        return config_type.is_config_scalar_valid(config_value)
    else:
        check.failed('Not a supported scalar {}'.format(config_type))


def validate_config(config_type, config_value):
    context = ValidationContext(
        config_type=check.inst_param(config_type, 'config_type', ConfigType),
        stack=EvaluationStack(config_type=config_type, entries=[]),
    )

    return _validate_config(context, config_value)


def _validate_config(context, config_value):
    check.inst_param(context, 'context', ValidationContext)

    kind = context.config_type.kind

    if kind == ConfigTypeKind.NULLABLE:
        return (
            EvaluateValueResult.for_value(None)
            if config_value is None
            else _validate_config(context.for_nullable_inner_type(), config_value)
        )

    if kind == ConfigTypeKind.ANY:
        return EvaluateValueResult.for_value(config_value)  # yolo

    # TODO: Consider blanket check against None here
    # https://github.com/dagster-io/dagster/issues/1988

    if kind == ConfigTypeKind.SCALAR:
        if not is_config_scalar_valid(context.config_type, config_value):
            return EvaluateValueResult.for_error(create_scalar_error(context, config_value))
        return EvaluateValueResult.for_value(config_value)
    elif kind == ConfigTypeKind.SELECTOR:
        return validate_selector_config(context, config_value)
    elif kind == ConfigTypeKind.DICT:
        return validate_dict_config(context, config_value)
    elif kind == ConfigTypeKind.PERMISSIVE_DICT:
        return validate_permissive_dict_config(context, config_value)
    elif kind == ConfigTypeKind.LIST:
        return validate_list_config(context, config_value)
    elif kind == ConfigTypeKind.ENUM:
        return validate_enum_config(context, config_value)
    else:
        check.failed('Unsupported ConfigTypeKind {}'.format(kind))


def validate_selector_config(context, config_value):
    check.inst_param(context, 'context', ValidationContext)
    check.param_invariant(context.config_type.kind == ConfigTypeKind.SELECTOR, 'selector_type')

    if config_value:
        if not isinstance(config_value, dict):
            return EvaluateValueResult.for_error(create_selector_type_error(context, config_value))

        if len(config_value) > 1:
            return EvaluateValueResult.for_error(
                create_selector_multiple_fields_error(context, config_value)
            )

        field_name, incoming_field_value = ensure_single_item(config_value)
        if field_name not in context.config_type.fields:
            return EvaluateValueResult.for_error(
                create_field_not_defined_error(context, field_name)
            )

    else:
        if len(context.config_type.fields) > 1:
            return EvaluateValueResult.for_error(
                create_selector_multiple_fields_no_field_selected_error(context)
            )

        field_name, field_def = ensure_single_item(context.config_type.fields)

        if not field_def.is_optional:
            return EvaluateValueResult.for_error(create_selector_unspecified_value_error(context))

        incoming_field_value = field_def.default_value if field_def.default_provided else None

    field_def = context.config_type.fields[field_name]

    child_evaluate_value_result = _validate_config(
        context.for_field(field_def, field_name), incoming_field_value
    )

    if child_evaluate_value_result.success:
        return EvaluateValueResult.for_value(
            frozendict({field_name: child_evaluate_value_result.value})
        )
    else:
        return child_evaluate_value_result


def _validate_fields(context, config_value, errors):
    field_errors = []
    new_config_value = {}
    for name, field_def in context.config_type.fields.items():
        if name in config_value:
            field_evr = _validate_config(context.for_field(field_def, name), config_value[name])

            if field_evr.errors:
                field_errors += field_evr.errors

            new_config_value[name] = field_evr.value
        elif field_def.default_provided:
            new_config_value[name] = field_def.default_value

    if field_errors:
        errors += field_errors

    if errors:
        return EvaluateValueResult.for_errors(errors)
    else:
        return EvaluateValueResult.for_value(frozendict(new_config_value))


def validate_permissive_dict_config(context, config_value):
    check.inst_param(context, 'context', ValidationContext)
    check.invariant(context.config_type.kind == ConfigTypeKind.PERMISSIVE_DICT)

    if config_value and not isinstance(config_value, dict):
        return EvaluateValueResult.for_error(create_dict_type_mismatch_error(context, config_value))

    # coercion and temp variable required because:
    # https://github.com/dagster-io/dagster/issues/1988
    config_dict_value = config_value or {}
    fields = context.config_type.fields

    errors = []
    _append_if_error(
        errors,
        _compute_missing_fields_error(
            context, fields, incoming_fields=set(config_dict_value.keys())
        ),
    )

    # copy to prevent default application from smashing original values
    evr = _validate_fields(context, copy.copy(config_dict_value), errors)
    if not evr.success:
        return evr

    # _validate_fields constructs a new dict with only the defined fields
    # The merge ensures that extra keys not in the field dictionary
    # are returned back, but that an modifications (e.g. default values)
    # as a result of validation are also returned
    return EvaluateValueResult.for_value(merge_dicts(config_dict_value, evr.value))


def validate_dict_config(context, config_value):
    check.inst_param(context, 'context', ValidationContext)
    check.invariant(context.config_type.kind == ConfigTypeKind.DICT)

    if config_value and not isinstance(config_value, dict):
        return EvaluateValueResult.for_error(create_dict_type_mismatch_error(context, config_value))

    # coercion and temp variable required because:
    # https://github.com/dagster-io/dagster/issues/1988
    config_dict_value = config_value or {}
    fields = context.config_type.fields

    defined_fields = set(fields.keys())
    incoming_fields = set(config_dict_value.keys())

    errors = []

    _append_if_error(errors, _compute_extra_fields(context, defined_fields, incoming_fields))
    _append_if_error(errors, _compute_missing_fields_error(context, fields, incoming_fields))

    return _validate_fields(context, config_dict_value, errors)


def _append_if_error(errors, maybe_error):
    if maybe_error:
        errors.append(maybe_error)


def _compute_extra_fields(context, defined_fields, incoming_fields):
    extra_fields = list(incoming_fields - defined_fields)

    if extra_fields:
        if len(extra_fields) == 1:
            return create_field_not_defined_error(context, extra_fields[0])
        else:
            return create_fields_not_defined_error(context, extra_fields)


def _compute_missing_fields_error(context, field_defs, incoming_fields):
    missing_fields = []

    for field_name, field_def in field_defs.items():
        if not field_def.is_optional and field_name not in incoming_fields:
            missing_fields.append(field_name)

    if missing_fields:
        if len(missing_fields) == 1:
            return create_missing_required_field_error(context, missing_fields[0])
        else:
            return create_missing_required_fields_error(context, missing_fields)


def validate_list_config(context, config_value):
    check.inst_param(context, 'context', ValidationContext)
    check.invariant(context.config_type.kind == ConfigTypeKind.LIST)

    if not isinstance(config_value, list):
        return EvaluateValueResult.for_error(create_list_error(context, config_value))

    evaluation_results = [
        _validate_config(context.for_list(index), config_item)
        for index, config_item in enumerate(config_value)
    ]

    values = []
    errors = []
    for result in evaluation_results:
        if result.success:
            values.append(result.value)
        else:
            errors += result.errors

    return EvaluateValueResult(not bool(errors), values, errors)


def validate_enum_config(context, config_value):
    check.inst_param(context, 'context', ValidationContext)
    check.invariant(context.config_type.kind == ConfigTypeKind.ENUM)

    if not isinstance(config_value, six.string_types):
        return EvaluateValueResult.for_error(create_enum_type_mismatch_error(context, config_value))

    if not context.config_type.is_valid_config_enum_value(config_value):
        return EvaluateValueResult.for_error(create_enum_value_missing_error(context, config_value))

    return EvaluateValueResult.for_value(context.config_type.to_python_value(config_value))
