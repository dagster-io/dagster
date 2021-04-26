from dagster import check
from dagster.utils import ensure_single_item, frozendict

from .config_type import ConfigScalarKind, ConfigTypeKind
from .errors import (
    create_array_error,
    create_dict_type_mismatch_error,
    create_enum_type_mismatch_error,
    create_enum_value_missing_error,
    create_field_not_defined_error,
    create_fields_not_defined_error,
    create_missing_required_field_error,
    create_missing_required_fields_error,
    create_none_not_allowed_error,
    create_scalar_error,
    create_selector_multiple_fields_error,
    create_selector_multiple_fields_no_field_selected_error,
    create_selector_type_error,
    create_selector_unspecified_value_error,
)
from .evaluate_value_result import EvaluateValueResult
from .field import resolve_to_config_type
from .iterate_types import config_schema_snapshot_from_config_type
from .post_process import post_process_config
from .snap import ConfigSchemaSnapshot, ConfigTypeSnap
from .stack import EvaluationStack
from .traversal_context import ValidationContext

VALID_FLOAT_TYPES = tuple([int, float])


def is_config_scalar_valid(config_type_snap, config_value):
    check.inst_param(config_type_snap, "config_type_snap", ConfigTypeSnap)
    check.param_invariant(config_type_snap.kind == ConfigTypeKind.SCALAR, "config_type_snap")
    if config_type_snap.scalar_kind == ConfigScalarKind.INT:
        return not isinstance(config_value, bool) and isinstance(config_value, int)
    elif config_type_snap.scalar_kind == ConfigScalarKind.STRING:
        return isinstance(config_value, str)
    elif config_type_snap.scalar_kind == ConfigScalarKind.BOOL:
        return isinstance(config_value, bool)
    elif config_type_snap.scalar_kind == ConfigScalarKind.FLOAT:
        return isinstance(config_value, VALID_FLOAT_TYPES)
    elif config_type_snap.scalar_kind is None:
        # historical snapshot without scalar kind. do no validation
        return True
    else:
        check.failed("Not a supported scalar {}".format(config_type_snap))


def validate_config(config_schema, config_value):

    config_type = resolve_to_config_type(config_schema)

    config_schema_snapshot = config_schema_snapshot_from_config_type(config_type)

    return validate_config_from_snap(
        config_schema_snapshot=config_schema_snapshot,
        config_type_key=config_type.key,
        config_value=config_value,
    )


def validate_config_from_snap(config_schema_snapshot, config_type_key, config_value):
    check.inst_param(config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot)
    check.str_param(config_type_key, "config_type_key")
    return _validate_config(
        ValidationContext(
            config_schema_snapshot=config_schema_snapshot,
            config_type_snap=config_schema_snapshot.get_config_snap(config_type_key),
            stack=EvaluationStack(entries=[]),
        ),
        config_value,
    )


def _validate_config(context, config_value):
    check.inst_param(context, "context", ValidationContext)

    kind = context.config_type_snap.kind

    if kind == ConfigTypeKind.NONEABLE:
        return (
            EvaluateValueResult.for_value(None)
            if config_value is None
            else _validate_config(context.for_nullable_inner_type(), config_value)
        )

    if kind == ConfigTypeKind.ANY:
        return EvaluateValueResult.for_value(config_value)  # yolo

    if config_value is None:
        return EvaluateValueResult.for_error(create_none_not_allowed_error(context))

    if kind == ConfigTypeKind.SCALAR:
        if not is_config_scalar_valid(context.config_type_snap, config_value):
            return EvaluateValueResult.for_error(create_scalar_error(context, config_value))
        return EvaluateValueResult.for_value(config_value)
    elif kind == ConfigTypeKind.SELECTOR:
        return validate_selector_config(context, config_value)
    elif kind == ConfigTypeKind.STRICT_SHAPE:
        return validate_shape_config(context, config_value)
    elif kind == ConfigTypeKind.PERMISSIVE_SHAPE:
        return validate_permissive_shape_config(context, config_value)
    elif kind == ConfigTypeKind.ARRAY:
        return validate_array_config(context, config_value)
    elif kind == ConfigTypeKind.ENUM:
        return validate_enum_config(context, config_value)
    elif kind == ConfigTypeKind.SCALAR_UNION:
        return _validate_scalar_union_config(context, config_value)
    else:
        check.failed("Unsupported ConfigTypeKind {}".format(kind))


def _validate_scalar_union_config(context, config_value):
    check.inst_param(context, "context", ValidationContext)
    check.param_invariant(context.config_type_snap.kind == ConfigTypeKind.SCALAR_UNION, "context")
    check.not_none_param(config_value, "config_value")

    if isinstance(config_value, dict) or isinstance(config_value, list):
        return _validate_config(
            context.for_new_config_type_key(context.config_type_snap.non_scalar_type_key),
            config_value,
        )
    else:
        return _validate_config(
            context.for_new_config_type_key(context.config_type_snap.scalar_type_key),
            config_value,
        )


def _validate_empty_selector_config(context):
    if len(context.config_type_snap.fields) > 1:
        return EvaluateValueResult.for_error(
            create_selector_multiple_fields_no_field_selected_error(context)
        )

    defined_field_snap = context.config_type_snap.fields[0]

    if defined_field_snap.is_required:
        return EvaluateValueResult.for_error(create_selector_unspecified_value_error(context))

    return EvaluateValueResult.for_value({})


def validate_selector_config(context, config_value):
    check.inst_param(context, "context", ValidationContext)
    check.param_invariant(context.config_type_snap.kind == ConfigTypeKind.SELECTOR, "selector_type")
    check.not_none_param(config_value, "config_value")

    # Special case the empty dictionary, meaning no values provided for the
    # value of the selector. # E.g. {'logging': {}}
    # If there is a single field defined on the selector and if it is optional
    # it passes validation. (e.g. a single logger "console")
    if config_value == {}:
        return _validate_empty_selector_config(context)

    # Now we ensure that the used-provided config has only a a single entry
    # and then continue the validation pass

    if not isinstance(config_value, dict):
        return EvaluateValueResult.for_error(create_selector_type_error(context, config_value))

    if len(config_value) > 1:
        return EvaluateValueResult.for_error(
            create_selector_multiple_fields_error(context, config_value)
        )

    field_name, field_value = ensure_single_item(config_value)

    if not context.config_type_snap.has_field(field_name):
        return EvaluateValueResult.for_error(create_field_not_defined_error(context, field_name))

    field_snap = context.config_type_snap.get_field(field_name)

    child_evaluate_value_result = _validate_config(
        context.for_field_snap(field_snap),
        # This is a very particular special case where we want someone
        # to be able to select a selector key *without* a value
        #
        # e.g.
        # storage:
        #   filesystem:
        #
        # And we want the default values of the child elements of filesystem:
        # to "fill in"
        {}
        if field_value is None
        and ConfigTypeKind.has_fields(
            context.config_schema_snapshot.get_config_snap(field_snap.type_key).kind
        )
        else field_value,
    )

    if child_evaluate_value_result.success:
        return EvaluateValueResult.for_value(
            frozendict({field_name: child_evaluate_value_result.value})
        )
    else:
        return child_evaluate_value_result


def _validate_shape_config(context, config_value, check_for_extra_incoming_fields):
    check.inst_param(context, "context", ValidationContext)
    check.not_none_param(config_value, "config_value")
    check.bool_param(check_for_extra_incoming_fields, "check_for_extra_incoming_fields")

    if config_value and not isinstance(config_value, dict):
        return EvaluateValueResult.for_error(create_dict_type_mismatch_error(context, config_value))

    field_snaps = context.config_type_snap.fields
    defined_field_names = {fs.name for fs in field_snaps}

    incoming_field_names = set(config_value.keys())

    errors = []

    if check_for_extra_incoming_fields:
        _append_if_error(
            errors,
            _check_for_extra_incoming_fields(context, defined_field_names, incoming_field_names),
        )

    _append_if_error(
        errors, _compute_missing_fields_error(context, field_snaps, incoming_field_names)
    )

    # dict is well-formed. now recursively validate all incoming fields

    field_errors = []
    for field_snap in context.config_type_snap.fields:
        name = field_snap.name
        if name in config_value:
            field_evr = _validate_config(context.for_field_snap(field_snap), config_value[name])

            if field_evr.errors:
                field_errors += field_evr.errors

    if field_errors:
        errors += field_errors

    if errors:
        return EvaluateValueResult.for_errors(errors)
    else:
        return EvaluateValueResult.for_value(frozendict(config_value))


def validate_permissive_shape_config(context, config_value):
    check.inst_param(context, "context", ValidationContext)
    check.invariant(context.config_type_snap.kind == ConfigTypeKind.PERMISSIVE_SHAPE)
    check.not_none_param(config_value, "config_value")

    return _validate_shape_config(context, config_value, check_for_extra_incoming_fields=False)


def validate_shape_config(context, config_value):
    check.inst_param(context, "context", ValidationContext)
    check.invariant(context.config_type_snap.kind == ConfigTypeKind.STRICT_SHAPE)
    check.not_none_param(config_value, "config_value")

    return _validate_shape_config(context, config_value, check_for_extra_incoming_fields=True)


def _append_if_error(errors, maybe_error):
    if maybe_error:
        errors.append(maybe_error)


def _check_for_extra_incoming_fields(context, defined_field_names, incoming_field_names):
    extra_fields = list(incoming_field_names - defined_field_names)

    if extra_fields:
        if len(extra_fields) == 1:
            return create_field_not_defined_error(context, extra_fields[0])
        else:
            return create_fields_not_defined_error(context, extra_fields)


def _compute_missing_fields_error(context, field_snaps, incoming_fields):
    missing_fields = []

    for field_snap in field_snaps:
        if field_snap.is_required and field_snap.name not in incoming_fields:
            missing_fields.append(field_snap.name)

    if missing_fields:
        if len(missing_fields) == 1:
            return create_missing_required_field_error(context, missing_fields[0])
        else:
            return create_missing_required_fields_error(context, missing_fields)


def validate_array_config(context, config_value):
    check.inst_param(context, "context", ValidationContext)
    check.invariant(context.config_type_snap.kind == ConfigTypeKind.ARRAY)
    check.not_none_param(config_value, "config_value")

    if not isinstance(config_value, list):
        return EvaluateValueResult.for_error(create_array_error(context, config_value))

    evaluation_results = [
        _validate_config(context.for_array(index), config_item)
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
    check.inst_param(context, "context", ValidationContext)
    check.invariant(context.config_type_snap.kind == ConfigTypeKind.ENUM)
    check.not_none_param(config_value, "config_value")

    if not isinstance(config_value, str):
        return EvaluateValueResult.for_error(create_enum_type_mismatch_error(context, config_value))

    if not context.config_type_snap.has_enum_value(config_value):
        return EvaluateValueResult.for_error(create_enum_value_missing_error(context, config_value))

    return EvaluateValueResult.for_value(config_value)


def process_config(config_type, config_dict) -> EvaluateValueResult:
    config_type = resolve_to_config_type(config_type)
    validate_evr = validate_config(config_type, config_dict)
    if not validate_evr.success:
        return validate_evr

    return post_process_config(config_type, validate_evr.value)
