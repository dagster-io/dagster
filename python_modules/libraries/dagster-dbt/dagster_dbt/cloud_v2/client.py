import datetime
import logging
import os
import time
from collections.abc import Mapping, Sequence
from typing import Any, Optional, cast

import requests
from dagster import Failure, MetadataValue, get_dagster_logger
from dagster._annotations import preview
from dagster._utils.cached_method import cached_method
from dagster_shared.dagster_model import DagsterModel
from pydantic import Field
from requests.exceptions import RequestException

from dagster_dbt.cloud_v2.types import DbtCloudJobRunStatusType, DbtCloudRun

DAGSTER_DBT_CLOUD_LIST_JOBS_INDIVIDUAL_REQUEST_LIMIT = int(
    os.getenv("DAGSTER_DBT_CLOUD_LIST_JOBS_INDIVIDUAL_REQUEST_LIMIT", "100")
)
DAGSTER_DBT_CLOUD_BATCH_RUNS_REQUEST_LIMIT = int(
    os.getenv("DAGSTER_DBT_CLOUD_BATCH_RUNS_REQUEST_LIMIT", "100")
)
DEFAULT_POLL_INTERVAL = 1
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

    def _get_artifact_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"Token {self.token}",
            }
        )
        return session

    def _make_request(
        self,
        method: str,
        endpoint: Optional[str],
        base_url: str,
        data: Optional[Mapping[str, Any]] = None,
        params: Optional[Mapping[str, Any]] = None,
        session_attr: str = "_get_session",
    ) -> Mapping[str, Any]:
        url = f"{base_url}/{endpoint}" if endpoint else base_url

        num_retries = 0
        while True:
            try:
                session = getattr(self, session_attr)()
                response = session.request(
                    method=method,
                    url=url,
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
        self,
        *,
        project_id: int,
        environment_id: int,
        job_name: str,
        description: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """Creates a dbt cloud job in a dbt Cloud workspace for a given project and environment.

        Args:
            project_id (str): The dbt Cloud Project ID. You can retrieve this value from the
                URL of the "Explore" tab in the dbt Cloud UI.
            environment_id (str): The dbt Cloud Environment ID. You can retrieve this value from the
                URL of the given environment page the dbt Cloud UI.
            job_name (str): The name of the job to create.
            description (Optional[str]): The description of the job to create.
                Defaults to `A job that runs dbt models, sources, and tests.`

        Returns:
            Dict[str, Any]: Parsed json data from the response to this request
        """
        if not description:
            description = "A job that runs dbt models, sources, and tests."
        return self._make_request(
            method="post",
            endpoint="jobs",
            base_url=self.api_v2_url,
            data={
                "account_id": self.account_id,
                "environment_id": environment_id,
                "project_id": project_id,
                "name": job_name,
                "description": description,
                "job_type": "other",
            },
        )["data"]

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
                "limit": DAGSTER_DBT_CLOUD_LIST_JOBS_INDIVIDUAL_REQUEST_LIMIT,
                "offset": len(results),
            },
        )["data"]:
            results.extend(jobs)
            if len(jobs) < DAGSTER_DBT_CLOUD_LIST_JOBS_INDIVIDUAL_REQUEST_LIMIT:
                break
        return results

    def get_job_details(self, job_id: int) -> Mapping[str, Any]:
        """Retrieves the details of a given dbt Cloud job.

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        return self._make_request(
            method="get",
            endpoint=f"jobs/{job_id}",
            base_url=self.api_v2_url,
        )["data"]

    def destroy_job(self, job_id: int) -> Mapping[str, Any]:
        """Destroys a given dbt Cloud job.

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        return self._make_request(
            method="delete",
            endpoint=f"jobs/{job_id}",
            base_url=self.api_v2_url,
        )["data"]

    def trigger_job_run(
        self, job_id: int, steps_override: Optional[Sequence[str]] = None
    ) -> Mapping[str, Any]:
        """Triggers a run for a given dbt Cloud Job.

        Args:
            job_id (str): The dbt Cloud Job ID. You can retrieve this value from the
                URL of the given job in the dbt Cloud UI.
            steps_override (Optional[Sequence[str]]): A list of dbt commands
                that overrides the dbt commands of the dbt Cloud job. If no list is passed,
                the dbt commands of the job are not overridden.

        Returns:
            List[Dict[str, Any]]: A List of parsed json data from the response to this request.
        """
        return self._make_request(
            method="post",
            endpoint=f"jobs/{job_id}/run",
            base_url=self.api_v2_url,
            data={"steps_override": steps_override, "cause": "Triggered by dagster."}
            if steps_override
            else None,
        )["data"]

    def get_runs_batch(
        self,
        project_id: int,
        environment_id: int,
        finished_at_lower_bound: datetime.datetime,
        finished_at_upper_bound: datetime.datetime,
        offset: int = 0,
    ) -> tuple[Sequence[Mapping[str, Any]], int]:
        """Retrieves a batch of dbt Cloud runs from a dbt Cloud workspace for a given project and environment.

        Args:
            project_id (str): The dbt Cloud Project ID. You can retrieve this value from the
                URL of the "Explore" tab in the dbt Cloud UI.
            environment_id (str): The dbt Cloud Environment ID. You can retrieve this value from the
                URL of the given environment page the dbt Cloud UI.
            finished_at_lower_bound (datetime.datetime): The first run in this batch will have finished
                at a time that is equal to or after this value.
            finished_at_upper_bound (datetime.datetime): The last run in this batch will have finished
                at a time that is equal to or before this value.
            offset (str): The pagination offset for this request.

        Returns:
            tuple[List[Dict[str, Any]], int]: A tuple containing:
                - a list of run details as parsed json data from the response to this request;
                - the total number of runs for the given parameters.
        """
        resp = self._make_request(
            method="get",
            endpoint="runs",
            base_url=self.api_v2_url,
            params={
                "account_id": self.account_id,
                "environment_id": environment_id,
                "project_id": project_id,
                "limit": DAGSTER_DBT_CLOUD_BATCH_RUNS_REQUEST_LIMIT,
                "offset": offset,
                "finished_at__range": f"""["{finished_at_lower_bound.isoformat()}", "{finished_at_upper_bound.isoformat()}"]""",
                "order_by": "finished_at",
            },
        )
        data = cast(Sequence[Mapping[str, Any]], resp["data"])
        total_count = resp["extra"]["pagination"]["total_count"]
        return data, total_count

    def get_run_details(self, run_id: int) -> Mapping[str, Any]:
        """Retrieves the details of a given dbt Cloud Run.

        Args:
            run_id (str): The dbt Cloud Run ID. You can retrieve this value from the
                URL of the given run in the dbt Cloud UI.

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        return self._make_request(
            method="get",
            endpoint=f"runs/{run_id}",
            base_url=self.api_v2_url,
        )["data"]

    def poll_run(
        self,
        run_id: int,
        poll_interval: Optional[float] = None,
        poll_timeout: Optional[float] = None,
    ) -> Mapping[str, Any]:
        """Given a dbt Cloud run, poll until the run completes.

        Args:
            run_id (str): The dbt Cloud Run ID. You can retrieve this value from the
                URL of the given run in the dbt Cloud UI.
            poll_interval (float): The time (in seconds) that will be waited between successive polls.
                By default, the interval is set to 1 second.
            poll_timeout (float): The maximum time that will waited before this operation is timed
                out. By default, this will time out after 60 seconds.

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        if not poll_interval:
            poll_interval = DEFAULT_POLL_INTERVAL
        if not poll_timeout:
            poll_timeout = DEFAULT_POLL_TIMEOUT
        start_time = time.time()
        while time.time() - start_time < poll_timeout:
            run_details = self.get_run_details(run_id)
            run = DbtCloudRun.from_run_details(run_details=run_details)
            if run.status == DbtCloudJobRunStatusType.SUCCESS:
                return run_details
            elif run.status in {
                DbtCloudJobRunStatusType.ERROR,
                DbtCloudJobRunStatusType.CANCELLED,
            }:
                raise Failure(
                    f"dbt Cloud run '{run.id}' failed!",
                    metadata={
                        "run_details": MetadataValue.json(run_details),
                    },
                )
            # Sleep for the configured time interval before polling again.
            time.sleep(poll_interval)
        raise Exception(f"Run {run.id} did not complete within {poll_timeout} seconds.")  # pyright: ignore[reportPossiblyUnboundVariable]

    def list_run_artifacts(
        self,
        run_id: int,
    ) -> Sequence[str]:
        """Retrieves a list of artifact names for a given dbt Cloud Run.

        Returns:
            List[str]: a list of artifact names taken from the response to this request.
        """
        return cast(
            Sequence[str],
            self._make_request(
                method="get",
                endpoint=f"runs/{run_id}/artifacts",
                base_url=self.api_v2_url,
                session_attr="_get_artifact_session",
            )["data"],
        )

    def get_run_artifact(self, run_id: int, path: str) -> Mapping[str, Any]:
        """Retrieves an artifact at the given path for a given dbt Cloud Run.

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        return self._make_request(
            method="get",
            endpoint=f"runs/{run_id}/artifacts/{path}",
            base_url=self.api_v2_url,
            session_attr="_get_artifact_session",
        )

    def get_run_results_json(self, run_id: int) -> Mapping[str, Any]:
        """Retrieves the run_results.json artifact of a given dbt Cloud Run.

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        return self.get_run_artifact(run_id=run_id, path="run_results.json")

    def get_run_manifest_json(self, run_id: int) -> Mapping[str, Any]:
        """Retrieves the manifest.json artifact of a given dbt Cloud Run.

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        return self.get_run_artifact(run_id=run_id, path="manifest.json")

    def get_project_details(self, project_id: int) -> Mapping[str, Any]:
        """Retrieves the details of a given dbt Cloud Project.

        Args:
            project_id (str): The dbt Cloud Project ID. You can retrieve this value from the
                URL of the "Explore" tab in the dbt Cloud UI.

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        return self._make_request(
            method="get",
            endpoint=f"projects/{project_id}",
            base_url=self.api_v2_url,
        )["data"]

    def get_environment_details(self, environment_id: int) -> Mapping[str, Any]:
        """Retrieves the details of a given dbt Cloud Environment.

        Args:
            environment_id (str): The dbt Cloud Environment ID. You can retrieve this value from the
                URL of the given environment page the dbt Cloud UI.

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        return self._make_request(
            method="get",
            endpoint=f"environments/{environment_id}",
            base_url=self.api_v2_url,
        )["data"]

    def get_account_details(self) -> Mapping[str, Any]:
        """Retrieves the details of the account associated to the dbt Cloud workspace.

        Returns:
            Dict[str, Any]: Parsed json data representing the API response.
        """
        return self._make_request(
            method="get",
            endpoint=None,
            base_url=self.api_v2_url,
        )["data"]

    def verify_connection(self) -> None:
        """Verifies the connection to the dbt Cloud REST API."""
        try:
            self.get_account_details()
        except Exception as e:
            raise Exception(
                f"Failed to verify connection to dbt Cloud REST API with the workspace client. Exception: {e}"
            )
