from __future__ import annotations

from typing import List, Mapping, Optional, Sequence, TypeVar, Union, cast

from typing_extensions import TypeAlias

import dagster._check as check
from dagster._config.traversal_context import TraversalContext
from dagster._utils import frozendict, single_item_dict_to_tuple

from ..config_type import ConfigScalarKind, ConfigTypeKind, RawConfigType, normalize_config_type
from ..errors import (
    EvaluationError,
    create_array_error,
    create_dict_type_mismatch_error,
    create_enum_type_mismatch_error,
    create_enum_value_missing_error,
    create_field_not_defined_error,
    create_field_substitution_collision_error,
    create_fields_not_defined_error,
    create_map_error,
    create_missing_required_field_error,
    create_missing_required_fields_error,
    create_none_not_allowed_error,
    create_scalar_error,
    create_selector_multiple_fields_error,
    create_selector_multiple_fields_no_field_selected_error,
    create_selector_type_error,
    create_selector_unspecified_value_error,
)
from ..evaluate_value_result import EvaluateValueResult
from ..snap import ConfigFieldSnap, ConfigSchemaSnap
from ..stack import EvaluationStack

VALID_FLOAT_TYPES = tuple([int, float])

ScalarConfigValue: TypeAlias = Union[int, float, str, bool]
ConfigValue: TypeAlias = Union[
    ScalarConfigValue,
    Mapping[str, "ConfigValue"],
    Sequence["ConfigValue"],
]
NoneableConfigValue: TypeAlias = Union[None, ConfigValue]

T = TypeVar("T")


def validate_config(
    config_value: T,
    *,
    config_type: Optional[RawConfigType] = None,
    config_schema_snap: Optional[ConfigSchemaSnap] = None,
    config_type_key: Optional[str] = None,
) -> EvaluateValueResult[T]:

    if config_schema_snap is not None:
        config_type_key = check.not_none(config_type_key)
    else:
        config_type = normalize_config_type(config_type)
        config_schema_snap = config_type.get_schema_snapshot()
        config_type_key = check.not_none(config_type.key)

    return _handle(
        ValidationContext(
            config_schema_snapshot=config_schema_snap,
            config_type_snap=config_schema_snap.get_config_type_snap(config_type_key),
            stack=EvaluationStack(entries=[]),
        ),
        config_value,
    )


def _handle(context: "ValidationContext", value: T) -> EvaluateValueResult[T]:
    check.inst_param(context, "context", ValidationContext)

    kind = context.config_type_snap.kind

    if kind == ConfigTypeKind.NONEABLE:
        result = _handle_noneable(context, value)
    elif kind == ConfigTypeKind.ANY:
        result = _handle_any(context, value)
    elif value is None:  # only Any and Noneable allow None
        return EvaluateValueResult.invalid(value, create_none_not_allowed_error(context))
    elif kind == ConfigTypeKind.SCALAR:
        result = _handle_scalar(context, cast(ScalarConfigValue, value))
    elif kind == ConfigTypeKind.ENUM:
        result = _handle_enum(context, value)
    elif kind == ConfigTypeKind.SELECTOR:
        result = _handle_selector(context, cast(Mapping[str, ConfigValue], value))
    elif kind == ConfigTypeKind.STRICT_SHAPE:
        result = _handle_shape(context, cast(Mapping[str, ConfigValue], value), is_permissive=False)
    elif kind == ConfigTypeKind.PERMISSIVE_SHAPE:
        result = _handle_shape(context, cast(Mapping[str, ConfigValue], value), is_permissive=True)
    elif kind == ConfigTypeKind.MAP:
        result = _handle_map(context, cast(Mapping[ScalarConfigValue, ConfigValue], value))
    elif kind == ConfigTypeKind.ARRAY:
        result = _handle_array(context, cast(Sequence[ConfigValue], value))
    elif kind == ConfigTypeKind.SCALAR_UNION:
        result = _handle_scalar_union(context, value)
    else:
        check.failed("Unsupported ConfigTypeKind {}".format(kind))

    return cast(EvaluateValueResult[T], result)


def _handle_noneable(context: ValidationContext, value: T) -> EvaluateValueResult[T]:
    if value is None:
        return EvaluateValueResult.valid(value)
    else:
        return _handle(context.for_nullable_inner_type(), value)


def _handle_any(_context: ValidationContext, value: T) -> EvaluateValueResult[T]:
    return EvaluateValueResult.valid(value)


def _handle_scalar(context: ValidationContext, value: T) -> EvaluateValueResult[T]:
    scalar_kind = context.config_type_snap.scalar_kind
    if scalar_kind == ConfigScalarKind.INT:
        is_valid = not isinstance(value, bool) and isinstance(value, int)
    elif scalar_kind == ConfigScalarKind.STRING:
        is_valid = isinstance(value, str)
    elif scalar_kind == ConfigScalarKind.BOOL:
        is_valid = isinstance(value, bool)
    elif scalar_kind == ConfigScalarKind.FLOAT:
        is_valid = isinstance(value, (float, int))
    elif scalar_kind is None:
        is_valid = isinstance(value, (float, int, str, bool))
    else:
        check.failed("Not a supported scalar {}".format(context.config_type_snap))

    if not is_valid:
        return EvaluateValueResult.invalid(value, create_scalar_error(context, value))
    else:
        return EvaluateValueResult.valid(value)


def _handle_enum(context: ValidationContext, value: T) -> EvaluateValueResult[T]:
    if not isinstance(value, str):
        return EvaluateValueResult.invalid(value, create_enum_type_mismatch_error(context, value))

    if not context.config_type_snap.has_enum_value(value):
        return EvaluateValueResult.invalid(value, create_enum_value_missing_error(context, value))

    return EvaluateValueResult.valid(value)


def _handle_selector(
    context: ValidationContext,
    value: T,
) -> EvaluateValueResult[T]:

    if not isinstance(value, Mapping):
        return EvaluateValueResult.invalid(value, create_selector_type_error(context, value))

    # Special case the empty dictionary, meaning no values provided for the
    # value of the selector. # E.g. {'logging': {}}
    # If there is a single field defined on the selector and if it is optional
    # it passes validation. (e.g. a single logger "console")
    if len(value) == 0:
        fields = check.not_none(context.config_type_snap.fields)
        if len(fields) > 1:
            return EvaluateValueResult.invalid(
                value, create_selector_multiple_fields_no_field_selected_error(context)
            )
        elif fields[0].is_required:
            return EvaluateValueResult.invalid(
                value, create_selector_unspecified_value_error(context)
            )
        else:
            return EvaluateValueResult.valid(value)

    elif len(value) > 1:
        return EvaluateValueResult.invalid(
            value, create_selector_multiple_fields_error(context, value)
        )

    field_name, field_value = single_item_dict_to_tuple(value)

    if not context.config_type_snap.has_field(field_name):
        return EvaluateValueResult.invalid(
            value, create_field_not_defined_error(context, field_name)
        )

    field_snap = context.config_type_snap.get_field(field_name)

    # Users may provide a selector key with a null value if the type of the selector value has
    # fields. An empty dictionary is passed in place of None.
    #
    # e.g.
    # storage:  # selector type
    #   filesystem:  # null value; type of `filesystem` field must have fields
    field_type = context.config_schema_snapshot.get_config_type_snap(field_snap.type_key)
    field_value = (
        cast(Mapping[ConfigValue, ConfigValue], {})
        if field_value is None and field_type.has_fields
        else field_value
    )
    child_result = _handle(context.for_field_snap(field_snap), field_value)

    if child_result.success:
        return EvaluateValueResult.valid(value)
    else:
        return EvaluateValueResult.invalid(value, *child_result.errors)


def _handle_shape(
    context: ValidationContext, value: T, is_permissive: bool
) -> EvaluateValueResult[T]:
    field_aliases = check.opt_mapping_param(
        context.config_type_snap.field_aliases,
        "field_aliases",
        key_type=str,
        value_type=str,
    )

    if not isinstance(value, dict):
        return EvaluateValueResult.invalid(value, create_dict_type_mismatch_error(context, value))

    field_snaps = check.not_none(context.config_type_snap.fields)
    defined_field_names = {check.not_none(fs.name) for fs in field_snaps}.union(
        set(field_aliases.values())
    )
    value_field_names = set(value.keys())

    errors: List[EvaluationError] = []

    # extra fields in strict shapes are invalid
    if not is_permissive:
        extra_fields = list(value_field_names - defined_field_names)
        if extra_fields:
            if len(extra_fields) == 1:
                errors.append(create_field_not_defined_error(context, extra_fields[0]))
            else:
                errors.append(create_fields_not_defined_error(context, extra_fields))

    # missing fields or name/alias collisions in either strict or permissive shapes are invalid
    missing_fields: List[str] = []
    for field_snap in field_snaps:
        name = check.not_none(field_snap.name)
        alias = field_aliases.get(name)
        names = [n for n in (name, alias) if n is not None]
        if field_snap.is_required and all(n not in value for n in names):
            missing_fields.append(name)
        elif name in value and alias is not None and alias in value:
            errors.append(
                create_field_substitution_collision_error(
                    context.for_field_snap(field_snap), name, alias
                )
            )
        elif name in value:
            field_result = _handle(context.for_field_snap(field_snap), value[name])
            errors.extend(field_result.errors)
        elif alias is not None and alias in value:
            field_result = _handle(context.for_field_snap(field_snap), value[alias])
            errors.extend(field_result.errors)

    if len(missing_fields) == 1:
        errors.append(create_missing_required_field_error(context, missing_fields[0]))
    elif len(missing_fields) > 1:
        errors.append(create_missing_required_fields_error(context, missing_fields))

    frozen_value = frozendict(value)
    if len(errors) > 0:
        return EvaluateValueResult.invalid(frozen_value, *errors)
    else:
        return EvaluateValueResult.valid(frozen_value)


def _handle_map(context: ValidationContext, value: T) -> EvaluateValueResult[T]:

    if not isinstance(value, dict):
        return EvaluateValueResult.invalid(value, create_map_error(context, value))

    child_results = [
        *[_handle(context.for_map_key(key), key) for key in value.keys()],
        *[_handle(context.for_map_value(key), config_item) for key, config_item in value.items()],
    ]
    errors = [error for result in child_results for error in result.errors]

    if len(errors) > 0:
        return EvaluateValueResult.invalid(value, *errors)
    else:
        return EvaluateValueResult.valid(value)


def _handle_array(context: ValidationContext, value: T) -> EvaluateValueResult[T]:
    if not isinstance(value, list):
        return EvaluateValueResult.invalid(value, create_array_error(context, value))

    child_results = [
        _handle(context.for_array_element(index), elem) for index, elem in enumerate(value)
    ]
    errors = [error for result in child_results for error in result.errors]

    if len(errors) > 0:
        return EvaluateValueResult.invalid(value, *errors)
    else:
        return EvaluateValueResult.valid(value)


def _handle_scalar_union(context: ValidationContext, value: T) -> EvaluateValueResult[T]:
    if isinstance(value, dict) or isinstance(value, list):
        return _handle(
            context.for_config_type(context.config_type_snap.non_scalar_type_key),
            value,
        )
    else:
        return _handle(
            context.for_config_type(context.config_type_snap.scalar_type_key),
            value,
        )


class ValidationContext(TraversalContext):

    def for_field_snap(self, field_snap: ConfigFieldSnap) -> "ValidationContext":
        check.inst_param(field_snap, "field_snap", ConfigFieldSnap)
        field_snap_name = check.not_none(field_snap.name)
        return ValidationContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_type_snap(field_snap.type_key),
            stack=self.stack.for_field(field_snap_name),
        )

    def for_array_element(self, index: int) -> "ValidationContext":
        check.int_param(index, "index")
        return ValidationContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_type_snap(
                self.config_type_snap.inner_type_key
            ),
            stack=self.stack.for_array_element(index),
        )

    def for_map_key(self, key: object) -> "ValidationContext":
        return ValidationContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_type_snap(
                self.config_type_snap.key_type_key
            ),
            stack=self.stack.for_map_key(key),
        )

    def for_map_value(self, key: object) -> "ValidationContext":
        return ValidationContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_type_snap(
                self.config_type_snap.inner_type_key
            ),
            stack=self.stack.for_map_value(key),
        )

    def for_config_type(self, config_type_key: str) -> "ValidationContext":
        check.str_param(config_type_key, "config_type_key")
        return ValidationContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_type_snap(config_type_key),
            stack=self.stack,
        )

    def for_nullable_inner_type(self) -> "ValidationContext":
        return ValidationContext(
            config_schema_snapshot=self.config_schema_snapshot,
            config_type_snap=self.config_schema_snapshot.get_config_type_snap(
                self.config_type_snap.inner_type_key
            ),
            stack=self.stack,
        )
