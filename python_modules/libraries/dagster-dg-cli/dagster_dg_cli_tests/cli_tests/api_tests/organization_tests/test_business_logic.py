"""Test organization business logic functions without mocks."""

import json

from dagster_dg_cli.cli.api.formatters import format_organization_settings, format_saml_result
from dagster_rest_resources.schemas.organization import OrganizationSettings
from dagster_rest_resources.schemas.saml import SamlOperationResult


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
