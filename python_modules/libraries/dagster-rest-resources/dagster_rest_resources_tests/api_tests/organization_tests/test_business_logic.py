"""Test organization business logic functions without mocks."""

import pytest
from dagster_rest_resources.graphql_adapter.organization import (
    process_organization_settings_response,
    process_set_organization_settings_response,
)

from dagster_rest_resources_tests.api_tests.test_dynamic_command_execution import (
    load_recorded_graphql_responses,
)


class TestProcessOrganizationSettingsResponse:
    """Test the pure function that processes organization settings responses."""

    def test_successful_response(self, snapshot):
        """Test processing a successful response."""
        response = load_recorded_graphql_responses("organization", "success_get_settings")[0]
        settings_data = response.get("organizationSettings", {})
        result = process_organization_settings_response(settings_data)

        snapshot.assert_match(result)

    def test_empty_settings(self, snapshot):
        """Test processing response with empty settings."""
        result = process_organization_settings_response({"settings": {}})
        snapshot.assert_match(result)


class TestProcessSetOrganizationSettingsResponse:
    """Test the pure function that processes set organization settings responses."""

    def test_successful_set(self, snapshot):
        """Test processing a successful set response."""
        response = {
            "__typename": "OrganizationSettings",
            "settings": {"sso_default_role": "EDITOR"},
        }
        result = process_set_organization_settings_response(response)
        snapshot.assert_match(result)

    def test_unauthorized_error(self):
        """Test processing an unauthorized error."""
        response = {
            "__typename": "UnauthorizedError",
            "message": "Not authorized",
        }
        with pytest.raises(ValueError, match="Error setting organization settings"):
            process_set_organization_settings_response(response)

    def test_python_error(self):
        """Test processing a PythonError."""
        response = {
            "__typename": "PythonError",
            "message": "Internal error",
        }
        with pytest.raises(ValueError, match="Error setting organization settings"):
            process_set_organization_settings_response(response)
