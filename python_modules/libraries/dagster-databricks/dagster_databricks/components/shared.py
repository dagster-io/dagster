from dataclasses import dataclass

from dagster import Resolvable
from dagster.components.resolved.core_models import ResolutionContext

from dagster_databricks.components.databricks_asset_bundle.resource import DatabricksWorkspace


@dataclass
class DatabricksWorkspaceArgs(Resolvable):
    """Aligns with DatabricksWorkspace.__new__."""

    host: str
    token: str


def resolve_databricks_workspace(context: ResolutionContext, model) -> DatabricksWorkspace:
    args = DatabricksWorkspaceArgs.resolve_from_model(context, model)
    return DatabricksWorkspace(
        host=args.host,
        token=args.token,
    )
