import logging
import time
from collections.abc import Mapping, Sequence
from typing import Any, Optional

import requests
from dagster import Failure, get_dagster_logger
from dagster._annotations import preview
from dagster._model import DagsterModel
from dagster._utils.cached_method import cached_method
from pydantic import Field
from requests.exceptions import RequestException

from dagster_dbt.cloud.types import DbtCloudJobRunStatusType

LIST_JOBS_INDIVIDUAL_REQUEST_LIMIT = 100
DEFAULT_POLL_TIMEOUT = 60


@preview
class DbtCloudWorkspaceClient(DagsterModel):
    account_id: int = Field(
        ...,
        description="The dbt Cloud Account ID. Can be found on the Account Info page of dbt Cloud.",
    )
    token: str = Field(
        ...,
        description="The token to access the dbt Cloud API. Can be either a personal token or a service token.",
    )
    access_url: str = Field(
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
    @cached_method
    def _log(self) -> logging.Logger:
        return get_dagster_logger()

    @property
    def api_v2_url(self) -> str:
        return f"{self.access_url}/api/v2/accounts/{self.account_id}"

    def _get_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
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
                resp_dict = response.json()
                return resp_dict["data"] if "data" in resp_dict else resp_dict
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
        """Creates a dbt cloud job in a dbt Cloud workspace for a given project and environment.

        Args:
            project_id (str): The dbt Cloud Project ID. You can retrieve this value from the
                URL of the "Explore" tab in the dbt Cloud UI.
            environment_id (str): The dbt Cloud Environment ID. You can retrieve this value from the
                URL of the given environment page the dbt Cloud UI.
            job_name (str): The name of the job to create.

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request
        """
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
        """Retrieves a list of dbt cloud jobs from a dbt Cloud workspace for a given project and environment.

        Args:
            project_id (str): The dbt Cloud Project ID. You can retrieve this value from the
                URL of the "Explore" tab in the dbt Cloud UI.
            environment_id (str): The dbt Cloud Environment ID. You can retrieve this value from the
                URL of the given environment page the dbt Cloud UI.

        Returns:
            List[Dict[str, Any]]: A List of parsed json data from the response to this request
        """
        results = []
        while jobs := self._make_request(
            method="get",
            endpoint="jobs",
            base_url=self.api_v2_url,
            params={
                "account_id": self.account_id,
                "environment_id": environment_id,
                "project_id": project_id,
                "limit": LIST_JOBS_INDIVIDUAL_REQUEST_LIMIT,
                "offset": len(results),
            },
        ):
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
            if run_details["status"] in {
                DbtCloudJobRunStatusType.SUCCESS,
                DbtCloudJobRunStatusType.ERROR,
                DbtCloudJobRunStatusType.CANCELLED,
            }:
                return run_details
            time.sleep(0.1)
        raise Exception(f"Run {job_run_id} did not complete within {poll_timeout} seconds.")
