"""Deployment output formatters for CLI display."""

from typing import TYPE_CHECKING, Literal

from rich.console import Console
from rich.table import Table

from dagster_dg_cli.cli.api.deployment.display_models import (
    DeploymentListDisplay,
    deployment_list_to_display,
)

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.deployment import DeploymentList

OutputFormat = Literal["table", "json", "markdown"]


def format_deployments(deployments: "DeploymentList", output_format: OutputFormat = "table") -> str:
    """Format deployment list for output."""
    if output_format == "json":
        return deployments.model_dump_json(indent=2)

    display = deployment_list_to_display(deployments)

    if output_format == "markdown":
        return _format_deployment_list_display_as_markdown(display)

    return _format_deployment_list_display_as_table(display)


def _format_deployment_list_display_as_table(display: DeploymentListDisplay) -> str:
    """Format deployment list display model as table."""
    if not display.items:
        return "No deployments found."

    table = Table(border_style="dim")
    table.add_column("Name", style="bold cyan", min_width=10)
    table.add_column("ID", justify="right", min_width=6)
    table.add_column("Type", style="bold", min_width=10)

    for deployment in display.items:
        table.add_row(
            deployment.name,
            deployment.id,
            deployment.type,
        )

    console = Console()
    with console.capture() as capture:
        console.print(table)
    return capture.get().rstrip()


def _format_deployment_list_display_as_markdown(display: DeploymentListDisplay) -> str:
    """Format deployment list display model as markdown."""
    if not display.items:
        return "No deployments found."

    lines = ["# Deployments", "", "| Name | ID | Type |", "|------|-----|------|"]

    for deployment in display.items:
        lines.append(f"| {deployment.name} | {deployment.id} | {deployment.type} |")

    return "\n".join(lines)
