"""Output formatters for CLI display."""

import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.asset import DgApiAsset, DgApiAssetList
    from dagster_dg_cli.api_layer.schemas.deployment import DeploymentList
    from dagster_dg_cli.api_layer.schemas.run import RunList


def format_deployments(deployments: "DeploymentList", as_json: bool) -> str:
    """Format deployment list for output."""
    if as_json:
        return deployments.model_dump_json(indent=2)

    lines = []
    for deployment in deployments.items:
        lines.extend(
            [
                f"Name: {deployment.name}",
                f"ID: {deployment.id}",
                f"Type: {deployment.type.value}",
                "",  # Empty line between deployments
            ]
        )

    return "\n".join(lines).rstrip()  # Remove trailing empty line


def format_assets(assets: "DgApiAssetList", as_json: bool) -> str:
    """Format asset list for output."""
    if as_json:
        return assets.model_dump_json(indent=2)

    lines = []
    for asset in assets.items:
        asset_lines = [
            f"Asset Key: {asset.asset_key}",
            f"ID: {asset.id}",
            f"Description: {asset.description or 'None'}",
            f"Group: {asset.group_name}",
            f"Kinds: {', '.join(asset.kinds) if asset.kinds else 'None'}",
        ]

        # Add status information if present
        if asset.status:
            asset_lines.extend(_format_asset_status_lines(asset.status))

        asset_lines.append("")  # Empty line between assets
        lines.extend(asset_lines)

    return "\n".join(lines).rstrip()  # Remove trailing empty line


def _format_timestamp(timestamp: float) -> str:
    """Format timestamp for human-readable display."""
    try:
        dt = datetime.datetime.fromtimestamp(timestamp / 1000)  # Assume milliseconds
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return f"Invalid timestamp: {timestamp}"


def _format_asset_status_lines(status) -> list[str]:
    """Format asset status information into human-readable lines."""
    lines = []

    # Overall health status
    if status.asset_health:
        lines.append(f"Asset Health: {status.asset_health}")
    if status.materialization_status:
        lines.append(f"Materialization Status: {status.materialization_status}")
    if status.freshness_status:
        lines.append(f"Freshness Status: {status.freshness_status}")
    if status.asset_checks_status:
        lines.append(f"Asset Checks Status: {status.asset_checks_status}")

    # Health metadata details
    if status.health_metadata:
        metadata = status.health_metadata
        if metadata.failed_run_id:
            lines.append(f"Failed Run ID: {metadata.failed_run_id}")
        if metadata.num_failed_partitions is not None:
            lines.append(
                f"Failed Partitions: {metadata.num_failed_partitions}/{metadata.total_num_partitions or 'unknown'}"
            )
        if metadata.num_failed_checks is not None:
            lines.append(
                f"Failed Checks: {metadata.num_failed_checks}/{metadata.total_num_checks or 'unknown'}"
            )
        if metadata.num_warning_checks is not None:
            lines.append(f"Warning Checks: {metadata.num_warning_checks}")
        if metadata.last_materialized_timestamp:
            lines.append(
                f"Last Materialized: {_format_timestamp(metadata.last_materialized_timestamp)}"
            )

    # Latest materialization
    if status.latest_materialization:
        mat = status.latest_materialization
        if mat.timestamp:
            lines.append(f"Latest Materialization: {_format_timestamp(mat.timestamp)}")
        if mat.run_id:
            lines.append(f"Latest Run ID: {mat.run_id}")
        if mat.partition:
            lines.append(f"Latest Partition: {mat.partition}")

    # Freshness info
    if status.freshness_info:
        freshness = status.freshness_info
        if freshness.current_lag_minutes is not None:
            lines.append(f"Current Lag: {freshness.current_lag_minutes:.1f} minutes")
        if freshness.current_minutes_late is not None:
            lines.append(f"Minutes Late: {freshness.current_minutes_late:.1f}")
        if freshness.maximum_lag_minutes is not None:
            lines.append(f"Max Allowed Lag: {freshness.maximum_lag_minutes:.1f} minutes")
        if freshness.cron_schedule:
            lines.append(f"Freshness Schedule: {freshness.cron_schedule}")

    # Asset checks details
    if status.checks_status and status.checks_status.total_num_checks is not None:
        checks = status.checks_status
        lines.append(f"Total Checks: {checks.total_num_checks}")
        if checks.num_failed_checks is not None:
            lines.append(f"Failed Checks: {checks.num_failed_checks}")
        if checks.num_warning_checks is not None:
            lines.append(f"Warning Checks: {checks.num_warning_checks}")

    return lines


def format_asset(asset: "DgApiAsset", as_json: bool) -> str:
    """Format single asset for output."""
    if as_json:
        return asset.model_dump_json(indent=2)

    lines = [
        f"Asset Key: {asset.asset_key}",
        f"ID: {asset.id}",
        f"Description: {asset.description or 'None'}",
        f"Group: {asset.group_name}",
        f"Kinds: {', '.join(asset.kinds) if asset.kinds else 'None'}",
    ]

    # Add status information if present
    if asset.status:
        lines.append("")
        lines.append("Status Information:")
        status_lines = _format_asset_status_lines(asset.status)
        for line in status_lines:
            lines.append(f"  {line}")

    if asset.metadata_entries:
        lines.append("")
        lines.append("Metadata:")
        for entry in asset.metadata_entries:
            value = entry.get("description", "")
            for key in ["text", "url", "path", "jsonString", "mdStr"]:
                if entry.get(key):
                    value = entry[key]
                    break
            for key in ["floatValue", "intValue", "boolValue"]:
                if entry.get(key) is not None:
                    value = str(entry[key])
                    break
            lines.append(f"  {entry['label']}: {value}")

    return "\n".join(lines)


def format_runs(runs: "RunList", as_json: bool) -> str:
    """Format run list for output."""
    if as_json:
        return runs.model_dump_json(indent=2)

    if not runs.items:
        return "No runs found."

    lines = []
    for run in runs.items:
        run_lines = [
            f"Run ID: {run.run_id}",
            f"Status: {run.status.value}",
            f"Job: {run.job_name}",
        ]

        if run.start_time:
            run_lines.append(f"Started: {run.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if run.end_time:
            run_lines.append(f"Ended: {run.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        elif run.status.value in ["STARTED", "STARTING"]:
            run_lines.append("Ended: Running")

        run_lines.append(f"Created: {run.creation_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if run.can_terminate:
            run_lines.append("Terminable: Yes")

        run_lines.append("")  # Empty line between runs
        lines.extend(run_lines)

    return "\n".join(lines).rstrip()  # Remove trailing empty line
