"""Test GraphQL error to REST API error mapping.

This module tests that GraphQL errors are properly mapped to REST-like error conventions
including correct HTTP status codes, error codes, and error type categorization.
"""

from dagster_dg_cli.cli.api.shared import (
    DgApiError,
    DgApiErrorMapping,
    get_error_type_from_status_code,
    get_graphql_error_mappings,
    get_or_create_dg_api_error,
)


class TestErrorMapping:
    """Test GraphQL to REST error mapping functionality."""

    def test_get_graphql_error_mappings_completeness(self):
        """Test that all expected GraphQL error types have mappings."""
        mappings = get_graphql_error_mappings()

        # Authentication/Authorization errors
        expected_auth_errors = {"UnauthorizedError"}

        # Not Found errors
        expected_not_found_errors = {
            "AssetNotFoundError",
            "PipelineNotFoundError",
            "RunNotFoundError",
            "ScheduleNotFoundError",
            "RepositoryNotFoundError",
            "ConfigTypeNotFoundError",
        }

        # Validation/Client errors
        expected_client_errors = {"InvalidSubsetError", "PartitionSubsetDeserializationError"}

        # Server/System errors
        expected_server_errors = {"PythonError", "SchedulerNotDefinedError"}

        # Migration/Upgrade errors
        expected_migration_errors = {
            "AssetCheckNeedsMigrationError",
            "AssetCheckNeedsUserCodeUpgrade",
            "AssetCheckNeedsAgentUpgradeError",
        }

        all_expected = (
            expected_auth_errors
            | expected_not_found_errors
            | expected_client_errors
            | expected_server_errors
            | expected_migration_errors
        )

        mapped_errors = set(mappings.keys())

        # Check that all expected errors are mapped
        missing_mappings = all_expected - mapped_errors
        assert not missing_mappings, f"Missing GraphQL error mappings: {missing_mappings}"

        # Check for unexpected mappings (informational, not an error)
        unexpected_mappings = mapped_errors - all_expected
        if unexpected_mappings:
            # Note: Additional error mappings found - this is informational, not a failure
            pass

    def test_error_mapping_structure(self):
        """Test that all error mappings have proper structure."""
        mappings = get_graphql_error_mappings()

        for graphql_type, mapping in mappings.items():
            # Should be DgApiErrorMapping instance
            assert isinstance(mapping, DgApiErrorMapping), (
                f"Mapping for {graphql_type} should be DgApiErrorMapping instance"
            )

            # Should have valid code
            assert mapping.code, f"Mapping for {graphql_type} should have non-empty code"
            assert isinstance(mapping.code, str), f"Code for {graphql_type} should be string"

            # Should have valid status code
            assert mapping.status_code, (
                f"Mapping for {graphql_type} should have non-zero status code"
            )
            assert isinstance(mapping.status_code, int), (
                f"Status code for {graphql_type} should be int"
            )
            assert mapping.status_code in {400, 401, 403, 404, 422, 500}, (
                f"Status code for {graphql_type} should be valid HTTP error code, got {mapping.status_code}"
            )

    def test_status_code_categorization(self):
        """Test that status codes map to correct error type categories."""
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
                f"Status code {status_code} should map to {expected_type}, got {actual_type}"
            )

    def test_unknown_status_code_default(self):
        """Test that unknown status codes default to server_error."""
        unknown_codes = [100, 200, 301, 418, 502, 503]  # Various non-error or unmapped codes

        for code in unknown_codes:
            error_type = get_error_type_from_status_code(code)
            assert error_type == "server_error", (
                f"Unknown status code {code} should default to server_error, got {error_type}"
            )

    def test_error_code_naming_conventions(self):
        """Test that error codes follow consistent naming conventions."""
        mappings = get_graphql_error_mappings()

        for graphql_type, mapping in mappings.items():
            code = mapping.code

            # Error codes should be uppercase
            assert code.isupper(), f"Error code {code} for {graphql_type} should be uppercase"

            # Error codes should use underscores, not hyphens or spaces
            assert " " not in code, (
                f"Error code {code} for {graphql_type} should not contain spaces"
            )
            assert "-" not in code, (
                f"Error code {code} for {graphql_type} should not contain hyphens"
            )

            # Error codes should be descriptive (more than 2 characters)
            assert len(code) > 2, f"Error code {code} for {graphql_type} should be descriptive"

    def test_status_code_consistency_by_category(self):
        """Test that similar error types have consistent status codes."""
        mappings = get_graphql_error_mappings()

        # Group errors by category
        not_found_errors = []
        migration_errors = []
        validation_errors = []

        for graphql_type, mapping in mappings.items():
            if "NotFound" in graphql_type:
                not_found_errors.append((graphql_type, mapping.status_code))
            elif "Migration" in graphql_type or "Upgrade" in graphql_type:
                migration_errors.append((graphql_type, mapping.status_code))
            elif "Invalid" in graphql_type or "Deserialization" in graphql_type:
                validation_errors.append((graphql_type, mapping.status_code))

        # All not found errors should be 404
        for error_type, status_code in not_found_errors:
            assert status_code == 404, (
                f"Not found error {error_type} should have status 404, got {status_code}"
            )

        # All migration/upgrade errors should be 422
        for error_type, status_code in migration_errors:
            assert status_code == 422, (
                f"Migration error {error_type} should have status 422, got {status_code}"
            )

        # All validation errors should be 400
        for error_type, status_code in validation_errors:
            assert status_code == 400, (
                f"Validation error {error_type} should have status 400, got {status_code}"
            )

    def test_dg_api_error_creation(self):
        """Test DgApiError creation with proper fields."""
        message = "Test error message"
        code = "TEST_ERROR"
        status_code = 400

        error = DgApiError(message, code, status_code)

        assert str(error) == message
        assert error.code == code
        assert error.status_code == status_code
        assert error.error_type == "client_error"  # 400 -> client_error

    def test_get_or_create_dg_api_error_with_known_type(self):
        """Test error creation from known GraphQL error type."""

        # Mock GraphQL error with known type
        class MockGraphQLError:
            def __init__(self, message: str, error_type: str):
                self.message = message
                self.extensions = {"errorType": error_type}

        graphql_error = MockGraphQLError("Asset not found", "AssetNotFoundError")
        api_error = get_or_create_dg_api_error(graphql_error)

        assert isinstance(api_error, DgApiError)
        assert api_error.code == "ASSET_NOT_FOUND"
        assert api_error.status_code == 404
        assert api_error.error_type == "not_found_error"
        assert "Asset not found" in str(api_error)

    def test_get_or_create_dg_api_error_with_unknown_type(self):
        """Test error creation from unknown GraphQL error type defaults to INTERNAL_ERROR."""

        # Mock GraphQL error with unknown type
        class MockGraphQLError:
            def __init__(self, message: str, error_type: str):
                self.message = message
                self.extensions = {"errorType": error_type}

        graphql_error = MockGraphQLError("Unknown error", "UnknownErrorType")
        api_error = get_or_create_dg_api_error(graphql_error)

        assert isinstance(api_error, DgApiError)
        assert api_error.code == "INTERNAL_ERROR"
        assert api_error.status_code == 500
        assert api_error.error_type == "server_error"

    def test_get_or_create_dg_api_error_without_extensions(self):
        """Test error creation from GraphQL error without extensions defaults to INTERNAL_ERROR."""

        # Mock GraphQL error without extensions
        class MockGraphQLError:
            def __init__(self, message: str):
                self.message = message

        graphql_error = MockGraphQLError("Error without extensions")
        api_error = get_or_create_dg_api_error(graphql_error)

        assert isinstance(api_error, DgApiError)
        assert api_error.code == "INTERNAL_ERROR"
        assert api_error.status_code == 500
        assert api_error.error_type == "server_error"

    def test_all_mapped_error_codes_unique(self):
        """Test that all error codes are unique across mappings."""
        mappings = get_graphql_error_mappings()

        codes = [mapping.code for mapping in mappings.values()]
        unique_codes = set(codes)

        assert len(codes) == len(unique_codes), (
            f"Found duplicate error codes: {[code for code in codes if codes.count(code) > 1]}"
        )

    def test_comprehensive_error_coverage(self):
        """Test that we have good coverage of different error scenarios."""
        mappings = get_graphql_error_mappings()

        # Count errors by status code
        status_counts = {}
        for mapping in mappings.values():
            status_counts[mapping.status_code] = status_counts.get(mapping.status_code, 0) + 1

        # Should have coverage for all major error categories
        assert 400 in status_counts, "Should have 400 client errors"
        assert 401 in status_counts, "Should have 401 authentication errors"
        assert 404 in status_counts, "Should have 404 not found errors"
        assert 422 in status_counts, "Should have 422 migration errors"
        assert 500 in status_counts, "Should have 500 server errors"

        # Should have reasonable coverage in each category
        assert status_counts.get(404, 0) >= 3, "Should have multiple not found error types"
        assert status_counts.get(422, 0) >= 2, "Should have multiple migration error types"
        assert status_counts.get(500, 0) >= 2, "Should have multiple server error types"
