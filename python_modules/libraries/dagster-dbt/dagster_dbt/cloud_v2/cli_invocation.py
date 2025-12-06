import sys
from collections.abc import Iterator, Mapping, Sequence
from typing import Any, Optional, Union

from dagster import (
    AssetCheckEvaluation,
    AssetCheckResult,
    AssetExecutionContext,
    AssetMaterialization,
    Output,
)
from dagster._record import record

from dagster_dbt.cloud_v2.client import DbtCloudWorkspaceClient
from dagster_dbt.cloud_v2.run_handler import DbtCloudJobRunHandler, DbtCloudJobRunResults
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator


@record
class DbtCloudCliInvocation:
    """Represents a dbt Cloud cli invocation."""

    args: Sequence[str]
    client: DbtCloudWorkspaceClient
    manifest: Mapping[str, Any]
    dagster_dbt_translator: DagsterDbtTranslator
    run_handler: DbtCloudJobRunHandler
    context: Optional[AssetExecutionContext]

    @classmethod
    def run(
        cls,
        job_id: int,
        args: Sequence[str],
        client: DbtCloudWorkspaceClient,
        manifest: Mapping[str, Any],
        dagster_dbt_translator: DagsterDbtTranslator,
        context: Optional[AssetExecutionContext] = None,
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
            context=context,
        )

    def wait(
        self, timeout: Optional[float] = None
    ) -> Iterator[Union[AssetCheckEvaluation, AssetCheckResult, AssetMaterialization, Output]]:
        run = self.run_handler.wait(timeout=timeout)

        # Write dbt Cloud run logs to stdout
        logs = self.run_handler.get_run_logs()
        if logs:
            sys.stdout.write(logs)

        if "run_results.json" in self.run_handler.list_run_artifacts():
            run_results = DbtCloudJobRunResults.from_run_results_json(
                run_results_json=self.run_handler.get_run_results()
            )
            yield from run_results.to_default_asset_events(
                client=self.client,
                manifest=self.manifest,
                dagster_dbt_translator=self.dagster_dbt_translator,
                context=self.context,
            )
        run.raise_for_status()
