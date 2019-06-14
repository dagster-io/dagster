import six

from dagster import check
from dagster.utils import single_item

from .errors import (
    create_composite_type_mismatch_error,
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
from .stack import get_friendly_path_info
from .traversal_context import TraversalContext


def _validate_config(context):
    check.inst_param(context, 'context', TraversalContext)

    if context.config_type.is_scalar:
        if not context.config_type.is_config_scalar_valid(context.config_value):
            context.add_error(create_scalar_error(context))
        return None

    elif context.config_type.is_any:
        # no-op: we're safe
        return context.config_value

    elif context.config_type.is_selector:
        return validate_selector_config_value(context)
    elif context.config_type.is_composite:
        return validate_composite_config_value(context)
    elif context.config_type.is_list:
        return validate_list_value(context)
    elif context.config_type.is_nullable:
        if context.config_value is not None:
            return _validate_config(
                TraversalContext(
                    context.config_type.inner_type,
                    context.config_value,
                    context.stack,
                    context.errors,
                )
            )
        return None
    elif context.config_type.is_enum:
        return validate_enum_value(context)
    else:
        check.failed('Unsupported type {name}'.format(name=context.config_type.name))


def validate_enum_value(context):
    check.inst_param(context, 'context', TraversalContext)
    check.param_invariant(context.config_type.is_enum, 'enum_type')

    if not isinstance(context.config_value, six.string_types):
        context.add_error(create_enum_type_mismatch_error(context))
        return None

    if not context.config_type.is_valid_config_enum_value(context.config_value):
        context.add_error(create_enum_value_missing_error(context))
        return None


## Selectors


def validate_selector_config_value(context):
    check.inst_param(context, 'context', TraversalContext)
    check.param_invariant(context.config_type.is_selector, 'selector_type')

    if context.config_value and not isinstance(context.config_value, dict):
        context.add_error(create_selector_type_error(context))
        return None

    if context.config_value and len(context.config_value) > 1:
        context.add_error(create_selector_multiple_fields_error(context))
        return None

    elif not context.config_value:
        if len(context.config_type.fields) > 1:
            context.add_error(create_selector_multiple_fields_no_field_selected_error(context))
            return None

        field_name, field_def = single_item(context.config_type.fields)

        if not field_def.is_optional:
            context.add_error(create_selector_unspecified_value_error(context))
            return None

        incoming_field_value = field_def.default_value if field_def.default_provided else None

    else:
        check.invariant(context.config_value and len(context.config_value) == 1)

        field_name, incoming_field_value = single_item(context.config_value)
        if field_name not in context.config_type.fields:
            context.add_error(create_field_not_defined_error(context, field_name))
            return None

    parent_field = context.config_type.fields[field_name]
    _validate_config(
        TraversalContext(
            parent_field.config_type,
            incoming_field_value,
            context.stack.with_field(field_name, parent_field),
            context.errors,
        )
    )


## Composites


def validate_composite_config_value(context):
    check.inst_param(context, 'context', TraversalContext)
    check.param_invariant(context.config_type.is_composite, 'composite_type')

    _, _path = get_friendly_path_info(context.stack)

    if context.config_value and not isinstance(context.config_value, dict):
        context.add_error(create_composite_type_mismatch_error(context))
        return None

    # ASK: this can crash on user error
    config_value = check.opt_dict_param(context.config_value, 'incoming_value', key_type=str)

    fields = context.config_type.fields

    defined_fields = set(fields.keys())
    incoming_fields = set(config_value.keys())
    extra_fields = list(incoming_fields - defined_fields)

    # Here, we support permissive composites. In cases where we know the set of permissible keys a
    # priori, we validate against the config. For permissive composites, we give the user an escape
    # hatch where they can specify arbitrary fields...
    if not context.config_type.is_permissive_composite:
        if extra_fields:
            if len(extra_fields) == 1:
                context.add_error(create_field_not_defined_error(context, extra_fields[0]))
            else:
                context.add_error(create_fields_not_defined_error(context, extra_fields))

    # ...However, for any fields the user *has* told us about, we validate against their config
    # specifications
    missing_fields = []
    for expected_field, field_def in fields.items():
        if expected_field in incoming_fields:
            _validate_config(
                TraversalContext(
                    field_def.config_type,
                    context.config_value[expected_field],
                    context.stack.with_field(expected_field, field_def),
                    context.errors,
                )
            )
        elif field_def.is_optional:
            pass

        else:
            check.invariant(not field_def.default_provided)
            missing_fields.append(expected_field)

    if missing_fields:
        if len(missing_fields) == 1:
            err = create_missing_required_field_error(context, missing_fields[0])
        else:
            err = create_missing_required_fields_error(context, missing_fields)
        context.add_error(err)


## Lists


def validate_list_value(context):
    check.inst_param(context, 'context', TraversalContext)
    check.param_invariant(context.config_type.is_list, 'list_type')

    config_type = context.config_type
    config_value = context.config_value

    if not isinstance(config_value, list):
        context.add_error(create_list_error(context))
        return None

    return [
        _validate_config(
            TraversalContext(
                config_type.inner_type, item, context.stack.with_list_index(index), context.errors
            )
        )
        for index, item in enumerate(config_value)
    ]
