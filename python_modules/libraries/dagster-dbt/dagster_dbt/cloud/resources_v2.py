import time
from collections.abc import Mapping, Sequence
from functools import lru_cache
from typing import Any, NamedTuple, Optional, Union

import requests
from dagster import (
    AssetCheckSpec,
    AssetSpec,
    Definitions,
    Failure,
    _check as check,
)
from dagster._annotations import preview
from dagster._config.pythonic_config import ConfigurableResource
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._model import DagsterModel
from dagster._utils.cached_method import cached_method
from pydantic import Field
from requests.exceptions import RequestException

from dagster_dbt.asset_utils import build_dbt_specs
from dagster_dbt.cloud.dbt_cloud_job_run import DbtCloudJobRun
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from dagster_dbt.cloud.types import DbtCloudWorkspaceData

LIST_JOBS_INDIVIDUAL_REQUEST_LIMIT = 100
DAGSTER_ADHOC_PREFIX = "DAGSTER_ADHOC_JOB__"

DBT_CLOUD_RECONSTRUCTION_METADATA_KEY_PREFIX = "__dbt_cloud"

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

    def get_run_artifact(self, job_run_id: int, path: str) -> Mapping[str, Any]:
        return self._make_request(
            method="get", endpoint=f"runs/{job_run_id}/artifacts/{path}", base_url=self.api_v2_url
        )

    def get_run_results_json(self, job_run_id: int) -> Mapping[str, Any]:
        return self.get_run_artifact(job_run_id=job_run_id, path="run_results.json")

    def get_run_manifest_json(self, job_run_id: int) -> Mapping[str, Any]:
        return self.get_run_artifact(job_run_id=job_run_id, path="manifest.json")


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

    @property
    def unique_id(self) -> str:
        return f"{self.project_id}-{self.environment_id}"

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

    def fetch_workspace_data(self) -> DbtCloudWorkspaceData:
        job_id = self._get_or_create_job()
        run = DbtCloudJobRun.run(
            job_id=job_id,
            args=["parse"],
            client=self.dbt_client,
        )
        run.wait_for_success()
        return DbtCloudWorkspaceData(
            project_id=self.project_id,
            environment_id=self.environment_id,
            job_id=job_id,
            manifest=run.get_manifest(),
        )

    # Cache spec retrieval for a specific translator class.
    @lru_cache(maxsize=1)
    def load_specs(
        self, dagster_dbt_translator: Optional[DagsterDbtTranslator] = None
    ) -> Sequence[Union[AssetSpec, AssetCheckSpec]]:
        dagster_dbt_translator = dagster_dbt_translator or DagsterDbtTranslator()

        with self.process_config_and_initialize_cm() as initialized_workspace:
            defs = DbtCloudWorkspaceDefsLoader(
                workspace=initialized_workspace,
                translator=dagster_dbt_translator,
            ).build_defs()
            asset_specs = check.is_list(
                defs.assets,
                AssetSpec,
            )
            asset_check_specs = check.is_list(
                defs.asset_checks,
                AssetCheckSpec,
            )
            return [*asset_specs, *asset_check_specs]

    def load_asset_specs(
        self, dagster_dbt_translator: Optional[DagsterDbtTranslator] = None
    ) -> Sequence[AssetSpec]:
        return [
            spec
            for spec in self.get_specs(dagster_dbt_translator=dagster_dbt_translator)
            if isinstance(spec, AssetSpec)
        ]

    def load_check_specs(
        self, dagster_dbt_translator: Optional[DagsterDbtTranslator] = None
    ) -> Sequence[AssetCheckSpec]:
        return [
            spec
            for spec in self.get_specs(dagster_dbt_translator=dagster_dbt_translator)
            if isinstance(spec, AssetCheckSpec)
        ]


@preview
def load_dbt_cloud_asset_specs(
    workspace: DbtCloudWorkspace, dagster_dbt_translator: Optional[DagsterDbtTranslator] = None
) -> Sequence[AssetSpec]:
    return workspace.load_asset_specs(dagster_dbt_translator=dagster_dbt_translator)


@preview
def load_dbt_cloud_check_specs(
    workspace: DbtCloudWorkspace, dagster_dbt_translator: Optional[DagsterDbtTranslator] = None
) -> Sequence[AssetCheckSpec]:
    return workspace.load_check_specs(dagster_dbt_translator=dagster_dbt_translator)


@preview
@record
class DbtCloudWorkspaceDefsLoader(StateBackedDefinitionsLoader[DbtCloudWorkspaceData]):
    workspace: DbtCloudWorkspace
    translator: DagsterDbtTranslator

    @property
    def defs_key(self) -> str:
        return f"{DBT_CLOUD_RECONSTRUCTION_METADATA_KEY_PREFIX}.{self.workspace.unique_id}"

    def fetch_state(self) -> DbtCloudWorkspaceData:
        return self.workspace.fetch_workspace_data()

    def defs_from_state(self, state: DbtCloudWorkspaceData) -> Definitions:
        all_asset_specs, all_check_specs = build_dbt_specs(
            manifest=state.manifest,
            translator=self.translator,
            select="fqn:*",
            exclude="",
            io_manager_key=None,
            project=None,
        )
        return Definitions(assets=all_asset_specs, asset_checks=all_check_specs)
