from pathlib import Path
from typing import TYPE_CHECKING, Any

import dagster._check as check
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster_cloud_cli.core.artifacts import download_artifact, upload_artifact
from dagster_cloud_cli.core.headers.auth import DagsterCloudInstanceScope
from dagster_shared.serdes import deserialize_value
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo
from typing_extensions import Self

if TYPE_CHECKING:
    from dagster_cloud.instance import DagsterCloudAgentInstance  # noqa: F401

GET_LATEST_DEFS_STATE_INFO_QUERY = """
    query getLatestDefsStateInfo {
        latestDefsStateInfo
    }
"""

SET_LATEST_VERSION_MUTATION = """
    mutation setLatestDefsStateVersion($key: String!, $version: String!) {
        defsState {
            setLatestDefsStateVersion(key: $key, version: $version) {
                ok
            }
        }
    }
"""


class GraphQLDefsStateStorage(DefsStateStorage["DagsterCloudAgentInstance"], ConfigurableClass):
    def __init__(
        self, inst_data: ConfigurableClassData | None = None, override_graphql_client=None
    ):
        """Initialize this class directly only for test (using `override_graphql_client`).
        Use the ConfigurableClass machinery to init from instance yaml.
        """
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._override_graphql_client = override_graphql_client

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @classmethod
    def from_config_value(cls, inst_data: ConfigurableClassData, config_value: Any) -> Self:
        return cls(inst_data=inst_data)

    @property
    def url(self) -> str:
        return self._instance.dagster_cloud_url

    @property
    def api_token(self) -> str:
        return check.not_none(self._instance.dagster_cloud_agent_token)

    @property
    def deployment(self) -> str:
        return check.not_none(self._instance.deployment_name)

    @property
    def graphql_client(self):
        return (
            self._override_graphql_client
            if self._override_graphql_client
            else self._instance.graphql_client
        )

    def _execute_query(self, query, variables=None, idempotent_mutation=False):
        return self.graphql_client.execute(
            query, variable_values=variables, idempotent_mutation=idempotent_mutation
        )

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

    def get_latest_defs_state_info(self) -> DefsStateInfo | None:
        res = self._execute_query(GET_LATEST_DEFS_STATE_INFO_QUERY)
        result = res["data"]["latestDefsStateInfo"]
        if result is not None:
            return deserialize_value(result, DefsStateInfo)
        else:
            return None

    def set_latest_version(self, key: str, version: str) -> None:
        self._execute_query(SET_LATEST_VERSION_MUTATION, variables={"key": key, "version": version})
