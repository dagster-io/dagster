from unittest.mock import Mock

import pytest
from dagster_rest_resources.__generated__.delete_deployment import (
    DeleteDeployment,
    DeleteDeploymentDeleteDeploymentDagsterCloudDeployment,
    DeleteDeploymentDeleteDeploymentDeleteFinalDeploymentError,
    DeleteDeploymentDeleteDeploymentDeploymentNotFoundError,
    DeleteDeploymentDeleteDeploymentPythonError,
    DeleteDeploymentDeleteDeploymentUnauthorizedError,
)
from dagster_rest_resources.__generated__.enums import DagsterCloudDeploymentType
from dagster_rest_resources.__generated__.get_deployment import (
    GetDeployment,
    GetDeploymentDeploymentByNameDagsterCloudDeployment,
    GetDeploymentDeploymentByNameDeploymentNotFoundError,
    GetDeploymentDeploymentByNamePythonError,
    GetDeploymentDeploymentByNameUnauthorizedError,
)
from dagster_rest_resources.__generated__.get_deployment_settings import (
    GetDeploymentSettings,
    GetDeploymentSettingsDeploymentSettings,
)
from dagster_rest_resources.__generated__.list_branch_deployments import (
    ListBranchDeployments,
    ListBranchDeploymentsBranchDeployments,
    ListBranchDeploymentsBranchDeploymentsNodes,
)
from dagster_rest_resources.__generated__.list_deployments import (
    ListDeployments,
    ListDeploymentsFullDeployments,
)
from dagster_rest_resources.__generated__.set_deployment_settings import (
    SetDeploymentSettings,
    SetDeploymentSettingsSetDeploymentSettingsDeleteFinalDeploymentError,
    SetDeploymentSettingsSetDeploymentSettingsDeploymentNotFoundError,
    SetDeploymentSettingsSetDeploymentSettingsDeploymentSettings,
    SetDeploymentSettingsSetDeploymentSettingsDuplicateDeploymentError,
    SetDeploymentSettingsSetDeploymentSettingsPythonError,
    SetDeploymentSettingsSetDeploymentSettingsUnauthorizedError,
)
from dagster_rest_resources.api.deployment import DgApiDeploymentApi
from dagster_rest_resources.gql_client import IGraphQLClient
from dagster_rest_resources.schemas.deployment import DgApiDeploymentList, DgApiDeploymentSettings
from dagster_rest_resources.schemas.exception import (
    DagsterPlusGraphqlError,
    DagsterPlusUnauthorizedError,
    UnconfirmedProdDeletionError,
)


class TestListDeployments:
    def test_returns_deployments(self):
        client = Mock(spec=IGraphQLClient)
        client.list_deployments.return_value = ListDeployments(
            fullDeployments=[
                ListDeploymentsFullDeployments(
                    deploymentId=1,
                    deploymentName="prod",
                    deploymentType=DagsterCloudDeploymentType.PRODUCTION,
                ),
                ListDeploymentsFullDeployments(
                    deploymentId=2,
                    deploymentName="branch",
                    deploymentType=DagsterCloudDeploymentType.BRANCH,
                ),
            ]
        )

        result = DgApiDeploymentApi(_client=client).list_deployments()

        assert result.total == 2
        assert result.items[0].id == 1
        assert result.items[1].id == 2

    def test_returns_empty(self):
        client = Mock(spec=IGraphQLClient)
        client.list_deployments.return_value = ListDeployments(fullDeployments=[])

        result = DgApiDeploymentApi(_client=client).list_deployments()

        assert result == DgApiDeploymentList(items=[], total=0)


class TestListBranchDeployments:
    def test_returns_branch_deployments(self):
        client = Mock(spec=IGraphQLClient)
        client.list_branch_deployments.return_value = ListBranchDeployments(
            branchDeployments=ListBranchDeploymentsBranchDeployments(
                nodes=[
                    ListBranchDeploymentsBranchDeploymentsNodes(
                        deploymentId=1,
                        deploymentName="test-deployment-name",
                        deploymentType=DagsterCloudDeploymentType.BRANCH,
                    ),
                ]
            )
        )

        result = DgApiDeploymentApi(_client=client).list_branch_deployments()

        assert result.total == 1
        assert result.items[0].id == 1

    def test_returns_empty(self):
        client = Mock(spec=IGraphQLClient)
        client.list_branch_deployments.return_value = ListBranchDeployments(
            branchDeployments=ListBranchDeploymentsBranchDeployments(nodes=[])
        )

        result = DgApiDeploymentApi(_client=client).list_branch_deployments()

        assert result == DgApiDeploymentList(items=[], total=0)


class TestGetDeployment:
    def test_returns_deployment(self):
        client = Mock(spec=IGraphQLClient)
        client.get_deployment.return_value = GetDeployment(
            deploymentByName=GetDeploymentDeploymentByNameDagsterCloudDeployment(
                __typename="DagsterCloudDeployment",
                deploymentId=1,
                deploymentName="prod",
                deploymentType=DagsterCloudDeploymentType.PRODUCTION,
            )
        )

        result = DgApiDeploymentApi(_client=client).get_deployment("prod")

        assert result.id == 1

    def test_not_found_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_deployment.return_value = GetDeployment(
            deploymentByName=GetDeploymentDeploymentByNameDeploymentNotFoundError(
                __typename="DeploymentNotFoundError",
                message="",
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Deployment not found"):
            DgApiDeploymentApi(_client=client).get_deployment("missing")

    def test_unauthorized_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_deployment.return_value = GetDeployment(
            deploymentByName=GetDeploymentDeploymentByNameUnauthorizedError(
                __typename="UnauthorizedError",
                message="",
            )
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error retrieving deployment"):
            DgApiDeploymentApi(_client=client).get_deployment("missing")

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.get_deployment.return_value = GetDeployment(
            deploymentByName=GetDeploymentDeploymentByNamePythonError(
                __typename="PythonError",
                message="",
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error retrieving deployment"):
            DgApiDeploymentApi(_client=client).get_deployment("prod")


class TestGetDeploymentSettings:
    def test_returns_settings(self):
        client = Mock(spec=IGraphQLClient)
        client.get_deployment_settings.return_value = GetDeploymentSettings(
            deploymentSettings=GetDeploymentSettingsDeploymentSettings(settings={"run_queue": {}})
        )

        result = DgApiDeploymentApi(_client=client).get_deployment_settings()

        assert result.settings == {"run_queue": {}}

    def test_returns_empty_when_none(self):
        client = Mock(spec=IGraphQLClient)
        client.get_deployment_settings.return_value = GetDeploymentSettings(deploymentSettings=None)

        result = DgApiDeploymentApi(_client=client).get_deployment_settings()

        assert result == DgApiDeploymentSettings(settings={})


class TestUpdateDeploymentSettings:
    def test_returns_settings(self):
        client = Mock(spec=IGraphQLClient)
        client.set_deployment_settings.return_value = SetDeploymentSettings(
            setDeploymentSettings=SetDeploymentSettingsSetDeploymentSettingsDeploymentSettings(
                __typename="DeploymentSettings",
                settings={"run_queue": {}},
            )
        )

        result = DgApiDeploymentApi(_client=client).update_deployment_settings(
            DgApiDeploymentSettings(settings={"run_queue": {}})
        )

        assert result.settings == {"run_queue": {}}

    def test_deployment_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.set_deployment_settings.return_value = SetDeploymentSettings(
            setDeploymentSettings=SetDeploymentSettingsSetDeploymentSettingsDeploymentNotFoundError(
                __typename="DeploymentNotFoundError",
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Deployment not found"):
            DgApiDeploymentApi(_client=client).update_deployment_settings(
                DgApiDeploymentSettings(settings={})
            )

    def test_duplicate_deployment_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.set_deployment_settings.return_value = SetDeploymentSettings(
            setDeploymentSettings=SetDeploymentSettingsSetDeploymentSettingsDuplicateDeploymentError(
                __typename="DuplicateDeploymentError",
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Duplicate deployment error"):
            DgApiDeploymentApi(_client=client).update_deployment_settings(
                DgApiDeploymentSettings(settings={})
            )

    def test_delete_final_deployment_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.set_deployment_settings.return_value = SetDeploymentSettings(
            setDeploymentSettings=SetDeploymentSettingsSetDeploymentSettingsDeleteFinalDeploymentError(
                __typename="DeleteFinalDeploymentError",
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Cannot delete the final deployment"):
            DgApiDeploymentApi(_client=client).update_deployment_settings(
                DgApiDeploymentSettings(settings={})
            )

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.set_deployment_settings.return_value = SetDeploymentSettings(
            setDeploymentSettings=SetDeploymentSettingsSetDeploymentSettingsUnauthorizedError(
                __typename="UnauthorizedError",
                message="",
            )
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Error setting deployment settings"):
            DgApiDeploymentApi(_client=client).update_deployment_settings(
                DgApiDeploymentSettings(settings={})
            )

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        client.set_deployment_settings.return_value = SetDeploymentSettings(
            setDeploymentSettings=SetDeploymentSettingsSetDeploymentSettingsPythonError(
                __typename="PythonError",
                message="",
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error setting deployment settings"):
            DgApiDeploymentApi(_client=client).update_deployment_settings(
                DgApiDeploymentSettings(settings={})
            )


class TestDeleteDeployment:
    def _setup_get_deployment(
        self,
        client: Mock,
        deployment_id: int,
        name: str,
        deployment_type: DagsterCloudDeploymentType,
    ):
        client.get_deployment.return_value = GetDeployment(
            deploymentByName=GetDeploymentDeploymentByNameDagsterCloudDeployment(
                __typename="DagsterCloudDeployment",
                deploymentId=deployment_id,
                deploymentName=name,
                deploymentType=deployment_type,
            )
        )

    def test_deletes_branch_deployment(self):
        client = Mock(spec=IGraphQLClient)
        self._setup_get_deployment(client, 1, "branch", DagsterCloudDeploymentType.BRANCH)
        client.delete_deployment.return_value = DeleteDeployment(
            deleteDeployment=DeleteDeploymentDeleteDeploymentDagsterCloudDeployment(
                __typename="DagsterCloudDeployment",
                deploymentId=1,
                deploymentName="branch",
                deploymentType=DagsterCloudDeploymentType.BRANCH,
            )
        )

        result = DgApiDeploymentApi(_client=client).delete_deployment("branch")

        assert result.id == 1

    def test_production_without_flag_raises(self):
        client = Mock(spec=IGraphQLClient)
        self._setup_get_deployment(client, 1, "prod", DagsterCloudDeploymentType.PRODUCTION)

        with pytest.raises(UnconfirmedProdDeletionError, match="production deployment"):
            DgApiDeploymentApi(_client=client).delete_deployment("prod")

    def test_production_with_flag_succeeds(self):
        client = Mock(spec=IGraphQLClient)
        self._setup_get_deployment(client, 1, "prod", DagsterCloudDeploymentType.PRODUCTION)
        client.delete_deployment.return_value = DeleteDeployment(
            deleteDeployment=DeleteDeploymentDeleteDeploymentDagsterCloudDeployment(
                __typename="DagsterCloudDeployment",
                deploymentId=1,
                deploymentName="prod",
                deploymentType=DagsterCloudDeploymentType.PRODUCTION,
            )
        )

        result = DgApiDeploymentApi(_client=client).delete_deployment(
            "prod", allow_full_deployment=True
        )

        assert result.id == 1

    def test_not_found_raises(self):
        client = Mock(spec=IGraphQLClient)
        self._setup_get_deployment(client, 1, "branch", DagsterCloudDeploymentType.BRANCH)
        client.delete_deployment.return_value = DeleteDeployment(
            deleteDeployment=DeleteDeploymentDeleteDeploymentDeploymentNotFoundError(
                __typename="DeploymentNotFoundError",
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Deployment not found"):
            DgApiDeploymentApi(_client=client).delete_deployment("branch")

    def test_delete_final_deployment_raises(self):
        client = Mock(spec=IGraphQLClient)
        self._setup_get_deployment(client, 1, "branch", DagsterCloudDeploymentType.BRANCH)
        client.delete_deployment.return_value = DeleteDeployment(
            deleteDeployment=DeleteDeploymentDeleteDeploymentDeleteFinalDeploymentError(
                __typename="DeleteFinalDeploymentError",
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Cannot delete the final deployment"):
            DgApiDeploymentApi(_client=client).delete_deployment("branch")

    def test_unauthorized_raises(self):
        client = Mock(spec=IGraphQLClient)
        self._setup_get_deployment(client, 1, "branch", DagsterCloudDeploymentType.BRANCH)
        client.delete_deployment.return_value = DeleteDeployment(
            deleteDeployment=DeleteDeploymentDeleteDeploymentUnauthorizedError(
                __typename="UnauthorizedError",
            )
        )

        with pytest.raises(DagsterPlusUnauthorizedError, match="Unauthorized to delete deployment"):
            DgApiDeploymentApi(_client=client).delete_deployment("branch")

    def test_python_error_raises(self):
        client = Mock(spec=IGraphQLClient)
        self._setup_get_deployment(client, 1, "branch", DagsterCloudDeploymentType.BRANCH)
        client.delete_deployment.return_value = DeleteDeployment(
            deleteDeployment=DeleteDeploymentDeleteDeploymentPythonError(
                __typename="PythonError",
                message="",
            )
        )

        with pytest.raises(DagsterPlusGraphqlError, match="Error deleting deployment"):
            DgApiDeploymentApi(_client=client).delete_deployment("branch")
