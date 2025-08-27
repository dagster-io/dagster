"""Output formatters for CLI display."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dagster_dg_cli.dagster_plus_api.schemas.asset import DgPlusApiAsset, DgPlusApiAssetList
    from dagster_dg_cli.dagster_plus_api.schemas.deployment import DeploymentList


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


def format_assets(assets: "DgPlusApiAssetList", as_json: bool) -> str:
    """Format asset list for output."""
    if as_json:
        return assets.model_dump_json(indent=2)

    lines = []

    # Handle empty asset list
    if not assets.items:
        lines.append("No assets found.")
    else:
        for asset in assets.items:
            lines.extend(
                [
                    f"Asset Key: {asset.asset_key}",
                    f"ID: {asset.id}",
                    f"Group: {asset.group_name}",
                    f"Description: {asset.description or '(none)'}",
                    f"Kinds: {', '.join(asset.kinds) if asset.kinds else '(none)'}",
                    "",  # Empty line between assets
                ]
            )

    # Add pagination info
    if assets.cursor or assets.has_more:
        lines.extend(
            [
                "Pagination:",
                f"  Has More: {assets.has_more}",
            ]
        )
        if assets.cursor:
            lines.append(f"  Next Cursor: {assets.cursor}")
        lines.append("")

    return "\n".join(lines).rstrip()  # Remove trailing empty line


def format_asset(asset: "DgPlusApiAsset", as_json: bool) -> str:
    """Format single asset for output."""
    if as_json:
        return asset.model_dump_json(indent=2)

    lines = [
        f"Asset Key: {asset.asset_key}",
        f"ID: {asset.id}",
        f"Group: {asset.group_name}",
        f"Description: {asset.description or '(none)'}",
        f"Kinds: {', '.join(asset.kinds) if asset.kinds else '(none)'}",
    ]

    if asset.metadata_entries:
        lines.extend(["", "Metadata:"])
        for entry in asset.metadata_entries:
            label = entry.get("label", "")
            description = entry.get("description", "")
            lines.append(f"  {label}: {description}")

    return "\n".join(lines)
