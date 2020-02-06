from dagster import check
from dagster.utils import ensure_single_item, frozendict, frozenlist

from .config_type import ConfigType, ConfigTypeKind
from .evaluate_value_result import EvaluateValueResult
from .stack import EvaluationStack
from .validation_context import ValidationContext


def post_process_config(config_type, config_value):
    ctx = ValidationContext(
        config_type=check.inst_param(config_type, 'config_type', ConfigType),
        stack=EvaluationStack(config_type=config_type, entries=[]),
    )
    return _post_process_config(ctx, config_value)


def _post_process_config(context, config_value):
    kind = context.config_type.kind

    if kind == ConfigTypeKind.SCALAR:
        return EvaluateValueResult.for_value(config_value)
    elif kind == ConfigTypeKind.ENUM:
        return EvaluateValueResult.for_value(context.config_type.to_python_value(config_value))
    elif kind == ConfigTypeKind.SELECTOR:
        return _post_process_config_to_selector(context, config_value)
    elif ConfigTypeKind.is_shape(kind):
        return _post_process_shape_config(context, config_value)
    elif kind == ConfigTypeKind.ARRAY:
        return _post_process_array_config(context, config_value)
    elif kind == ConfigTypeKind.NONEABLE:
        if config_value is None:
            return EvaluateValueResult.for_value(None)
        return _post_process_config(context.for_nullable_inner_type(), config_value)
    elif kind == ConfigTypeKind.ANY:
        return EvaluateValueResult.for_value(config_value)
    elif context.config_type.kind == ConfigTypeKind.SCALAR_UNION:
        return _post_process_scalar_union_type(context, config_value)
    else:
        check.failed('Unsupported type {name}'.format(name=context.config_type.name))


def _post_process_scalar_union_type(context, config_value):
    if isinstance(config_value, dict) or isinstance(config_value, list):
        return _post_process_config(
            context.for_new_config_type(context.config_type.non_scalar_type), config_value
        )
    else:
        return _post_process_config(
            context.for_new_config_type(context.config_type.scalar_type), config_value
        )


def _post_process_config_to_selector(context, config_value):
    check.invariant(
        context.config_type.kind == ConfigTypeKind.SELECTOR,
        'Non-selector not caught in validation',
    )

    if config_value:
        check.invariant(config_value and len(config_value) == 1)
        field_name, incoming_field_value = ensure_single_item(config_value)
    else:
        field_name, field_def = ensure_single_item(context.config_type.fields)
        incoming_field_value = field_def.default_value if field_def.default_provided else None

    field_def = context.config_type.fields[field_name]

    field_evr = _post_process_config(
        context.for_field(field_def, field_name),
        {}
        if incoming_field_value is None and ConfigTypeKind.has_fields(field_def.config_type.kind)
        else incoming_field_value,
    )
    if field_evr.success:
        return EvaluateValueResult.for_value(frozendict({field_name: field_evr.value}))

    return field_evr


def _post_process_shape_config(context, config_value):
    check.invariant(ConfigTypeKind.is_shape(context.config_type.kind), 'Unexpected non shape type')
    config_value = check.opt_dict_param(config_value, 'config_value', key_type=str)

    fields = context.config_type.fields
    incoming_fields = set(config_value.keys())

    processed_fields = {}

    for expected_field, field_def in fields.items():
        if expected_field in incoming_fields:
            processed_fields[expected_field] = _post_process_config(
                context.for_field(field_def, expected_field), config_value[expected_field]
            )

        elif field_def.default_provided:
            processed_fields[expected_field] = _post_process_config(
                context.for_field(field_def, expected_field), field_def.default_value
            )

        elif not field_def.is_optional:
            check.failed('Missing non-optional composite member not caught in validation')

    # For permissive composite fields, we skip applying defaults because these fields are unknown
    # to us

    if context.config_type.kind == ConfigTypeKind.PERMISSIVE_SHAPE:
        defined_fields = set(fields.keys())
        extra_fields = incoming_fields - defined_fields
        for extra_field in extra_fields:
            processed_fields[extra_field] = EvaluateValueResult.for_value(config_value[extra_field])

    errors = [result.error for result in processed_fields.values() if not result.success]
    if errors:
        return EvaluateValueResult.for_errors(errors)
    return EvaluateValueResult.for_value(
        frozendict({key: result.value for key, result in processed_fields.items()})
    )


def _post_process_array_config(context, config_value):
    check.invariant(context.config_type.kind == ConfigTypeKind.ARRAY, 'Unexpected non array type')

    if not config_value:
        return EvaluateValueResult.for_value([])

    if context.config_type.inner_type.kind != ConfigTypeKind.NONEABLE:
        if any((cv is None for cv in config_value)):
            check.failed('Null array member not caught in validation')

    results = [
        _post_process_config(context.for_array(idx), item) for idx, item in enumerate(config_value)
    ]

    errors = [result.error for result in results if not result.success]
    if errors:
        return EvaluateValueResult.for_errors(errors)

    return EvaluateValueResult.for_value(frozenlist([result.value for result in results]))
