import sys
from typing import Any, Dict, List, Mapping, Optional, cast

import dagster._check as check
from dagster._utils import ensure_single_item, frozendict, frozenlist
from dagster._utils.error import serializable_error_info_from_exc_info

from .config_type import ConfigType, ConfigTypeKind
from .errors import EvaluationError, PostProcessingError, create_failed_post_processing_error
from .evaluate_value_result import EvaluateValueResult
from .stack import EvaluationStack
from .traversal_context import TraversalContext, TraversalType


def post_process_config(config_type: ConfigType, config_value: Any) -> EvaluateValueResult[Any]:
    ctx = TraversalContext.from_config_type(
        config_type=check.inst_param(config_type, "config_type", ConfigType),
        stack=EvaluationStack(entries=[]),
        traversal_type=TraversalType.RESOLVE_DEFAULTS_AND_POSTPROCESS,
    )
    return _recursively_process_config(ctx, config_value)


def resolve_defaults(config_type: ConfigType, config_value: Any) -> EvaluateValueResult[Any]:
    ctx = TraversalContext.from_config_type(
        config_type=check.inst_param(config_type, "config_type", ConfigType),
        stack=EvaluationStack(entries=[]),
        traversal_type=TraversalType.RESOLVE_DEFAULTS,
    )

    return _recursively_process_config(ctx, config_value)


def _recursively_process_config(
    context: TraversalContext, config_value: Any
) -> EvaluateValueResult[Any]:
    evr = _recursively_resolve_defaults(context, config_value)

    if evr.success:
        if not context.do_post_process:
            return evr
        return _post_process(context, evr.value)
    else:
        return evr


def _recursively_resolve_defaults(  # type: ignore # mypy missing check.failed NoReturn
    context: TraversalContext, config_value: Any
) -> EvaluateValueResult[Any]:
    kind = context.config_type.kind

    if kind == ConfigTypeKind.SCALAR:
        return EvaluateValueResult.for_value(config_value)
    elif kind == ConfigTypeKind.ENUM:
        return EvaluateValueResult.for_value(config_value)
    elif kind == ConfigTypeKind.SELECTOR:
        return _recurse_in_to_selector(context, config_value)
    elif ConfigTypeKind.is_shape(kind):
        return _recurse_in_to_shape(context, config_value)
    elif kind == ConfigTypeKind.ARRAY:
        return _recurse_in_to_array(context, config_value)
    elif kind == ConfigTypeKind.MAP:
        return _recurse_in_to_map(context, config_value)
    elif kind == ConfigTypeKind.NONEABLE:
        if config_value is None:
            return EvaluateValueResult.for_value(None)
        else:
            return _recursively_process_config(context.for_nullable_inner_type(), config_value)
    elif kind == ConfigTypeKind.ANY:
        return EvaluateValueResult.for_value(config_value)
    elif context.config_type.kind == ConfigTypeKind.SCALAR_UNION:
        return _recurse_in_to_scalar_union(context, config_value)
    else:
        check.failed(f"Unsupported type {context.config_type.key}")


def _post_process(context: TraversalContext, config_value: Any) -> EvaluateValueResult[Any]:
    try:
        new_value = context.config_type.post_process(config_value)
        return EvaluateValueResult.for_value(new_value)
    except PostProcessingError:
        error_data = serializable_error_info_from_exc_info(sys.exc_info())
        return EvaluateValueResult.for_error(
            create_failed_post_processing_error(context, config_value, error_data)
        )


def _recurse_in_to_scalar_union(
    context: TraversalContext, config_value: Any
) -> EvaluateValueResult[Any]:
    if isinstance(config_value, dict) or isinstance(config_value, list):
        return _recursively_process_config(
            context.for_new_config_type(context.config_type.non_scalar_type), config_value  # type: ignore
        )
    else:
        return _recursively_process_config(
            context.for_new_config_type(context.config_type.scalar_type), config_value  # type: ignore
        )


def _recurse_in_to_selector(
    context: TraversalContext, config_value: Mapping[str, Any]
) -> EvaluateValueResult[Any]:
    check.invariant(
        context.config_type.kind == ConfigTypeKind.SELECTOR,
        "Non-selector not caught in validation",
    )

    if config_value:
        check.invariant(config_value and len(config_value) == 1)
        field_name, incoming_field_value = ensure_single_item(config_value)
    else:
        field_name, field_def = ensure_single_item(context.config_type.fields)  # type: ignore
        incoming_field_value = field_def.default_value if field_def.default_provided else None

    field_def = context.config_type.fields[field_name]  # type: ignore

    field_evr = _recursively_process_config(
        context.for_field(field_def, field_name),
        {}
        if incoming_field_value is None and ConfigTypeKind.has_fields(field_def.config_type.kind)
        else incoming_field_value,
    )
    if field_evr.success:
        return EvaluateValueResult.for_value(frozendict({field_name: field_evr.value}))

    return field_evr


def _recurse_in_to_shape(
    context: TraversalContext, config_value: Optional[Mapping[str, object]]
) -> EvaluateValueResult[Any]:
    check.invariant(ConfigTypeKind.is_shape(context.config_type.kind), "Unexpected non shape type")
    config_value = check.opt_mapping_param(config_value, "config_value", key_type=str)

    fields = context.config_type.fields  # type: ignore

    field_aliases: Dict[str, str] = check.opt_dict_param(
        getattr(context.config_type, "field_aliases", None),
        "field_aliases",
        key_type=str,
        value_type=str,
    )

    incoming_fields = config_value.keys()

    processed_fields = {}

    for expected_field, field_def in fields.items():
        if expected_field in incoming_fields:
            processed_fields[expected_field] = _recursively_process_config(
                context.for_field(field_def, expected_field),
                config_value[expected_field],
            )
        elif expected_field in field_aliases and field_aliases[expected_field] in incoming_fields:
            processed_fields[expected_field] = _recursively_process_config(
                context.for_field(field_def, expected_field),
                config_value[field_aliases[expected_field]],
            )

        elif field_def.default_provided:
            processed_fields[expected_field] = _recursively_process_config(
                context.for_field(field_def, expected_field), field_def.default_value
            )

        elif field_def.is_required:
            check.failed("Missing required composite member not caught in validation")

    # For permissive composite fields, we skip applying defaults because these fields are unknown
    # to us
    if context.config_type.kind == ConfigTypeKind.PERMISSIVE_SHAPE:
        defined_fields = fields.keys()
        extra_fields = [field for field in incoming_fields if field not in defined_fields]
        for extra_field in extra_fields:
            processed_fields[extra_field] = EvaluateValueResult.for_value(config_value[extra_field])

    errors: List[EvaluationError] = []
    for result in processed_fields.values():
        if not result.success:
            errors.extend(check.not_none(result.errors))

    if errors:
        return EvaluateValueResult.for_errors(errors)

    return EvaluateValueResult.for_value(
        frozendict({key: result.value for key, result in processed_fields.items()})
    )


def _recurse_in_to_array(context: TraversalContext, config_value: Any) -> EvaluateValueResult[Any]:
    check.invariant(context.config_type.kind == ConfigTypeKind.ARRAY, "Unexpected non array type")

    if not config_value:
        return EvaluateValueResult.for_value([])

    if context.config_type.inner_type.kind != ConfigTypeKind.NONEABLE:  # type: ignore
        if any((cv is None for cv in config_value)):
            check.failed("Null array member not caught in validation")

    results = [
        _recursively_process_config(context.for_array(idx), item)
        for idx, item in enumerate(config_value)
    ]

    errors: List[EvaluationError] = []
    for result in results:
        if not result.success:
            errors.extend(check.not_none(result.errors))

    if errors:
        return EvaluateValueResult.for_errors(errors)

    return EvaluateValueResult.for_value(frozenlist([result.value for result in results]))


def _recurse_in_to_map(context: TraversalContext, config_value: Any) -> EvaluateValueResult[Any]:
    check.invariant(
        context.config_type.kind == ConfigTypeKind.MAP,
        "Unexpected non map type",
    )

    if not config_value:
        return EvaluateValueResult.for_value({})

    config_value = cast(Dict[object, object], config_value)

    if any((ck is None for ck in config_value.keys())):
        check.failed("Null map key not caught in validation")
    if context.config_type.inner_type.kind != ConfigTypeKind.NONEABLE:  # type: ignore
        if any((cv is None for cv in config_value.values())):
            check.failed("Null map member not caught in validation")

    results = {
        key: _recursively_process_config(context.for_map(key), item)
        for key, item in config_value.items()
    }

    errors: List[EvaluationError] = []
    for result in results.values():
        if not result.success:
            errors.extend(check.not_none(result.errors))

    if errors:
        return EvaluateValueResult.for_errors(errors)

    return EvaluateValueResult.for_value(
        frozendict({key: result.value for key, result in results.items()})
    )
