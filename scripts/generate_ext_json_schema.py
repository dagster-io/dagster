import json
import os
from typing import (
    Any,
    Dict,
    List,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import jsonschema
from dagster_ext import (
    ExtContextData,
    ExtMessage,
    get_ext_json_schema_path,
)
from pydantic import BaseModel, create_model
from typing_extensions import TypedDict, TypeGuard

OUTPUT_FILEPATH = os.path.join(
    os.path.dirname(__file__), "../python_modules/dagster-ext/ext_protocol_schema.json"
)

MODEL_CACHE: Dict[str, Any] = {}


def main():
    context_schema = create_pydantic_model_from_typeddict(ExtContextData).model_json_schema()
    message_schema = create_pydantic_model_from_typeddict(ExtMessage).model_json_schema()
    inject_dagster_ext_version_field(message_schema)
    jsonschema.Draft7Validator.check_schema(context_schema)
    jsonschema.Draft7Validator.check_schema(message_schema)

    with open(get_ext_json_schema_path("context"), "w") as f:
        f.write(json.dumps(context_schema, indent=2))
    with open(get_ext_json_schema_path("message"), "w") as f:
        f.write(json.dumps(message_schema, indent=2))


def create_pydantic_model_from_typeddict(typed_dict_cls: Type[TypedDict]) -> Type[BaseModel]:
    """Create a Pydantic model from a TypedDict class.

    We use this instead of the Pydantic-provided `create_model_from_typeddict` because we need to
    handle nested `TypedDict`. This funciton will convert any child `TypedDict` to a Pydantic model,
    which is necessary for Pydantic JSON schema generation to work correctly.
    """
    if typed_dict_cls.__name__ not in MODEL_CACHE:
        annotations = get_type_hints(typed_dict_cls)
        fields: Dict[str, Tuple[Type, ...]] = {}
        for name, field_type in annotations.items():
            pydantic_type = normalize_field_type(field_type)
            fields[name] = (pydantic_type, ...)
        MODEL_CACHE[typed_dict_cls.__name__] = create_model(typed_dict_cls.__name__, **fields)  # type: ignore
    return MODEL_CACHE[typed_dict_cls.__name__]


def inject_dagster_ext_version_field(schema: Dict[str, Any]) -> None:
    """Add `__dagster_ext_version` field to the schema.
    This field is excluded from the Pydantic-constructed schema because it is underscore-prefixed,
    which means it is not treated as a field by Pydantic.
    """
    schema["properties"]["__dagster_ext_version"] = {"type": "string"}


def normalize_field_type(field_type: Type) -> Type:
    origin = get_origin(field_type)
    if origin is not None:  # composite type
        new_args = tuple(normalize_field_type(arg) for arg in get_args(field_type))
        return origin[new_args]
    elif is_typed_dict_class(field_type):
        return create_pydantic_model_from_typeddict(field_type)
    else:
        return field_type


def is_typed_dict_class(cls: Type) -> TypeGuard[Type[TypedDict]]:
    x = isinstance(cls, type) and issubclass(cls, dict) and get_type_hints(cls) is not None
    return x


def parse_type(typ) -> Tuple[bool, Type]:
    origin = get_origin(typ)
    args = get_args(typ)
    is_optional = origin is Union and len(args) == 2 and any(arg is type(None) for arg in args)
    unwrapped_type = args[0] if is_optional else typ
    return is_optional, unwrapped_type


def merge_schemas(*schemas: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple JSON schemas into a single schema with a top-level `oneOf` property.

    This function is necessary because Pydantic does not support merging schemas.
    """
    one_of: List[Any] = []
    defs = {}
    for schema in schemas:
        defs.update(schema.get("$defs", {}))
        defs[schema["title"]] = {k: v for k, v in schema.items() if k != "definitions"}
        one_of.append({"$ref": f"#/$defs/{schema['title']}"})
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "oneOf": one_of,
        "$defs": defs,
    }


if __name__ == "__main__":
    main()
