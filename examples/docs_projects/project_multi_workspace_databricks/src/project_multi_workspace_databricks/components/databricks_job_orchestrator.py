from datetime import timedelta
from typing import Any, Mapping, Optional

import dagster as dg
from dagster_databricks import DatabricksClient
from pydantic import Field


class WorkspaceConfig(dg.Model):
    """Configuration for connecting to a Databricks workspace."""

    host: str = Field(..., description="Databricks workspace host URL")
    token: str = Field(..., description="Databricks personal access token")


class AssetDefinition(dg.Model):
    """Definition of an asset produced by a Databricks job."""

    key: str = Field(
        ..., description="Asset key (can include slashes for multi-part keys)"
    )
    description: Optional[str] = Field(
        default=None, description="Description of what this asset contains"
    )
    group_name: Optional[str] = Field(
        default=None, description="Asset group for organization"
    )
    deps: list[str] = Field(
        default_factory=list, description="List of upstream asset keys this depends on"
    )


class DatabricksJobOrchestrator(dg.Component, dg.Model, dg.Resolvable):
    """Orchestrates Databricks job execution across multiple workspaces.

    This component creates Dagster assets that execute Databricks jobs and wait for
    completion. Ideal for data mesh architectures where jobs are distributed across
    multiple Databricks workspaces.
    """

    job_id: int = Field(..., description="The Databricks job ID to execute")
    job_parameters: Optional[Mapping[str, Any]] = Field(
        default=None, description="Parameters to pass to the Databricks job"
    )
    workspace_config: WorkspaceConfig = Field(
        ..., description="Databricks workspace connection configuration"
    )
    assets: list[AssetDefinition] = Field(
        ..., description="Assets produced by this Databricks job"
    )

    def execute(self) -> Mapping[str, Any]:
        """Execute the Databricks job and return execution metadata."""
        client = DatabricksClient(
            host=self.workspace_config.host,
            token=self.workspace_config.token,
        )
        workspace = client.workspace_client
        run_response = workspace.jobs.run_now(job_id=self.job_id)
        finished = run_response.result(timeout=timedelta(hours=1))
        return {
            "start_time": finished.start_time,
            "end_time": finished.end_time,
            "run_id": finished.run_id,
        }

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions:
        """Build Dagster definitions for this component."""
        enriched_specs = []
        for asset_def in self.assets:
            key_parts = asset_def.key.split("/")
            asset_key = dg.AssetKey(key_parts)
            deps = [dg.AssetKey(dep.split("/")) for dep in asset_def.deps]
            description = asset_def.description or (
                f"Asset {asset_def.key} produced by Databricks job {self.job_id}"
            )
            metadata: dict[str, Any] = {
                "databricks_job_id": self.job_id,
                "databricks_host": self.workspace_config.host,
                "job_parameters": self.job_parameters or {},
            }
            spec = dg.AssetSpec(
                key=asset_key,
                description=description,
                metadata=metadata,
                kinds={"databricks"},
                group_name=asset_def.group_name,
                deps=deps,
            )
            enriched_specs.append(spec)

        component = self

        @dg.multi_asset(
            name=f"databricks_job_{self.job_id}",
            specs=enriched_specs,
        )
        def databricks_job_asset(context: dg.AssetExecutionContext):
            """Execute the Databricks job and materialize all assets."""
            context.log.info(f"Executing Databricks job {component.job_id}")
            result = component.execute()
            context.log.info(f"Job completed: {result}")
            for spec in enriched_specs:
                yield dg.MaterializeResult(
                    asset_key=spec.key,
                    metadata={
                        "execution_start_time": result["start_time"],
                        "execution_end_time": result["end_time"],
                        "databricks_run_id": result["run_id"],
                    },
                )

        return dg.Definitions(assets=[databricks_job_asset])
