import inspect
from enum import Enum
from typing import (
    Any,
    Optional,
    Type,
    TypeVar,
)

from pydantic import ConstrainedFloat, ConstrainedInt, ConstrainedStr
from typing_extensions import TypeAlias

from dagster import (
    Enum as DagsterEnum,
)
from dagster._config.config_type import (
    Array,
    ConfigFloatInstance,
    ConfigType,
    Noneable,
)
from dagster._config.post_process import resolve_defaults
from dagster._config.source import BoolSource, IntSource, StringSource
from dagster._config.validate import validate_config
from dagster._core.definitions.definition_config_schema import (
    DefinitionConfigSchema,
)
from dagster._core.errors import (
    DagsterInvalidConfigDefinitionError,
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    DagsterInvalidPythonicConfigDefinitionError,
)

from .attach_other_object_to_context import (
    IAttachDifferentObjectToOpContext as IAttachDifferentObjectToOpContext,
)

try:
    from functools import cached_property  # type: ignore  # (py37 compat)
except ImportError:

    class cached_property:
        pass


from pydantic.fields import (
    SHAPE_DICT,
    SHAPE_LIST,
    SHAPE_MAPPING,
    SHAPE_SINGLETON,
    ModelField,
)

import dagster._check as check
from dagster import Field, Selector
from dagster._config.field_utils import (
    FIELD_NO_DEFAULT_PROVIDED,
    Map,
    convert_potential_field,
)

from .inheritance_utils import safe_is_subclass


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


PydanticShapeType: TypeAlias = int

MAPPING_TYPES = {SHAPE_MAPPING, SHAPE_DICT}
MAPPING_KEY_TYPE_TO_SCALAR = {
    StringSource: str,
    IntSource: int,
    BoolSource: bool,
    ConfigFloatInstance: float,
}


def _wrap_config_type(
    shape_type: PydanticShapeType,
    key_type: Optional[ConfigType],
    config_type: ConfigType,
) -> ConfigType:
    """Based on a Pydantic shape type, wraps a config type in the appropriate Dagster config wrapper.
    For example, if the shape type is a Pydantic list, the config type will be wrapped in an Array.
    """
    if shape_type == SHAPE_SINGLETON:
        return config_type
    elif shape_type == SHAPE_LIST:
        return Array(config_type)
    elif shape_type in MAPPING_TYPES:
        if key_type not in MAPPING_KEY_TYPE_TO_SCALAR:
            raise NotImplementedError(
                f"Pydantic shape type is a mapping, but key type {key_type} is not a valid "
                "Map key type. Valid Map key types are: "
                f"{', '.join([str(t) for t in MAPPING_KEY_TYPE_TO_SCALAR.keys()])}."
            )
        return Map(MAPPING_KEY_TYPE_TO_SCALAR[key_type], config_type)
    else:
        raise NotImplementedError(f"Pydantic shape type {shape_type} not supported.")


def _get_inner_field_if_exists(
    shape_type: PydanticShapeType, field: ModelField
) -> Optional[ModelField]:
    """Grabs the inner Pydantic field type for a data structure such as a list or dictionary.

    Returns None for types which have no inner field.
    """
    # See https://github.com/pydantic/pydantic/blob/v1.10.3/pydantic/fields.py#L758 for
    # where sub_fields is set.
    if shape_type == SHAPE_SINGLETON:
        return None
    elif shape_type == SHAPE_LIST:
        # List has a single subfield, which is the type of the list elements.
        return check.not_none(field.sub_fields)[0]
    elif shape_type in MAPPING_TYPES:
        # Mapping has a single subfield, which is the type of the mapping values.
        return check.not_none(field.sub_fields)[0]
    else:
        raise NotImplementedError(f"Pydantic shape type {shape_type} not supported.")


def _convert_pydantic_field(pydantic_field: ModelField, model_cls: Optional[Type] = None) -> Field:
    """Transforms a Pydantic field into a corresponding Dagster config field.


    Args:
        pydantic_field (ModelField): The Pydantic field to convert.
        model_cls (Optional[Type]): The Pydantic model class that the field belongs to. This is
            used for error messages.
    """
    from .config import Config, infer_schema_from_config_class

    key_type = (
        _config_type_for_pydantic_field(pydantic_field.key_field)
        if pydantic_field.key_field
        else None
    )
    if pydantic_field.field_info.discriminator:
        return _convert_pydantic_descriminated_union_field(pydantic_field)

    if safe_is_subclass(pydantic_field.type_, Config):
        inferred_field = infer_schema_from_config_class(
            pydantic_field.type_,
            description=pydantic_field.field_info.description,
        )
        wrapped_config_type = _wrap_config_type(
            shape_type=pydantic_field.shape,
            config_type=inferred_field.config_type,
            key_type=key_type,
        )
        return Field(
            config=(
                Noneable(wrapped_config_type) if pydantic_field.allow_none else wrapped_config_type
            ),
            description=inferred_field.description,
            is_required=_is_pydantic_field_required(pydantic_field),
        )
    else:
        # For certain data structure types, we need to grab the inner Pydantic field (e.g. List type)
        inner_field = _get_inner_field_if_exists(pydantic_field.shape, pydantic_field)
        if inner_field:
            config_type = _convert_pydantic_field(inner_field, model_cls=model_cls).config_type
        else:
            config_type = _config_type_for_pydantic_field(pydantic_field)

        wrapped_config_type = _wrap_config_type(
            shape_type=pydantic_field.shape, config_type=config_type, key_type=key_type
        )

        return Field(
            config=(
                Noneable(wrapped_config_type) if pydantic_field.allow_none else wrapped_config_type
            ),
            description=pydantic_field.field_info.description,
            is_required=_is_pydantic_field_required(pydantic_field),
            default_value=(
                pydantic_field.default
                if pydantic_field.default is not None
                else FIELD_NO_DEFAULT_PROVIDED
            ),
        )


def _config_type_for_pydantic_field(pydantic_field: ModelField) -> ConfigType:
    """Generates a Dagster ConfigType from a Pydantic field.

    Args:
        pydantic_field (ModelField): The Pydantic field to convert.
    """
    return _config_type_for_type_on_pydantic_field(
        pydantic_field.type_,
    )


def _config_type_for_type_on_pydantic_field(
    potential_dagster_type: Any,
) -> ConfigType:
    """Generates a Dagster ConfigType from a Pydantic field's Python type.

    Args:
        potential_dagster_type (Any): The Python type of the Pydantic field.
    """
    # special case pydantic constrained types to their source equivalents
    if safe_is_subclass(potential_dagster_type, ConstrainedStr):
        return StringSource
    # no FloatSource, so we just return float
    elif safe_is_subclass(potential_dagster_type, ConstrainedFloat):
        potential_dagster_type = float
    elif safe_is_subclass(potential_dagster_type, ConstrainedInt):
        return IntSource

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


def _is_pydantic_field_required(pydantic_field: ModelField) -> bool:
    # required is of type BoolUndefined = Union[bool, UndefinedType] in Pydantic

    if isinstance(pydantic_field.required, bool):
        return pydantic_field.required

    raise Exception(
        "pydantic.field.required is their UndefinedType sentinel value which we "
        "do not fully understand the semantics of right now. For the time being going "
        "to throw an error to figure see when we actually encounter this state."
    )


def _convert_pydantic_descriminated_union_field(pydantic_field: ModelField) -> Field:
    """Builds a Selector config field from a Pydantic field which is a descriminated union.

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
    from .config import Config, infer_schema_from_config_class

    sub_fields_mapping = pydantic_field.sub_fields_mapping
    if not sub_fields_mapping or not all(
        issubclass(pydantic_field.type_, Config) for pydantic_field in sub_fields_mapping.values()
    ):
        raise NotImplementedError("Descriminated unions with non-Config types are not supported.")

    # First, we generate a mapping between the various discriminator values and the
    # Dagster config fields that correspond to them. We strip the discriminator key
    # from the fields, since the user should not have to specify it.

    assert pydantic_field.sub_fields_mapping
    dagster_config_field_mapping = {
        discriminator_value: infer_schema_from_config_class(
            field.type_,
            fields_to_omit=(
                {pydantic_field.field_info.discriminator}
                if pydantic_field.field_info.discriminator
                else None
            ),
        )
        for discriminator_value, field in sub_fields_mapping.items()
    }

    # We then nest the union fields under a Selector. The keys for the selector
    # are the various discriminator values
    return Field(config=Selector(fields=dagster_config_field_mapping))


def infer_schema_from_config_annotation(model_cls: Any, config_arg_default: Any) -> Field:
    """Parses a structured config class or primitive type and returns a corresponding Dagster config Field."""
    from .config import Config, infer_schema_from_config_class

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
