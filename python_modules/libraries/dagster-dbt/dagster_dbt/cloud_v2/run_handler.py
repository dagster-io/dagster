from collections.abc import Iterator, Mapping, Sequence
from typing import Any, Optional

from dagster import AssetMaterialization
from dagster._annotations import preview
from dagster._record import record
from dbt.contracts.results import NodeStatus
from dbt.node_types import NodeType
from dbt.version import __version__ as dbt_version
from packaging import version

from dagster_dbt.asset_utils import build_dbt_specs
from dagster_dbt.cloud_v2.client import DbtCloudWorkspaceClient
from dagster_dbt.cloud_v2.types import DbtCloudJobRunStatusType, DbtCloudRun, DbtCloudWorkspaceData
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

IS_DBT_CORE_VERSION_LESS_THAN_1_8_0 = version.parse(dbt_version) < version.parse("1.8.0")
if IS_DBT_CORE_VERSION_LESS_THAN_1_8_0:
    REFABLE_NODE_TYPES = NodeType.refable()  # type: ignore
else:
    from dbt.node_types import REFABLE_NODE_TYPES as REFABLE_NODE_TYPES


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


@preview
@record
class DbtCloudJobRunResults:
    """Represents the run results of a dbt Cloud job run."""

    run_id: int
    run_results = Mapping[str, Any]

    def to_default_asset_events(
        self,
        workspace_data: DbtCloudWorkspaceData,
        dagster_dbt_translator: Optional[DagsterDbtTranslator] = None,
    ) -> Iterator[AssetMaterialization]:
        """Convert the run results of a dbt Cloud job run to a set of corresponding Dagster events.

        Args:
            workspace_data (DbtCloudWorkspaceData): The data of the dbt Cloud workspace.
            dagster_dbt_translator (DagsterDbtTranslator): Optionally, a custom translator for
                linking dbt nodes to Dagster assets.

        Returns:
            Iterator[AssetMaterialization]:
                A set of corresponding Dagster events.

                The following are yielded:
                - AssetMaterialization for refables (e.g. models, seeds, snapshots.)
        """
        dagster_dbt_translator = dagster_dbt_translator or DagsterDbtTranslator()
        manifest = workspace_data.manifest

        invocation_id: str = self.run_results["metadata"]["invocation_id"]
        for result in self.run_results["results"]:
            unique_id: str = result["unique_id"]
            dbt_resource_props = manifest["nodes"][unique_id]

            default_metadata = {
                "unique_id": unique_id,
                "invocation_id": invocation_id,
                "Execution Duration": result["execution_time"],
            }

            resource_type: str = dbt_resource_props["resource_type"]
            result_status: str = result["status"]
            materialization: str = dbt_resource_props["config"]["materialized"]

            is_ephemeral = materialization == "ephemeral"
            is_successful = result_status == NodeStatus.Success

            # Build the specs for the given unique ID
            asset_specs, check_specs = build_dbt_specs(
                manifest=manifest,
                translator=dagster_dbt_translator,
                select=unique_id,
                exclude="",
                io_manager_key=None,
                project=None,
            )

            if resource_type in REFABLE_NODE_TYPES and is_successful and not is_ephemeral:
                spec = asset_specs[0]
                yield AssetMaterialization(
                    asset_key=spec.key,
                    metadata=default_metadata,
                )
