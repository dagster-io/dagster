from functools import cached_property
from typing import TYPE_CHECKING, NamedTuple

from dagster_dlift.client import DbtCloudClient
from dagster_dlift.compute import compute_environment_data

if TYPE_CHECKING:
    from dagster_dlift.translator import DbtCloudProjectEnvironmentData


class DbtCloudCredentials(NamedTuple):
    account_id: str
    token: str
    access_url: str
    discovery_api_url: str


# Eventually a configurable resource
class DBTCloudProjectEnvironment:
    """Represents an environment within a project of dbt cloud."""

    def __init__(self, credentials: DbtCloudCredentials, project_id: int, environment_id: int):
        self.credentials = credentials
        self.project_id = project_id
        self.environment_id = environment_id

    @cached_property
    def client(self) -> DbtCloudClient:
        return DbtCloudClient(
            account_id=self.credentials.account_id,
            token=self.credentials.token,
            access_url=self.credentials.access_url,
            discovery_api_url=self.credentials.discovery_api_url,
        )

    def compute_data(self) -> "DbtCloudProjectEnvironmentData":
        return compute_environment_data(
            project_id=self.project_id, environment_id=self.environment_id, client=self.client
        )
