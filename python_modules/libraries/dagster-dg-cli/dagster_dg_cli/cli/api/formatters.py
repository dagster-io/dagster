"""Output formatters for CLI display."""

import datetime
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.agent import DgApiAgent, DgApiAgentList
    from dagster_dg_cli.api_layer.schemas.asset import (
        DgApiAsset,
        DgApiAssetEventList,
        DgApiAssetList,
        DgApiAssetStatus,
        DgApiEvaluationRecordList,
    )
    from dagster_dg_cli.api_layer.schemas.code_location import (
        DgApiAddCodeLocationResult,
        DgApiCodeLocation,
        DgApiCodeLocationList,
        DgApiDeleteCodeLocationResult,
    )
    from dagster_dg_cli.api_layer.schemas.deployment import (
        Deployment,
        DeploymentList,
        DeploymentSettings,
    )
    from dagster_dg_cli.api_layer.schemas.issue import DgApiIssue, DgApiIssueList
    from dagster_dg_cli.api_layer.schemas.run import DgApiRun, DgApiRunList
    from dagster_dg_cli.api_layer.schemas.run_event import RunEventList
    from dagster_dg_cli.api_layer.schemas.schedule import DgApiSchedule, DgApiScheduleList
    from dagster_dg_cli.api_layer.schemas.secret import DgApiSecret, DgApiSecretList
    from dagster_dg_cli.api_layer.schemas.sensor import DgApiSensor, DgApiSensorList

MAX_COL_WIDTH = 60


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render an aligned table with auto-sized columns.

    Calculates column widths from headers + data, truncates long values with '...'.
    """
    if not rows:
        return ""

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(cell))

    # Cap column widths
    col_widths = [min(w, MAX_COL_WIDTH) for w in col_widths]

    def _format_row(cells: list[str]) -> str:
        parts = []
        for i, raw_cell in enumerate(cells):
            width = col_widths[i] if i < len(col_widths) else len(raw_cell)
            display_cell = raw_cell
            if len(display_cell) > width:
                display_cell = display_cell[: width - 3] + "..."
            if i < len(cells) - 1:
                parts.append(display_cell.ljust(width))
            else:
                parts.append(display_cell)  # no trailing padding on last column
        return "  ".join(parts)

    lines = [_format_row(headers)]
    for row in rows:
        lines.append(_format_row(row))

    return "\n".join(lines)


def format_detail(fields: list[tuple[str, str]]) -> str:
    """Format key-value pairs with aligned values."""
    if not fields:
        return ""
    max_key_len = max(len(k) for k, _ in fields)
    lines = []
    for key, value in fields:
        padding = " " * (max_key_len - len(key) + 1)
        lines.append(f"{key}:{padding}{value}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------


def _format_timestamp(timestamp: float, unit: str = "seconds") -> str:
    """Format timestamp for human-readable display.

    Args:
        timestamp: The timestamp value
        unit: Either "milliseconds" or "seconds" to indicate the timestamp unit
    """
    try:
        if unit == "milliseconds":
            dt = datetime.datetime.fromtimestamp(timestamp / 1000, tz=datetime.timezone.utc)
        elif unit == "seconds":
            dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
        else:
            raise ValueError(f"Unsupported unit: {unit}")
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, OSError):
        return f"Invalid timestamp: {timestamp}"


def _format_timestamp_epoch(epoch: float) -> str:
    """Format a Unix epoch (seconds) to readable string."""
    return _format_timestamp(epoch, "seconds")


# ---------------------------------------------------------------------------
# Deployment formatters
# ---------------------------------------------------------------------------


def format_deployments(deployments: "DeploymentList", as_json: bool) -> str:
    """Format deployment list for output."""
    if as_json:
        return deployments.model_dump_json(indent=2)

    headers = ["NAME", "ID", "TYPE"]
    rows = [[dep.name, str(dep.id), dep.type.value] for dep in deployments.items]
    return format_table(headers, rows)


def format_deployment(deployment: "Deployment", as_json: bool) -> str:
    """Format single deployment for output."""
    if as_json:
        return deployment.model_dump_json(indent=2)

    return format_detail(
        [
            ("Name", deployment.name),
            ("ID", str(deployment.id)),
            ("Type", deployment.type.value),
        ]
    )


def format_deployment_settings(settings: "DeploymentSettings", as_json: bool) -> str:
    """Format deployment settings for output."""
    if as_json:
        return settings.model_dump_json(indent=2)

    import yaml

    return yaml.dump(settings.settings, default_flow_style=False, sort_keys=False).rstrip()


# ---------------------------------------------------------------------------
# Asset formatters
# ---------------------------------------------------------------------------


def format_assets(assets: "DgApiAssetList", as_json: bool) -> str:
    """Format asset list for output."""
    if as_json:
        return assets.model_dump_json(indent=2)

    headers = ["ASSET KEY", "GROUP", "DESCRIPTION", "KINDS"]
    rows = []
    for asset in assets.items:
        rows.append(
            [
                asset.asset_key,
                asset.group_name,
                asset.description or "",
                ", ".join(asset.kinds) if asset.kinds else "",
            ]
        )

    return format_table(headers, rows)


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
        f"Deps: {', '.join(asset.dependency_keys) if asset.dependency_keys else 'None'}",
    ]

    return "\n".join(lines)


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
                f"Last Materialized: {_format_timestamp(metadata.last_materialized_timestamp, 'milliseconds')}"
            )

    # Latest materialization
    if status.latest_materialization:
        mat = status.latest_materialization
        if mat.timestamp:
            lines.append(
                f"Latest Materialization: {_format_timestamp(mat.timestamp, 'milliseconds')}"
            )
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


def format_asset_health(status: "DgApiAssetStatus", as_json: bool) -> str:
    """Format asset health status for output."""
    if as_json:
        return status.model_dump_json(indent=2)

    lines = [f"Asset Key: {status.asset_key}", ""]
    status_lines = _format_asset_status_lines(status)
    if status_lines:
        lines.extend(status_lines)
    else:
        lines.append("No health data available.")

    return "\n".join(lines)


def format_asset_events(event_list: "DgApiAssetEventList", as_json: bool) -> str:
    """Format asset events for output."""
    if as_json:
        return event_list.model_dump_json(indent=2)

    if not event_list.items:
        return "No events found."

    headers = ["TIMESTAMP", "TYPE", "RUN ID", "PARTITION"]
    rows = []
    for event in event_list.items:
        rows.append(
            [
                _format_timestamp(float(event.timestamp), "milliseconds"),
                event.event_type,
                event.run_id,
                event.partition or "",
            ]
        )

    return format_table(headers, rows)


def format_asset_evaluations(evaluations: "DgApiEvaluationRecordList", as_json: bool) -> str:
    """Format asset evaluation records for output."""
    if as_json:
        return evaluations.model_dump_json(indent=2)

    if not evaluations.items:
        return "No evaluation records found."

    headers = ["EVAL ID", "TIMESTAMP", "NUM REQUESTED", "RUN IDS"]
    rows = []
    for record in evaluations.items:
        timestamp = _format_timestamp(record.timestamp, "seconds")
        num_requested = str(record.num_requested) if record.num_requested is not None else "-"
        run_ids = ", ".join(record.run_ids) if record.run_ids else "-"
        rows.append([str(record.evaluation_id), timestamp, num_requested, run_ids])

    lines = [format_table(headers, rows)]

    # Append node summaries inline after each record's row
    # We need to rebuild to interleave nodes — use manual approach
    if any(record.evaluation_nodes for record in evaluations.items):
        # Rebuild with node info
        table_lines = format_table(headers, rows).split("\n")
        result_lines = [table_lines[0]]  # header
        row_idx = 1
        for record in evaluations.items:
            if row_idx < len(table_lines):
                result_lines.append(table_lines[row_idx])
                row_idx += 1
            if record.evaluation_nodes:
                for node in record.evaluation_nodes:
                    label = node.user_label or " > ".join(node.expanded_label) or node.unique_id
                    true_str = str(node.num_true) if node.num_true is not None else "-"
                    cand_str = str(node.num_candidates) if node.num_candidates is not None else "-"
                    result_lines.append(f"    {label} (true={true_str}, candidates={cand_str})")
        return "\n".join(result_lines)

    return lines[0]


# ---------------------------------------------------------------------------
# Agent formatters
# ---------------------------------------------------------------------------


def format_agents(agents: "DgApiAgentList", as_json: bool) -> str:
    """Format agent list for output."""
    if as_json:
        return agents.model_dump_json(indent=2)

    headers = ["LABEL", "ID", "STATUS", "LAST HEARTBEAT"]
    rows = []
    for agent in agents.items:
        display_label = agent.agent_label or f"Agent {agent.id[:8]}"
        heartbeat = (
            _format_timestamp(agent.last_heartbeat_time, "seconds")
            if agent.last_heartbeat_time
            else "Never"
        )
        rows.append([display_label, agent.id, agent.status.value, heartbeat])

    return format_table(headers, rows)


def format_agent(agent: "DgApiAgent", as_json: bool) -> str:
    """Format single agent for output."""
    if as_json:
        return agent.model_dump_json(indent=2)

    display_label = agent.agent_label or f"Agent {agent.id[:8]}"
    heartbeat = (
        _format_timestamp(agent.last_heartbeat_time, "seconds")
        if agent.last_heartbeat_time
        else "Never"
    )
    fields = [
        ("Label", display_label),
        ("ID", agent.id),
        ("Status", agent.status.value),
        ("Last Heartbeat", heartbeat),
    ]

    lines = [format_detail(fields)]

    if agent.metadata:
        lines.append("")
        lines.append("Metadata:")
        for meta in agent.metadata:
            lines.append(f"  {meta.key}: {meta.value}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Secret formatters
# ---------------------------------------------------------------------------


def format_secrets(secrets: "DgApiSecretList", as_json: bool) -> str:
    """Format secret list for output.

    Note: Secret values are never shown in list format for security.
    """
    if as_json:
        return secrets.model_dump_json(indent=2)

    if not secrets.items:
        return "No secrets found."

    headers = ["NAME", "LOCATIONS", "SCOPES", "UPDATED"]
    rows = []
    for secret in secrets.items:
        locations = ", ".join(secret.location_names) if secret.location_names else "All"
        scopes = _format_secret_scopes(secret)
        updated = ""
        if secret.update_timestamp:
            updated = secret.update_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        rows.append([secret.name, locations, scopes, updated])

    return format_table(headers, rows)


def format_secret(secret: "DgApiSecret", as_json: bool, show_value: bool = False) -> str:
    """Format single secret for output.

    Args:
        secret: Secret to format
        as_json: Whether to output JSON format
        show_value: Whether to include the secret value (security sensitive)
    """
    if as_json:
        if not show_value and secret.value is not None:
            # Create a copy with hidden value for JSON output
            secret_dict = secret.model_dump()
            secret_dict["value"] = "<hidden>"
            return json.dumps(secret_dict, indent=2, default=str)
        return secret.model_dump_json(indent=2)

    lines = [
        f"Name: {secret.name}",
        f"Locations: {', '.join(secret.location_names) if secret.location_names else 'All code locations'}",
        f"Scopes: {_format_secret_scopes(secret)}",
        "Permissions:",
        f"  Can Edit: {'Yes' if secret.can_edit_secret else 'No'}",
        f"  Can View Value: {'Yes' if secret.can_view_secret_value else 'No'}",
    ]

    # Show value only if explicitly requested and available
    if show_value:
        if secret.value is not None:
            lines.extend(
                [
                    "",
                    "Value:",
                    f"  {secret.value}",
                ]
            )
        else:
            lines.extend(
                [
                    "",
                    "Value: <not available - you may not have permission to view this value>",
                ]
            )
    else:
        lines.extend(
            [
                "",
                "Value: <hidden - use --show-value to display>",
            ]
        )

    if secret.updated_by:
        lines.extend(
            [
                "",
                f"Updated By: {secret.updated_by.email}",
            ]
        )

    if secret.update_timestamp:
        lines.append(f"Updated: {secret.update_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

    return "\n".join(lines)


def _format_secret_scopes(secret: "DgApiSecret") -> str:
    """Format secret scopes into human-readable string."""
    scopes = []

    if secret.full_deployment_scope:
        scopes.append("Full Deployment")

    if secret.all_branch_deployments_scope:
        scopes.append("All Branch Deployments")

    if secret.specific_branch_deployment_scope:
        scopes.append(f"Branch: {secret.specific_branch_deployment_scope}")

    if secret.local_deployment_scope:
        scopes.append("Local Deployment")

    return ", ".join(scopes) if scopes else "None"


# ---------------------------------------------------------------------------
# Run formatters
# ---------------------------------------------------------------------------


def format_run(run: "DgApiRun", as_json: bool) -> str:
    """Format single run for output."""
    if as_json:
        return run.model_dump_json(indent=2)

    fields = [
        ("Run ID", run.id),
        ("Status", run.status.value),
        ("Created", str(run.created_at)),
    ]

    if run.started_at:
        fields.append(("Started", str(run.started_at)))
    if run.ended_at:
        fields.append(("Ended", str(run.ended_at)))
    if run.job_name:
        fields.append(("Pipeline", run.job_name))

    return format_detail(fields)


def format_runs_list(runs_list: "DgApiRunList", as_json: bool) -> str:
    """Format run list for output."""
    if as_json:
        return runs_list.model_dump_json(indent=2)

    if not runs_list.items:
        return "No runs found."

    headers = ["ID", "STATUS", "JOB", "CREATED"]
    rows = []
    for run in runs_list.items:
        rows.append(
            [
                run.id,
                run.status.value,
                run.job_name or "N/A",
                str(run.created_at),
            ]
        )

    lines = [format_table(headers, rows)]

    if runs_list.has_more:
        lines.append("Note: More runs available (use --limit to increase or --cursor to paginate)")

    return "\n".join(lines)


def format_logs_table(events: "RunEventList", run_id: str) -> str:
    """Format logs as human-readable table."""
    if not events.items:
        return f"No logs found for run {run_id}"

    lines = [f"Logs for run {run_id}:", ""]

    # Use original fixed-width format for log tables since messages can be very long
    header = f"{'TIMESTAMP':<20} {'LEVEL':<8} {'STEP_KEY':<25} {'MESSAGE'}"
    separator = "-" * 80
    lines.extend([header, separator])

    for i, event in enumerate(events.items):
        timestamp_ms = int(event.timestamp)
        dt = datetime.datetime.fromtimestamp(timestamp_ms / 1000.0)
        timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")

        level = event.level.value
        step_key = (event.step_key or "")[:24]
        message = event.message

        row = f"{timestamp_str:<20} {level:<8} {step_key:<25} {message}"
        lines.append(row)

        # Add stack trace for error events
        if event.error and event.error.stack:
            lines.append("")
            lines.append("Stack Trace:")
            stack_trace = event.error.get_stack_trace_string()
            for stack_line in stack_trace.split("\n"):
                if stack_line.strip():
                    lines.append(f"  {stack_line}")
            lines.append("")

    lines.extend(["", f"Total log entries: {events.total}"])
    if events.has_more:
        lines.append("Note: More logs available (use --limit to increase or --cursor to paginate)")

    return "\n".join(lines)


def format_logs_json(events: "RunEventList") -> str:
    """Format logs as JSON."""
    return events.model_dump_json(indent=2)


# ---------------------------------------------------------------------------
# Schedule formatters
# ---------------------------------------------------------------------------


def format_schedules(schedules: "DgApiScheduleList", as_json: bool) -> str:
    """Format schedule list for output."""
    if as_json:
        schedules_dict = schedules.model_dump()
        for schedule in schedules_dict["items"]:
            schedule.pop("code_location_origin", None)
            schedule.pop("id", None)
        return json.dumps(schedules_dict, indent=2)

    headers = ["NAME", "STATUS", "CRON", "PIPELINE"]
    rows = []
    for schedule in schedules.items:
        rows.append(
            [
                schedule.name,
                schedule.status.value,
                schedule.cron_schedule,
                schedule.pipeline_name,
            ]
        )

    return format_table(headers, rows)


def format_schedule(schedule: "DgApiSchedule", as_json: bool) -> str:
    """Format single schedule for output."""
    if as_json:
        schedule_dict = schedule.model_dump()
        schedule_dict.pop("code_location_origin", None)
        schedule_dict.pop("id", None)
        return json.dumps(schedule_dict, indent=2)

    fields = [
        ("Name", schedule.name),
        ("Status", schedule.status.value),
        ("Cron Schedule", schedule.cron_schedule),
        ("Pipeline", schedule.pipeline_name),
        ("Description", schedule.description or "None"),
    ]

    if schedule.execution_timezone:
        fields.append(("Timezone", schedule.execution_timezone))

    if schedule.next_tick_timestamp:
        next_tick_str = _format_timestamp(schedule.next_tick_timestamp)
        fields.append(("Next Tick", next_tick_str))

    return format_detail(fields)


# ---------------------------------------------------------------------------
# Sensor formatters
# ---------------------------------------------------------------------------


def format_sensors(sensors: "DgApiSensorList", as_json: bool) -> str:
    """Format sensor list for output."""
    if as_json:
        sensors_dict = sensors.model_dump()
        for sensor in sensors_dict["items"]:
            sensor.pop("repository_origin", None)
            sensor.pop("id", None)
        return json.dumps(sensors_dict, indent=2)

    headers = ["NAME", "STATUS", "TYPE"]
    rows = []
    for sensor in sensors.items:
        rows.append(
            [
                sensor.name,
                sensor.status.value,
                sensor.sensor_type.value,
            ]
        )

    return format_table(headers, rows)


def format_sensor(sensor: "DgApiSensor", as_json: bool) -> str:
    """Format single sensor for output."""
    if as_json:
        sensor_dict = sensor.model_dump()
        sensor_dict.pop("repository_origin", None)
        sensor_dict.pop("id", None)
        return json.dumps(sensor_dict, indent=2)

    fields = [
        ("Name", sensor.name),
        ("Status", sensor.status.value),
        ("Type", sensor.sensor_type.value),
        ("Description", sensor.description or "None"),
    ]

    if sensor.next_tick_timestamp:
        next_tick_str = _format_timestamp(sensor.next_tick_timestamp)
        fields.append(("Next Tick", next_tick_str))

    return format_detail(fields)


# ---------------------------------------------------------------------------
# Issue formatters
# ---------------------------------------------------------------------------


def format_issue(issue: "DgApiIssue", as_json: bool) -> str:
    """Format a single issue for output."""
    if as_json:
        return issue.model_dump_json(indent=2)

    fields: list[tuple[str, str]] = [
        ("Title", issue.title),
        ("Status", issue.status.value),
        ("Created By", issue.created_by_email),
    ]

    if issue.run_id is not None:
        fields.append(("Run ID", issue.run_id))
    if issue.asset_key is not None:
        fields.append(("Asset Key", str(issue.asset_key)))

    fields.append(("Description", issue.description))

    if issue.context is not None:
        fields.append(("Additional Context", issue.context))

    return format_detail(fields)


def format_issues(issue_list: "DgApiIssueList", as_json: bool) -> str:
    """Format a list of issues for output."""
    if as_json:
        return issue_list.model_dump_json(indent=2)

    if not issue_list.items:
        return "No issues found."

    headers = ["STATUS", "TITLE", "ID", "CREATED BY"]
    rows = [
        [issue.status.value, issue.title, issue.id, issue.created_by_email]
        for issue in issue_list.items
    ]

    lines = [format_table(headers, rows)]

    if issue_list.has_more:
        lines.append("Note: More issues available (use --cursor to paginate)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Code location formatters
# ---------------------------------------------------------------------------


def format_code_locations(locations: "DgApiCodeLocationList", as_json: bool) -> str:
    """Format code location list for output."""
    if as_json:
        return locations.model_dump_json(indent=2)

    headers = ["NAME", "IMAGE", "STATUS"]
    rows = [[loc.location_name, loc.image or "", loc.status or ""] for loc in locations.items]
    return format_table(headers, rows)


def format_code_location(location: "DgApiCodeLocation", as_json: bool) -> str:
    """Format single code location for output."""
    if as_json:
        return location.model_dump_json(indent=2)

    fields = [
        ("Name", location.location_name),
        ("Image", location.image or "None"),
    ]
    if location.code_source:
        cs = location.code_source
        if cs.module_name:
            fields.append(("Module", cs.module_name))
        if cs.package_name:
            fields.append(("Package", cs.package_name))
        if cs.python_file:
            fields.append(("File", cs.python_file))

    return format_detail(fields)



def format_add_code_location_result(result: "DgApiAddCodeLocationResult", as_json: bool) -> str:
    """Format add code location result for output."""
    if as_json:
        return result.model_dump_json(indent=2)

    return f"Added or updated code location '{result.location_name}'."


def format_delete_code_location_result(
    result: "DgApiDeleteCodeLocationResult", as_json: bool
) -> str:
    """Format delete code location result for output."""
    if as_json:
        return result.model_dump_json(indent=2)

    return f"Deleted code location '{result.location_name}'."
