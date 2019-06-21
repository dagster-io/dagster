import copy

from collections import namedtuple

import six

from dagster import check
from dagster.core.definitions.environment_configs import is_solid_container_config
from dagster.core.definitions.solid import CompositeSolidDefinition
from dagster.core.errors import user_code_error_boundary, DagsterUserCodeExecutionError
from dagster.core.types.config import ConfigType
from dagster.utils import single_item

from .errors import (
    create_bad_mapping_error,
    create_bad_mapping_solids_key_error,
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
from .stack import get_friendly_path_msg, EvaluationStack
from .traversal_context import TraversalContext


def evaluate_config(config_type, config_value, pipeline=None, seen_handles=None):
    check.inst_param(config_type, 'config_type', ConfigType)

    errors = []
    stack = EvaluationStack(config_type=config_type, entries=[])

    value = _evaluate_config(
        TraversalContext(config_type, config_value, stack, errors, pipeline, seen_handles)
    )

    return (errors, value)


def _evaluate_config(context):
    check.inst_param(context, 'context', TraversalContext)

    if context.config_type.is_scalar:
        if not context.config_type.is_config_scalar_valid(context.config_value):
            context.add_error(create_scalar_error(context))
            return None
        return context.config_value

    elif context.config_type.is_any:
        return context.config_value  # yolo

    elif context.config_type.is_selector:
        return evaluate_selector_config(context)

    elif context.config_type.is_composite:
        return evaluate_composite_config(context)

    elif context.config_type.is_list:
        return evaluate_list_config(context)

    elif context.config_type.is_nullable:
        if context.config_value is not None:
            return _evaluate_config(context.for_nullable_inner_type())
        return None

    elif context.config_type.is_enum:
        return evaluate_enum_config(context)

    else:
        check.failed('Unsupported type {name}'.format(name=context.config_type.name))


def evaluate_enum_config(context):
    check.inst_param(context, 'context', TraversalContext)
    check.param_invariant(context.config_type.is_enum, 'enum_type')

    if not isinstance(context.config_value, six.string_types):
        context.add_error(create_enum_type_mismatch_error(context))
        return None

    if not context.config_type.is_valid_config_enum_value(context.config_value):
        context.add_error(create_enum_value_missing_error(context))
        return None

    return context.config_type.to_python_value(context.config_value)


## Selectors


def evaluate_selector_config(context):
    check.inst_param(context, 'context', TraversalContext)
    check.param_invariant(context.config_type.is_selector, 'selector_type')

    if context.config_value:
        if not isinstance(context.config_value, dict):
            context.add_error(create_selector_type_error(context))
            return None

        if len(context.config_value) > 1:
            context.add_error(create_selector_multiple_fields_error(context))
            return None

        field_name, incoming_field_value = single_item(context.config_value)
        if field_name not in context.config_type.fields:
            context.add_error(create_field_not_defined_error(context, field_name))
            return None

    else:
        if len(context.config_type.fields) > 1:
            context.add_error(create_selector_multiple_fields_no_field_selected_error(context))
            return None

        field_name, field_def = single_item(context.config_type.fields)

        if not field_def.is_optional:
            context.add_error(create_selector_unspecified_value_error(context))
            return None

        incoming_field_value = field_def.default_value if field_def.default_provided else None

    field_def = context.config_type.fields[field_name]

    child_value = _evaluate_config(context.for_field(field_def, field_name, incoming_field_value))

    return {field_name: child_value}


## Composites


def evaluate_composite_config(context):
    check.inst_param(context, 'context', TraversalContext)
    check.param_invariant(context.config_type.is_composite, 'composite_type')

    fields = context.config_type.fields

    if context.config_value and not isinstance(context.config_value, dict):
        context.add_error(create_composite_type_mismatch_error(context))
        return None

    result = _evaluate_composite_solid_config(context)
    if result.errors:
        for error in result.errors:
            context.add_error(error)
        return None

    if result.value:
        return result.value

    # ASK: this can crash on user error
    config_value = check.opt_dict_param(context.config_value, 'incoming_value', key_type=str)

    defined_fields = set(fields.keys())
    incoming_fields = set(config_value.keys())
    extra_fields = list(incoming_fields - defined_fields)

    # We'll build up a dict of processed config values below
    output_config_value = {}

    # Here, we support permissive composites. In cases where we know the set of permissible keys a
    # priori, we validate against the config:
    if not context.config_type.is_permissive_composite:
        if extra_fields:
            if len(extra_fields) == 1:
                context.add_error(create_field_not_defined_error(context, extra_fields[0]))
            else:
                context.add_error(create_fields_not_defined_error(context, extra_fields))

    # And for permissive fields, we just pass along to the output without further validation
    else:
        for field_name in extra_fields:
            output_config_value[field_name] = config_value[field_name]

    # ...However, for any fields the user *has* told us about, we validate against their config
    # specifications
    missing_fields = []

    for key, field_def in fields.items():
        if key in incoming_fields:
            output_config_value[key] = _evaluate_config(
                context.for_field(field_def, key, context.config_value[key])
            )

        elif field_def.is_optional:
            if field_def.default_provided:
                output_config_value[key] = field_def.default_value

        else:
            check.invariant(not field_def.default_provided)
            missing_fields.append(key)

    if missing_fields:
        if len(missing_fields) == 1:
            err = create_missing_required_field_error(context, missing_fields[0])
        else:
            err = create_missing_required_fields_error(context, missing_fields)
        context.add_error(err)

    return output_config_value


class CompositeSolidEvaluationResult(namedtuple('_CompositeSolidEvaluationResult', 'errors value')):
    def __new__(cls, errors, value):
        return super(CompositeSolidEvaluationResult, cls).__new__(
            cls, check.opt_list_param(errors, 'errors'), value
        )


def _evaluate_composite_solid_config(context):
    '''Evaluates config for a composite solid and returns CompositeSolidEvaluationResult
    '''
    # Support config mapping override functions
    if not is_solid_container_config(context.config_type):
        return CompositeSolidEvaluationResult(None, None)

    handle = context.config_type.handle

    # If we've already seen this handle, skip -- we've already run the block of code below
    if not handle or handle in context.seen_handles:
        return CompositeSolidEvaluationResult(None, None)

    solid_def = context.pipeline.get_solid(context.config_type.handle).definition

    has_mapping = isinstance(solid_def, CompositeSolidDefinition) and solid_def.has_config_mapping

    # If there's no config mapping function provided for this composite solid, bail
    if not has_mapping:
        return CompositeSolidEvaluationResult(None, None)

    # ensure we don't mutate the source environment dict
    copy_config_value = copy.deepcopy(context.config_value.get('config'))

    with user_code_error_boundary(
        DagsterUserCodeExecutionError,
        'error occurred during execution of user config mapping function {fn} defined'
        ' {path_msg}'.format(
            fn=solid_def.config_mapping.config_mapping_fn.__name__,
            path_msg=get_friendly_path_msg(context.stack),
        ),
    ):
        mapped_config_value = solid_def.config_mapping.config_mapping_fn(copy_config_value)

    if not mapped_config_value:
        return CompositeSolidEvaluationResult(None, None)

    solid_def_name = context.pipeline.get_solid(handle).definition.name

    # Perform basic validation on the mapped config value; remaining validation will happen via the
    # evaluate_config call below
    if not isinstance(mapped_config_value, dict):
        errors = [
            create_bad_mapping_error(context, solid_def_name, str(handle), mapped_config_value)
        ]
        return CompositeSolidEvaluationResult(errors, None)

    if 'solids' in context.config_value:
        errors = [create_bad_mapping_solids_key_error(context, solid_def_name, str(handle))]
        return CompositeSolidEvaluationResult(errors, None)

    # We first validate the provided environment config as normal against the composite solid config
    # schema. This will perform a full traversal rooted at the SolidContainerConfigDict and thread
    # errors up to the root
    errors, _ = evaluate_config(
        context.config_type,
        context.config_value,
        pipeline=context.pipeline,
        seen_handles=context.seen_handles + [handle],
    )
    if errors:
        return CompositeSolidEvaluationResult(errors, None)

    # We've validated the composite solid config; now validate the mapping fn overrides
    # against the config schema subtree for child solids
    errors, config_value = evaluate_config(
        context.config_type.child_solids_config_field.config_type,
        mapped_config_value,
        pipeline=context.pipeline,
        seen_handles=context.seen_handles + [handle],
    )
    if errors:
        prefix = (
            'Config override mapping function defined by solid {handle_name} from '
            'definition {solid_def_name} {path_msg} caused error: '.format(
                path_msg=get_friendly_path_msg(context.stack),
                handle_name=str(handle),
                solid_def_name=solid_def_name,
            )
        )
        errors = [e._replace(message=prefix + e.message) for e in errors]
        return CompositeSolidEvaluationResult(errors, None)

    return CompositeSolidEvaluationResult(None, {'solids': config_value})


## Lists


def evaluate_list_config(context):
    check.inst_param(context, 'context', TraversalContext)
    check.param_invariant(context.config_type.is_list, 'list_type')

    config_value = context.config_value

    if not isinstance(config_value, list):
        context.add_error(create_list_error(context))
        return None

    return [
        _evaluate_config(context.for_list(index, item)) for index, item in enumerate(config_value)
    ]
