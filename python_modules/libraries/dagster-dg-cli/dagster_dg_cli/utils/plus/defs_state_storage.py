from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from dagster._core.instance.types import T_DagsterInstance
from dagster._core.storage.defs_state.base import DefsStateStorage
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


class DagsterPlusCliDefsStateStorage(DefsStateStorage[T_DagsterInstance]):
    """DefsStateStorage that can be instantiated from a DagsterPlusCliConfig,
    intended for use within the CLI.
    """

    def __init__(self, url: str, api_token: str, deployment: str, graphql_client):
        self._url = url
        self._api_token = api_token
        self._deployment = deployment
        self._graphql_client = graphql_client

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
        return DefsStateInfo.from_graphql(latest_info)

    def set_latest_version(self, key: str, version: str) -> None:
        result = self._execute_query(
            SET_LATEST_VERSION_MUTATION, variables={"key": key, "version": version}
        )
        check.invariant(
            result.get("setLatestDefsStateVersion", {}).get("ok"),
            f"Failed to set latest version. Result: {result}",
        )
