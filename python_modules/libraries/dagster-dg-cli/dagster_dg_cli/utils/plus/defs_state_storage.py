from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, Optional

from dagster._core.instance.types import T_DagsterInstance
from dagster._core.storage.defs_state.base import DefsStateStorage
from dagster_cloud_cli.core.artifacts import download_artifact, upload_artifact
from dagster_cloud_cli.core.headers.auth import DagsterCloudInstanceScope
from dagster_shared import check
from dagster_shared.plus.config import DagsterPlusCliConfig
from dagster_shared.serdes import deserialize_value
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateInfo

from dagster_dg_cli.utils.plus.gql_client import DagsterPlusGraphQLClient

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


class BaseGraphQLDefsStateStorage(
    DefsStateStorage[T_DagsterInstance], ABC, Generic[T_DagsterInstance]
):
    """Base implementation of a DefsStateStorage that uses a GraphQL client to
    interact with the Dagster+ API.
    """

    @property
    @abstractmethod
    def url(self) -> str: ...

    @property
    @abstractmethod
    def api_token(self) -> str: ...

    @property
    @abstractmethod
    def deployment(self) -> str: ...

    @property
    @abstractmethod
    def graphql_client(self) -> Any: ...

    def _execute_query(self, query, variables=None, idempotent_mutation=False):
        return self.graphql_client.execute(
            query, variable_values=variables, idempotent_mutation=idempotent_mutation
        )

    def _get_artifact_key(self, key: str, version: str) -> str:
        return f"__state__/{key}/{version}"

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
        result = res["data"]["latestDefsStateInfo"]
        if result is not None:
            return deserialize_value(result, DefsStateInfo)
        else:
            return None

    def set_latest_version(self, key: str, version: str) -> None:
        self._execute_query(SET_LATEST_VERSION_MUTATION, variables={"key": key, "version": version})


class DagsterPlusCliDefsStateStorage(BaseGraphQLDefsStateStorage):
    """DefsStateStorage that can be instantiated from a DagsterPlusCliConfig,
    intended for use within the CLI.
    """

    def __init__(self, url: str, api_token: str, deployment: str, graphql_client):
        self._url = url
        self._api_token = api_token
        self._deployment = deployment
        self._graphql_client = graphql_client

    @staticmethod
    def from_config(config: DagsterPlusCliConfig) -> "DagsterPlusCliDefsStateStorage":
        return DagsterPlusCliDefsStateStorage(
            url=check.not_none(config.url),
            api_token=check.not_none(config.user_token),
            deployment=check.not_none(config.default_deployment),
            graphql_client=DagsterPlusGraphQLClient.from_config(config),
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
