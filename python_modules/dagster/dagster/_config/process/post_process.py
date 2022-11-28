import sys
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, TypeVar, cast

import dagster._check as check
from dagster._utils import frozendict, frozenlist, single_item_dict_to_tuple
from dagster._utils.error import serializable_error_info_from_exc_info

from .config_type import ConfigType, ConfigTypeKind
from .errors import EvaluationError, PostProcessingError, create_failed_post_processing_error
from .evaluate_value_result import EvaluateValueResult
from .stack import EvaluationStack
from .traversal_context import TraversalContext, TraversalType

T = TypeVar("T")


def post_process_config(config_type: ConfigType, config_value: Any) -> EvaluateValueResult[Any]:
    ctx = TraversalContext.from_config_type(
        config_type=check.inst_param(config_type, "config_type", ConfigType),
        stack=EvaluationStack(entries=[]),
        traversal_type=TraversalType.RESOLVE_DEFAULTS_AND_CALL_POSTPROCESS_HOOKS,
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


def _post_process(context: TraversalContext, config_value: Any) -> EvaluateValueResult[Any]:
    try:
        new_value = context.config_type.post_process(config_value)
        return EvaluateValueResult.for_value(new_value)
    except PostProcessingError:
        error_data = serializable_error_info_from_exc_info(sys.exc_info())
        return EvaluateValueResult.for_error(
            create_failed_post_processing_error(context, config_value, error_data)
        )


def _handle(context: TraversalContext, config_value: Any) -> EvaluateValueResult[Any]:
    kind = context.config_type.kind

    if kind == ConfigTypeKind.SCALAR:
        return _handle_scalar(context, config_value)
    elif kind == ConfigTypeKind.ENUM:
        return _handle_enum(context, config_value)
    elif kind == ConfigTypeKind.SELECTOR:
        return _handle_selector(context, config_value)
    elif ConfigTypeKind.is_shape(kind):
        return _handle_shape(context, config_value)
    elif kind == ConfigTypeKind.ARRAY:
        return _handle_array(context, config_value)
    elif kind == ConfigTypeKind.MAP:
        return _handle_map(context, config_value)
    elif kind == ConfigTypeKind.NONEABLE:
        if config_value is None:
            return EvaluateValueResult.for_value(None)
        else:
            return _handle(context.for_nullable_inner_type(), config_value)
    elif kind == ConfigTypeKind.ANY:
        return EvaluateValueResult.for_value(config_value)
    elif context.config_type.kind == ConfigTypeKind.SCALAR_UNION:
        return _handle_scalar_union(context, config_value)
    else:
        check.failed(f"Unsupported type {context.config_type.key}")


def _handle_scalar(_context: TraversalContext, value: T) -> EvaluateValueResult[T]:
    return EvaluateValueResult.valid(value)


def _handle_enum(_context: TraversalContext, value: T) -> EvaluateValueResult[T]:
    return EvaluateValueResult.valid(value)


def _handle_selector(
    context: TraversalContext, value: Mapping[str, Any]
) -> EvaluateValueResult[Any]:

    if value:
        field_name, field_value = single_item_dict_to_tuple(value)
        field_def = context.config_type.fields[field_name]
    else:
        field_name, field_def = single_item_dict_to_tuple(context.config_type.fields)
        if field_def.default_provided:
            field_value = field_def.default_value
        elif ConfigTypeKind.has_fields(field_def.config_type.kind):
            field_value = {}
        else:
            field_value = None

    child_result = _handle(context.for_field(field_def, field_name), field_value)
    processed_value = frozendict({field_name: child_result.value})
    return _package_result(processed_value, child_result.errors)

def _handle_shape(
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

    resolved_values: Dict[str, object] = {}
    for expected_field, field_def in fields.items():
        alias = field_aliases.get(expected_field)
        if expected_field in incoming_fields:
            resolved_values[expected_field] = config_value[expected_field]
        elif alias is not None and alias in incoming_fields:
            resolved_values[expected_field] = config_value[alias]
        elif field_def.default_provided:
            resolved_values[expected_field] = field_def.default_value
        elif field_def.is_required:
            check.failed("Missing required composite member not caught in validation")

    child_results: Dict[str, EvaluateValueResult[Any]] = {}
    for field_name, field_value in resolved_values.items():
        child_results[field_name] = _handle(
            context.for_field(fields[field_name], field_name),
            field_value,
        )

    # For permissive composite fields, we skip applying defaults because these fields are unknown
    # to us
    if context.config_type.kind == ConfigTypeKind.PERMISSIVE_SHAPE:
        for field_name in incoming_fields:
            if field_name not in fields and field_name not in field_aliases:
                child_results[field_name] = EvaluateValueResult.valid(config_value[field_name])


    errors = _gather_child_errors(child_results.values())
    processed_value = frozendict({key: result.value for key, result in child_results.items()})
    return _package_result(processed_value, errors)


def _handle_map(context: TraversalContext, value: Any) -> EvaluateValueResult[Any]:
    value = value or {}

    child_results = {
        key: _handle(context.for_map(key), item) for key, item in value.items()
    }

    errors = _gather_child_errors(child_results.values())
    processed_value = frozendict({key: result.value for key, result in child_results.items()})
    return _package_result(processed_value, errors)

def _handle_array(context: TraversalContext, value: Any) -> EvaluateValueResult[Any]:
    value = value or []

    child_results = [
        _handle(context.for_array_element(idx), item) for idx, item in enumerate(value)
    ]

    errors = _gather_child_errors(child_results)
    processed_value = frozenlist([result.value for result in child_results])
    return _package_result(processed_value, errors)


def _handle_scalar_union(context: TraversalContext, value: Any) -> EvaluateValueResult[Any]:
    if isinstance(value, dict) or isinstance(value, list):
        return _handle(
            context.for_new_config_type(context.config_type.non_scalar_type), value
        )
    else:
        return _handle(
            context.for_new_config_type(context.config_type.scalar_type), value
        )

def _gather_child_errors(child_results: Iterable[EvaluateValueResult[Any]]) -> Sequence[EvaluationError]:
    errors: List[EvaluationError] = []
    for result in child_results:
        if not result.success:
            errors.extend(result.errors)
    return errors

def _package_result(value: T, errors: Sequence[EvaluationError]) -> EvaluateValueResult[T]:
    if len(errors) == 0:
        return EvaluateValueResult.valid(value)
    else:
        return EvaluateValueResult.invalid(value, *errors)

class DefaultResolutionContext(TraversalContext):
    __slots__ = ["_config_type", "_traversal_type", "_all_config_types"]

    def __init__(
        self,
        config_schema_snapshot: ConfigSchemaSnap,
        config_type_snap: ConfigTypeSnap,
        config_type: ConfigType,
        stack: EvaluationStack,
        traversal_type: TraversalType,
    ):
        super(TraversalContext, self).__init__(
            config_schema_snapshot=config_schema_snapshot,
            config_type_snap=config_type_snap,
            stack=stack,
        )
        self._config_type = check.inst_param(config_type, "config_type", ConfigType)
        self._traversal_type = check.inst_param(traversal_type, "traversal_type", TraversalType)

    @staticmethod
    def from_config_type(
        config_type: ConfigType,
        stack: EvaluationStack,
        traversal_type: TraversalType,
    ) -> "TraversalContext":
        return TraversalContext(
            config_schema_snapshot=config_type.get_schema_snapshot(),
            config_type_snap=config_type.get_snapshot(),
            config_type=config_type,
            stack=stack,
            traversal_type=traversal_type,
        )

    @property
    def config_type(self) -> ConfigType:
        return self._config_type

    @property
    def traversal_type(self) -> TraversalType:
        return self._traversal_type

    @property
    def do_post_process(self) -> bool:
        return self.traversal_type == TraversalType.RESOLVE_DEFAULTS_AND_POSTPROCESS

    def for_array_element(self, index: int) -> "TraversalContext":
        check.int_param(index, "index")
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_type_snap(
                self.config_type_snap.inner_type_key
            ),
            config_type=self.config_type.inner_type,  # type: ignore
            stack=self.stack.for_array_element(index),
            traversal_type=self.traversal_type,
        )

    def for_map(self, key: object) -> "TraversalContext":
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_type_snap(
                self.config_type_snap.inner_type_key
            ),
            config_type=self.config_type.inner_type,  # type: ignore
            stack=self.stack.for_map_value(key),
            traversal_type=self.traversal_type,
        )

    def for_field(self, field_def: Field, field_name: str) -> "TraversalContext":
        check.inst_param(field_def, "field_def", Field)
        check.str_param(field_name, "field_name")
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_type_snap(
                field_def.config_type.key
            ),
            config_type=field_def.config_type,
            stack=self.stack.for_field(field_name),
            traversal_type=self.traversal_type,
        )

    def for_nullable_inner_type(self) -> "TraversalContext":
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_type_snap(
                self.config_type_snap.inner_type_key
            ),
            config_type=self.config_type.inner_type,  # type: ignore
            stack=self.stack,
            traversal_type=self.traversal_type,
        )

    def for_new_config_type(self, config_type: ConfigType) -> "TraversalContext":
        return TraversalContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_type_snap(config_type.key),
            config_type=config_type,
            stack=self.stack,
            traversal_type=self.traversal_type,
        )
