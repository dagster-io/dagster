"""Test organization business logic functions without mocks."""

import json

import pytest
from dagster_dg_cli.api_layer.graphql_adapter.organization import (
    process_organization_settings_response,
    process_set_organization_settings_response,
)
from dagster_dg_cli.api_layer.schemas.organization import OrganizationSettings
from dagster_dg_cli.api_layer.schemas.saml import SamlOperationResult
from dagster_dg_cli.cli.api.formatters import format_organization_settings, format_saml_result

from dagster_dg_cli_tests.cli_tests.api_tests.test_dynamic_command_execution import (
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


class TestFormatOrganizationSettings:
    """Test the organization settings formatting functions."""

    def test_format_settings_text(self, snapshot):
        """Test formatting settings as YAML text."""
        settings = OrganizationSettings(
            settings={
                "run_queue_config": {"max_concurrent_runs": 25},
                "sso_default_role": "VIEWER",
            }
        )
        result = format_organization_settings(settings, as_json=False)
        snapshot.assert_match(result)

    def test_format_settings_json(self, snapshot):
        """Test formatting settings as JSON."""
        settings = OrganizationSettings(
            settings={
                "run_queue_config": {"max_concurrent_runs": 25},
                "sso_default_role": "VIEWER",
            }
        )
        result = format_organization_settings(settings, as_json=True)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)


class TestFormatSamlResult:
    """Test the SAML result formatting functions."""

    def test_format_saml_result_text(self, snapshot):
        """Test formatting SAML result as text."""
        result = SamlOperationResult(message="SAML metadata uploaded successfully.")
        output = format_saml_result(result, as_json=False)
        snapshot.assert_match(output)

    def test_format_saml_result_json(self, snapshot):
        """Test formatting SAML result as JSON."""
        result = SamlOperationResult(message="SAML metadata uploaded successfully.")
        output = format_saml_result(result, as_json=True)
        parsed = json.loads(output)
        snapshot.assert_match(parsed)
