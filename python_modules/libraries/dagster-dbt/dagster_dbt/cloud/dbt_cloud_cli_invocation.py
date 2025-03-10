from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Union

from dagster import AssetCheckResult, AssetMaterialization
from dagster._annotations import preview
from dagster._record import record

from dagster_dbt.cloud.dbt_cloud_job_run import DbtCloudJobRun
from dagster_dbt.cloud.types import DbtCloudWorkspaceData
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator

if TYPE_CHECKING:
    from dagster_dbt.cloud.resources_v2 import DbtCloudClient


@preview
@record
class DbtCloudCliInvocation:
    """Represents a dbt Cloud cli invocation."""

    run: DbtCloudJobRun
    translator: DagsterDbtTranslator
    workspace_data: DbtCloudWorkspaceData

    @classmethod
    def run(
        cls,
        job_id: int,
        args: Sequence[str],
        client: "DbtCloudClient",
        translator: DagsterDbtTranslator,
        workspace_data: DbtCloudWorkspaceData,
    ) -> "DbtCloudCliInvocation":
        dbt_cloud_run = DbtCloudJobRun.run(job_id=job_id, args=args, client=client)
        return DbtCloudCliInvocation(
            run=dbt_cloud_run, translator=translator, workspace_data=workspace_data
        )

    def get_asset_events(
        self,
    ) -> Iterator[Union[AssetMaterialization, AssetCheckResult]]:
        raise NotImplementedError()
