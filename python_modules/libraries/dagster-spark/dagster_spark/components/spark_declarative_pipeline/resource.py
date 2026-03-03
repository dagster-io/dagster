"""Resource for running Spark Declarative Pipelines and discovering datasets.

SparkPipelinesResource provides discover_datasets (via dry-run or source_only) and
run_and_observe (run spark-pipelines with log streaming and MaterializeResult yields).
"""

import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal

from dagster import AssetKey, ConfigurableResource, MaterializeResult

from dagster_spark.components.spark_declarative_pipeline.discovery import (
    DiscoveredDataset,
    DiscoveryMode,
    SparkPipelinesDryRunError,
    discover_datasets_fn,
    parse_dry_run_output_to_datasets,
)

ExecutionMode = Literal["incremental", "full_refresh"]


class SparkPipelinesResource(ConfigurableResource):
    """Dagster resource for Spark Declarative Pipelines: discovery and run.

    Use discover_datasets to get datasets from spark-pipelines dry-run (or source_only).
    Use run_and_observe inside an asset to run the pipeline and yield MaterializeResults.
    """

    def discover_datasets(
        self,
        pipeline_spec_path: str | Path,
        discovery_mode: DiscoveryMode = "dry_run_only",
        working_dir: str | Path | None = None,
        source_only_datasets: list[DiscoveredDataset] | None = None,
    ) -> list[DiscoveredDataset]:
        """Discover datasets for the given pipeline spec using the configured discovery_mode.

        Args:
            pipeline_spec_path: Path to the pipeline spec file (YAML).
            discovery_mode: One of dry_run_only, dry_run_with_fallback, source_only.
            working_dir: Optional working directory for the dry-run subprocess.
            source_only_datasets: Optional list used when mode is source_only or as fallback.

        Returns:
            List of DiscoveredDataset.
        """
        return discover_datasets_fn(
            pipeline_spec_path=pipeline_spec_path,
            discovery_mode=discovery_mode,
            working_dir=working_dir,
            source_only_datasets=source_only_datasets,
        )

    def run_and_observe(
        self,
        context: Any,
        pipeline_spec_path: str | Path,
        working_dir: str | Path | None = None,
        execution_mode: ExecutionMode = "incremental",
        extra_args: list[str] | None = None,
        asset_keys: list[AssetKey] | None = None,
    ) -> Iterator[MaterializeResult]:
        """Run spark-pipelines run with log streaming; yield MaterializeResult per asset on success.

        Uses Popen to stream stdout/stderr line-by-line and logs each line via context.log.info.
        Passes --full-refresh or --refresh based on execution_mode, then optional comma-separated
        dataset list from asset_keys. Only yields MaterializeResults if the process exits with
        returncode == 0; otherwise raises SparkPipelinesDryRunError with the captured log.

        Args:
            context: Asset execution context (used for context.log.info).
            pipeline_spec_path: Path to the pipeline spec file (YAML).
            working_dir: Optional working directory for the subprocess.
            execution_mode: "incremental" (--refresh) or "full_refresh" (--full-refresh).
            extra_args: Optional extra CLI arguments appended to the command.
            asset_keys: Optional list of asset keys to materialize (passed as dataset list).

        Yields:
            MaterializeResult for each materialized asset on success.

        Raises:
            SparkPipelinesDryRunError: If spark-pipelines run exits with non-zero return code.
        """
        path_str = str(pipeline_spec_path)
        cmd = ["spark-pipelines", "run", path_str]
        if execution_mode == "full_refresh":
            cmd.append("--full-refresh")
        else:
            cmd.append("--refresh")
        if asset_keys:
            datasets_str = ",".join(k.to_user_string() for k in asset_keys)
            if datasets_str:
                cmd.append(datasets_str)
        if extra_args:
            cmd.extend(extra_args)

        cwd = str(working_dir) if working_dir else None
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            bufsize=1,
        )
        log_lines: list[str] = []
        if process.stdout:
            for raw_line in process.stdout:
                line = raw_line.rstrip("\n\r")
                if line:
                    log_lines.append(line)
                    if context is not None and hasattr(context, "log"):
                        context.log.info(line)
        process.wait()
        returncode = process.returncode

        if returncode != 0:
            captured = "\n".join(log_lines) if log_lines else "(no output)"
            raise SparkPipelinesDryRunError(
                f"spark-pipelines run failed with return code {returncode}",
                stderr=captured,
                returncode=returncode,
            )

        if asset_keys:
            for k in asset_keys:
                yield MaterializeResult(asset_key=k)
            return

        # Fallback: parse stdout for reported materialized keys (use captured log as stdout)
        stdout_text = "\n".join(log_lines)
        datasets = parse_dry_run_output_to_datasets(stdout_text)
        for ds in datasets:
            yield MaterializeResult(asset_key=AssetKey([ds.name]))
        if not datasets:
            yield MaterializeResult(asset_key=AssetKey(["spark_pipeline"]))
