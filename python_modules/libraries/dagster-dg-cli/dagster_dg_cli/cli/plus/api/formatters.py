"""Output formatters for CLI display."""

from dagster_dg_cli.dagster_plus_api.schemas.deployment import DeploymentList


def format_deployments(deployments: DeploymentList, as_json: bool) -> str:
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
