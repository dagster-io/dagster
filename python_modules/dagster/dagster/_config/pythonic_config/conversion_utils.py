import inspect
from collections.abc import Mapping
from enum import Enum
from typing import Annotated, Any, Literal, Optional, TypeVar, Union

from dagster_shared.dagster_model.pydantic_compat_layer import (
    ModelFieldCompat,
    PydanticUndefined,
    model_fields,
)
from typing_extensions import get_args, get_origin

import dagster._check as check
from dagster._config import (
    Enum as DagsterEnum,
    EnumValue as DagsterEnumValue,
    Field,
    Selector,
)
from dagster._config.config_type import Array, ConfigType, Noneable
from dagster._config.field_utils import FIELD_NO_DEFAULT_PROVIDED, Map, convert_potential_field
from dagster._config.post_process import resolve_defaults
from dagster._config.pythonic_config.attach_other_object_to_context import (
    IAttachDifferentObjectToOpContext as IAttachDifferentObjectToOpContext,
)
from dagster._config.pythonic_config.type_check_utils import safe_is_subclass
from dagster._config.source import BoolSource, IntSource, StringSource
from dagster._config.validate import validate_config
from dagster._core.definitions.definition_config_schema import DefinitionConfigSchema
from dagster._core.errors import (
    DagsterInvalidConfigDefinitionError,
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    DagsterInvalidPythonicConfigDefinitionError,
)
from dagster._utils.typing_api import is_closed_python_optional_type


# This is from https://github.com/dagster-io/dagster/pull/11470
def _apply_defaults_to_schema_field(field: Field, additional_default_values: Any) -> Field:
    # This work by validating the top-level config and then
    # just setting it at that top-level field. Config fields
    # can actually take nested values so we only need to set it
    # at a single level

    evr = validate_config(field.config_type, additional_default_values)

    if not evr.success:
        raise DagsterInvalidConfigError(
            "Incorrect values passed to .configured",
            evr.errors,
            additional_default_values,
        )

    if field.default_provided:
        # In the case where there is already a default config value
        # we can apply "additional" defaults by actually invoking
        # the config machinery. Meaning we pass the new_additional_default_values
        # and then resolve the existing defaults over them. This preserves the default
        # values that are not specified in new_additional_default_values and then
        # applies the new value as the default value of the field in question.
        defaults_processed_evr = resolve_defaults(field.config_type, additional_default_values)
        check.invariant(
            defaults_processed_evr.success,
            "Since validation passed, this should always work.",
        )
        default_to_pass = defaults_processed_evr.value
        return copy_with_default(field, default_to_pass)
    else:
        return copy_with_default(field, additional_default_values)


def copy_with_default(old_field: Field, new_config_value: Any) -> Field:
    return Field(
        config=old_field.config_type,
        default_value=new_config_value,
        is_required=False,
        description=old_field.description,
    )


def _curry_config_schema(schema_field: Field, data: Any) -> DefinitionConfigSchema:
    """Return a new config schema configured with the passed in data."""
    return DefinitionConfigSchema(_apply_defaults_to_schema_field(schema_field, data))


TResValue = TypeVar("TResValue")


def _convert_pydantic_field(
    pydantic_field: ModelFieldCompat,
    model_cls: Optional[type] = None,
    default: Optional[Mapping[str, Any]] = None,
) -> Field:
    """Transforms a Pydantic field into a corresponding Dagster config field.


    Args:
        pydantic_field (ModelFieldCompat): The Pydantic field to convert.
        model_cls (Optional[Type]): The Pydantic model class that the field belongs to. This is
            used for error messages.
    """
    from dagster._config.pythonic_config.config import Config, infer_schema_from_config_class

    if pydantic_field.discriminator:
        return _convert_pydantic_discriminated_union_field(pydantic_field)

    if get_origin(pydantic_field.annotation) == Literal:
        return _convert_typing_literal_field(pydantic_field)

    field_type = pydantic_field.annotation
    if safe_is_subclass(field_type, Config):
        default = None
        if pydantic_field.default and isinstance(pydantic_field.default, Config):
            default = pydantic_field.default._get_non_default_public_field_values()  # noqa: SLF001
        inferred_field = infer_schema_from_config_class(
            field_type, description=pydantic_field.description, default=default
        )
        return inferred_field
    else:
        if not pydantic_field.is_required() and not is_closed_python_optional_type(field_type):
            field_type = Optional[field_type]

        config_type = _config_type_for_type_on_pydantic_field(field_type)

        default_to_pass = (
            default
            if default
            else (
                pydantic_field.default
                if pydantic_field.default is not PydanticUndefined
                else FIELD_NO_DEFAULT_PROVIDED
            )
        )
        if isinstance(default_to_pass, Enum):
            default_to_pass = default_to_pass.name

        return Field(
            config=config_type,
            description=pydantic_field.description,
            is_required=pydantic_field.is_required()
            and not is_closed_python_optional_type(field_type),
            default_value=default_to_pass,
        )


def strip_wrapping_annotated_types(potentially_annotated_type: Any) -> Any:
    """For a type that is wrapped in Annotated, return the unwrapped type. Recursive,
    so it will unwrap nested Annotated types.

    e.g. Annotated[Annotated[List[str], "foo"], "bar] -> List[str]
    """
    while get_origin(potentially_annotated_type) == Annotated:
        potentially_annotated_type = get_args(potentially_annotated_type)[0]
    return potentially_annotated_type


def _config_type_for_type_on_pydantic_field(
    potential_dagster_type: Any,
) -> ConfigType:
    """Generates a Dagster ConfigType from a Pydantic field's Python type.

    Args:
        potential_dagster_type (Any): The Python type of the Pydantic field.
    """
    potential_dagster_type = strip_wrapping_annotated_types(potential_dagster_type)

    try:
        # Pydantic 1.x
        from pydantic import ConstrainedFloat, ConstrainedInt, ConstrainedStr

        # special case pydantic constrained types to their source equivalents
        if safe_is_subclass(potential_dagster_type, ConstrainedStr):  # type: ignore
            return StringSource
        # no FloatSource, so we just return float
        elif safe_is_subclass(potential_dagster_type, ConstrainedFloat):  # type: ignore
            potential_dagster_type = float
        elif safe_is_subclass(potential_dagster_type, ConstrainedInt):  # type: ignore
            return IntSource
    except ImportError:
        # These types do not exist in Pydantic 2.x
        pass

    if safe_is_subclass(get_origin(potential_dagster_type), list):
        list_inner_type = get_args(potential_dagster_type)[0]
        return Array(_config_type_for_type_on_pydantic_field(list_inner_type))
    elif is_closed_python_optional_type(potential_dagster_type):
        optional_inner_type = next(
            arg for arg in get_args(potential_dagster_type) if arg is not type(None)
        )
        return Noneable(_config_type_for_type_on_pydantic_field(optional_inner_type))
    elif safe_is_subclass(get_origin(potential_dagster_type), dict) or safe_is_subclass(
        get_origin(potential_dagster_type), Mapping
    ):
        key_type, value_type = get_args(potential_dagster_type)
        return Map(
            key_type,
            _config_type_for_type_on_pydantic_field(value_type),
        )

    from dagster._config.pythonic_config.config import Config, infer_schema_from_config_class

    if safe_is_subclass(potential_dagster_type, Config):
        inferred_field = infer_schema_from_config_class(
            potential_dagster_type,
        )
        return inferred_field.config_type

    if safe_is_subclass(potential_dagster_type, Enum):
        return DagsterEnum.from_python_enum_direct_values(potential_dagster_type)

    # special case raw python literals to their source equivalents
    if potential_dagster_type is str:
        return StringSource
    elif potential_dagster_type is int:
        return IntSource
    elif potential_dagster_type is bool:
        return BoolSource
    else:
        return convert_potential_field(potential_dagster_type).config_type


def _convert_pydantic_discriminated_union_field(pydantic_field: ModelFieldCompat) -> Field:
    """Builds a Selector config field from a Pydantic field which is a discriminated union.

    For example:

    class Cat(Config):
        pet_type: Literal["cat"]
        meows: int

    class Dog(Config):
        pet_type: Literal["dog"]
        barks: float

    class OpConfigWithUnion(Config):
        pet: Union[Cat, Dog] = Field(..., discriminator="pet_type")

    Becomes:

    Shape({
      "pet": Selector({
          "cat": Shape({"meows": Int}),
          "dog": Shape({"barks": Float}),
      })
    })
    """
    from dagster._config.pythonic_config.config import Config, infer_schema_from_config_class

    field_type = pydantic_field.annotation
    discriminator = pydantic_field.discriminator if pydantic_field.discriminator else None

    if not get_origin(field_type) == Union:
        raise DagsterInvalidDefinitionError("Discriminated union must be a Union type.")

    sub_fields = get_args(field_type)
    if not all(issubclass(sub_field, Config) for sub_field in sub_fields):
        raise NotImplementedError("Discriminated unions with non-Config types are not supported.")

    sub_fields_mapping = {}
    if discriminator:
        for sub_field in sub_fields:
            sub_field_annotation = model_fields(sub_field)[discriminator].annotation

            for sub_field_key in get_args(sub_field_annotation):
                sub_fields_mapping[sub_field_key] = sub_field

    # First, we generate a mapping between the various discriminator values and the
    # Dagster config fields that correspond to them. We strip the discriminator key
    # from the fields, since the user should not have to specify it.

    dagster_config_field_mapping = {
        discriminator_value: infer_schema_from_config_class(
            field,
            fields_to_omit=({discriminator} if discriminator else None),
        )
        for discriminator_value, field in sub_fields_mapping.items()
    }

    # We then nest the union fields under a Selector. The keys for the selector
    # are the various discriminator values
    return Field(config=Selector(fields=dagster_config_field_mapping))


def _convert_typing_literal_field(pydantic_field: ModelFieldCompat) -> Field:
    """Builds a Enum config field from a Pydantic field which is a Literal type.

    For example:

    class ConfigWithLiteral(Config):
        pet: Literal["cat", "dog"]

    Becomes:

    Shape({
      "pet": Enum(["cat", "dog"])
      })
    })
    """
    field_type = pydantic_field.annotation

    if not get_origin(field_type) == Literal:
        raise DagsterInvalidDefinitionError("Must be a Literal type.")

    sub_fields = get_args(field_type)

    default_to_pass = (
        pydantic_field.default
        if pydantic_field.default is not PydanticUndefined
        else FIELD_NO_DEFAULT_PROVIDED
    )

    return Field(
        config=DagsterEnum(
            str(str(field_type).lstrip("typing.")),
            list(map(DagsterEnumValue, sub_fields)),
        ),
        description=pydantic_field.description,
        is_required=pydantic_field.is_required() and not is_closed_python_optional_type(field_type),
        default_value=default_to_pass,
    )


def infer_schema_from_config_annotation(model_cls: Any, config_arg_default: Any) -> Field:
    """Parses a structured config class or primitive type and returns a corresponding Dagster config Field."""
    from dagster._config.pythonic_config.config import Config, infer_schema_from_config_class

    if safe_is_subclass(model_cls, Config):
        check.invariant(
            config_arg_default is inspect.Parameter.empty,
            "Cannot provide a default value when using a Config class",
        )
        return infer_schema_from_config_class(model_cls)

    # If were are here config is annotated with a primitive type
    # We do a conversion to a type as if it were a type on a pydantic field
    try:
        inner_config_type = _config_type_for_type_on_pydantic_field(model_cls)
    except (DagsterInvalidDefinitionError, DagsterInvalidConfigDefinitionError):
        raise DagsterInvalidPythonicConfigDefinitionError(
            invalid_type=model_cls, config_class=None, field_name=None
        )

    return Field(
        config=inner_config_type,
        default_value=(
            FIELD_NO_DEFAULT_PROVIDED
            if config_arg_default is inspect.Parameter.empty
            else config_arg_default
        ),
    )
