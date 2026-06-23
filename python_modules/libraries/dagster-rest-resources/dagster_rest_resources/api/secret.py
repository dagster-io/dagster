from dataclasses import dataclass

from typing_extensions import assert_never

from dagster_rest_resources.__generated__.fragments import SecretFields
from dagster_rest_resources.__generated__.get_secret_with_value import (
    GetSecretWithValueSecretsOrErrorSecretsSecrets,
)
from dagster_rest_resources.__generated__.input_types import SecretScopesInput
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
)
from dagster_rest_resources.schemas.secret import DgApiSecret, DgApiSecretList, DgApiUpdatedBy


def _build_scopes_input(scope: str | None) -> SecretScopesInput:
    if scope == "deployment":
        return SecretScopesInput(
            fullDeploymentScope=True,
            localDeploymentScope=True,
        )
    else:
        return SecretScopesInput(
            fullDeploymentScope=True,
            localDeploymentScope=True,
            allBranchDeploymentsScope=True,
        )


@dataclass(frozen=True)
class DgApiSecretApi:
    _client: IGraphQLClient

    def list_secrets(
        self,
        location_name: str | None = None,
        scope: str | None = None,
        limit: int | None = None,
    ) -> DgApiSecretList:
        response = self._client.list_secrets(
            location_name=location_name,
            scopes=_build_scopes_input(scope),
        )
        result = response.secrets_or_error
        if result is None:
            return DgApiSecretList(items=[], total=0)

        match result.typename__:
            case "Secrets":
                items = [self._build_secret(s) for s in result.secrets]  # ty: ignore[unresolved-attribute]
                return DgApiSecretList(
                    items=items[:limit] if limit is not None else items,
                    total=len(items),
                )
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(f"Error listing secrets: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error listing secrets: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def get_secret(
        self,
        secret_name: str,
        location_name: str | None = None,
        include_value: bool = False,
    ) -> DgApiSecret:
        scopes = _build_scopes_input(scope=None)

        result = (
            self._client.get_secret_with_value(
                location_name=location_name,
                scopes=scopes,
                secret_name=secret_name,
            )
            if include_value
            else self._client.list_secrets(
                location_name=location_name,
                scopes=scopes,
                secret_name=secret_name,
            )
        ).secrets_or_error
        if result is None:
            raise DagsterPlusGraphqlError(f"Secret '{secret_name}' not found")

        match result.typename__:
            case "Secrets":
                if not result.secrets:  # ty: ignore[unresolved-attribute]
                    raise DagsterPlusGraphqlError(f"Secret '{secret_name}' not found")
                secret = result.secrets[0]  # ty: ignore[unresolved-attribute]
                return self._build_secret(
                    secret,
                    value=secret.secret_value
                    if isinstance(secret, GetSecretWithValueSecretsOrErrorSecretsSecrets)
                    else None,
                )
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(f"Error fetching secret: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error fetching secret: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def _build_secret(
        self,
        secret: SecretFields,
        value: str | None = None,
    ) -> DgApiSecret:
        return DgApiSecret(
            id=secret.id,
            name=secret.secret_name,
            value=value,
            location_names=list(secret.location_names),
            full_deployment_scope=secret.full_deployment_scope,
            all_branch_deployments_scope=secret.all_branch_deployments_scope,
            specific_branch_deployment_scope=secret.specific_branch_deployment_scope,
            local_deployment_scope=secret.local_deployment_scope,
            can_view_secret_value=secret.can_view_secret_value,
            can_edit_secret=secret.can_edit_secret,
            updated_by=DgApiUpdatedBy(email=secret.updated_by.email) if secret.updated_by else None,
            update_timestamp=secret.update_timestamp,
        )
