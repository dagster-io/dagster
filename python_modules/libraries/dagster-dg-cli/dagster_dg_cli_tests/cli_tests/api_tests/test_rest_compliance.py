"""Test suite to ensure REST compliance for Dagster Plus API interfaces."""

import inspect
from types import UnionType
from typing import Union, get_args, get_origin

import pytest
from pydantic import BaseModel

from dagster_dg_cli_tests.cli_tests.api_tests.api_classes import get_all_api_classes
from dagster_dg_cli_tests.cli_tests.api_tests.rest_compliance_infrastructure import (
    REST_PREFIXES,
    is_allowed_type,
    is_pydantic_model,
)


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
                    if get_origin(return_type) in (Union, UnionType):
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
                            is_optional = origin in (Union, UnionType) and type(None) in get_args(
                                param.annotation
                            )
                            assert is_optional or param.default is None, (
                                f"{api_class.__name__}.{method_name} parameter '{param_name}' "
                                f"has a default value but is not typed as Optional"
                            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
