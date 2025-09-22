"""Test secret business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

from datetime import datetime

from dagster_dg_cli.api_layer.schemas.secret import (
    DgApiSecret,
    DgApiSecretList,
    DgApiSecretScopesInput,
    DgApiUpdatedBy,
)
from dagster_dg_cli.cli.api.formatters import format_secret, format_secrets


class TestFormatSecrets:
    """Test the secret formatting functions."""

    def _create_sample_secret_list(self):
        """Create sample SecretList for testing."""
        secrets = [
            DgApiSecret(
                id="secret-1-uuid-12345",
                name="database_password",
                value="super_secret_value",  # Would be hidden in actual output
                location_names=["data_pipeline", "analytics"],
                full_deployment_scope=True,
                all_branch_deployments_scope=False,
                specific_branch_deployment_scope=None,
                local_deployment_scope=False,
                can_view_secret_value=True,
                can_edit_secret=True,
                updated_by=DgApiUpdatedBy(email="admin@company.com"),
                update_timestamp=datetime(
                    2022, 1, 1, 14, 20, 0
                ),  # UTC to avoid timezone edge cases
            ),
            DgApiSecret(
                id="secret-2-uuid-67890",
                name="api_key",
                value=None,  # No value - might not have permission to view
                location_names=[],  # All locations
                full_deployment_scope=False,
                all_branch_deployments_scope=True,
                specific_branch_deployment_scope=None,
                local_deployment_scope=False,
                can_view_secret_value=False,
                can_edit_secret=False,
                updated_by=None,
                update_timestamp=None,
            ),
            DgApiSecret(
                id="secret-3-uuid-abcdef",
                name="staging_token",
                value="staging_value_123",
                location_names=["staging_app"],
                full_deployment_scope=False,
                all_branch_deployments_scope=False,
                specific_branch_deployment_scope="staging",
                local_deployment_scope=True,
                can_view_secret_value=True,
                can_edit_secret=True,
                updated_by=DgApiUpdatedBy(email="dev@company.com"),
                update_timestamp=datetime(2022, 1, 1, 14, 21, 0),  # UTC
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
            name="development_secret",
            value="dev_secret_value",
            location_names=["dev_pipeline", "test_pipeline"],
            full_deployment_scope=False,
            all_branch_deployments_scope=False,
            specific_branch_deployment_scope=None,
            local_deployment_scope=True,
            can_view_secret_value=True,
            can_edit_secret=True,
            updated_by=DgApiUpdatedBy(email="developer@company.com"),
            update_timestamp=datetime(2022, 1, 1, 14, 20, 0),
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
            name="simple_secret",
            value="simple_value",
            location_names=[],
            full_deployment_scope=True,
            all_branch_deployments_scope=False,
            specific_branch_deployment_scope=None,
            local_deployment_scope=False,
            can_view_secret_value=True,
            can_edit_secret=True,
            updated_by=None,
            update_timestamp=None,
        )
        with fixed_timezone("UTC"):
            result = format_secret(secret, as_json=False)

        snapshot.assert_match(result)

    def test_format_secret_with_all_scopes(self, snapshot):
        """Test formatting secret with all scope types enabled."""
        from dagster_shared.utils.timing import fixed_timezone

        secret = DgApiSecret(
            id="multi-scope-secret-uuid",
            name="multi_scope_secret",
            value="multi_scope_value",
            location_names=["location1", "location2"],
            full_deployment_scope=True,
            all_branch_deployments_scope=True,
            specific_branch_deployment_scope="feature-branch",
            local_deployment_scope=True,
            can_view_secret_value=True,
            can_edit_secret=False,
            updated_by=DgApiUpdatedBy(email="system@company.com"),
            update_timestamp=datetime(2022, 1, 1, 14, 22, 0),
        )
        with fixed_timezone("UTC"):
            result = format_secret(secret, as_json=False)

        snapshot.assert_match(result)

    def test_format_secret_no_permissions(self, snapshot):
        """Test formatting secret with no permissions."""
        from dagster_shared.utils.timing import fixed_timezone

        secret = DgApiSecret(
            id="no-perm-secret-uuid",
            name="restricted_secret",
            value=None,  # No access to value
            location_names=["secure_location"],
            full_deployment_scope=False,
            all_branch_deployments_scope=False,
            specific_branch_deployment_scope=None,
            local_deployment_scope=False,
            can_view_secret_value=False,
            can_edit_secret=False,
            updated_by=DgApiUpdatedBy(email="admin@company.com"),
            update_timestamp=datetime(2022, 1, 1, 14, 23, 0),
        )
        with fixed_timezone("UTC"):
            result = format_secret(secret, as_json=False)

        snapshot.assert_match(result)


class TestSecretDataProcessing:
    """Test processing of secret data structures.

    This class tests any pure functions that process the raw GraphQL responses
    into our domain models and data model creation.
    """

    def test_secret_creation_with_all_scopes(self, snapshot):
        """Test creating secrets with all possible scope combinations."""
        secrets = []

        # Test different scope combinations
        scope_combinations = [
            {"full_deployment_scope": True, "all_branch_deployments_scope": False},
            {"full_deployment_scope": False, "all_branch_deployments_scope": True},
            {
                "full_deployment_scope": False,
                "all_branch_deployments_scope": False,
                "specific_branch_deployment_scope": "main",
            },
            {"local_deployment_scope": True},
            {
                "full_deployment_scope": True,
                "all_branch_deployments_scope": True,
                "local_deployment_scope": True,
            },
        ]

        for i, scopes in enumerate(scope_combinations):
            secret = DgApiSecret(
                id=f"scope-test-secret-{i}",
                name=f"scope_test_secret_{i}",
                value=f"test_value_{i}",
                location_names=[f"location_{i}"],
                full_deployment_scope=scopes.get("full_deployment_scope", False),
                all_branch_deployments_scope=scopes.get("all_branch_deployments_scope", False),
                specific_branch_deployment_scope=scopes.get(
                    "specific_branch_deployment_scope", None
                ),
                local_deployment_scope=scopes.get("local_deployment_scope", False),
                can_view_secret_value=True,
                can_edit_secret=True,
                updated_by=DgApiUpdatedBy(email=f"user{i}@company.com"),
                update_timestamp=datetime(2022, 1, 1, 14, 20, i),
            )
            secrets.append(secret)

        secret_list = DgApiSecretList(items=secrets, total=len(secrets))

        # Test JSON serialization works correctly for all scopes
        result = secret_list.model_dump_json(indent=2)
        import json

        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_secret_updated_by_handling(self):
        """Test secret updated_by entry creation and access."""
        secret = DgApiSecret(
            id="updated-by-test-secret",
            name="updated_by_test",
            value="test_value",
            location_names=["test_location"],
            full_deployment_scope=True,
            all_branch_deployments_scope=False,
            specific_branch_deployment_scope=None,
            local_deployment_scope=False,
            can_view_secret_value=True,
            can_edit_secret=True,
            updated_by=DgApiUpdatedBy(email="test@company.com"),
            update_timestamp=datetime(2022, 1, 1, 14, 20, 0),
        )

        assert secret.updated_by is not None
        assert secret.updated_by.email == "test@company.com"
        assert secret.update_timestamp == datetime(2022, 1, 1, 14, 20, 0)

    def test_secret_list_total_count(self):
        """Test that SecretList properly tracks total count."""
        secrets = [
            DgApiSecret(
                id=f"secret-{i}",
                name=f"secret_{i}",
                value=f"value_{i}",
                location_names=[],
                full_deployment_scope=True,
                all_branch_deployments_scope=False,
                specific_branch_deployment_scope=None,
                local_deployment_scope=False,
                can_view_secret_value=True,
                can_edit_secret=True,
                updated_by=None,
                update_timestamp=None,
            )
            for i in range(3)
        ]

        secret_list = DgApiSecretList(
            items=secrets, total=10
        )  # Total could be different from items length (pagination)

        assert len(secret_list.items) == 3
        assert secret_list.total == 10

    def test_secret_scopes_input_to_dict(self):
        """Test SecretScopesInput conversion to dict."""
        # Test with all fields
        scopes_input = DgApiSecretScopesInput(
            full_deployment_scope=True,
            all_branch_deployments_scope=False,
            specific_branch_deployment_scope="main",
            local_deployment_scope=True,
        )

        result = scopes_input.to_dict()
        expected = {
            "fullDeploymentScope": True,
            "allBranchDeploymentsScope": False,
            "specificBranchDeploymentScope": "main",
            "localDeploymentScope": True,
        }
        assert result == expected

        # Test with None values (should be excluded)
        scopes_input_sparse = DgApiSecretScopesInput(
            full_deployment_scope=True,
            all_branch_deployments_scope=None,
            specific_branch_deployment_scope=None,
            local_deployment_scope=False,
        )

        result_sparse = scopes_input_sparse.to_dict()
        expected_sparse = {
            "fullDeploymentScope": True,
            "localDeploymentScope": False,
        }
        assert result_sparse == expected_sparse

    def test_secret_permissions_combinations(self):
        """Test secret with various permission combinations."""
        permission_combos = [
            {"can_view_secret_value": True, "can_edit_secret": True},
            {"can_view_secret_value": True, "can_edit_secret": False},
            {"can_view_secret_value": False, "can_edit_secret": False},
            {"can_view_secret_value": False, "can_edit_secret": True},  # Unusual but possible
        ]

        for i, perms in enumerate(permission_combos):
            secret = DgApiSecret(
                id=f"perm-test-secret-{i}",
                name=f"permission_test_{i}",
                value="test_value" if perms["can_view_secret_value"] else None,
                location_names=[],
                full_deployment_scope=True,
                all_branch_deployments_scope=False,
                specific_branch_deployment_scope=None,
                local_deployment_scope=False,
                can_view_secret_value=perms["can_view_secret_value"],
                can_edit_secret=perms["can_edit_secret"],
                updated_by=None,
                update_timestamp=None,
            )

            assert secret.can_view_secret_value == perms["can_view_secret_value"]
            assert secret.can_edit_secret == perms["can_edit_secret"]

    def test_secret_value_hiding_in_json_format(self):
        """Test that secret values are properly hidden in JSON output when requested."""
        secret = DgApiSecret(
            id="value-hiding-test",
            name="secret_with_value",
            value="super_secret_password",
            location_names=["secure_app"],
            full_deployment_scope=True,
            all_branch_deployments_scope=False,
            specific_branch_deployment_scope=None,
            local_deployment_scope=False,
            can_view_secret_value=True,
            can_edit_secret=True,
            updated_by=None,
            update_timestamp=None,
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
