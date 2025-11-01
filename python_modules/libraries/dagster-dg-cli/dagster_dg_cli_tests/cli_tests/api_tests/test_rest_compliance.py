"""Test suite to ensure REST compliance for Dagster Plus API interfaces."""

import inspect
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

    def test_error_handling_consistency(self):
        """Test that all API methods handle errors consistently."""
        from dagster_dg_cli.cli.api.shared import get_graphql_error_mappings

        # Verify error mapping completeness
        mappings = get_graphql_error_mappings()
        assert mappings, "GraphQL error mappings should be defined"

        # Verify all error mappings have required structure
        for error_type, mapping in mappings.items():
            assert hasattr(mapping, "code"), f"Error mapping for {error_type} missing code"
            assert hasattr(mapping, "status_code"), (
                f"Error mapping for {error_type} missing status_code"
            )
            assert isinstance(mapping.code, str), f"Error code for {error_type} should be string"
            assert isinstance(mapping.status_code, int), (
                f"Status code for {error_type} should be int"
            )

            # Status codes should be valid HTTP error codes
            valid_statuses = {400, 401, 403, 404, 422, 500}
            assert mapping.status_code in valid_statuses, (
                f"Invalid status code {mapping.status_code} for {error_type}"
            )

    def test_error_response_format_consistency(self):
        """Test that error responses follow consistent format across all domains."""
        from dagster_dg_cli.cli.api.shared import DgApiError, format_error_for_output

        # Test JSON error format
        test_error = DgApiError("Test error message", "TEST_ERROR", 400)
        json_output, json_exit_code = format_error_for_output(test_error, output_json=True)

        # Should be valid JSON
        import json

        try:
            json_data = json.loads(json_output)
        except json.JSONDecodeError:
            pytest.fail("Error output should be valid JSON")

        # Should have required fields
        required_fields = {"error", "code", "statusCode", "type"}
        assert set(json_data.keys()) >= required_fields, (
            f"JSON error response missing required fields: {required_fields - set(json_data.keys())}"
        )

        # Test text error format
        text_output, text_exit_code = format_error_for_output(test_error, output_json=False)

        # Should start with consistent prefix
        assert text_output.startswith("Error querying Dagster Plus API: "), (
            "Text error output should have consistent prefix"
        )

        # Exit codes should map correctly
        assert json_exit_code == 1, "400 status should map to exit code 1"
        assert text_exit_code == 1, "400 status should map to exit code 1"

    def test_error_code_naming_conventions(self):
        """Test that error codes follow consistent naming conventions."""
        from dagster_dg_cli.cli.api.shared import get_graphql_error_mappings

        mappings = get_graphql_error_mappings()

        for mapping in mappings.values():
            code = mapping.code

            # Should be uppercase
            assert code.isupper(), f"Error code {code} should be uppercase"

            # Should use underscores
            assert " " not in code, f"Error code {code} should not contain spaces"
            assert "-" not in code, f"Error code {code} should use underscores, not hyphens"

            # Should be descriptive
            assert len(code) > 2, f"Error code {code} should be descriptive (more than 2 chars)"

            # Should end with _ERROR or be a resource-specific format
            valid_suffixes = ["_ERROR", "_REQUIRED", "_NOT_FOUND", "_DEFINED"]
            valid_formats = ["UNAUTHORIZED", "FORBIDDEN", "INTERNAL_ERROR"]

            is_valid = (
                any(code.endswith(suffix) for suffix in valid_suffixes)
                or code in valid_formats
                or "_NOT_" in code  # Patterns like ASSET_NOT_FOUND
            )

            assert is_valid, f"Error code {code} should follow naming conventions"

    def test_status_code_categorization(self):
        """Test that status codes properly categorize error types."""
        from dagster_dg_cli.cli.api.shared import get_error_type_from_status_code

        # Test expected mappings
        expected_mappings = {
            400: "client_error",
            401: "authentication_error",
            403: "authorization_error",
            404: "not_found_error",
            422: "migration_error",
            500: "server_error",
        }

        for status_code, expected_type in expected_mappings.items():
            actual_type = get_error_type_from_status_code(status_code)
            assert actual_type == expected_type, (
                f"Status {status_code} should map to {expected_type}, got {actual_type}"
            )

        # Test unknown status defaults to server_error
        unknown_status = 418  # I'm a teapot
        assert get_error_type_from_status_code(unknown_status) == "server_error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
