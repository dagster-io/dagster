"""Infrastructure for REST compliance testing of Dagster Plus API interfaces."""

import importlib
import inspect
import pkgutil
from functools import cache
from typing import Union, get_args, get_origin

from pydantic import BaseModel

# Primitive types allowed in REST APIs
ALLOWED_PRIMITIVES = (str, int, float, bool, type(None))

# REST method prefixes and their meanings
REST_PREFIXES = {
    "list_": "GET collection",
    "get_": "GET single resource",
    "create_": "POST resource",
    "update_": "PUT/PATCH resource",
    "delete_": "DELETE resource",
    "action_": "POST custom action",
}


@cache
def get_pydantic_models_from_schemas():
    """Discover all Pydantic models from the schemas package."""
    models = set()
    schemas_module = importlib.import_module("dagster_dg_cli.api_layer.schemas")

    # Iterate through all modules in the schemas package
    for _, module_name, _ in pkgutil.iter_modules(schemas_module.__path__):
        full_module_name = f"dagster_dg_cli.api_layer.schemas.{module_name}"
        module = importlib.import_module(full_module_name)
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj != BaseModel:
                models.add(name)

    return frozenset(models)  # Return frozenset for hashability with @cache


def is_pydantic_model(type_hint) -> bool:
    """Check if a type hint is a Pydantic BaseModel subclass."""
    # Handle string annotations (forward references)
    if isinstance(type_hint, str):
        # Check against discovered Pydantic models
        return type_hint in get_pydantic_models_from_schemas()

    # Handle Optional types
    if get_origin(type_hint) in (Union, type(Union)):
        # Check all args in the Union
        args = get_args(type_hint)
        # Filter out NoneType
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return is_pydantic_model(non_none_args[0])
        return False

    # Check if it's a class and subclass of BaseModel
    return inspect.isclass(type_hint) and issubclass(type_hint, BaseModel)


def is_allowed_type(type_hint) -> bool:
    """Check if a type hint is allowed (primitive or Pydantic model)."""
    # Handle Optional types
    if get_origin(type_hint) in (Union, type(Union)):
        args = get_args(type_hint)
        return all(is_allowed_type(arg) for arg in args)

    # Check if it's a primitive or Pydantic model
    return type_hint in ALLOWED_PRIMITIVES or is_pydantic_model(type_hint)
