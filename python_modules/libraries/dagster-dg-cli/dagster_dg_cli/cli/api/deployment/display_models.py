"""Deployment display models for consistent formatting across output formats.

These models represent the normalized view of deployment data that should be displayed,
ensuring consistency across table, JSON, and markdown formats.
"""

from typing import TYPE_CHECKING

from dagster import _check as check
from dagster._record import record

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.deployment import Deployment, DeploymentList


@record
class DeploymentDisplay:
    """Normalized display representation of a deployment."""

    name: str
    id: str
    type: str


@record
class DeploymentListDisplay:
    """Normalized display representation of a deployment list."""

    items: list[DeploymentDisplay]
    total: int


def deployment_to_display(deployment: "Deployment") -> DeploymentDisplay:
    """Convert API deployment model to display model."""
    from dagster_dg_cli.api_layer.schemas.deployment import Deployment

    check.inst_param(deployment, "deployment", Deployment)

    return DeploymentDisplay(
        name=deployment.name,
        id=str(deployment.id),
        type=deployment.type.value,
    )


def deployment_list_to_display(deployments: "DeploymentList") -> DeploymentListDisplay:
    """Convert API deployment list model to display model."""
    from dagster_dg_cli.api_layer.schemas.deployment import DeploymentList

    check.inst_param(deployments, "deployments", DeploymentList)

    items = []
    for deployment in deployments.items:
        items.append(deployment_to_display(deployment))

    return DeploymentListDisplay(
        items=items,
        total=deployments.total,
    )
