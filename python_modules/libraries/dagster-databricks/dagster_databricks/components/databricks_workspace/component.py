import asyncio
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Optional

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetSpec,
    Definitions,
    MaterializeResult,
    MetadataValue,
    Resolvable,
    ResolvedAssetSpec,
    multi_asset,
)
from dagster._annotations import beta
from dagster._serdes import whitelist_for_serdes
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
from dagster_databricks.components.databricks_asset_bundle.configs import DatabricksJob
from dagster_databricks.components.databricks_asset_bundle.resource import DatabricksWorkspace
from dagster_databricks.components.databricks_workspace.fetcher import (
    fetch_databricks_workspace_data,
)
from dagster_databricks.components.databricks_workspace.schema import (
    DatabricksFilter,
    ResolvedDatabricksFilter,
)


@whitelist_for_serdes
@record
class DatabricksWorkspaceData:
    """Container for serialized Databricks workspace state."""

    jobs: list[DatabricksJob]


def _snake_case(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9]+", "_", str(name))
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower().strip("_")


@beta
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

    assets_by_task_key: Annotated[
        Optional[dict[str, list[ResolvedAssetSpec]]],
        Resolver.default(
            description="Optional mapping of Databricks task keys to lists of Dagster AssetSpecs.",
        ),
    ] = None

    defs_state: ResolvedDefsStateConfig = field(
        default_factory=DefsStateConfigArgs.legacy_code_server_snapshots
    )

    @property
    def defs_state_config(self) -> DefsStateConfig:
        default_key = f"{self.__class__.__name__}[{self.workspace.host}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=default_key)

    def get_state(self) -> DatabricksWorkspaceData:
        """Fetch current workspace state (list of Jobs)."""
        client = self.workspace.get_client()
        databricks_filter = self.databricks_filter or DatabricksFilter(include_job=lambda j: True)
        jobs = asyncio.run(fetch_databricks_workspace_data(client, databricks_filter))
        return DatabricksWorkspaceData(jobs=jobs)

    def write_state_to_path(self, state_path: Path) -> None:
        """Serializes the fetched state to disk."""
        state = self.get_state()
        state_path.write_text(serialize_value(state))

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
                current_task_key = getattr(task, "task_key", "unknown")
                specs = self.get_asset_specs(job_name=job.name, task=task)

                for spec in specs:
                    job_specs.append(spec)
                    task_key_map[spec.key] = current_task_key

            if not job_specs:
                continue

            asset_name = f"databricks_job_{job.job_id}"

            #  Factory to capture job-level variables
            def make_job_asset_fn(
                captured_job_id, captured_job_name, captured_specs, captured_key_map
            ):
                # Define one multi-asset for the whole job
                @multi_asset(name=asset_name, specs=captured_specs, can_subset=True)
                def _job_multi_asset(context: AssetExecutionContext):
                    """Execute the Databricks job containing these tasks."""
                    client = self.workspace.get_client()

                    selected_keys = context.selected_asset_keys
                    context.log.info(
                        f"Triggering Databricks job {captured_job_id} for keys: {selected_keys}"
                    )

                    run = client.jobs.run_now(job_id=captured_job_id)

                    if run.run_page_url:
                        context.log.info(f"Databricks run URL: {run.run_page_url}")

                    client.jobs.wait_get_run_job_terminated_or_skipped(run.run_id)

                    final_run = client.jobs.get_run(run.run_id)

                    state_obj = final_run.state
                    result_state = state_obj.result_state if state_obj else None

                    if result_state != RunResultState.SUCCESS:
                        status_str = result_state.value if result_state else "UNKNOWN"
                        error_msg = (
                            f"Databricks job {captured_job_id} failed with state: {status_str}. "
                            f"View run: {run.run_page_url}"
                        )
                        context.log.error(error_msg)
                        raise Exception(error_msg)

                    context.log.info(f"Job finished with state: {result_state.value}")

                    for spec in captured_specs:
                        if spec.key in selected_keys:
                            task_key = captured_key_map.get(spec.key)
                            yield MaterializeResult(
                                asset_key=spec.key,
                                metadata={
                                    "job_id": MetadataValue.int(captured_job_id),
                                    "job_name": MetadataValue.text(captured_job_name),
                                    "task_key": MetadataValue.text(task_key) if task_key else None,
                                    "run_id": MetadataValue.int(run.run_id),
                                    "run_url": MetadataValue.url(run.run_page_url)
                                    if run.run_page_url
                                    else None,
                                    "final_state": MetadataValue.text(result_state.value),
                                },
                            )

                return _job_multi_asset

            asset_def = make_job_asset_fn(job.job_id, job.name, job_specs, task_key_map)
            databricks_assets.append(asset_def)

        return Definitions(assets=databricks_assets)

    def get_asset_specs(self, job_name: str, task: Any) -> list[AssetSpec]:
        """Return a list of AssetSpec objects for the given task."""
        task_key = getattr(task, "task_key", None)

        if task_key and self.assets_by_task_key and task_key in self.assets_by_task_key:
            return self.assets_by_task_key[task_key]

        clean_job = _snake_case(job_name)
        clean_task = _snake_case(task_key or "unknown")

        return [
            AssetSpec(
                key=AssetKey([clean_job, clean_task]),
                description=f"Databricks task {clean_task} in job {job_name}",
                kinds={"databricks"},
                metadata={"task_key": task_key, "job_name": job_name} if task_key else {},
            )
        ]
