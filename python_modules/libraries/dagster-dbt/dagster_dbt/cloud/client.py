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

LIST_JOBS_INDIVIDUAL_REQUEST_LIMIT = 100


@preview
class DbtCloudWorkspaceClient(DagsterModel):
    account_id: str = Field(
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
                "account_id": int(self.account_id),
                "environment_id": environment_id,
                "project_id": project_id,
                "name": job_name,
                "description": "A job that runs dbt models, sources, and tests.",
                "job_type": "other",
            },
        )["data"]

    def list_jobs(
        self,
        project_id: int,
        environment_id: int,
    ) -> Sequence[Mapping[str, Any]]:
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
        )["data"]:
            results.extend(jobs)
            if len(jobs) < LIST_JOBS_INDIVIDUAL_REQUEST_LIMIT:
                break
        return results
