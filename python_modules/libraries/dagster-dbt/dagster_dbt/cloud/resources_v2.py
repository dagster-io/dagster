from collections.abc import Sequence
from functools import lru_cache
from typing import NamedTuple, Optional, Union

from dagster import (
    AssetCheckSpec,
    AssetSpec,
    Definitions,
    _check as check,
    multi_asset_check,
)
from dagster._annotations import preview
from dagster._config.pythonic_config import ConfigurableResource
from dagster._config.pythonic_config.resource import ResourceDependency
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._record import record
from dagster._utils.cached_method import cached_method
from pydantic import Field

from dagster_dbt.asset_utils import build_dbt_specs
from dagster_dbt.cloud.client_v2 import DbtCloudClient
from dagster_dbt.cloud.dbt_cloud_job_run import DbtCloudJobRun
from dagster_dbt.cloud.types import DbtCloudWorkspaceData
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

DAGSTER_ADHOC_PREFIX = "DAGSTER_ADHOC_JOB__"

DBT_CLOUD_RECONSTRUCTION_METADATA_KEY_PREFIX = "__dbt_cloud"


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
            client=self.get_client(),
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
                [
                    check_spec
                    for asset_def in defs.asset_checks
                    for check_spec in asset_def.check_specs
                ],
                AssetCheckSpec,
            )
            return [*asset_specs, *asset_check_specs]

    def load_asset_specs(
        self, dagster_dbt_translator: Optional[DagsterDbtTranslator] = None
    ) -> Sequence[AssetSpec]:
        return [
            spec
            for spec in self.load_specs(dagster_dbt_translator=dagster_dbt_translator)
            if isinstance(spec, AssetSpec)
        ]

    def load_check_specs(
        self, dagster_dbt_translator: Optional[DagsterDbtTranslator] = None
    ) -> Sequence[AssetCheckSpec]:
        return [
            spec
            for spec in self.load_specs(dagster_dbt_translator=dagster_dbt_translator)
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

        @multi_asset_check(specs=all_check_specs)
        def _all_asset_checks(): ...

        return Definitions(assets=all_asset_specs, asset_checks=[_all_asset_checks])
