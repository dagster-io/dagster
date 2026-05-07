from dataclasses import dataclass

from typing_extensions import assert_never

from dagster_rest_resources.__generated__.enums import DagsterCloudDeploymentType, PullRequestStatus
from dagster_rest_resources.__generated__.input_types import DeploymentSettingsInput
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.deployment import (
    DgApiDeployment,
    DgApiDeploymentList,
    DgApiDeploymentSettings,
)
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
    UnconfirmedProdDeletionError,
)


@dataclass(frozen=True)
class DgApiDeploymentApi:
    _client: IGraphQLClient

    def list_deployments(self) -> DgApiDeploymentList:
        result = self._client.list_deployments()
        deployments = [
            DgApiDeployment(id=d.deployment_id, name=d.deployment_name, type=d.deployment_type)
            for d in result.full_deployments
        ]
        return DgApiDeploymentList(items=deployments, total=len(deployments))

    def list_branch_deployments(
        self, limit: int = 50, pull_request_status: PullRequestStatus | None = None
    ) -> DgApiDeploymentList:
        result = self._client.list_branch_deployments(
            limit=limit, pull_request_status=pull_request_status
        )
        deployments = [
            DgApiDeployment(id=d.deployment_id, name=d.deployment_name, type=d.deployment_type)
            for d in result.branch_deployments.nodes
        ]
        return DgApiDeploymentList(items=deployments, total=len(deployments))

    def get_deployment(self, name: str) -> DgApiDeployment:
        result = self._client.get_deployment(deployment_name=name).deployment_by_name

        match result.typename__:
            case "DagsterCloudDeployment":
                return DgApiDeployment(
                    id=result.deployment_id,  # ty: ignore[unresolved-attribute]
                    name=result.deployment_name,  # ty: ignore[unresolved-attribute]
                    type=result.deployment_type,  # ty: ignore[unresolved-attribute]
                )
            case "DeploymentNotFoundError":
                raise DagsterPlusGraphqlError(f"Deployment not found: {name}")
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(f"Error retrieving deployment: {result.message}")  # ty: ignore[unresolved-attribute]
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error retrieving deployment: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)

    def get_deployment_settings(self) -> DgApiDeploymentSettings:
        result = self._client.get_deployment_settings().deployment_settings
        if result is None:
            return DgApiDeploymentSettings(settings={})
        return DgApiDeploymentSettings(settings=result.settings or {})

    def update_deployment_settings(
        self, settings: DgApiDeploymentSettings
    ) -> DgApiDeploymentSettings:
        result = self._client.set_deployment_settings(
            deployment_settings=DeploymentSettingsInput(settings=settings.settings)
        ).set_deployment_settings

        match result.typename__:
            case "DeploymentSettings":
                return DgApiDeploymentSettings(settings=result.settings or {})  # ty: ignore[unresolved-attribute]
            case "DeploymentNotFoundError":
                raise DagsterPlusGraphqlError("Deployment not found")
            case "DuplicateDeploymentError":
                raise DagsterPlusGraphqlError("Duplicate deployment error")
            case "DeleteFinalDeploymentError":
                raise DagsterPlusGraphqlError("Cannot delete the final deployment")
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError(
                    f"Error setting deployment settings: {result.message}"  # ty: ignore[unresolved-attribute]
                )
            case "PythonError":
                raise DagsterPlusGraphqlError(
                    f"Error setting deployment settings: {result.message}"  # ty: ignore[unresolved-attribute]
                )
            case _ as unreachable:
                assert_never(unreachable)

    def delete_deployment(self, name: str, allow_full_deployment: bool = False) -> DgApiDeployment:
        deployment = self.get_deployment(name)

        if deployment.type == DagsterCloudDeploymentType.PRODUCTION and not allow_full_deployment:
            raise UnconfirmedProdDeletionError(f"Deployment '{name}' is a production deployment.")

        result = self._client.delete_deployment(deployment_id=deployment.id).delete_deployment

        match result.typename__:
            case "DagsterCloudDeployment":
                return DgApiDeployment(
                    id=result.deployment_id,  # ty: ignore[unresolved-attribute]
                    name=result.deployment_name,  # ty: ignore[unresolved-attribute]
                    type=result.deployment_type,  # ty: ignore[unresolved-attribute]
                )
            case "DeploymentNotFoundError":
                raise DagsterPlusGraphqlError(f"Deployment not found: {name}")
            case "DeleteFinalDeploymentError":
                raise DagsterPlusGraphqlError("Cannot delete the final deployment")
            case "UnauthorizedError":
                raise DagsterPlusUnauthorizedError("Unauthorized to delete deployment")
            case "PythonError":
                raise DagsterPlusGraphqlError(f"Error deleting deployment: {result.message}")  # ty: ignore[unresolved-attribute]
            case _ as unreachable:
                assert_never(unreachable)
