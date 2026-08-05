import random
import time
from collections.abc import Sequence
from typing import Literal, NamedTuple

from dagster import (
    AssetCheckSpec,
    AssetExecutionContext,
    AssetSpec,
    ConfigurableResource,
    Definitions,
    Failure,
    Resolvable,
    _check as check,
    multi_asset_check,
)
from dagster._annotations import public
from dagster._config.pythonic_config.resource import ResourceDependency
from dagster._core.definitions.definitions_load_context import StateBackedDefinitionsLoader
from dagster._record import record
from dagster._utils.cached_method import cached_method
from pydantic import Field

from dagster_dbt.asset_utils import (
    DAGSTER_DBT_CLOUD_ACCOUNT_ID_METADATA_KEY,
    DAGSTER_DBT_CLOUD_ENVIRONMENT_ID_METADATA_KEY,
    DAGSTER_DBT_CLOUD_PROJECT_ID_METADATA_KEY,
    DBT_DEFAULT_EXCLUDE,
    DBT_DEFAULT_SELECT,
    DBT_DEFAULT_SELECTOR,
    build_dbt_specs,
    get_updated_cli_invocation_params_for_context,
)
from dagster_dbt.cloud_v2.cli_invocation import DbtCloudCliInvocation
from dagster_dbt.cloud_v2.client import DbtCloudWorkspaceClient
from dagster_dbt.cloud_v2.run_handler import DbtCloudJobRunHandler
from dagster_dbt.cloud_v2.types import DbtCloudJob, DbtCloudWorkspaceData
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, validate_opt_translator
from dagster_dbt.utils import clean_name

DAGSTER_ADHOC_PREFIX = "DAGSTER_ADHOC_JOB__"
DBT_CLOUD_RECONSTRUCTION_METADATA_KEY_PREFIX = "__dbt_cloud"
DAGSTER_DBT_CLOUD_ADHOC_JOB_WAIT_TIMEOUT_SECONDS = 300
DAGSTER_DBT_CLOUD_ADHOC_JOB_WAIT_POLL_INTERVAL_SECONDS = 5

DbtCloudAdhocJobPoolMode = Literal["overflow", "wait", "fail"]


def get_dagster_adhoc_job_name(project_id: int, environment_id: int, index: int = 0) -> str:
    """Returns the name of the ad hoc job for the given project, environment, and pool index.

    The job at index 0 keeps the unsuffixed name to preserve the name of pre-existing
    single-job deployments. Indices greater than 0 get an ``__{index}`` suffix.
    """
    base = f"{DAGSTER_ADHOC_PREFIX}{project_id}__{environment_id}"
    name = base if index == 0 else f"{base}__{index}"
    # Clean the name and convert it to uppercase
    return clean_name(name).upper()


@public
class DbtCloudCredentials(NamedTuple):
    """The DbtCloudCredentials to access your dbt Cloud workspace.

    Args:
        account_id (int): The ID of your dbt Cloud account.
        token (str): Your dbt Cloud API token.
        access_url (str): Your dbt Cloud workspace URL.
    """

    account_id: int
    token: str
    access_url: str


@public
class DbtCloudWorkspace(ConfigurableResource, Resolvable):
    """This class represents a dbt Cloud workspace and provides utilities
    to interact with dbt Cloud APIs.

    Args:
        credentials (DbtCloudCredentials): An instance of DbtCloudCredentials class.
        project_id (int): The ID of the dbt cloud project to use for this resource.
        environment_id (int): The ID of the environment to use for the dbt Cloud
            project used in this resource.
        adhoc_job_name (Optional[str]): The name of the ad hoc job that will be
            created by Dagster in your dbt Cloud workspace. This ad hoc job is
            used to parse your project and materialize your dbt Cloud assets.
            If not provided, this job name will be generated using your project
            ID and environment ID. When ``adhoc_job_pool_size > 1``, this value
            is used as a prefix and the additional jobs receive an ``__{index}``
            suffix.
        adhoc_job_pool_size (int): The number of ad hoc jobs to create in your
            dbt Cloud workspace. dbt Cloud only allows one concurrent run per
            job, so a value greater than 1 lets Dagster run multiple dbt Cloud
            invocations concurrently (e.g., partitioned backfills, two Dagster
            jobs targeting different assets). Defaults to 1.
        adhoc_job_pool_mode (Literal["overflow", "wait", "fail"]): What to do
            when every ad hoc job in the pool already has an active run at
            ``cli()`` time. ``overflow`` (default) triggers the run on the
            first job regardless and lets dbt Cloud queue it. ``wait`` polls
            until a job frees up. ``fail`` raises immediately.
        request_max_retries (int): The maximum number of times requests to the
            dbt Cloud API should be retried before failing.
        request_retry_delay (float): Time (in seconds) to wait between each
            request retry.
        request_timeout: Time (in seconds) after which the requests to dbt Cloud
            are declared timed out.
    """

    credentials: ResourceDependency[DbtCloudCredentials]
    project_id: int = Field(description="The ID of the dbt Cloud project to use for this resource.")
    environment_id: int = Field(
        description="The ID of environment to use for the dbt Cloud project used in this resource."
    )
    adhoc_job_name: str | None = Field(
        default=None,
        description=(
            "The name of the ad hoc job that will be created by Dagster in your dbt Cloud workspace. "
            "This ad hoc job is used to parse your project and materialize your dbt Cloud assets. "
            "If not provided, this job name will be generated using your project ID and environment ID. "
            "When `adhoc_job_pool_size > 1`, this value is used as a prefix for the additional jobs, "
            "which receive an `__{index}` suffix."
        ),
    )
    adhoc_job_pool_size: int = Field(
        default=1,
        ge=1,
        description=(
            "The number of ad hoc jobs to create in your dbt Cloud workspace. dbt Cloud only "
            "allows one concurrent run per job, so a value greater than 1 lets Dagster run "
            "multiple dbt Cloud invocations concurrently."
        ),
    )
    adhoc_job_pool_mode: DbtCloudAdhocJobPoolMode = Field(
        default="overflow",
        description=(
            "What to do when every ad hoc job in the pool already has an active run at the time "
            "a new invocation is requested. `overflow` triggers the run on the first job and lets "
            "dbt Cloud queue it. `wait` polls until a job frees up. `fail` raises immediately."
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

    def _get_adhoc_job_name_for_index(self, index: int) -> str:
        if self.adhoc_job_name is not None:
            return self.adhoc_job_name if index == 0 else f"{self.adhoc_job_name}__{index}"
        return get_dagster_adhoc_job_name(
            project_id=self.project_id,
            environment_id=self.environment_id,
            index=index,
        )

    def _get_or_create_dagster_adhoc_jobs(self) -> Sequence[DbtCloudJob]:
        """Get or create the pool of ad hoc dbt Cloud jobs for this workspace.

        The job at index 0 keeps the unsuffixed name so existing single-job deployments
        continue to use the same dbt Cloud job after an upgrade.

        Returns:
            Sequence[DbtCloudJob]: One DbtCloudJob per pool index, in order.
        """
        client = self.get_client()
        expected_job_names = [
            self._get_adhoc_job_name_for_index(index=i) for i in range(self.adhoc_job_pool_size)
        ]
        existing_jobs_by_name = {
            job_details.get("name"): DbtCloudJob.from_job_details(job_details)
            for job_details in client.list_jobs(
                project_id=self.project_id,
                environment_id=self.environment_id,
            )
        }

        adhoc_jobs: list[DbtCloudJob] = []
        for expected_job_name in expected_job_names:
            if expected_job_name in existing_jobs_by_name:
                adhoc_jobs.append(existing_jobs_by_name[expected_job_name])
                continue
            adhoc_jobs.append(
                DbtCloudJob.from_job_details(
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
            )
        return adhoc_jobs

    @cached_method
    def fetch_workspace_data(self) -> DbtCloudWorkspaceData:
        adhoc_jobs = self._get_or_create_dagster_adhoc_jobs()
        # Parse runs once at code-server load time on the first job of the pool;
        # there is no need to round-robin since parse is sequential and rare.
        parse_job = adhoc_jobs[0]
        run_handler = DbtCloudJobRunHandler.run(
            job_id=parse_job.id,
            args=["parse"],
            client=self.get_client(),
        )
        run = run_handler.wait()
        run.raise_for_status()
        return DbtCloudWorkspaceData(
            project_id=self.project_id,
            environment_id=self.environment_id,
            adhoc_job_ids=[job.id for job in adhoc_jobs],
            manifest=run_handler.get_manifest(),
            jobs=self.get_client().list_jobs(
                project_id=self.project_id,
                environment_id=self.environment_id,
            ),
        )

    def _pick_available_adhoc_job_id(self, adhoc_job_ids: Sequence[int]) -> int:
        """Greedy selection: return the first ad hoc job in the pool with no active
        run. When all jobs are busy, fall back to the configured ``adhoc_job_pool_mode``.

        For a pool of size 1, this short-circuits and never queries dbt Cloud.
        """
        if len(adhoc_job_ids) == 1:
            return adhoc_job_ids[0]

        deadline = time.time() + DAGSTER_DBT_CLOUD_ADHOC_JOB_WAIT_TIMEOUT_SECONDS
        while True:
            active_adhoc_job_ids = self.get_client().get_active_job_ids(
                project_id=self.project_id,
                environment_id=self.environment_id,
                job_ids=adhoc_job_ids,
            )
            for job_id in adhoc_job_ids:
                if job_id not in active_adhoc_job_ids:
                    return job_id

            if self.adhoc_job_pool_mode == "fail":
                raise Failure(
                    f"All {len(adhoc_job_ids)} ad hoc dbt Cloud jobs in the pool have an "
                    f"active run. Increase `adhoc_job_pool_size` or set "
                    f"`adhoc_job_pool_mode` to `overflow` or `wait`."
                )
            if self.adhoc_job_pool_mode == "overflow":
                # Spread the overflow across the pool rather than always piling on
                # the first job.
                return random.choice(adhoc_job_ids)
            # wait
            if time.time() >= deadline:
                raise Failure(
                    f"Timed out after {DAGSTER_DBT_CLOUD_ADHOC_JOB_WAIT_TIMEOUT_SECONDS}s "
                    f"waiting for an ad hoc dbt Cloud job in the pool to free up."
                )
            time.sleep(DAGSTER_DBT_CLOUD_ADHOC_JOB_WAIT_POLL_INTERVAL_SECONDS)

    def get_or_fetch_workspace_data(self) -> DbtCloudWorkspaceData:
        return DbtCloudWorkspaceDefsLoader(
            workspace=self,
            translator=DagsterDbtTranslator(),
            select=DBT_DEFAULT_SELECT,
            exclude=DBT_DEFAULT_EXCLUDE,
            selector=DBT_DEFAULT_SELECTOR,
        ).get_or_fetch_state()

    # Cache spec retrieval for a specific translator class and dbt selection args.
    @cached_method
    def load_specs(
        self,
        select: str,
        exclude: str,
        selector: str,
        dagster_dbt_translator: DagsterDbtTranslator | None = None,
    ) -> Sequence[AssetSpec | AssetCheckSpec]:
        dagster_dbt_translator = dagster_dbt_translator or DagsterDbtTranslator()

        with self.process_config_and_initialize_cm() as initialized_workspace:
            defs = DbtCloudWorkspaceDefsLoader(
                workspace=initialized_workspace,
                translator=dagster_dbt_translator,
                select=select,
                exclude=exclude,
                selector=selector,
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
        self,
        select: str,
        exclude: str,
        selector: str,
        dagster_dbt_translator: DagsterDbtTranslator | None = None,
    ) -> Sequence[AssetSpec]:
        return [
            spec
            for spec in self.load_specs(
                dagster_dbt_translator=dagster_dbt_translator,
                select=select,
                exclude=exclude,
                selector=selector,
            )
            if isinstance(spec, AssetSpec)
        ]

    def load_check_specs(
        self,
        select: str,
        exclude: str,
        selector: str,
        dagster_dbt_translator: DagsterDbtTranslator | None = None,
    ) -> Sequence[AssetCheckSpec]:
        return [
            spec
            for spec in self.load_specs(
                dagster_dbt_translator=dagster_dbt_translator,
                select=select,
                exclude=exclude,
                selector=selector,
            )
            if isinstance(spec, AssetCheckSpec)
        ]

    @public
    def cli(
        self,
        args: Sequence[str],
        dagster_dbt_translator: DagsterDbtTranslator | None = None,
        context: AssetExecutionContext | None = None,
    ) -> DbtCloudCliInvocation:
        """Creates a dbt CLI invocation with the dbt Cloud client.

        Args:
            args: (Sequence[str]): The dbt CLI command to execute.
            dagster_dbt_translator (Optional[DagsterDbtTranslator]): Allows customizing how to map
                dbt models, seeds, etc. to asset keys and asset metadata.
            context (Optional[AssetExecutionContext]): The execution context.
        """
        dagster_dbt_translator = validate_opt_translator(dagster_dbt_translator)
        dagster_dbt_translator = dagster_dbt_translator or DagsterDbtTranslator()

        client = self.get_client()
        workspace_data = self.get_or_fetch_workspace_data()
        job_id = self._pick_available_adhoc_job_id(workspace_data.adhoc_job_ids)
        manifest = workspace_data.manifest

        updated_params = get_updated_cli_invocation_params_for_context(
            context=context, manifest=manifest, dagster_dbt_translator=dagster_dbt_translator
        )
        manifest = updated_params.manifest
        dagster_dbt_translator = updated_params.dagster_dbt_translator
        selection_args = updated_params.selection_args
        indirect_selection = updated_params.indirect_selection

        # set dbt indirect selection if needed to execute specific dbt tests due to asset check
        # selection
        indirect_selection_args = (
            [f"--indirect-selection {indirect_selection}"] if indirect_selection else []
        )

        full_dbt_args = [*args, *selection_args, *indirect_selection_args]

        # We pass the manifest instead of the workspace data
        # because we use the manifest included in the asset definitions
        # when this method is called inside a function decorated with `@dbt_cloud_assets`
        return DbtCloudCliInvocation.run(
            job_id=job_id,
            args=full_dbt_args,
            client=client,
            manifest=manifest,
            dagster_dbt_translator=dagster_dbt_translator,
            context=context,
        )


def load_dbt_cloud_asset_specs(
    workspace: DbtCloudWorkspace,
    dagster_dbt_translator: DagsterDbtTranslator | None = None,
    select: str = DBT_DEFAULT_SELECT,
    exclude: str = DBT_DEFAULT_EXCLUDE,
    selector: str = DBT_DEFAULT_SELECTOR,
) -> Sequence[AssetSpec]:
    return workspace.load_asset_specs(
        dagster_dbt_translator=dagster_dbt_translator,
        select=select,
        exclude=exclude,
        selector=selector,
    )


def load_dbt_cloud_check_specs(
    workspace: DbtCloudWorkspace,
    dagster_dbt_translator: DagsterDbtTranslator | None = None,
    select: str = DBT_DEFAULT_SELECT,
    exclude: str = DBT_DEFAULT_EXCLUDE,
    selector: str = DBT_DEFAULT_SELECTOR,
) -> Sequence[AssetCheckSpec]:
    return workspace.load_check_specs(
        dagster_dbt_translator=dagster_dbt_translator,
        select=select,
        exclude=exclude,
        selector=selector,
    )


@record
class DbtCloudWorkspaceDefsLoader(StateBackedDefinitionsLoader[DbtCloudWorkspaceData]):
    workspace: DbtCloudWorkspace
    translator: DagsterDbtTranslator
    select: str
    exclude: str
    selector: str

    @property
    def defs_key(self) -> str:
        return f"{DBT_CLOUD_RECONSTRUCTION_METADATA_KEY_PREFIX}.{self.workspace.unique_id}"

    def fetch_state(self) -> DbtCloudWorkspaceData:
        return self.workspace.fetch_workspace_data()

    def defs_from_state(self, state: DbtCloudWorkspaceData) -> Definitions:
        all_asset_specs, all_check_specs = build_dbt_specs(
            manifest=state.manifest,
            translator=self.translator,
            select=self.select,
            exclude=self.exclude,
            selector=self.selector,
            io_manager_key=None,
            project=None,
        )

        all_asset_specs = [
            spec.replace_attributes(kinds={"dbtcloud"} | spec.kinds - {"dbt"}).merge_attributes(
                metadata={
                    DAGSTER_DBT_CLOUD_ACCOUNT_ID_METADATA_KEY: self.workspace.credentials.account_id,
                    DAGSTER_DBT_CLOUD_PROJECT_ID_METADATA_KEY: state.project_id,
                    DAGSTER_DBT_CLOUD_ENVIRONMENT_ID_METADATA_KEY: state.environment_id,
                }
            )
            for spec in all_asset_specs
        ]

        # External facing checks are not supported yet
        # https://linear.app/dagster-labs/issue/AD-915/support-external-asset-checks-in-dbt-cloud-v2
        @multi_asset_check(specs=all_check_specs)
        def _all_asset_checks(): ...

        return Definitions(assets=all_asset_specs, asset_checks=[_all_asset_checks])
