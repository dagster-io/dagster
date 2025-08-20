from collections.abc import Iterator
from typing import Any

from dagster import AssetExecutionContext, AssetMaterialization, ConfigurableResource
from dagster_shared.utils.cached_method import cached_method
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs
from pydantic import Field


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
        self, tasks: Any, context: AssetExecutionContext
    ) -> Iterator[AssetMaterialization]:
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
            parameters = task.task_parameters
            context.log.info(f"Task {task_key}: parameters={parameters}")

            databricks_task = jobs.SubmitTask(task_key)
            databricks_tasks_by_task_key[task_key] = databricks_task

        # TODO: implement submit tasks and poll at client level
        for task_key in databricks_tasks_by_task_key.keys():
            yield AssetMaterialization(asset_key=selected_task_key_to_asset_key_mapping[task_key])
