import time
from collections.abc import Mapping, Sequence
from typing import Any, NamedTuple, Optional

import requests
from dagster import Failure
from dagster._annotations import preview
from dagster._config.pythonic_config import ConfigurableResource
from dagster._model import DagsterModel
from dagster._utils.cached_method import cached_method
from pydantic import Field
from requests.exceptions import RequestException

LIST_JOBS_INDIVIDUAL_REQUEST_LIMIT = 100
DAGSTER_ADHOC_PREFIX = "DAGSTER_ADHOC_JOB__"

DEFAULT_POLL_TIMEOUT = 60


def get_job_name(environment_id: int, project_id: int) -> str:
    return f"{DAGSTER_ADHOC_PREFIX}{project_id}__{environment_id}"


@preview
class DbtCloudClient(DagsterModel):
    account_id: int = Field(
        ...,
        description="The dbt Cloud Account ID. Can be found on the Account Info page of dbt Cloud.",
    )
    token: int = Field(
        ...,
        description="The token to access the dbt Cloud API. Can be either a personal token or a service token.",
    )
    access_url: int = Field(
        ...,
        description="The access URL for your dbt Cloud workspace.",
    )
    request_max_retries: int = Field(
        ...,
        description=(
            "The maximum number of times requests to the dbt Cloud API should be retried "
            "before failing."
        ),
    )
    request_retry_delay: float = Field(
        ...,
        description="Time (in seconds) to wait between each request retry.",
    )
    request_timeout: int = Field(
        ...,
        description="Time (in seconds) after which the requests to dbt Cloud are declared timed out.",
    )

    @property
    def api_v2_url(self) -> str:
        return f"{self.access_url}/api/v2/accounts/{self.account_id}"

    def _get_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "Accept": "application/json",
                "Authorization": f"Token {self.token}",
            }
        )
        return session

    def _make_request(
        self,
        method: str,
        endpoint: str,
        base_url: str,
        data: Optional[Mapping[str, Any]] = None,
        params: Optional[Mapping[str, Any]] = None,
    ) -> Mapping[str, Any]:
        url = f"{base_url}/{endpoint}"

        num_retries = 0
        while True:
            try:
                session = self._get_session()
                response = session.request(
                    method=method,
                    url=f"{self.api_v2_url}/{endpoint}",
                    json=data,
                    params=params,
                    timeout=self.request_timeout,
                )
                response.raise_for_status()
                return response.json()
            except RequestException as e:
                self._log.error(
                    f"Request to dbt Cloud API failed for url {url} with method {method} : {e}"
                )
                if num_retries == self.request_max_retries:
                    break
                num_retries += 1
                time.sleep(self.request_retry_delay)

        raise Failure(f"Max retries ({self.request_max_retries}) exceeded with url: {url}.")

    def create_job(
        self, *, project_id: int, environment_id: int, job_name: str
    ) -> Mapping[str, Any]:
        """Creates a dbt cloud job spec'ed to do what dagster expects."""
        return self._make_request(
            method="post",
            endpoint="jobs",
            base_url=self.api_v2_url,
            data={
                "account_id": self.account_id,
                "environment_id": environment_id,
                "project_id": project_id,
                "name": job_name,
                "description": "A job that runs dbt models, sources, and tests.",
                "job_type": "other",
            },
        )

    def list_jobs(
        self,
        project_id: int,
        environment_id: int,
    ) -> Sequence[Mapping[str, Any]]:
        results = []
        while jobs := self._make_request(
            method="get",
            endpoint="jobs",
            params={
                "account_id": self.account_id,
                "environment_id": environment_id,
                "project_id": project_id,
                "limit": LIST_JOBS_INDIVIDUAL_REQUEST_LIMIT,
                "offset": len(results),
            },
        )["data"]:
            results.extend(jobs)
            if len(jobs) < LIST_JOBS_INDIVIDUAL_REQUEST_LIMIT:
                break
        return results

    def trigger_job(self, job_id: int, steps: Optional[Sequence[str]] = None) -> Mapping[str, Any]:
        return self._make_request(
            method="post",
            endpoint=f"jobs/{job_id}/run",
            base_url=self.api_v2_url,
            data={"steps_override": steps, "cause": "Triggered by dagster."},
        )

    def _get_job_run_details(self, job_run_id: int) -> Mapping[str, Any]:
        return self._make_request(
            method="get",
            endpoint=f"runs/{job_run_id}",
            base_url=self.api_v2_url,
        )

    def poll_run(self, job_run_id: int, poll_timeout: Optional[float] = None) -> Mapping[str, Any]:
        if not poll_timeout:
            poll_timeout = DEFAULT_POLL_TIMEOUT
        start_time = time.time()
        while time.time() - start_time < poll_timeout:
            run_details = self._get_job_run_details(job_run_id)
            if run_details["data"]["status"] in {10, 20, 30}:
                return run_details
            time.sleep(0.1)
        raise Exception(f"Run {job_run_id} did not complete within {poll_timeout} seconds.")


@preview
class DbtCloudCredentials(NamedTuple):
    account_id: int
    token: str
    access_url: str


@preview
class DbtCloudWorkspace(ConfigurableResource):
    """This class represents a dbt Cloud workspace and provides utilities
    to interact with dbt Cloud APIs.
    """

    credentials: DbtCloudCredentials = Field(
        description="The DbtCloudCredentials to access your dbt Cloud Workspace."
    )
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
