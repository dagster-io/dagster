from dagster import check
from dagster.utils import ensure_single_item

from .config_type import ConfigType, ConfigTypeKind


def post_process_config(config_type, config_value):
    check.inst_param(config_type, 'config_type', ConfigType)

    kind = config_type.kind

    if kind == ConfigTypeKind.SCALAR:
        return config_value
    elif kind == ConfigTypeKind.ENUM:
        return config_type.to_python_value(config_value)
    elif kind == ConfigTypeKind.SELECTOR:
        return post_process_config_to_selector(config_type, config_value)
    elif ConfigTypeKind.is_shape(kind):
        return post_process_shape_config(config_type, config_value)
    elif kind == ConfigTypeKind.ARRAY:
        return post_process_array_config(config_type, config_value)
    elif kind == ConfigTypeKind.NONEABLE:
        if config_value is None:
            return None
        return post_process_config(config_type.inner_type, config_value)
    elif kind == ConfigTypeKind.ANY:
        return config_value
    elif config_type.kind == ConfigTypeKind.SCALAR_UNION:
        return post_process_scalar_union_type(config_type, config_value)
    else:
        check.failed('Unsupported type {name}'.format(name=config_type.name))


def post_process_scalar_union_type(scalar_union_type, config_value):
    if isinstance(config_value, dict) or isinstance(config_value, list):
        return post_process_config(scalar_union_type.non_scalar_type, config_value)
    else:
        return post_process_config(scalar_union_type.scalar_type, config_value)


def post_process_config_to_selector(selector_type, config_value):
    check.param_invariant(
        selector_type.kind == ConfigTypeKind.SELECTOR,
        'selector_type',
        'Non-selector not caught in validation',
    )

    if config_value:
        check.invariant(config_value and len(config_value) == 1)
        field_name, incoming_field_value = ensure_single_item(config_value)
    else:
        field_name, field_def = ensure_single_item(selector_type.fields)
        incoming_field_value = field_def.default_value if field_def.default_provided else None

    parent_field = selector_type.fields[field_name]
    field_value = post_process_config(parent_field.config_type, incoming_field_value)
    return {field_name: field_value}


def post_process_shape_config(shape_type, config_value):
    check.param_invariant(ConfigTypeKind.is_shape(shape_type.kind), 'shape_type')
    config_value = check.opt_dict_param(config_value, 'config_value', key_type=str)

    fields = shape_type.fields
    incoming_fields = set(config_value.keys())

    processed_fields = {}

    for expected_field, field_def in fields.items():
        if expected_field in incoming_fields:
            processed_fields[expected_field] = post_process_config(
                field_def.config_type, config_value[expected_field]
            )

        elif field_def.default_provided:
            processed_fields[expected_field] = field_def.default_value

        elif not field_def.is_optional:
            check.failed('Missing non-optional composite member not caught in validation')

    # For permissive composite fields, we skip applying defaults because these fields are unknown
    # to us

    if shape_type.kind == ConfigTypeKind.PERMISSIVE_SHAPE:
        defined_fields = set(fields.keys())
        extra_fields = incoming_fields - defined_fields
        for extra_field in extra_fields:
            processed_fields[extra_field] = config_value[extra_field]

    return processed_fields


def post_process_array_config(array_type, config_value):
    check.param_invariant(array_type.kind == ConfigTypeKind.ARRAY, 'array_type')

    if not config_value:
        return []

    if array_type.inner_type.kind != ConfigTypeKind.NONEABLE:
        if any((cv is None for cv in config_value)):
            check.failed('Null array member not caught in validation')

    return [post_process_config(array_type.inner_type, item) for item in config_value]
