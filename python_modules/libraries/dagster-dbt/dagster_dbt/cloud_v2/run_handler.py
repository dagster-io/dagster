from collections.abc import Iterator, Mapping, Sequence
from typing import Any, Optional, Union

from dagster import AssetCheckEvaluation, AssetCheckSeverity, AssetMaterialization, MetadataValue
from dagster._annotations import preview
from dagster._record import record
from dateutil import parser
from dbt.contracts.results import NodeStatus, TestStatus
from dbt.node_types import NodeType
from dbt.version import __version__ as dbt_version
from packaging import version

from dagster_dbt.asset_utils import build_dbt_specs, get_asset_check_key_for_test
from dagster_dbt.cloud_v2.client import DbtCloudWorkspaceClient
from dagster_dbt.cloud_v2.types import DbtCloudJobRunStatusType, DbtCloudRun
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

IS_DBT_CORE_VERSION_LESS_THAN_1_8_0 = version.parse(dbt_version) < version.parse("1.8.0")
if IS_DBT_CORE_VERSION_LESS_THAN_1_8_0:
    REFABLE_NODE_TYPES = NodeType.refable()  # type: ignore
else:
    from dbt.node_types import REFABLE_NODE_TYPES as REFABLE_NODE_TYPES

COMPLETED_AT_TIMESTAMP_METADATA_KEY = "dagster_dbt/completed_at_timestamp"


@preview
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

    def wait_for_success(self) -> Optional[DbtCloudJobRunStatusType]:
        run_details = self.client.poll_run(run_id=self.run_id)
        dbt_cloud_run = DbtCloudRun.from_run_details(run_details=run_details)
        return dbt_cloud_run.status

    def get_run_results(self) -> Mapping[str, Any]:
        return self.client.get_run_results_json(run_id=self.run_id)

    def get_manifest(self) -> Mapping[str, Any]:
        return self.client.get_run_manifest_json(run_id=self.run_id)

    def list_run_artifacts(self) -> Sequence[str]:
        return self.client.list_run_artifacts(run_id=self.run_id)


def get_completed_at_timestamp(result: Mapping[str, Any]) -> float:
    # result["timing"] is a list of events in run_results.json
    # For successful models and passing tests,
    # the last item of that list includes the timing details of the execution.
    return parser.parse(result["timing"][-1]["completed_at"]).timestamp()


@preview
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
    ) -> Iterator[Union[AssetMaterialization, AssetCheckEvaluation]]:
        """Convert the run results of a dbt Cloud job run to a set of corresponding Dagster events.

        Args:
            client (DbtCloudWorkspaceClient): The client for the dbt Cloud workspace.
            manifest (Mapping[str, Any]): The dbt manifest blob.
            dagster_dbt_translator (DagsterDbtTranslator): Optionally, a custom translator for
                linking dbt nodes to Dagster assets.

        Returns:
            Iterator[Union[AssetMaterialization, AssetCheckEvaluation]]:
                A set of corresponding Dagster events.

                The following are yielded:
                - AssetMaterialization for refables (e.g. models, seeds, snapshots.)
                - AssetCheckEvaluation for dbt tests.
        """
        dagster_dbt_translator = dagster_dbt_translator or DagsterDbtTranslator()

        run = DbtCloudRun.from_run_details(run_details=client.get_run_details(run_id=self.run_id))

        invocation_id: str = self.run_results["metadata"]["invocation_id"]
        for result in self.run_results["results"]:
            unique_id: str = result["unique_id"]
            dbt_resource_props: Mapping[str, Any] = manifest["nodes"][unique_id]
            selector: str = ".".join(dbt_resource_props["fqn"])

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
                select=selector,
                exclude="",
                io_manager_key=None,
                project=None,
            )

            if (
                resource_type in REFABLE_NODE_TYPES
                and result_status == NodeStatus.Success
                and not is_ephemeral
            ):
                spec = asset_specs[0]
                yield AssetMaterialization(
                    asset_key=spec.key,
                    metadata={
                        **default_metadata,
                        COMPLETED_AT_TIMESTAMP_METADATA_KEY: MetadataValue.timestamp(
                            get_completed_at_timestamp(result=result)
                        ),
                    },
                )
            elif resource_type == NodeType.Test and result_status == NodeStatus.Pass:
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
                )

                if asset_check_key is not None:
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
