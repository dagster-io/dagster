from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from dagster._config import Field, Shape
from dagster._core.instance.types import T_DagsterInstance
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster._serdes.config_class import ConfigurableClass, ConfigurableClassData
from dagster_cloud_cli.core.artifacts import download_artifact, upload_artifact
from dagster_cloud_cli.core.headers.auth import DagsterCloudInstanceScope
from dagster_shared import check
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo

if TYPE_CHECKING:
    from dagster_cloud_cli.commands.ci.state import LocationState


GET_LATEST_DEFS_STATE_INFO_QUERY = """
    query getLatestDefsStateInfo {
        latestDefsStateInfo {
            keyStateInfo {
                name
                info {
                    version
                    createTimestamp
                }
            }
        }
    }
"""

SET_LATEST_VERSION_MUTATION = """
    mutation setLatestDefsStateVersion($key: String!, $version: String!) {
        setLatestDefsStateVersion(key: $key, version: $version) {
            ok
        }
    }
"""


class DagsterPlusCliDefsStateStorage(DefsStateStorage[T_DagsterInstance], ConfigurableClass):
    """DefsStateStorage that can be instantiated from a DagsterPlusCliConfig,
    intended for use within the CLI.
    """

    def __init__(
        self,
        url: str,
        api_token: str,
        deployment: str,
        graphql_client,
        organization: str,
        inst_data: Optional[ConfigurableClassData] = None,
    ):
        self._url = url
        self._api_token = api_token
        self._deployment = deployment
        self._graphql_client = graphql_client
        self._organization = organization
        self._inst_data = inst_data

    @classmethod
    def from_location_state(
        cls, location_state: "LocationState", api_token: str, organization: str
    ):
        from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient

        return cls(
            location_state.url,
            api_token,
            location_state.deployment_name,
            DagsterPlusGraphQLClient.from_location_state(location_state, api_token, organization),
            organization,
        )

    @property
    def inst_data(self) -> Optional[ConfigurableClassData]:
        return self._inst_data

    @classmethod
    def config_type(cls):
        return Shape(
            {
                "url": Field(str, is_required=True),
                "api_token": Field(str, is_required=True),
                "deployment": Field(str, is_required=True),
                "organization": Field(str, is_required=True),
            }
        )

    @classmethod
    def from_config_value(cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]):
        from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient

        url = check.str_param(config_value.get("url"), "url")
        api_token = check.str_param(config_value.get("api_token"), "api_token")
        deployment = check.str_param(config_value.get("deployment"), "deployment")
        organization = check.str_param(config_value.get("organization"), "organization")

        # Create graphql client from config
        graphql_client = DagsterPlusGraphQLClient(
            url=f"{url}/graphql",
            headers={
                "Dagster-Cloud-Api-Token": api_token,
                "Dagster-Cloud-Organization": organization,
                "Dagster-Cloud-Deployment": deployment,
            },
        )

        return cls(
            url=url,
            api_token=api_token,
            deployment=deployment,
            graphql_client=graphql_client,
            organization=organization,
            inst_data=inst_data,
        )

    @property
    def url(self) -> str:
        return self._url

    @property
    def api_token(self) -> str:
        return self._api_token

    @property
    def deployment(self) -> str:
        return self._deployment

    @property
    def graphql_client(self) -> Any:
        return self._graphql_client

    def _execute_query(self, query, variables=None):
        return self.graphql_client.execute(query, variables=variables)

    def _get_artifact_key(self, key: str, version: str) -> str:
        return f"__state__/{self._sanitize_key(key)}/{version}"

    def download_state_to_path(self, key: str, version: str, path: Path) -> None:
        download_artifact(
            url=self.url,
            scope=DagsterCloudInstanceScope.DEPLOYMENT,
            api_token=self.api_token,
            key=self._get_artifact_key(key, version),
            path=path,
            deployment=self.deployment,
        )

    def upload_state_from_path(self, key: str, version: str, path: Path) -> None:
        upload_artifact(
            url=self.url,
            scope=DagsterCloudInstanceScope.DEPLOYMENT,
            api_token=self.api_token,
            key=self._get_artifact_key(key, version),
            path=path,
            deployment=self.deployment,
        )
        self.set_latest_version(key, version)

    def get_latest_defs_state_info(self) -> Optional[DefsStateInfo]:
        res = self._execute_query(GET_LATEST_DEFS_STATE_INFO_QUERY)
        latest_info = res["latestDefsStateInfo"]
        return DefsStateInfo.from_graphql(latest_info) if latest_info else None

    def set_latest_version(self, key: str, version: str) -> None:
        result = self._execute_query(
            SET_LATEST_VERSION_MUTATION, variables={"key": key, "version": version}
        )
        check.invariant(
            result.get("setLatestDefsStateVersion", {}).get("ok"),
            f"Failed to set latest version. Result: {result}",
        )
