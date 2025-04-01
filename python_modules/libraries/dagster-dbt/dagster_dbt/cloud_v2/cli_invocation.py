from collections.abc import Iterator, Mapping, Sequence
from typing import Any, Union

from dagster import AssetCheckEvaluation, AssetMaterialization
from dagster._annotations import preview
from dagster._record import record

from dagster_dbt.cloud_v2.client import DbtCloudWorkspaceClient
from dagster_dbt.cloud_v2.run_handler import DbtCloudJobRunHandler, DbtCloudJobRunResults
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator


@preview
@record
class DbtCloudCliInvocation:
    """Represents a dbt Cloud cli invocation."""

    args: Sequence[str]
    client: DbtCloudWorkspaceClient
    manifest: Mapping[str, Any]
    dagster_dbt_translator: DagsterDbtTranslator
    run_handler: DbtCloudJobRunHandler

    @classmethod
    def run(
        cls,
        job_id: int,
        args: Sequence[str],
        client: DbtCloudWorkspaceClient,
        manifest: Mapping[str, Any],
        dagster_dbt_translator: DagsterDbtTranslator,
    ) -> "DbtCloudCliInvocation":
        run_handler = DbtCloudJobRunHandler.run(
            job_id=job_id,
            args=args,
            client=client,
        )
        return DbtCloudCliInvocation(
            args=args,
            client=client,
            manifest=manifest,
            dagster_dbt_translator=dagster_dbt_translator,
            run_handler=run_handler,
        )

    def wait(self) -> Iterator[Union[AssetMaterialization, AssetCheckEvaluation]]:
        self.run_handler.wait_for_success()
        if "run_results.json" not in self.run_handler.list_run_artifacts():
            return
        run_results = DbtCloudJobRunResults.from_run_results_json(
            run_results_json=self.run_handler.get_run_results()
        )
        yield from run_results.to_default_asset_events(
            client=self.client,
            manifest=self.manifest,
            dagster_dbt_translator=self.dagster_dbt_translator,
        )
