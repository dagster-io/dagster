"""Output formatters for CLI display."""

import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.agent import DgApiAgent, DgApiAgentList
    from dagster_dg_cli.api_layer.schemas.asset import DgApiAsset, DgApiAssetList
    from dagster_dg_cli.api_layer.schemas.deployment import Deployment, DeploymentList
    from dagster_dg_cli.api_layer.schemas.secret import DgApiSecret, DgApiSecretList


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


def format_deployment(deployment: "Deployment", as_json: bool) -> str:
    """Format single deployment for output."""
    if as_json:
        return deployment.model_dump_json(indent=2)

    lines = [
        f"Name: {deployment.name}",
        f"ID: {deployment.id}",
        f"Type: {deployment.type.value}",
    ]

    return "\n".join(lines)


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
            f"Deps: {', '.join(asset.dependency_keys) if asset.dependency_keys else 'None'}",
        ]

        # Add status information if present
        if asset.status:
            asset_lines.extend(_format_asset_status_lines(asset.status))

        asset_lines.append("")  # Empty line between assets
        lines.extend(asset_lines)

    return "\n".join(lines).rstrip()  # Remove trailing empty line


def _format_timestamp(timestamp: float, unit: str = "seconds") -> str:
    """Format timestamp for human-readable display.

    Args:
        timestamp: The timestamp value
        unit: Either "milliseconds" or "seconds" to indicate the timestamp unit
    """
    try:
        if unit == "milliseconds":
            dt = datetime.datetime.fromtimestamp(timestamp / 1000)
        elif unit == "seconds":
            dt = datetime.datetime.fromtimestamp(timestamp)
        else:
            raise ValueError(f"Unsupported unit: {unit}")
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


def format_agents(agents: "DgApiAgentList", as_json: bool) -> str:
    """Format agent list for output."""
    if as_json:
        return agents.model_dump_json(indent=2)

    lines = []
    for agent in agents.items:
        # Use agent_label if available, otherwise format as "Agent {first_8_chars_of_id}"
        display_label = agent.agent_label or f"Agent {agent.id[:8]}"
        lines.extend(
            [
                f"Label: {display_label}",
                f"ID: {agent.id}",
                f"Status: {agent.status.value}",
                f"Last Heartbeat: {_format_timestamp(agent.last_heartbeat_time, 'seconds') if agent.last_heartbeat_time else 'Never'}",
                "",  # Empty line between agents
            ]
        )

    return "\n".join(lines).rstrip()  # Remove trailing empty line


def format_agent(agent: "DgApiAgent", as_json: bool) -> str:
    """Format single agent for output."""
    if as_json:
        return agent.model_dump_json(indent=2)

    # Use agent_label if available, otherwise format as "Agent {first_8_chars_of_id}"
    display_label = agent.agent_label or f"Agent {agent.id[:8]}"
    lines = [
        f"Label: {display_label}",
        f"ID: {agent.id}",
        f"Status: {agent.status.value}",
        f"Last Heartbeat: {_format_timestamp(agent.last_heartbeat_time, 'seconds') if agent.last_heartbeat_time else 'Never'}",
    ]

    if agent.metadata:
        lines.append("")
        lines.append("Metadata:")
        for meta in agent.metadata:
            lines.append(f"  {meta.key}: {meta.value}")

    return "\n".join(lines)


def format_secrets(secrets: "DgApiSecretList", as_json: bool) -> str:
    """Format secret list for output.

    Note: Secret values are never shown in list format for security.
    """
    if as_json:
        return secrets.model_dump_json(indent=2)

    if not secrets.items:
        return "No secrets found."

    lines = []
    for secret in secrets.items:
        lines.extend(
            [
                f"Name: {secret.name}",
                f"Locations: {', '.join(secret.location_names) if secret.location_names else 'All code locations'}",
                f"Scopes: {_format_secret_scopes(secret)}",
                f"Can Edit: {'Yes' if secret.can_edit_secret else 'No'}",
                f"Can View Value: {'Yes' if secret.can_view_secret_value else 'No'}",
            ]
        )

        if secret.updated_by:
            lines.append(f"Updated By: {secret.updated_by.email}")

        if secret.update_timestamp:
            lines.append(f"Updated: {secret.update_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        lines.append("")  # Empty line between secrets

    return "\n".join(lines).rstrip()  # Remove trailing empty line


def format_secret(secret: "DgApiSecret", as_json: bool, show_value: bool = False) -> str:
    """Format single secret for output.

    Args:
        secret: Secret to format
        as_json: Whether to output JSON format
        show_value: Whether to include the secret value (security sensitive)
    """
    import json

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
