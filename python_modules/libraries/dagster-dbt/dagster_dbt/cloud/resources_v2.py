from typing import NamedTuple

from dagster._annotations import preview
from dagster._config.pythonic_config import ConfigurableResource
from dagster._config.pythonic_config.resource import ResourceDependency
from dagster._utils.cached_method import cached_method
from pydantic import Field

from dagster_dbt.cloud.client_v2 import DbtCloudClient

DAGSTER_ADHOC_PREFIX = "DAGSTER_ADHOC_JOB__"


def get_job_name(environment_id: int, project_id: int) -> str:
    return f"{DAGSTER_ADHOC_PREFIX}{project_id}__{environment_id}"


@preview
class DbtCloudCredentials(NamedTuple):
    """The DbtCloudCredentials to access your dbt Cloud Workspace."""

    account_id: int
    token: str
    access_url: str


@preview
class DbtCloudWorkspace(ConfigurableResource):
    """This class represents a dbt Cloud workspace and provides utilities
    to interact with dbt Cloud APIs.
    """

    credentials: ResourceDependency[DbtCloudCredentials]
    project_id: int = Field(description="The ID of the dbt Cloud project to use for this resource.")
    environment_id: int = Field(
        description="The ID of environment to use for the dbt Cloud project used in this resource."
    )
    request_max_retries: int = Field(
        default=3,
        description=(
            "The maximum number of times requests to the dbt Cloud API should be retried "
            "before failing."
        ),
    )
    request_retry_delay: float = Field(
        default=0.25,
        description="Time (in seconds) to wait between each request retry.",
    )
    request_timeout: int = Field(
        default=15,
        description="Time (in seconds) after which the requests to dbt Cloud are declared timed out.",
    )

    @cached_method
    def get_client(self) -> DbtCloudClient:
        return DbtCloudClient(
            account_id=self.credentials.account_id,
            token=self.credentials.token,
            access_url=self.credentials.access_url,
            request_max_retries=self.request_max_retries,
            request_retry_delay=self.request_retry_delay,
            request_timeout=self.request_timeout,
        )

    def _get_or_create_job(self) -> int:
        """Get or create a dbt Cloud job for the given project and environment in this dbt Cloud Workspace."""
        client = self.get_client()
        expected_job_name = get_job_name(
            project_id=self.project_id, environment_id=self.environment_id
        )
        if expected_job_name in {
            job["name"]
            for job in client.list_jobs(
                project_id=self.project_id,
                environment_id=self.environment_id,
            )
        }:
            return next(
                job["id"]
                for job in client.list_jobs(
                    project_id=self.project_id,
                    environment_id=self.environment_id,
                )
                if job["name"] == expected_job_name
            )
        return client.create_job(
            project_id=self.project_id,
            environment_id=self.environment_id,
            job_name=expected_job_name,
        )
