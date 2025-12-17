from collections.abc import Iterator, Mapping, Sequence
from typing import Any, Optional, Union

from dagster import (
    AssetCheckEvaluation,
    AssetCheckResult,
    AssetCheckSeverity,
    AssetExecutionContext,
    AssetMaterialization,
    MetadataValue,
    Output,
    get_dagster_logger,
)
from dagster._record import record
from dagster._time import get_current_timestamp
from dateutil import parser
from requests.exceptions import RequestException

from dagster_dbt.asset_utils import build_dbt_specs, get_asset_check_key_for_test
from dagster_dbt.cloud_v2.client import DbtCloudWorkspaceClient
from dagster_dbt.cloud_v2.types import DbtCloudRun
from dagster_dbt.compat import REFABLE_NODE_TYPES, NodeStatus, NodeType, TestStatus
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

COMPLETED_AT_TIMESTAMP_METADATA_KEY = "dagster_dbt/completed_at_timestamp"

logger = get_dagster_logger()


@record
class DbtCloudJobRunHandler:
    """Handles the process of a dbt Cloud job run."""

    job_id: int
    run_id: int
    args: Sequence[str]
    client: DbtCloudWorkspaceClient

    @classmethod
    def run(
        cls, job_id: int, args: Sequence[str], client: DbtCloudWorkspaceClient
    ) -> "DbtCloudJobRunHandler":
        run_details = client.trigger_job_run(job_id, steps_override=[" ".join(["dbt", *args])])
        dbt_cloud_run = DbtCloudRun.from_run_details(run_details=run_details)
        return DbtCloudJobRunHandler(
            job_id=job_id,
            run_id=dbt_cloud_run.id,
            args=args,
            client=client,
        )

    def wait(self, timeout: Optional[float] = None) -> DbtCloudRun:
        run_details = self.client.poll_run(run_id=self.run_id, poll_timeout=timeout)
        dbt_cloud_run = DbtCloudRun.from_run_details(run_details=run_details)
        return dbt_cloud_run

    def get_run_results(self) -> Mapping[str, Any]:
        return self.client.get_run_results_json(run_id=self.run_id)

    def get_manifest(self) -> Mapping[str, Any]:
        return self.client.get_run_manifest_json(run_id=self.run_id)

    def list_run_artifacts(self) -> Sequence[str]:
        return self.client.list_run_artifacts(run_id=self.run_id)

    def get_run_logs(self) -> Optional[str]:
        """Retrieves the stdout/stderr logs from the completed dbt Cloud run.

        This method fetches logs from the run_steps by calling get_run_details
        with include_related=["run_steps"].

        Returns:
            Optional[str]: The concatenated log text content from all run steps,
                or None if logs are not available.
        """
        try:
            return self.client.get_run_logs(run_id=self.run_id)
        except RequestException as e:
            logger.warning(f"Failed to retrieve logs for run {self.run_id}: {e}")
            return None


def get_completed_at_timestamp(result: Mapping[str, Any]) -> float:
    timing = result["timing"]
    if len(timing) == 0:
        # as a fallback, use the current timestamp
        return get_current_timestamp()
    # result["timing"] is a list of events in run_results.json
    # For successful models and passing tests,
    # the last item of that list includes the timing details of the execution.
    return parser.parse(result["timing"][-1]["completed_at"]).timestamp()


@record
class DbtCloudJobRunResults:
    """Represents the run results of a dbt Cloud job run."""

    run_id: int
    run_results: Mapping[str, Any]

    @classmethod
    def from_run_results_json(cls, run_results_json: Mapping[str, Any]) -> "DbtCloudJobRunResults":
        return cls(
            run_id=int(run_results_json["metadata"]["env"]["DBT_CLOUD_RUN_ID"]),
            run_results=run_results_json,
        )

    def to_default_asset_events(
        self,
        client: DbtCloudWorkspaceClient,
        manifest: Mapping[str, Any],
        dagster_dbt_translator: Optional[DagsterDbtTranslator] = None,
        context: Optional[AssetExecutionContext] = None,
    ) -> Iterator[Union[AssetCheckEvaluation, AssetCheckResult, AssetMaterialization, Output]]:
        """Convert the run results of a dbt Cloud job run to a set of corresponding Dagster events.

        Args:
            client (DbtCloudWorkspaceClient): The client for the dbt Cloud workspace.
            manifest (Mapping[str, Any]): The dbt manifest blob.
            dagster_dbt_translator (DagsterDbtTranslator): Optionally, a custom translator for
                linking dbt nodes to Dagster assets.
            context (Optional[AssetExecutionContext]): The execution context.

        Returns:
            Iterator[Union[AssetCheckEvaluation, AssetCheckResult, AssetMaterialization, Output]]:
                A set of corresponding Dagster events.

                In a Dagster asset definition, the following are yielded:
                - Output for refables (e.g. models, seeds, snapshots.)
                - AssetCheckResult for dbt tests.

                For ad hoc usage, the following are yielded:
                - AssetMaterialization for refables (e.g. models, seeds, snapshots.)
                - AssetCheckEvaluation for dbt tests.
        """
        dagster_dbt_translator = dagster_dbt_translator or DagsterDbtTranslator()
        has_asset_def: bool = bool(context and context.has_assets_def)

        run = DbtCloudRun.from_run_details(run_details=client.get_run_details(run_id=self.run_id))

        invocation_id: str = self.run_results["metadata"]["invocation_id"]
        for result in self.run_results["results"]:
            unique_id: str = result["unique_id"]
            dbt_resource_props: Mapping[str, Any] = manifest["nodes"].get(unique_id)
            if not dbt_resource_props:
                logger.warning(
                    f"Unique ID {unique_id} not found in manifest. "
                    f"This can happen if you are parsing old runs fetched via the sensor, "
                    f"or if your manifest is out of date. "
                    f"Reloading your code location will fix the latter."
                )
                continue
            select: str = ".".join(dbt_resource_props["fqn"])

            default_metadata = {
                "unique_id": unique_id,
                "invocation_id": invocation_id,
                "execution_duration": result["execution_time"],
            }

            if run.url:
                default_metadata["run_url"] = MetadataValue.url(run.url)

            resource_type: str = dbt_resource_props["resource_type"]
            result_status: str = result["status"]
            materialization: str = dbt_resource_props["config"]["materialized"]

            is_ephemeral = materialization == "ephemeral"

            # Build the specs for the given unique ID
            asset_specs, _ = build_dbt_specs(
                manifest=manifest,
                translator=dagster_dbt_translator,
                select=select,
                exclude="",
                selector="",
                io_manager_key=None,
                project=None,
            )

            if (
                resource_type in REFABLE_NODE_TYPES
                and result_status == NodeStatus.Success
                and not is_ephemeral
            ):
                spec = asset_specs[0]
                metadata = {
                    **default_metadata,
                    COMPLETED_AT_TIMESTAMP_METADATA_KEY: MetadataValue.timestamp(
                        get_completed_at_timestamp(result=result)
                    ),
                }
                if context and has_asset_def:
                    yield Output(
                        value=None,
                        output_name=spec.key.to_python_identifier(),
                        metadata=metadata,
                    )
                else:
                    yield AssetMaterialization(
                        asset_key=spec.key,
                        metadata=metadata,
                    )
            elif resource_type == NodeType.Test:
                metadata = {
                    **default_metadata,
                    "status": result_status,
                    COMPLETED_AT_TIMESTAMP_METADATA_KEY: MetadataValue.timestamp(
                        get_completed_at_timestamp(result=result)
                    ),
                }
                if result["failures"] is not None:
                    metadata["dagster_dbt/failed_row_count"] = result["failures"]

                asset_check_key = get_asset_check_key_for_test(
                    manifest=manifest,
                    dagster_dbt_translator=dagster_dbt_translator,
                    test_unique_id=unique_id,
                    project=None,
                )

                if (
                    context
                    and has_asset_def
                    and asset_check_key is not None
                    and asset_check_key in context.selected_asset_check_keys
                ):
                    # The test is an asset check in an asset, so yield an `AssetCheckResult`.
                    yield AssetCheckResult(
                        passed=result_status == TestStatus.Pass,
                        asset_key=asset_check_key.asset_key,
                        check_name=asset_check_key.name,
                        metadata=metadata,
                        severity=(
                            AssetCheckSeverity.WARN
                            if result_status == TestStatus.Warn
                            else AssetCheckSeverity.ERROR
                        ),
                    )
                elif not has_asset_def and asset_check_key is not None:
                    yield AssetCheckEvaluation(
                        passed=result_status == TestStatus.Pass,
                        asset_key=asset_check_key.asset_key,
                        check_name=asset_check_key.name,
                        metadata=metadata,
                        severity=(
                            AssetCheckSeverity.WARN
                            if result_status == TestStatus.Warn
                            else AssetCheckSeverity.ERROR
                        ),
                    )
