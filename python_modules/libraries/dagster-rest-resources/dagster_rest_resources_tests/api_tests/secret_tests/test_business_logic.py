"""Test secret business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

from datetime import datetime

from dagster_rest_resources.schemas.secret import (
    DgApiSecret,
    DgApiSecretList,
    DgApiSecretScopesInput,
    DgApiUpdatedBy,
)


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
                secretName=f"scope_test_secret_{i}",
                secretValue=f"test_value_{i}",
                locationNames=[f"location_{i}"],
                fullDeploymentScope=scopes.get("full_deployment_scope", False),
                allBranchDeploymentsScope=scopes.get("all_branch_deployments_scope", False),
                specificBranchDeploymentScope=scopes.get("specific_branch_deployment_scope", None),
                localDeploymentScope=scopes.get("local_deployment_scope", False),
                canViewSecretValue=True,
                canEditSecret=True,
                updatedBy=DgApiUpdatedBy(email=f"user{i}@company.com"),
                updateTimestamp=datetime(2022, 1, 1, 14, 20, i),
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
            secretName="updated_by_test",
            secretValue="test_value",
            locationNames=["test_location"],
            fullDeploymentScope=True,
            allBranchDeploymentsScope=False,
            specificBranchDeploymentScope=None,
            localDeploymentScope=False,
            canViewSecretValue=True,
            canEditSecret=True,
            updatedBy=DgApiUpdatedBy(email="test@company.com"),
            updateTimestamp=datetime(2022, 1, 1, 14, 20, 0),
        )

        assert secret.updated_by is not None
        assert secret.updated_by.email == "test@company.com"
        assert secret.update_timestamp == datetime(2022, 1, 1, 14, 20, 0)

    def test_secret_list_total_count(self):
        """Test that SecretList properly tracks total count."""
        secrets = [
            DgApiSecret(
                id=f"secret-{i}",
                secretName=f"secret_{i}",
                secretValue=f"value_{i}",
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
            fullDeploymentScope=True,
            allBranchDeploymentsScope=False,
            specificBranchDeploymentScope="main",
            localDeploymentScope=True,
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
            fullDeploymentScope=True,
            allBranchDeploymentsScope=None,
            specificBranchDeploymentScope=None,
            localDeploymentScope=False,
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
                secretName=f"permission_test_{i}",
                secretValue="test_value" if perms["can_view_secret_value"] else None,
                locationNames=[],
                fullDeploymentScope=True,
                allBranchDeploymentsScope=False,
                specificBranchDeploymentScope=None,
                localDeploymentScope=False,
                canViewSecretValue=perms["can_view_secret_value"],
                canEditSecret=perms["can_edit_secret"],
                updatedBy=None,
                updateTimestamp=None,
            )

            assert secret.can_view_secret_value == perms["can_view_secret_value"]
            assert secret.can_edit_secret == perms["can_edit_secret"]
