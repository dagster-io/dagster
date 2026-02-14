from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Optional

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetsDefinition,
    AssetSpec,
    Definitions,
    MaterializeResult,
    MetadataValue,
    Resolvable,
    ResolvedAssetSpec,
    multi_asset,
)
from dagster._serdes import whitelist_for_serdes
from dagster._symbol_annotations.lifecycle import preview
from dagster.components import Resolver
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.utils.defs_state import (
    DefsStateConfig,
    DefsStateConfigArgs,
    ResolvedDefsStateConfig,
)
from dagster_shared.record import record
from dagster_shared.serdes.serdes import deserialize_value, serialize_value
from databricks.sdk.service.jobs import RunResultState

from dagster_databricks.components.databricks_asset_bundle.component import (
    DatabricksWorkspaceArgs,
    resolve_databricks_workspace,
)
from dagster_databricks.components.databricks_asset_bundle.configs import (
    DatabricksBaseTask,
    DatabricksJob,
)
from dagster_databricks.components.databricks_asset_bundle.resource import DatabricksWorkspace
from dagster_databricks.components.databricks_workspace.schema import ResolvedDatabricksFilter
from dagster_databricks.utils import snake_case


@whitelist_for_serdes
@record
class DatabricksWorkspaceData:
    """Container for serialized Databricks workspace state."""

    jobs: list[DatabricksJob]


@preview
@dataclass
class DatabricksWorkspaceComponent(StateBackedComponent, Resolvable):
    """Component that fetches Databricks workspace jobs and exposes them as assets."""

    workspace: Annotated[
        DatabricksWorkspace,
        Resolver(
            resolve_databricks_workspace,
            model_field_type=DatabricksWorkspaceArgs.model(),
            description="The mapping defining a DatabricksWorkspace.",
        ),
    ]

    databricks_filter: Annotated[
        Optional[ResolvedDatabricksFilter],
        Resolver.default(description="Filter which Databricks jobs to include"),
    ] = None

    assets_by_job_task_key: Annotated[
        Optional[dict[str, dict[str, list[ResolvedAssetSpec]]]],
        Resolver.default(
            description="Optional mapping of Databricks job names to task keys to lists of Dagster AssetSpecs. "
            "Structure: {job_name: {task_key: [AssetSpec, ...]}}. "
            "Both job name and task key are required to uniquely identify a task.",
        ),
    ] = None

    defs_state: ResolvedDefsStateConfig = field(
        default_factory=DefsStateConfigArgs.legacy_code_server_snapshots
    )

    @property
    def defs_state_config(self) -> DefsStateConfig:
        default_key = f"{self.__class__.__name__}[{self.workspace.host}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=default_key)

    async def write_state_to_path(self, state_path: Path) -> None:
        """Async implementation of state fetching."""
        jobs = await self.workspace.fetch_jobs(self.databricks_filter)

        data = DatabricksWorkspaceData(jobs=jobs)
        state_path.write_text(serialize_value(data))

    def build_defs_from_state(self, context: Any, state_path: Optional[Path]) -> Definitions:
        """Build Dagster Definitions from the cached state."""
        if not state_path or not state_path.exists():
            return Definitions()

        workspace_data = deserialize_value(state_path.read_text(), DatabricksWorkspaceData)
        jobs_state = workspace_data.jobs

        databricks_assets = []

        for job in jobs_state:
            job_specs = []
            task_key_map = {}
            tasks = job.tasks or []

            for task in tasks:
                specs = self.get_asset_specs(task=task, job_name=job.name)

                for spec in specs:
                    job_specs.append(spec)
                    task_key_map[spec.key] = task.task_key

            if job_specs:
                asset_def = self._create_job_asset_def(job, job_specs, task_key_map)
                databricks_assets.append(asset_def)

        return Definitions(assets=databricks_assets)

    def _create_job_asset_def(
        self, job: DatabricksJob, specs: list[Any], task_key_map: dict[AssetKey, str]
    ) -> AssetsDefinition:
        asset_name = f"databricks_job_{job.job_id}"

        @multi_asset(name=asset_name, specs=specs, can_subset=True)
        def _execution_fn(context: AssetExecutionContext):
            client = self.workspace.get_client()
            selected_keys = context.selected_asset_keys

            # Get tasks to run from the job-specific mapping
            job_task_mapping = (self.assets_by_job_task_key or {}).get(job.name, {})
            tasks_to_run = [
                task_key
                for task_key, task_specs in job_task_mapping.items()
                if any(spec.key in selected_keys for spec in task_specs)
            ]
            context.log.info(f"Triggering Databricks job {job.job_id} for tasks: {tasks_to_run}")

            run = client.jobs.run_now(
                job_id=job.job_id, only=tasks_to_run if tasks_to_run else None
            )
            if run.run_page_url:
                context.log.info(f"Run URL: {run.run_page_url}")

            client.jobs.wait_get_run_job_terminated_or_skipped(run.run_id)

            final_run = client.jobs.get_run(run.run_id)
            state_obj = final_run.state
            result_state = state_obj.result_state if state_obj else None

            if result_state != RunResultState.SUCCESS:
                status_str = result_state.value if result_state else "UNKNOWN"
                error_msg = f"Job {job.job_id} failed: {status_str}. URL: {run.run_page_url}"
                context.log.error(error_msg)
                raise Exception(error_msg)

            for spec in specs:
                if spec.key in selected_keys:
                    # Look up task key from the map we built during spec creation
                    current_task_key = task_key_map.get(spec.key, "unknown")
                    yield MaterializeResult(
                        asset_key=spec.key,
                        metadata={
                            "dagster-databricks/job_id": MetadataValue.int(job.job_id),
                            "dagster-databricks/run_id": MetadataValue.int(run.run_id),
                            "dagster-databricks/run_url": MetadataValue.url(run.run_page_url or ""),
                            "dagster-databricks/task_key": current_task_key,
                        },
                    )

        return _execution_fn

    def get_asset_specs(self, task: DatabricksBaseTask, job_name: str) -> list[AssetSpec]:
        """Return a list of AssetSpec objects for the given task.

        If assets_by_job_task_key is configured with a mapping for this job and task,
        returns the configured specs with Databricks metadata added.
        Otherwise, returns a default spec with key [job_name, task_key].
        """
        task_key = task.task_key
        clean_job = snake_case(job_name)

        # Look up by job name first, then task key
        job_mapping = (self.assets_by_job_task_key or {}).get(job_name, {})
        if task_key in job_mapping:
            return [
                spec.merge_attributes(
                    kinds={"databricks"},
                    metadata={
                        "dagster-databricks/task_key": task_key,
                        "dagster-databricks/job_name": job_name,
                    },
                )
                for spec in job_mapping[task_key]
            ]

        clean_task = snake_case(task_key)

        return [
            AssetSpec(
                key=AssetKey([clean_job, clean_task]),
                description=f"Databricks task {task_key} in job {job_name}",
                kinds={"databricks"},
                metadata={
                    "dagster-databricks/task_key": task_key,
                    "dagster-databricks/job_name": job_name,
                },
            )
        ]
