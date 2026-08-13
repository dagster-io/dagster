import sys
from collections.abc import Iterator, Mapping, Sequence
from typing import Any

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
    context: AssetExecutionContext | None

    @classmethod
    def run(
        cls,
        job_id: int,
        args: Sequence[str],
        client: DbtCloudWorkspaceClient,
        manifest: Mapping[str, Any],
        dagster_dbt_translator: DagsterDbtTranslator,
        context: AssetExecutionContext | None = None,
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
        self,
        timeout: float | None = None,
        *,
        monitor_runs: bool = False,
        fail_fast: bool = False,
        poll_interval: int = 5,
    ) -> Iterator[AssetCheckEvaluation | AssetCheckResult | AssetMaterialization | Output]:
        """Wait for a dbt Cloud run to finish, yielding Dagster events.

        Default behavior (``monitor_runs=False``): block until the run is done, then
        emit events from ``run_results.json``. Preserves existing semantics — no
        change for callers that don't opt into monitoring.

        When ``monitor_runs=True``: poll the run's step debug logs and emit
        materializations/asset-check-results as models complete mid-run. Downstream
        automation reacts in seconds instead of waiting for the whole Cloud run.

        - ``fail_fast=True``: cancel the Cloud run on first failure, raise ``Failure``.
        - ``fail_fast=False``: log failures, keep yielding partials, raise ``Failure``
          only after the run itself terminates.
        - ``poll_interval``: seconds between debug-log polls (default 5).
        """
        if monitor_runs:
            from dagster_dbt.cloud_v2.run_monitor import monitor_run_iter

            yield from monitor_run_iter(
                run_id=self.run_handler.run_id,
                client=self.client,
                manifest=self.manifest,
                translator=self.dagster_dbt_translator,
                context=self.context,
                fail_fast=fail_fast,
                poll_interval=poll_interval,
            )
            return

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
