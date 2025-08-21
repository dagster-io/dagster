from collections.abc import Iterator
from typing import TYPE_CHECKING

from dagster import AssetExecutionContext, AssetMaterialization, ConfigurableResource
from dagster_shared.utils.cached_method import cached_method
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import compute, jobs
from pydantic import Field

from dagster_databricks.components.databricks_asset_bundle.configs import (
    ResolvedDatabricksExistingClusterConfig,
    ResolvedDatabricksNewClusterConfig,
)

if TYPE_CHECKING:
    from dagster_databricks.components.databricks_asset_bundle.component import (
        DatabricksAssetBundleComponent,
    )


class DatabricksWorkspace(ConfigurableResource):
    """Represents a workspace in Databricks and provides utilities
    to interact with the Databricks SDK.
    """

    host: str = Field(description="The host used to connect to the Databricks Workspace.")
    token: str = Field(description="The token used to connect to Databricks Workspace.")

    @cached_method
    def get_client(self) -> WorkspaceClient:
        return WorkspaceClient(
            host=self.host,
            token=self.token,
        )

    def submit_and_poll(
        self, component: "DatabricksAssetBundleComponent", context: AssetExecutionContext
    ) -> Iterator[AssetMaterialization]:
        tasks = component.databricks_config.tasks

        # Get selected asset keys that are being materialized
        assets_def = context.assets_def
        selected_asset_keys = context.selected_asset_keys
        context.log.info(f"Selected assets: {selected_asset_keys}")

        # Filter tasks to only include those that correspond to selected assets
        selected_specs = [
            assets_def.specs_by_key[selected_key] for selected_key in selected_asset_keys
        ]
        selected_task_key_to_asset_key_mapping = {
            spec.metadata["task_key"].value: spec.key for spec in selected_specs
        }
        selected_tasks_by_task_key = {
            task.task_key: task
            for task in tasks
            if task.task_key in selected_task_key_to_asset_key_mapping.keys()
        }

        context.log.info(f"Running {len(selected_tasks_by_task_key)} out of {len(tasks)} tasks")

        if not selected_tasks_by_task_key:
            context.log.info("No tasks selected for execution")

        # Create Databricks SDK task objects only for selected tasks
        databricks_tasks_by_task_key = {}
        for task_key, task in selected_tasks_by_task_key.items():
            # TODO: support common config
            context.log.info(f"Task {task_key}: parameters={task.task_parameters}")

            # Create the SubmitTask params dictionary
            submit_task_params = {"task_key": task_key}

            # Convert dependency config to TaskDependency objects
            task_dependencies = [
                jobs.TaskDependency(task_key=dep_config.task_key, outcome=dep_config.outcome)
                for dep_config in task.depends_on
            ]
            task_dependency_config = {"depends_on": task_dependencies} if task_dependencies else {}
            context.log.info(f"Task {task_key} depends on: {task_dependencies}")

            # Determine cluster configuration based on task type
            compute_config = {}
            if task.needs_cluster:
                if isinstance(component.compute_config, ResolvedDatabricksExistingClusterConfig):
                    compute_config["existing_cluster_id"] = (
                        component.compute_config.existing_cluster_id
                    )
                elif isinstance(component.compute_config, ResolvedDatabricksNewClusterConfig):
                    compute_config["new_cluster"] = compute.ClusterSpec(
                        spark_version=component.compute_config.spark_version,
                        node_type_id=component.compute_config.node_type_id,
                        num_workers=component.compute_config.num_workers,
                    )

            submit_task_params = {
                **submit_task_params,
                **task_dependency_config,
                **compute_config,
            }

            databricks_task = jobs.SubmitTask(**submit_task_params)
            databricks_tasks_by_task_key[task_key] = databricks_task

        # TODO: implement submit tasks and poll at client level
        for task_key in databricks_tasks_by_task_key.keys():
            yield AssetMaterialization(asset_key=selected_task_key_to_asset_key_mapping[task_key])
