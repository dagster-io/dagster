import subprocess

import dagster as dg


class ScriptConfig(dg.Config):
    script_path: str
    args: list[str] = []


@dg.asset
def run_python_script(
    context: dg.AssetExecutionContext,
    config: ScriptConfig,
) -> dg.MaterializeResult:
    """Run an existing Python script as a Dagster asset.

    The script runs unmodified via subprocess, allowing you to bring existing
    cron job scripts into Dagster without changing them.
    """
    cmd = ["python", config.script_path, *config.args]
    context.log.info(f"Running script: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    if result.stdout:
        context.log.info(result.stdout)
    if result.stderr:
        context.log.warning(result.stderr)

    return dg.MaterializeResult(
        metadata={
            "return_code": result.returncode,
            "stdout_preview": result.stdout[:500] if result.stdout else "",
        }
    )


# Optional: daily-partitioned variant that passes --date to the script
daily_partitions = dg.DailyPartitionsDefinition(start_date="2024-01-01")


@dg.asset(partitions_def=daily_partitions)
def run_daily_script(
    context: dg.AssetExecutionContext,
    config: ScriptConfig,
) -> dg.MaterializeResult:
    """Run an existing daily script for a specific date partition.

    Passes the partition date as --date YYYY-MM-DD to the script, replacing
    the need to parameterise cron jobs manually.
    """
    cmd = ["python", config.script_path, "--date", context.partition_key, *config.args]
    context.log.info(f"Running script for {context.partition_key}: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    if result.stdout:
        context.log.info(result.stdout)
    if result.stderr:
        context.log.warning(result.stderr)

    return dg.MaterializeResult(
        metadata={
            "return_code": result.returncode,
            "date": context.partition_key,
        }
    )
