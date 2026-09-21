from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.fragments import SecretFieldsUpdatedBy
from dagster_rest_resources.__generated__.get_secret_with_value import (
    GetSecretWithValue,
    GetSecretWithValueSecretsOrErrorSecrets,
    GetSecretWithValueSecretsOrErrorSecretsSecrets,
)
from dagster_rest_resources.__generated__.list_secrets import (
    ListSecrets,
    ListSecretsSecretsOrErrorPythonError,
    ListSecretsSecretsOrErrorSecrets,
    ListSecretsSecretsOrErrorSecretsSecrets,
    ListSecretsSecretsOrErrorUnauthorizedError,
)
from dagster_rest_resources.api.secret import DgApiSecretApi
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)
from dagster_rest_resources.schemas.secret import DgApiSecretList


def _make_secret(
    id: str = "secret-id",
    secret_name: str = "test-name",
    location_names: list[str] | None = None,
    full_deployment_scope: bool = True,
    all_branch_deployments_scope: bool = False,
    specific_branch_deployment_scope: str | None = None,
    local_deployment_scope: bool = False,
    can_view_secret_value: bool = True,
    can_edit_secret: bool = True,
    updated_by_email: str | None = "test@email",
    update_timestamp: float | None = 1234567890.0,
) -> ListSecretsSecretsOrErrorSecretsSecrets:
    return ListSecretsSecretsOrErrorSecretsSecrets(
        id=id,
        secretName=secret_name,
        locationNames=location_names or [],
        fullDeploymentScope=full_deployment_scope,
        allBranchDeploymentsScope=all_branch_deployments_scope,
        specificBranchDeploymentScope=specific_branch_deployment_scope,
        localDeploymentScope=local_deployment_scope,
        canViewSecretValue=can_view_secret_value,
        canEditSecret=can_edit_secret,
        updatedBy=None
        if updated_by_email is None
        else SecretFieldsUpdatedBy(email=updated_by_email),
        updateTimestamp=update_timestamp,
    )


class TestListSecrets:
    def test_returns_secrets(self):
        client = Mock(spec=IGraphQLClient)
        client.list_secrets.return_value = ListSecrets(
            secretsOrError=ListSecretsSecretsOrErrorSecrets(
                __typename="Secrets",
                secrets=[
                    _make_secret(id="id-1"),
                    _make_secret(id="id-2"),
                ],
            )
        )

        result = DgApiSecretApi(_client=client).list_secrets()

        assert result.total == 2
        assert result.items[0].id == "id-1"
        assert result.items[1].id == "id-2"

    def test_returns_empty_list(self):
        client = Mock(spec=IGraphQLClient)
        client.list_secrets.return_value = ListSecrets(
            secretsOrError=ListSecretsSecretsOrErrorSecrets(
                __typename="Secrets",
                secrets=[],
            )
        )

        result = DgApiSecretApi(_client=client).list_secrets()

        assert result == DgApiSecretList(items=[], total=0)

    def test_none_response_returns_empty(self):
        client = Mock(spec=IGraphQLClient)
        client.list_secrets.return_value = ListSecrets(secretsOrError=None)

        result = DgApiSecretApi(_client=client).list_secrets()

        assert result == DgApiSecretList(items=[], total=0)

    def test_truncates_to_limit(self):
        client = Mock(spec=IGraphQLClient)
        client.list_secrets.return_value = ListSecrets(
            secretsOrError=ListSecretsSecretsOrErrorSecrets(
                __typename="Secrets",
                secrets=[_make_secret(id=f"id-{i}") for i in range(5)],
            )
        )

        result = DgApiSecretApi(_client=client).list_secrets(limit=2)

        assert result.total == 5
        assert len(result.items) == 2
        assert result.items[0].id == "id-0"
        assert result.items[1].id == "id-1"

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_secrets.return_value = ListSecrets(
            secretsOrError=ListSecretsSecretsOrErrorUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error listing secrets"):
            DgApiSecretApi(_client=client).list_secrets()

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_secrets.return_value = ListSecrets(
            secretsOrError=ListSecretsSecretsOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error listing secrets"):
            DgApiSecretApi(_client=client).list_secrets()


class TestGetSecret:
    def test_returns_secret(self):
        client = Mock(spec=IGraphQLClient)
        client.list_secrets.return_value = ListSecrets(
            secretsOrError=ListSecretsSecretsOrErrorSecrets(
                __typename="Secrets",
                secrets=[
                    ListSecretsSecretsOrErrorSecretsSecrets(
                        id="id-1",
                        secretName="test-name",
                        locationNames=["loc-a", "loc-b"],
                        fullDeploymentScope=True,
                        allBranchDeploymentsScope=False,
                        specificBranchDeploymentScope="main",
                        localDeploymentScope=False,
                        canViewSecretValue=True,
                        canEditSecret=True,
                        updatedBy=SecretFieldsUpdatedBy(email="user@example.com"),
                        updateTimestamp=1234567890.0,
                    )
                ],
            )
        )

        result = DgApiSecretApi(_client=client).get_secret("test-name")

        assert result.id == "id-1"
        assert result.name == "test-name"
        assert result.location_names == ["loc-a", "loc-b"]
        assert result.full_deployment_scope is True
        assert result.all_branch_deployments_scope is False
        assert result.specific_branch_deployment_scope == "main"
        assert result.local_deployment_scope is False
        assert result.can_view_secret_value is True
        assert result.can_edit_secret is True
        assert result.updated_by is not None
        assert result.updated_by.email == "user@example.com"
        assert result.update_timestamp == 1234567890.0

        assert result.value is None

    def test_returns_secret_with_value(self):
        client = Mock(spec=IGraphQLClient)
        client.get_secret_with_value.return_value = GetSecretWithValue(
            secretsOrError=GetSecretWithValueSecretsOrErrorSecrets(
                __typename="Secrets",
                secrets=[
                    GetSecretWithValueSecretsOrErrorSecretsSecrets(
                        id="id-1",
                        secretName="test-name",
                        secretValue="test-value",
                        locationNames=["loc-a", "loc-b"],
                        fullDeploymentScope=True,
                        allBranchDeploymentsScope=False,
                        specificBranchDeploymentScope="main",
                        localDeploymentScope=False,
                        canViewSecretValue=True,
                        canEditSecret=True,
                        updatedBy=SecretFieldsUpdatedBy(email="user@example.com"),
                        updateTimestamp=1234567890.0,
                    )
                ],
            )
        )

        result = DgApiSecretApi(_client=client).get_secret("my_secret", include_value=True)

        assert result.id == "id-1"
        assert result.name == "test-name"
        assert result.location_names == ["loc-a", "loc-b"]
        assert result.full_deployment_scope is True
        assert result.all_branch_deployments_scope is False
        assert result.specific_branch_deployment_scope == "main"
        assert result.local_deployment_scope is False
        assert result.can_view_secret_value is True
        assert result.can_edit_secret is True
        assert result.updated_by is not None
        assert result.updated_by.email == "user@example.com"
        assert result.update_timestamp == 1234567890.0

        assert result.value == "test-value"

    def test_none_response_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_secrets.return_value = ListSecrets(secretsOrError=None)

        with pytest.raises(DagsterPlusGraphqlError, match="Secret 'none' not found"):
            DgApiSecretApi(_client=client).get_secret("none")

    def test_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_secrets.return_value = ListSecrets(
            secretsOrError=ListSecretsSecretsOrErrorSecrets(
                __typename="Secrets",
                secrets=[],
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Secret 'missing' not found"):
            DgApiSecretApi(_client=client).get_secret("missing")

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_secrets.return_value = ListSecrets(
            secretsOrError=ListSecretsSecretsOrErrorUnauthorizedError(
                __typename="UnauthorizedError", message=""
            )
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error fetching secret"):
            DgApiSecretApi(_client=client).get_secret("test-name")

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.list_secrets.return_value = ListSecrets(
            secretsOrError=ListSecretsSecretsOrErrorPythonError(
                __typename="PythonError", message=""
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error fetching secret"):
            DgApiSecretApi(_client=client).get_secret("test-name")
