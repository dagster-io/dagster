from dagster import check
from dagster.utils import single_item

from .config import ConfigType


def apply_default_values(config_type, config_value):
    check.inst_param(config_type, 'config_type', ConfigType)

    if config_type.is_scalar:
        return config_value
    elif config_type.is_enum:
        return config_type.to_python_value(config_value)
    elif config_type.is_selector:
        return apply_default_values_to_selector(config_type, config_value)
    elif config_type.is_composite:
        return apply_defaults_to_composite_type(config_type, config_value)
    elif config_type.is_list:
        return apply_defaults_to_list_type(config_type, config_value)
    elif config_type.is_nullable:
        if config_value is None:
            return None
        return apply_default_values(config_type.inner_type, config_value)
    elif config_type.is_any:
        return config_value
    else:
        check.failed('Unsupported type {name}'.format(name=config_type.name))


def apply_default_values_to_selector(selector_type, config_value):
    check.param_invariant(
        selector_type.is_selector, 'selector_type', 'Non-selector not caught in validation'
    )

    if config_value:
        check.invariant(config_value and len(config_value) == 1)
        field_name, incoming_field_value = single_item(config_value)
    else:
        field_name, field_def = single_item(selector_type.fields)
        incoming_field_value = field_def.default_value if field_def.default_provided else None

    parent_field = selector_type.fields[field_name]
    field_value = apply_default_values(parent_field.config_type, incoming_field_value)
    return {field_name: field_value}


def apply_defaults_to_composite_type(composite_type, config_value):
    check.param_invariant(composite_type.is_composite, 'composite_type')
    config_value = check.opt_dict_param(config_value, 'config_value', key_type=str)

    fields = composite_type.fields
    incoming_fields = set(config_value.keys())

    processed_fields = {}

    for expected_field, field_def in fields.items():
        if expected_field in incoming_fields:
            processed_fields[expected_field] = apply_default_values(
                field_def.config_type, config_value[expected_field]
            )

        elif field_def.default_provided:
            processed_fields[expected_field] = field_def.default_value

        elif not field_def.is_optional:
            check.failed('Missing non-optional composite member not caught in validation')

    # For permissive composite fields, we skip applying defaults because these fields are unknown
    # to us
    if composite_type.is_permissive_composite:
        defined_fields = set(fields.keys())
        extra_fields = incoming_fields - defined_fields
        for extra_field in extra_fields:
            processed_fields[extra_field] = config_value[extra_field]

    return processed_fields


def apply_defaults_to_list_type(list_type, config_value):
    check.param_invariant(list_type.is_list, 'list_type')

    if not config_value:
        return []

    if not list_type.inner_type.is_nullable:
        if any((cv is None for cv in config_value)):
            check.failed('Null list member not caught in validation')

    return [apply_default_values(list_type.inner_type, item) for item in config_value]
