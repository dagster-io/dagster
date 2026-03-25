"""Resource for running Spark Declarative Pipelines and discovering datasets.

SparkPipelinesResource provides discover_datasets (via dry-run or source_only) and
run_and_observe (run spark-pipelines with log streaming). The asset yields MaterializeResults.
"""

import os
import subprocess
from collections import deque
from pathlib import Path
from typing import Any, Literal

from dagster import AssetKey, ConfigurableResource
from dagster._annotations import preview, public
from pydantic import Field

from dagster_spark.components.spark_declarative_pipeline.discovery import (
    DiscoveredDataset,
    DiscoveryMode,
    SparkPipelinesExecutionError,
    discover_datasets_fn,
)

ExecutionMode = Literal["incremental", "full_refresh"]


@public
@preview
class SparkPipelinesResource(ConfigurableResource):
    """Dagster resource for Spark Declarative Pipelines: discovery and run.

    Use discover_datasets to get datasets from spark-pipelines dry-run (or source_only).
    Use run_and_observe inside an asset to run the pipeline and yield MaterializeResults.
    """

    spark_pipelines_cmd: str = Field(
        default="spark-pipelines",
        description="Executable name or path for the spark-pipelines CLI.",
    )
    dry_run_extra_args: list[str] = Field(
        default_factory=list,
        description="Extra CLI arguments appended to spark-pipelines dry-run.",
    )
    run_extra_args: list[str] = Field(
        default_factory=list,
        description="Extra CLI arguments appended to spark-pipelines run (before any per-call extra_args).",
    )

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
            spark_pipelines_cmd=self.spark_pipelines_cmd,
            dry_run_extra_args=self.dry_run_extra_args,
        )

    def run_and_observe(
        self,
        context: Any,
        pipeline_spec_path: str | Path,
        working_dir: str | Path | None = None,
        execution_mode: ExecutionMode = "incremental",
        extra_args: list[str] | None = None,
        asset_keys: list[AssetKey] | None = None,
    ) -> None:
        """Run spark-pipelines run with log streaming; does not yield (asset yields MaterializeResults).

        Uses Popen to stream stdout/stderr line-by-line and logs each line via context.log.info.
        Passes --full-refresh or --refresh based on execution_mode, then optional comma-separated
        dataset list from asset_keys. The calling multi_asset must yield one MaterializeResult per
        selected asset key after this returns.

        Args:
            context: Asset execution context (used for context.log.info).
            pipeline_spec_path: Path to the pipeline spec file (YAML).
            working_dir: Optional working directory for the subprocess.
            execution_mode: "incremental" (--refresh) or "full_refresh" (--full-refresh).
            extra_args: Optional extra CLI arguments appended to the command.
            asset_keys: Optional list of asset keys to materialize (passed as dataset list).

        Raises:
            SparkPipelinesExecutionError: If spark-pipelines run exits with non-zero return code.
        """
        path_str = str(pipeline_spec_path)
        cmd = [self.spark_pipelines_cmd, "run", "--spec", path_str]
        if execution_mode == "full_refresh":
            if asset_keys:
                cmd.append("--full-refresh")
                datasets_str = ",".join(".".join(k.path) for k in asset_keys)
                if datasets_str:
                    cmd.append(datasets_str)
            else:
                cmd.append("--full-refresh-all")
        else:
            if asset_keys:
                cmd.append("--refresh")
                datasets_str = ",".join(".".join(k.path) for k in asset_keys)
                if datasets_str:
                    cmd.append(datasets_str)
        cmd.extend(self.run_extra_args)
        if extra_args:
            cmd.extend(extra_args)

        cwd = str(working_dir) if working_dir else None
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            env=env,
            bufsize=1,
        )
        log_lines: deque[str] = deque(maxlen=1000)
        try:
            if process.stdout:
                for raw_line in process.stdout:
                    line = raw_line.rstrip("\n\r")
                    if line:
                        log_lines.append(line)
                        if context is not None and hasattr(context, "log"):
                            context.log.info(line)
        finally:
            process.wait()
        returncode = process.returncode

        if returncode != 0:
            captured = "\n".join(log_lines) if log_lines else "(no output)"
            raise SparkPipelinesExecutionError(
                f"spark-pipelines run failed with return code {returncode}",
                stderr=captured,
                returncode=returncode,
            )

        if asset_keys is None and context is not None and hasattr(context, "log"):
            context.log.info(
                "spark-pipelines run completed successfully (full graph; asset will yield results)."
            )
