"""Test suite to ensure REST compliance for Dagster Plus API interfaces."""

import importlib
import inspect
import pkgutil
from functools import cache
from typing import Union, get_args, get_origin

import pytest
from dagster_dg_cli.dagster_plus_api.api.deployments import DeploymentAPI
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


def get_all_api_classes():
    """Get all API classes to test."""
    # For now just DeploymentAPI, but this can be expanded
    return [DeploymentAPI]


@cache
def get_pydantic_models_from_schemas():
    """Discover all Pydantic models from the schemas package."""
    models = set()
    schemas_module = importlib.import_module("dagster_dg_cli.dagster_plus_api.schemas")

    # Iterate through all modules in the schemas package
    for _, module_name, _ in pkgutil.iter_modules(schemas_module.__path__):
        full_module_name = f"dagster_dg_cli.dagster_plus_api.schemas.{module_name}"
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


class TestRestCompliance:
    """Test REST compliance for API interfaces."""

    def test_method_naming_conventions(self):
        """Test that all public methods follow REST naming conventions."""
        for api_class in get_all_api_classes():
            public_methods = [
                method
                for method in dir(api_class)
                if not method.startswith("_") and callable(getattr(api_class, method))
            ]

            # Remove __init__ and other special methods
            public_methods = [m for m in public_methods if not m.startswith("__")]

            for method_name in public_methods:
                valid_prefix = any(
                    method_name.startswith(prefix) for prefix in REST_PREFIXES.keys()
                )
                assert valid_prefix, (
                    f"{api_class.__name__}.{method_name} doesn't follow REST naming conventions. "
                    f"Should start with one of: {', '.join(REST_PREFIXES.keys())}"
                )

    def test_type_signatures(self):
        """Test that methods only use primitives and Pydantic models."""
        for api_class in get_all_api_classes():
            public_methods = [
                method
                for method in dir(api_class)
                if not method.startswith("_") and callable(getattr(api_class, method))
            ]

            # Remove __init__ and other special methods
            public_methods = [m for m in public_methods if not m.startswith("__")]

            for method_name in public_methods:
                method = getattr(api_class, method_name)
                if not callable(method):
                    continue

                sig = inspect.signature(method)

                # Check parameters (skip 'self')
                for param_name, param in sig.parameters.items():
                    if param_name == "self":
                        continue

                    if param.annotation != inspect.Parameter.empty:
                        assert is_allowed_type(param.annotation), (
                            f"{api_class.__name__}.{method_name} parameter '{param_name}' "
                            f"has invalid type {param.annotation}. "
                            f"Only primitives and Pydantic models are allowed."
                        )

                # Check return type
                if sig.return_annotation != inspect.Signature.empty:
                    # Return types must be Pydantic models (not primitives)
                    assert is_pydantic_model(sig.return_annotation), (
                        f"{api_class.__name__}.{method_name} return type {sig.return_annotation} "
                        f"must be a Pydantic model."
                    )

    def test_response_consistency(self):
        """Test that list methods return consistent response structures."""
        for api_class in get_all_api_classes():
            public_methods = [
                method
                for method in dir(api_class)
                if not method.startswith("_") and callable(getattr(api_class, method))
            ]

            for method_name in public_methods:
                if not method_name.startswith("list_"):
                    continue

                method = getattr(api_class, method_name)
                sig = inspect.signature(method)

                if sig.return_annotation != inspect.Signature.empty:
                    return_type = sig.return_annotation

                    # Get the actual class if it's Optional
                    if get_origin(return_type) in (Union, type(Union)):
                        args = get_args(return_type)
                        non_none_args = [arg for arg in args if arg is not type(None)]
                        if non_none_args:
                            return_type = non_none_args[0]

                    # Check that it's a Pydantic model with an 'items' field
                    if inspect.isclass(return_type) and issubclass(return_type, BaseModel):
                        fields = return_type.model_fields
                        assert "items" in fields, (
                            f"{api_class.__name__}.{method_name} return type {return_type.__name__} "
                            f"should have an 'items' field for list responses."
                        )

    def test_parameter_patterns(self):
        """Test that parameters follow consistent patterns."""
        for api_class in get_all_api_classes():
            public_methods = [
                method
                for method in dir(api_class)
                if not method.startswith("_") and callable(getattr(api_class, method))
            ]

            for method_name in public_methods:
                method = getattr(api_class, method_name)
                if not callable(method):
                    continue

                sig = inspect.signature(method)

                for param_name, param in sig.parameters.items():
                    if param_name == "self":
                        continue

                    # Check ID parameters use consistent naming
                    if "id" in param_name.lower():
                        # IDs should be in format resource_id (e.g., deployment_id)
                        assert param_name.endswith("_id") or param_name == "id", (
                            f"{api_class.__name__}.{method_name} parameter '{param_name}' "
                            f"should follow pattern 'resource_id' (e.g., deployment_id)"
                        )

                    # Check Optional parameters have proper typing
                    if param.default != inspect.Parameter.empty:
                        # Parameters with defaults should be Optional
                        if param.annotation != inspect.Parameter.empty:
                            origin = get_origin(param.annotation)
                            is_optional = origin in (Union, type(Union)) and type(None) in get_args(
                                param.annotation
                            )
                            assert is_optional or param.default is None, (
                                f"{api_class.__name__}.{method_name} parameter '{param_name}' "
                                f"has a default value but is not typed as Optional"
                            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
