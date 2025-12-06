import asyncio
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Optional

import dagster as dg
from dagster import AssetExecutionContext, AssetSpec, Resolvable, multi_asset
from dagster._annotations import beta
from dagster._core.definitions.definitions_class import Definitions
from dagster.components import Resolver
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.utils.defs_state import (
    DefsStateConfig,
    DefsStateConfigArgs,
    ResolvedDefsStateConfig,
)
from dagster_shared.serdes.serdes import deserialize_value, serialize_value
from databricks.sdk import WorkspaceClient

from dagster_databricks.components.databricks_asset_bundle.configs import Job
from dagster_databricks.components.databricks_workspace.fetcher import (
    fetch_databricks_workspace_data,
)
from dagster_databricks.components.databricks_workspace.schema import (
    AssetSpecConfig,
    DatabricksFilterConfig,
    DatabricksWorkspaceConfig,
    resolve_databricks_filter,
)

DatabricksJobInfo = dict[str, Any]


def _snake_case(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9]+", "_", str(name))
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower().strip("_")


@beta
@dataclass
class DatabricksWorkspaceComponent(StateBackedComponent, Resolvable):
    """Component that fetches Databricks workspace jobs and exposes them as assets."""

    workspace: Annotated[
        DatabricksWorkspaceConfig,
        Resolver.default(description="Databricks workspace connection info"),
    ]

    databricks_filter: Annotated[
        Optional[DatabricksFilterConfig],
        Resolver.default(description="Filter which Databricks jobs to include"),
    ] = None

    assets_by_task_key: Annotated[
        Optional[dict[str, AssetSpecConfig]],
        Resolver.default(
            description="Optional mapping of Databricks task keys to Dagster AssetSpecs.",
        ),
    ] = None

    defs_state: ResolvedDefsStateConfig = field(
        default_factory=DefsStateConfigArgs.legacy_code_server_snapshots
    )

    @property
    def defs_state_config(self) -> DefsStateConfig:
        default_key = f"{self.__class__.__name__}[{self.workspace.host}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=default_key)

    def get_state(self) -> list[Job]:
        """Fetch current workspace state (list of Jobs)."""
        client = WorkspaceClient(host=self.workspace.host, token=self.workspace.token)

        filter_config = self.databricks_filter or DatabricksFilterConfig()
        databricks_filter = resolve_databricks_filter(filter_config)

        return asyncio.run(fetch_databricks_workspace_data(client, databricks_filter))

    def write_state_to_path(self, state_path: Path) -> None:
        """Serializes the fetched state to disk."""
        jobs = self.get_state()
        state_path.write_text(serialize_value(jobs))

    def build_defs_from_state(self, context: Any, state_path: Path) -> dg.Definitions:
        """Build Dagster Definitions from the cached state."""
        if not state_path or not state_path.exists():
            return dg.Definitions()

        jobs_state = deserialize_value(state_path.read_text(), list[Job])

        databricks_assets = []
        for job in jobs_state:
            tasks = getattr(job, "tasks", []) if not isinstance(job, dict) else job.get("tasks", [])

            for task in tasks:
                specs = self.get_asset_specs(task)

                asset_name = specs[0].key.path[-1] if specs else f"task_{id(task)}"

                @multi_asset(name=asset_name, specs=specs)
                def _task_multi_asset(context: AssetExecutionContext):
                    context.log.info(f"Executing Databricks task: {asset_name}")
                    return None

                databricks_assets.append(_task_multi_asset)

        return Definitions(assets=databricks_assets)

    def get_asset_specs(self, task: Any) -> list[AssetSpec]:
        """Return a list of AssetSpec objects for the given task."""
        if isinstance(task, dict):
            task_key = task.get("task_key")
        else:
            task_key = getattr(task, "task_key", None)

        if task_key and self.assets_by_task_key and task_key in self.assets_by_task_key:
            user_config = self.assets_by_task_key[task_key]

            return [
                AssetSpec(
                    key=user_config.key,
                    group_name=user_config.group,
                    description=user_config.description,
                    kinds={"databricks"},
                    metadata={"task_key": task_key},
                )
            ]

        task_name = task_key or "unknown_task"
        key = _snake_case(task_name)

        return [
            AssetSpec(
                key=key,
                description=f"Databricks task {task_name}",
                kinds={"databricks"},
                metadata={"task_key": task_key} if task_key else {},
            )
        ]
