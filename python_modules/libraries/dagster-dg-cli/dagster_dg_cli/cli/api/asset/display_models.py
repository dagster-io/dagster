"""Asset display models for consistent formatting across output formats.

These models represent the normalized view of asset data that should be displayed,
ensuring consistency across table, JSON, and markdown formats.
"""

from typing import TYPE_CHECKING, Optional

from dagster import _check as check
from dagster._record import record

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.asset import DgApiAsset, DgApiAssetList


@record
class MetadataEntry:
    """Normalized metadata entry for display."""

    label: str
    display_name: str
    value: str
    is_url: bool = False


@record
class MetadataSection:
    """A section of metadata entries."""

    name: str
    color: str
    entries: list[MetadataEntry]


@record
class AssetDisplay:
    """Normalized display representation of a single asset."""

    asset_key: str
    group_name: Optional[str]
    kinds: list[str]
    description: Optional[str]
    tags: list[tuple[str, str]]
    metadata_sections: list[MetadataSection]
    id: str


@record
class AssetListItemDisplay:
    """Normalized display representation of an asset in a list."""

    asset_key: str
    group_name: str
    kinds_text: str
    description_text: str


@record
class AssetListDisplay:
    """Normalized display representation of an asset list."""

    items: list[AssetListItemDisplay]
    cursor: Optional[str]
    has_more: bool


def _extract_metadata_value(entry: dict) -> str:
    """Extract the actual value from a metadata entry."""
    value = entry.get("description", "")
    if not value:
        for key in ["text", "url", "path", "jsonString", "mdStr"]:
            if entry.get(key):
                return entry[key]

    for key in ["floatValue", "intValue", "boolValue"]:
        if entry.get(key) is not None:
            return str(entry[key])

    return value


def _is_useful_metadata_entry(entry: dict) -> bool:
    """Filter out useless metadata entries."""
    value = _extract_metadata_value(entry)
    return bool(value and value != "None")


def _create_display_name(label: str) -> str:
    """Convert technical metadata labels to friendly display names."""
    label_mappings = {
        "dagster/table_name": "Table",
        "dagster-dbt/materialization_type": "Type",
        "dagster_dbt/unique_id": "Model",
        "dagster/code_references": "Code References",
        "url": "URL",
    }
    return label_mappings.get(label, label)


def _categorize_metadata_entries(entries: list[dict]) -> list[MetadataSection]:
    """Group metadata entries by prefix and create sections."""
    categories = {}

    for entry in entries:
        if not _is_useful_metadata_entry(entry):
            continue

        label = entry.get("label", "")

        if "/" in label:
            prefix = label.split("/")[0] + "/"
        else:
            prefix = "other"

        if prefix not in categories:
            categories[prefix] = []
        categories[prefix].append(entry)

    sections = []

    sorted_prefixes = []
    if "other" in categories:
        sorted_prefixes.append("other")
    sorted_prefixes.extend(sorted([p for p in categories.keys() if p != "other"]))

    for prefix in sorted_prefixes:
        entries_list = []
        for entry in categories[prefix]:
            label = entry.get("label", "")
            value = _extract_metadata_value(entry)
            display_name = _create_display_name(label)
            is_url = label == "url"

            entries_list.append(
                MetadataEntry(
                    label=label,
                    display_name=display_name,
                    value=value,
                    is_url=is_url,
                )
            )

        if prefix == "other":
            section = MetadataSection(
                name="Metadata",
                color="bold",
                entries=entries_list,
            )
        else:
            section_name = prefix.rstrip("/")
            section = MetadataSection(
                name=section_name,
                color="blue",
                entries=entries_list,
            )

        sections.append(section)

    return sections


def asset_to_display(asset: "DgApiAsset") -> AssetDisplay:
    """Convert API asset model to display model."""
    from dagster_dg_cli.api_layer.schemas.asset import DgApiAsset

    check.inst_param(asset, "asset", DgApiAsset)

    tags = []
    if asset.tags:
        for tag in asset.tags:
            tags.append((tag["key"], tag["value"]))

    metadata_sections = []
    if asset.metadata_entries:
        metadata_sections = _categorize_metadata_entries(asset.metadata_entries)

    return AssetDisplay(
        asset_key=asset.asset_key,
        group_name=asset.group_name,
        kinds=asset.kinds or [],
        description=asset.description,
        tags=tags,
        metadata_sections=metadata_sections,
        id=asset.id,
    )


def asset_list_to_display(assets: "DgApiAssetList") -> AssetListDisplay:
    """Convert API asset list model to display model."""
    from dagster_dg_cli.api_layer.schemas.asset import DgApiAssetList

    check.inst_param(assets, "assets", DgApiAssetList)

    items = []
    for asset in assets.items:
        kinds_text = ", ".join(asset.kinds) if asset.kinds else "none"
        description_text = asset.description or "none"

        if len(description_text) > 60:
            description_text = description_text[:57] + "..."

        items.append(
            AssetListItemDisplay(
                asset_key=asset.asset_key,
                group_name=asset.group_name or "none",
                kinds_text=kinds_text,
                description_text=description_text,
            )
        )

    return AssetListDisplay(
        items=items,
        cursor=assets.cursor,
        has_more=assets.has_more,
    )
