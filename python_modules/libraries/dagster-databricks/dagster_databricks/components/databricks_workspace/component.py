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

from dagster_databricks.components.databricks_asset_bundle.configs import DatabricksJob
from dagster_databricks.components.databricks_asset_bundle.resource import (
    DatabricksWorkspace,
)
from dagster_databricks.components.databricks_asset_bundle.component import (
    DatabricksWorkspaceArgs,
    resolve_databricks_workspace,
)
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

    def build_defs_from_state(self, context: Any, state_path: Path) -> Definitions:
        """Build Dagster Definitions from the cached state."""
        if not state_path or not state_path.exists():
            return Definitions()

        workspace_data = deserialize_value(state_path.read_text(), DatabricksWorkspaceData)
        jobs_state = workspace_data.jobs

        databricks_assets = []
        for job in jobs_state:
            tasks = job.tasks or []
            for task in tasks:
                current_task_key = getattr(task, "task_key", "unknown")
                specs = self.get_asset_specs(job_name=job.name, task=task)
                asset_name = specs[0].key.path[-1] if specs else f"task_{id(task)}"

                def make_asset_fn(captured_job_id, captured_task_key, captured_job_name):
                    
                    @multi_asset(name=asset_name, specs=specs)
                    def _task_multi_asset(context: AssetExecutionContext):
                        """Execute the corresponding Databricks job when the asset is materialized."""
                        client = self.workspace.get_client()

                        # Trigger the Databricks job
                        context.log.info(f"Triggering Databricks job {captured_job_id} for task {captured_task_key}")
                        run = client.jobs.run_now(job_id=captured_job_id)
                        run_id = run.run_id
                        run_url = getattr(run, "run_page_url", None)

                        if run_url:
                            context.log.info(f"Databricks job run URL: {run_url}")

                        client.jobs.wait_get_run_job_terminated_or_skipped(run_id)

                        final_run = client.jobs.get_run(run_id)
                        state_obj = getattr(final_run, "state", None)
                        result_state_obj = getattr(state_obj, "result_state", None)
                        final_state = result_state_obj.value if result_state_obj else "UNKNOWN"

                        for spec in specs:
                            yield MaterializeResult(
                                asset_key=spec.key,
                                metadata={
                                    "job_id": MetadataValue.int(captured_job_id),
                                    "job_name": MetadataValue.text(captured_job_name),
                                    "task_key": MetadataValue.text(captured_task_key) if captured_task_key else None,
                                    "run_id": MetadataValue.int(run_id),
                                    "run_url": MetadataValue.url(run_url),
                                    "final_state": MetadataValue.text(final_state),
                                },
                            )
                    
                    return _task_multi_asset

                asset_definition = make_asset_fn(job.job_id, current_task_key, job.name)
                databricks_assets.append(asset_definition)

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
