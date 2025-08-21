from collections.abc import Iterator, Mapping
from typing import TYPE_CHECKING, Any

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetMaterialization,
    ConfigurableResource,
    MaterializeResult,
)
from dagster_shared.utils.cached_method import cached_method
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import compute, jobs
from pydantic import Field

from dagster_databricks.components.databricks_asset_bundle.configs import (
    ResolvedDatabricksExistingClusterConfig,
    ResolvedDatabricksNewClusterConfig,
    ResolvedDatabricksServerlessConfig,
    parse_libraries,
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
        databricks_tasks = []
        for task_key, task in selected_tasks_by_task_key.items():
            # TODO: support common config
            context.log.info(f"Task {task_key}: parameters={task.task_parameters}")

            # Create the SubmitTask params dictionary
            submit_task_params = {
                "task_key": task_key,
                task.submit_task_key: task.to_databricks_sdk_task(),
            }

            # Convert dependency config to TaskDependency objects
            task_dependencies = [
                jobs.TaskDependency(task_key=dep_config.task_key, outcome=dep_config.outcome)
                for dep_config in task.depends_on
            ]
            task_dependency_config = {"depends_on": task_dependencies} if task_dependencies else {}
            context.log.info(f"Task {task_key} depends on: {task_dependencies}")

            # Determine cluster configuration based on task type
            compute_config = {}
            if task.needs_cluster and not (
                isinstance(component.compute_config, ResolvedDatabricksServerlessConfig)
                and component.compute_config.is_serverless
            ):
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

            libraries_list = parse_libraries(task.libraries)
            libraries_config = {"libraries": libraries_list} if libraries_list else {}
            context.log.info(f"Task {task_key} has {len(libraries_list)} libraries configured")

            submit_task_params = {
                **submit_task_params,
                **task_dependency_config,
                **compute_config,
                **libraries_config,
            }

            databricks_tasks.append(jobs.SubmitTask(**submit_task_params))

        # Prepare job submission parameters
        job_submit_params = {
            "run_name": f"{assets_def.node_def.name}_{context.run_id}",
            "tasks": databricks_tasks,
        }

        job_run = self._submit_job(params=job_submit_params)
        context.log.info(f"Databricks job submitted with run ID: {job_run.run_id}")

        # Build Databricks job run URL
        workspace_url = self.host.rstrip("/")
        job_run_url = f"{workspace_url}/jobs/{job_run.job_id}/runs/{job_run.run_id}"
        context.log.info(f"Databricks job run URL: {job_run_url}")

        final_run = self._poll_run(run_id=job_run.run_id)
        context.log.info(f"Job completed with overall state: {final_run.state.result_state}")
        context.log.info(f"View job details: {job_run_url}")

        # Get individual task run states
        for run_task in final_run.tasks:
            task_key = run_task.task_key
            task_state = (
                run_task.state.result_state.value if run_task.state.result_state else "UNKNOWN"
            )

            # Build task-specific URL (task tab within the job run)
            task_url = f"{job_run_url}#task/{task_key}"

            context.log.info(f"Task {task_key} completed with state: {task_state}")
            context.log.info(f"Task {task_key} details: {task_url}")

            if task_state == "SUCCESS":
                if task_key in selected_task_key_to_asset_key_mapping:
                    yield MaterializeResult(
                        asset_key=selected_task_key_to_asset_key_mapping[task_key]
                    )
                else:
                    context.log.warning(
                        f"An unexpected asset was materialized for task: {task_key}. "
                        f"Yielding a materialization event."
                    )
                    yield AssetMaterialization(asset_key=AssetKey(task_key))

    def _submit_job(self, params: Mapping[str, Any]) -> jobs.Run:
        client = self.get_client()
        job_run = client.jobs.submit(**params)
        return client.jobs.get_run(run_id=job_run.run_id)

    def _poll_run(self, run_id: int) -> jobs.Run:
        client = self.get_client()
        # Wait for job completion
        client.jobs.wait_get_run_job_terminated_or_skipped(run_id)
        # Get final job status
        return client.jobs.get_run(run_id)
