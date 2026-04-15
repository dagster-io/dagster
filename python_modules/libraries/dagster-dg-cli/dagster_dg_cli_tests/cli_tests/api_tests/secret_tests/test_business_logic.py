"""Test secret business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

from datetime import datetime

from dagster_dg_cli.cli.api.formatters import format_secret, format_secrets
from dagster_rest_resources.schemas.secret import DgApiSecret, DgApiSecretList, DgApiUpdatedBy


class TestFormatSecrets:
    """Test the secret formatting functions."""

    def _create_sample_secret_list(self):
        """Create sample SecretList for testing."""
        secrets = [
            DgApiSecret(
                id="secret-1-uuid-12345",
                secretName="database_password",
                secretValue="super_secret_value",  # Would be hidden in actual output
                locationNames=["data_pipeline", "analytics"],
                fullDeploymentScope=True,
                allBranchDeploymentsScope=False,
                specificBranchDeploymentScope=None,
                localDeploymentScope=False,
                canViewSecretValue=True,
                canEditSecret=True,
                updatedBy=DgApiUpdatedBy(email="admin@company.com"),
                updateTimestamp=datetime(2022, 1, 1, 14, 20, 0),  # UTC to avoid timezone edge cases
            ),
            DgApiSecret(
                id="secret-2-uuid-67890",
                secretName="api_key",
                secretValue=None,  # No value - might not have permission to view
                locationNames=[],  # All locations
                fullDeploymentScope=False,
                allBranchDeploymentsScope=True,
                specificBranchDeploymentScope=None,
                localDeploymentScope=False,
                canViewSecretValue=False,
                canEditSecret=False,
                updatedBy=None,
                updateTimestamp=None,
            ),
            DgApiSecret(
                id="secret-3-uuid-abcdef",
                secretName="staging_token",
                secretValue="staging_value_123",
                locationNames=["staging_app"],
                fullDeploymentScope=False,
                allBranchDeploymentsScope=False,
                specificBranchDeploymentScope="staging",
                localDeploymentScope=True,
                canViewSecretValue=True,
                canEditSecret=True,
                updatedBy=DgApiUpdatedBy(email="dev@company.com"),
                updateTimestamp=datetime(2022, 1, 1, 14, 21, 0),  # UTC
            ),
        ]
        return DgApiSecretList(items=secrets, total=3)

    def _create_empty_secret_list(self):
        """Create empty SecretList for testing."""
        return DgApiSecretList(items=[], total=0)

    def _create_single_secret(self):
        """Create single Secret for testing."""
        return DgApiSecret(
            id="single-secret-uuid-xyz",
            secretName="development_secret",
            secretValue="dev_secret_value",
            locationNames=["dev_pipeline", "test_pipeline"],
            fullDeploymentScope=False,
            allBranchDeploymentsScope=False,
            specificBranchDeploymentScope=None,
            localDeploymentScope=True,
            canViewSecretValue=True,
            canEditSecret=True,
            updatedBy=DgApiUpdatedBy(email="developer@company.com"),
            updateTimestamp=datetime(2022, 1, 1, 14, 20, 0),
        )

    def test_format_secrets_text_output(self, snapshot):
        """Test formatting secrets as text."""
        from dagster_shared.utils.timing import fixed_timezone

        secret_list = self._create_sample_secret_list()
        with fixed_timezone("UTC"):
            result = format_secrets(secret_list, as_json=False)

        # Snapshot the entire text output
        snapshot.assert_match(result)

    def test_format_secrets_json_output(self, snapshot):
        """Test formatting secrets as JSON."""
        secret_list = self._create_sample_secret_list()
        result = format_secrets(secret_list, as_json=True)

        # For JSON, we want to snapshot the parsed structure to avoid formatting differences
        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_empty_secrets_text_output(self, snapshot):
        """Test formatting empty secret list as text."""
        secret_list = self._create_empty_secret_list()
        result = format_secrets(secret_list, as_json=False)

        snapshot.assert_match(result)

    def test_format_empty_secrets_json_output(self, snapshot):
        """Test formatting empty secret list as JSON."""
        secret_list = self._create_empty_secret_list()
        result = format_secrets(secret_list, as_json=True)

        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_single_secret_text_output(self, snapshot):
        """Test formatting single secret as text."""
        from dagster_shared.utils.timing import fixed_timezone

        secret = self._create_single_secret()
        with fixed_timezone("UTC"):
            result = format_secret(secret, as_json=False)

        snapshot.assert_match(result)

    def test_format_single_secret_text_output_with_value(self, snapshot):
        """Test formatting single secret as text with value shown."""
        from dagster_shared.utils.timing import fixed_timezone

        secret = self._create_single_secret()
        with fixed_timezone("UTC"):
            result = format_secret(secret, as_json=False, show_value=True)

        snapshot.assert_match(result)

    def test_format_single_secret_json_output(self, snapshot):
        """Test formatting single secret as JSON."""
        secret = self._create_single_secret()
        result = format_secret(secret, as_json=True)

        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_single_secret_json_output_with_value(self, snapshot):
        """Test formatting single secret as JSON with value shown."""
        secret = self._create_single_secret()
        result = format_secret(secret, as_json=True, show_value=True)

        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_secret_without_metadata(self, snapshot):
        """Test formatting secret with no metadata."""
        from dagster_shared.utils.timing import fixed_timezone

        secret = DgApiSecret(
            id="simple-secret-uuid",
            secretName="simple_secret",
            secretValue="simple_value",
            locationNames=[],
            fullDeploymentScope=True,
            allBranchDeploymentsScope=False,
            specificBranchDeploymentScope=None,
            localDeploymentScope=False,
            canViewSecretValue=True,
            canEditSecret=True,
            updatedBy=None,
            updateTimestamp=None,
        )
        with fixed_timezone("UTC"):
            result = format_secret(secret, as_json=False)

        snapshot.assert_match(result)

    def test_format_secret_with_all_scopes(self, snapshot):
        """Test formatting secret with all scope types enabled."""
        from dagster_shared.utils.timing import fixed_timezone

        secret = DgApiSecret(
            id="multi-scope-secret-uuid",
            secretName="multi_scope_secret",
            secretValue="multi_scope_value",
            locationNames=["location1", "location2"],
            fullDeploymentScope=True,
            allBranchDeploymentsScope=True,
            specificBranchDeploymentScope="feature-branch",
            localDeploymentScope=True,
            canViewSecretValue=True,
            canEditSecret=False,
            updatedBy=DgApiUpdatedBy(email="system@company.com"),
            updateTimestamp=datetime(2022, 1, 1, 14, 22, 0),
        )
        with fixed_timezone("UTC"):
            result = format_secret(secret, as_json=False)

        snapshot.assert_match(result)

    def test_format_secret_no_permissions(self, snapshot):
        """Test formatting secret with no permissions."""
        from dagster_shared.utils.timing import fixed_timezone

        secret = DgApiSecret(
            id="no-perm-secret-uuid",
            secretName="restricted_secret",
            secretValue=None,  # No access to value
            locationNames=["secure_location"],
            fullDeploymentScope=False,
            allBranchDeploymentsScope=False,
            specificBranchDeploymentScope=None,
            localDeploymentScope=False,
            canViewSecretValue=False,
            canEditSecret=False,
            updatedBy=DgApiUpdatedBy(email="admin@company.com"),
            updateTimestamp=datetime(2022, 1, 1, 14, 23, 0),
        )
        with fixed_timezone("UTC"):
            result = format_secret(secret, as_json=False)

        snapshot.assert_match(result)

    def test_format_secret_value_hiding_in_json_format(self):
        """Test that secret values are properly hidden in JSON output when requested."""
        secret = DgApiSecret(
            id="value-hiding-test",
            secretName="secret_with_value",
            secretValue="super_secret_password",
            locationNames=["secure_app"],
            fullDeploymentScope=True,
            allBranchDeploymentsScope=False,
            specificBranchDeploymentScope=None,
            localDeploymentScope=False,
            canViewSecretValue=True,
            canEditSecret=True,
            updatedBy=None,
            updateTimestamp=None,
        )

        # Test with show_value=False (default) - should hide value
        result_hidden = format_secret(secret, as_json=True, show_value=False)
        import json

        parsed_hidden = json.loads(result_hidden)
        assert parsed_hidden["value"] == "<hidden>"

        # Test with show_value=True - should show actual value
        result_shown = format_secret(secret, as_json=True, show_value=True)
        parsed_shown = json.loads(result_shown)
        assert parsed_shown["value"] == "super_secret_password"
