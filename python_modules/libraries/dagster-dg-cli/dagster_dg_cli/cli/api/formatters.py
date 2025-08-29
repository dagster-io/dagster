"""Output formatters for CLI display."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.asset import DgApiAsset, DgApiAssetList
    from dagster_dg_cli.api_layer.schemas.deployment import DeploymentList


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
        lines.extend(
            [
                f"Asset Key: {asset.asset_key}",
                f"ID: {asset.id}",
                f"Description: {asset.description or 'None'}",
                f"Group: {asset.group_name}",
                f"Kinds: {', '.join(asset.kinds) if asset.kinds else 'None'}",
                "",  # Empty line between assets
            ]
        )

    return "\n".join(lines).rstrip()  # Remove trailing empty line


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
