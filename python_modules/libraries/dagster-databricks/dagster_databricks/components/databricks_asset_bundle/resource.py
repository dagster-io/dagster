import asyncio
from collections.abc import Iterator, Mapping
from typing import TYPE_CHECKING, Any

import aiohttp

DATABRICKS_JOBS_API_PATH = "/api/2.1/jobs"
MAX_CONCURRENT_REQUESTS = 10
MAX_RETRIES = 5
RATE_LIMIT_STATUS_CODE = 429
JOBS_LIST_PAGE_SIZE = 100
CONNECT_TIMEOUT_SECONDS = 30
READ_TIMEOUT_SECONDS = 60

from dagster import (
    AssetExecutionContext,
    ConfigurableResource,
    Failure,
    MaterializeResult,
    _check as check,
)
from dagster._annotations import preview
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster_shared.utils.cached_method import cached_method
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import compute, jobs
from pydantic import Field

from dagster_databricks.components.databricks_asset_bundle.configs import (
    DatabricksJob,
    DatabricksUnknownTask,
    ResolvedDatabricksExistingClusterConfig,
    ResolvedDatabricksNewClusterConfig,
    ResolvedDatabricksServerlessConfig,
    parse_libraries,
    parse_task_from_config,
)
from dagster_databricks.utils import build_job_run_url

if TYPE_CHECKING:
    from dagster_databricks.components.databricks_asset_bundle.component import (
        DatabricksAssetBundleComponent,
    )


@preview
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

    async def fetch_jobs(self, databricks_filter: Any) -> list[DatabricksJob]:
        """Fetches all jobs from the Databricks workspace using async I/O.

        Handles pagination via has_more/next_page_token, rate-limit retries with
        bounded exponential backoff, and concurrent job detail fetches with a
        shared aiohttp session.
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        base_url = self.host.rstrip("/")

        timeout = aiohttp.ClientTimeout(
            connect=CONNECT_TIMEOUT_SECONDS, sock_read=READ_TIMEOUT_SECONDS
        )
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            # Phase 1: paginate through the jobs list
            list_url = f"{base_url}{DATABRICKS_JOBS_API_PATH}/list"
            all_jobs_lite: list[dict[str, Any]] = []
            params: dict[str, Any] = {"limit": JOBS_LIST_PAGE_SIZE}
            data: dict[str, Any] = {}

            while True:
                list_wait: int = 0
                for list_attempt in range(MAX_RETRIES + 1):
                    list_wait = 0
                    async with session.get(list_url, params=params) as resp:
                        if resp.status == RATE_LIMIT_STATUS_CODE:
                            if list_attempt >= MAX_RETRIES:
                                resp.raise_for_status()
                            retry_after = resp.headers.get("Retry-After")
                            try:
                                list_wait = (
                                    int(retry_after) if retry_after else min(2**list_attempt, 30)
                                )
                            except (ValueError, TypeError):
                                list_wait = min(2**list_attempt, 30)
                        else:
                            resp.raise_for_status()
                            data = await resp.json()
                    # Release response context before sleeping so connections return to pool
                    if list_wait:
                        await asyncio.sleep(list_wait)
                        continue
                    break

                all_jobs_lite.extend(data.get("jobs", []))

                if not data.get("has_more", False):
                    break

                next_token = data.get("next_page_token")
                if not next_token:
                    raise ValueError(
                        "Databricks Jobs List API returned has_more=True but did not"
                        " provide a next_page_token. Cannot continue pagination."
                    )
                params["page_token"] = next_token

            # Phase 2: filter, then fetch full job details concurrently
            job_ids_to_fetch = [
                j["job_id"]
                for j in all_jobs_lite
                if not databricks_filter or databricks_filter.include_job(j)
            ]

            if not job_ids_to_fetch:
                return []

            semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

            async def _fetch_single_job(job_id: int) -> dict:
                url = f"{base_url}{DATABRICKS_JOBS_API_PATH}/get?job_id={job_id}"
                for retries in range(MAX_RETRIES + 1):
                    wait: int = 0
                    async with semaphore:
                        async with session.get(url) as resp:
                            if resp.status == RATE_LIMIT_STATUS_CODE:
                                if retries >= MAX_RETRIES:
                                    resp.raise_for_status()
                                retry_after = resp.headers.get("Retry-After")
                                try:
                                    wait = int(retry_after) if retry_after else min(2**retries, 30)
                                except (ValueError, TypeError):
                                    wait = min(2**retries, 30)
                            elif not resp.ok:
                                resp.raise_for_status()
                            else:
                                return await resp.json()
                    # Semaphore released — sleep and retry outside the lock to prevent deadlock
                    await asyncio.sleep(wait)
                raise RuntimeError(f"Exhausted {MAX_RETRIES} retries fetching job {job_id}")

            raw_jobs = await asyncio.gather(*[_fetch_single_job(jid) for jid in job_ids_to_fetch])

        return self._parse_raw_jobs(raw_jobs)

    @staticmethod
    def _parse_raw_jobs(raw_jobs: list[dict]) -> list[DatabricksJob]:
        final_jobs = []
        for rj in raw_jobs:
            settings = rj.get("settings", {})
            job_name = settings.get("name", "Unnamed Job")
            raw_tasks = settings.get("tasks", [])

            parsed_tasks = []
            for task_dict in raw_tasks:
                augmented_task = {**task_dict, "job_name": job_name}
                task = parse_task_from_config(augmented_task)
                if task is not None:
                    parsed_tasks.append(task)
                elif task_dict.get("task_key"):
                    parsed_tasks.append(DatabricksUnknownTask.from_job_task_config(augmented_task))

            final_jobs.append(DatabricksJob(job_id=rj["job_id"], name=job_name, tasks=parsed_tasks))

        return final_jobs

    def submit_and_poll(
        self, component: "DatabricksAssetBundleComponent", context: AssetExecutionContext
    ) -> Iterator[MaterializeResult]:
        # Get selected asset keys that are being materialized
        assets_def = context.assets_def
        selected_asset_keys = context.selected_asset_keys
        context.log.info(f"Selected assets: {selected_asset_keys}")

        # Determine the job name from the first spec's metadata
        first_spec_metadata = next(iter(assets_def.specs)).metadata
        job_name = first_spec_metadata["job_name"].value
        tasks_by_task_key = component.databricks_config.tasks_by_job_and_task_key[job_name]

        # Build a map from asset key to task key using all specs
        asset_key_to_task_key: dict = {}
        for spec in assets_def.specs:
            asset_key_to_task_key[spec.key] = spec.metadata["task_key"].value

        # Determine which tasks to submit based on selected asset keys
        selected_task_keys = {
            asset_key_to_task_key[key]
            for key in selected_asset_keys
            if key in asset_key_to_task_key
        }
        context.log.info(f"Selected tasks for job {job_name}: {selected_task_keys}")

        # Build SubmitTask objects for each selected task
        submit_tasks = []
        for task_key in selected_task_keys:
            task = tasks_by_task_key[task_key]
            context.log.info(f"Task {task_key}: parameters={task.task_parameters}")

            submit_task_params: dict = {
                "task_key": task_key,
                task.submit_task_key: task.to_databricks_sdk_task(),
            }

            # Determine cluster configuration based on task type
            if task.needs_cluster and not (
                isinstance(component.compute_config, ResolvedDatabricksServerlessConfig)
                and component.compute_config.is_serverless
            ):
                if isinstance(component.compute_config, ResolvedDatabricksExistingClusterConfig):
                    submit_task_params["existing_cluster_id"] = (
                        component.compute_config.existing_cluster_id
                    )
                elif isinstance(component.compute_config, ResolvedDatabricksNewClusterConfig):
                    submit_task_params["new_cluster"] = compute.ClusterSpec(
                        spark_version=component.compute_config.spark_version,
                        node_type_id=component.compute_config.node_type_id,
                        num_workers=component.compute_config.num_workers,
                    )

            libraries_list = parse_libraries(task.libraries)
            if libraries_list:
                submit_task_params["libraries"] = libraries_list
            context.log.info(f"Task {task_key} has {len(libraries_list)} libraries configured")

            # Add intra-job dependencies for selected tasks only
            selected_deps = [
                jobs.TaskDependency(task_key=dep.task_key, outcome=dep.outcome)
                for dep in task.depends_on
                if dep.task_key in selected_task_keys
            ]
            if selected_deps:
                submit_task_params["depends_on"] = selected_deps

            submit_tasks.append(jobs.SubmitTask(**submit_task_params))

        # Submit all selected tasks as a single Databricks job run
        job_submit_params = {
            "run_name": f"{assets_def.node_def.name}_{context.run_id}",
            "tasks": submit_tasks,
        }

        job_run = self._submit_job(params=job_submit_params)
        run_id = check.not_none(job_run.run_id)
        job_id = check.not_none(job_run.job_id)
        context.log.info(f"Databricks job submitted with run ID: {run_id}")

        # Build Databricks job run URL
        job_run_url = build_job_run_url(self.host, job_id, run_id)
        context.log.info(f"Databricks job run URL: {job_run_url}")

        try:
            final_run = self._poll_run(run_id=run_id)
        except DagsterExecutionInterruptedError:
            context.log.info(f"Run interrupted! Cancelling Databricks job run {run_id}.")
            try:
                self.get_client().jobs.cancel_run(run_id)
            except Exception as e:
                context.log.warning(f"Failed to cancel Databricks job run {run_id}: {e}")
            raise

        final_run_state = check.not_none(final_run.state)
        context.log.info(f"Job completed with overall state: {final_run_state.result_state}")
        context.log.info(f"View job details: {job_run_url}")

        # Check individual task results
        final_run_tasks = check.not_none(final_run.tasks)
        failed_tasks = []
        for run_task in final_run_tasks:
            task_state = (
                run_task.state.result_state.value
                if run_task.state and run_task.state.result_state
                else "UNKNOWN"
            )
            context.log.info(f"Task {run_task.task_key} completed with state: {task_state}")
            if task_state != "SUCCESS":
                failed_tasks.append(run_task.task_key)

        if failed_tasks:
            raise Failure(f"Tasks failed in job run {run_id}: {failed_tasks}. URL: {job_run_url}")

        # Yield results for selected assets in spec order (topological) to satisfy
        # Dagster's requirement that multi_asset outputs are yielded in dependency order.
        for spec in assets_def.specs:
            asset_key = spec.key
            if asset_key not in selected_asset_keys:
                continue
            task_key = asset_key_to_task_key.get(asset_key, "unknown")
            yield MaterializeResult(
                asset_key=asset_key,
                metadata={
                    "dagster-databricks/run_id": run_id,
                    "dagster-databricks/run_url": job_run_url,
                    "dagster-databricks/task_key": task_key,
                },
            )

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
