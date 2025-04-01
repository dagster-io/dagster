import re
from collections.abc import Sequence
from functools import cached_property, lru_cache
from typing import NamedTuple, Optional, Union

from dagster import (
    AssetCheckSpec,
    AssetSpec,
    ConfigurableResource,
    Definitions,
    _check as check,
    multi_asset_check,
)
from dagster._annotations import preview
from dagster._config.pythonic_config.resource import ResourceDependency
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._record import record
from dagster._utils.cached_method import cached_method
from pydantic import Field

from dagster_dbt.asset_utils import build_dbt_specs
from dagster_dbt.cloud_v2.cli_invocation import DbtCloudCliInvocation
from dagster_dbt.cloud_v2.client import DbtCloudWorkspaceClient
from dagster_dbt.cloud_v2.run_handler import DbtCloudJobRunHandler
from dagster_dbt.cloud_v2.types import (
    DbtCloudAccount,
    DbtCloudEnvironment,
    DbtCloudJob,
    DbtCloudProject,
    DbtCloudWorkspaceData,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

DAGSTER_ADHOC_PREFIX = "DAGSTER_ADHOC_JOB__"
DBT_CLOUD_RECONSTRUCTION_METADATA_KEY_PREFIX = "__dbt_cloud"


def get_dagster_adhoc_job_name(
    project_id: int,
    project_name: Optional[str],
    environment_id: int,
    environment_name: Optional[str],
) -> str:
    name = (
        f"{DAGSTER_ADHOC_PREFIX}{project_name or project_id}__{environment_name or environment_id}"
    )
    # Clean the name and convert it to uppercase
    return re.sub(r"[^A-Z0-9]+", "_", name.upper())


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
    adhoc_job_name: Optional[str] = Field(
        default=None,
        description=(
            "The name of the ad hoc job that will be created by Dagster in your dbt Cloud workspace. "
            "This ad hoc job is used to parse your project and materialize your dbt Cloud assets. "
            "If not provided, this job name will be generated using your project ID and environment ID."
        ),
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
        """Unique ID for this dbt Cloud workspace, which is composed of the project ID and environment ID.

        Returns:
            str: the unique ID for this dbt Cloud workspace.
        """
        return f"{self.project_id}-{self.environment_id}"

    @cached_property
    def account_name(self) -> Optional[str]:
        """The name of the account for this dbt Cloud workspace.

        Returns:
            str: the name of the account for this dbt Cloud workspace.
        """
        account = DbtCloudAccount.from_account_details(
            account_details=self.get_client().get_account_details()
        )
        return account.name

    @cached_property
    def project_name(self) -> Optional[str]:
        """The name of the project for this dbt Cloud workspace.

        Returns:
            str: the name of the project for this dbt Cloud workspace.
        """
        project = DbtCloudProject.from_project_details(
            project_details=self.get_client().get_project_details(project_id=self.project_id)
        )
        return project.name

    @cached_property
    def environment_name(self) -> Optional[str]:
        """The name of the environment for this dbt Cloud workspace.

        Returns:
            str: the name of the environment for this dbt Cloud workspace.
        """
        environment = DbtCloudEnvironment.from_environment_details(
            environment_details=self.get_client().get_environment_details(
                environment_id=self.environment_id
            )
        )
        return environment.name

    @cached_method
    def get_client(self) -> DbtCloudWorkspaceClient:
        """Get the dbt Cloud client to interact with this dbt Cloud workspace.

        Returns:
            DbtCloudWorkspaceClient: The dbt Cloud client to interact with the dbt Cloud workspace.
        """
        return DbtCloudWorkspaceClient(
            account_id=self.credentials.account_id,
            token=self.credentials.token,
            access_url=self.credentials.access_url,
            request_max_retries=self.request_max_retries,
            request_retry_delay=self.request_retry_delay,
            request_timeout=self.request_timeout,
        )

    def _get_or_create_dagster_adhoc_job(self) -> DbtCloudJob:
        """Get or create an ad hoc dbt Cloud job for the given project and environment in this dbt Cloud Workspace.

        Returns:
            DbtCloudJob: Internal representation of the dbt Cloud job.
        """
        client = self.get_client()
        expected_job_name = self.adhoc_job_name or get_dagster_adhoc_job_name(
            project_id=self.project_id,
            project_name=self.project_name,
            environment_id=self.environment_id,
            environment_name=self.environment_name,
        )
        jobs = [
            DbtCloudJob.from_job_details(job_details)
            for job_details in client.list_jobs(
                project_id=self.project_id,
                environment_id=self.environment_id,
            )
        ]

        if expected_job_name in {job.name for job in jobs}:
            return next(job for job in jobs if job.name == expected_job_name)
        return DbtCloudJob.from_job_details(
            client.create_job(
                project_id=self.project_id,
                environment_id=self.environment_id,
                job_name=expected_job_name,
                description=(
                    "This job is used by Dagster to parse your dbt Cloud workspace "
                    "and to kick off runs of dbt Cloud models."
                ),
            )
        )

    def _fetch_workspace_data(self) -> DbtCloudWorkspaceData:
        job = self._get_or_create_dagster_adhoc_job()
        run_handler = DbtCloudJobRunHandler.run(
            job_id=job.id,
            args=["parse"],
            client=self.get_client(),
        )
        run_handler.wait_for_success()
        return DbtCloudWorkspaceData(
            project_id=self.project_id,
            environment_id=self.environment_id,
            job_id=job.id,
            manifest=run_handler.get_manifest(),
        )

    def fetch_workspace_data(self) -> DbtCloudWorkspaceData:
        return DbtCloudWorkspaceDefsLoader(
            workspace=self, translator=DagsterDbtTranslator()
        ).get_or_fetch_state()

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
                    for asset_def in defs.asset_checks or []
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

    def cli(
        self, args: Sequence[str], dagster_dbt_translator: Optional[DagsterDbtTranslator] = None
    ) -> DbtCloudCliInvocation:
        """Creates a dbt cli invocation with the dbt Cloud client."""
        dagster_dbt_translator = dagster_dbt_translator or DagsterDbtTranslator()
        workspace_data = self.fetch_workspace_data()
        # We pass the manifest instead of the workspace data
        # because we use the manifest included in the asset definitions
        # when this method is called inside a function decorated with `@dbt_cloud_assets`
        return DbtCloudCliInvocation.run(
            job_id=workspace_data.job_id,
            args=args,
            client=self.get_client(),
            manifest=workspace_data.manifest,
            dagster_dbt_translator=dagster_dbt_translator,
        )


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
        return self.workspace._fetch_workspace_data()  # noqa

    def defs_from_state(self, state: DbtCloudWorkspaceData) -> Definitions:
        all_asset_specs, all_check_specs = build_dbt_specs(
            manifest=state.manifest,
            translator=self.translator,
            select="fqn:*",
            exclude="",
            io_manager_key=None,
            project=None,
        )

        all_asset_specs = [
            spec.replace_attributes(kinds={"dbtcloud"} | spec.kinds - {"dbt"})
            for spec in all_asset_specs
        ]

        # External facing checks are not supported yet
        # https://linear.app/dagster-labs/issue/AD-915/support-external-asset-checks-in-dbt-cloud-v2
        @multi_asset_check(specs=all_check_specs)
        def _all_asset_checks(): ...

        return Definitions(assets=all_asset_specs, asset_checks=[_all_asset_checks])
