"""Asset output formatters for CLI display."""

import re
from typing import TYPE_CHECKING, Literal

from rich.console import Console
from rich.table import Table
from rich.text import Text

from dagster_dg_cli.cli.api.asset.display_models import (
    AssetDisplay,
    AssetListDisplay,
    MetadataSection,
    asset_list_to_display,
    asset_to_display,
)

if TYPE_CHECKING:
    from dagster_dg_cli.api_layer.schemas.asset import DgApiAsset, DgApiAssetList

OutputFormat = Literal["table", "json", "markdown"]


def _enhance_sql_formatting(sql_content: str) -> str:
    """Apply consistent indentation to SQL content within code blocks."""
    lines = sql_content.split("\n")
    formatted_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped:
            if any(
                stripped.lower().startswith(keyword)
                for keyword in [
                    "select",
                    "from",
                    "where",
                    "with",
                    "left join",
                    "right join",
                    "inner join",
                    "join",
                ]
            ):
                formatted_lines.append(f"    {stripped}")
            elif stripped.startswith(("),", ") as", ")", "and ", "or ", "on ")):
                formatted_lines.append(f"    {stripped}")
            else:
                formatted_lines.append(f"      {stripped}")
        else:
            formatted_lines.append("")

    return "\n".join(formatted_lines)


def _process_description_with_code_blocks(description: str, format_sql: bool = True) -> list[Text]:
    """Process description text, enhancing SQL code blocks while preserving structure."""
    if not description:
        return []

    lines = []
    current_text = []
    in_code_block = False
    code_block_type = None
    code_content = []

    for line in description.split("\n"):
        code_block_match = re.match(r"```(\w+)?", line.strip())
        if code_block_match and not in_code_block:
            if current_text:
                for text_line in current_text:
                    lines.append(Text(f"  {text_line}" if text_line.strip() else ""))
                current_text = []

            in_code_block = True
            code_block_type = code_block_match.group(1) or ""
            lines.append(Text(f"  {line.strip()}"))
            code_content = []

        elif line.strip() == "```" and in_code_block:
            if code_content and code_block_type and code_block_type.lower() == "sql" and format_sql:
                enhanced_sql = _enhance_sql_formatting("\n".join(code_content))
                for sql_line in enhanced_sql.split("\n"):
                    lines.append(Text(f"  {sql_line}" if sql_line.strip() else ""))
            else:
                for code_line in code_content:
                    lines.append(Text(f"  {code_line}"))

            lines.append(Text(f"  {line.strip()}"))
            in_code_block = False
            code_block_type = None
            code_content = []

        elif in_code_block:
            code_content.append(line)

        else:
            current_text.append(line)

    if current_text:
        for text_line in current_text:
            lines.append(Text(f"  {text_line}" if text_line.strip() else ""))

    return lines


def _create_horizontal_separator(section_name: str, section_color: str, width: int = 70) -> Text:
    """Create a styled horizontal separator with section name."""
    prefix = "━━━ "
    suffix_length = width - len(prefix) - len(section_name) - 1
    suffix = "━" * max(suffix_length, 3)

    separator_text = Text(f"{prefix}{section_name} {suffix}", style=section_color)
    return separator_text


def format_assets(assets: "DgApiAssetList", output_format: OutputFormat = "table") -> str:
    """Format asset list for output."""
    if output_format == "json":
        return assets.model_dump_json(indent=2)

    display = asset_list_to_display(assets)

    if output_format == "markdown":
        return _format_asset_list_display_as_markdown(display)

    return _format_asset_list_display_as_table(display)


def format_asset(asset: "DgApiAsset", output_format: OutputFormat = "table") -> str:
    """Format single asset for output."""
    if output_format == "json":
        return asset.model_dump_json(indent=2)

    display = asset_to_display(asset)

    if output_format == "markdown":
        return _format_asset_display_as_markdown(display)

    return _format_asset_display_as_table(display)


def _format_asset_list_display_as_table(display: AssetListDisplay) -> str:
    """Format asset list display model as table."""
    if not display.items:
        return "No assets found."

    table = Table(border_style="dim")
    table.add_column("Asset Key", style="bold cyan", no_wrap=True, min_width=20)
    table.add_column("Group", style="bold", min_width=12)
    table.add_column("Kinds", style="bold", min_width=12)
    table.add_column("Description", style="bold", max_width=60, no_wrap=True)

    for item in display.items:
        table.add_row(
            item.asset_key,
            item.group_name,
            item.kinds_text,
            item.description_text,
        )

    console = Console()
    with console.capture() as capture:
        console.print(table)
    return capture.get().rstrip()


def _format_asset_list_display_as_markdown(display: AssetListDisplay) -> str:
    """Format asset list display model as markdown."""
    if not display.items:
        return "No assets found."

    lines = [
        "# Assets",
        "",
        "| Asset Key | Group | Kinds | Description |",
        "|-----------|-------|-------|-------------|",
    ]

    for item in display.items:
        description_text = item.description_text.replace("|", "\\|").replace("\n", " ")
        if len(description_text) > 100:
            description_text = description_text[:97] + "..."

        lines.append(
            f"| {item.asset_key} | {item.group_name} | {item.kinds_text} | {description_text} |"
        )

    return "\n".join(lines)


def _format_asset_display_as_table(display: AssetDisplay) -> str:
    """Format asset display model as rich table."""
    console = Console()
    lines = []

    header_text = Text(f"Asset: {display.asset_key}", style="bold cyan")
    if display.group_name:
        header_text.append(f" [{display.group_name}]", style="dim")
    lines.append(header_text)

    if display.kinds:
        kinds_text = Text("Kinds: ", style="bold")
        kinds_text.append(", ".join(display.kinds), style="blue")
        lines.append(kinds_text)

    if display.tags:
        tags_text = Text("Tags: ", style="bold")
        tag_strings = [f"{key}={value}" for key, value in display.tags]
        tags_text.append(", ".join(tag_strings), style="green")
        lines.append(tags_text)

    lines.append(Text(""))

    if display.description:
        lines.append(_create_horizontal_separator("Description", "blue"))
        desc_lines = _process_description_with_code_blocks(display.description, format_sql=True)
        lines.extend(desc_lines)
        lines.append(Text(""))

    for section in display.metadata_sections:
        lines.extend(_format_metadata_section_display(section))

    lines.append(_create_horizontal_separator("Technical Details", "dim"))
    id_text = Text("ID:", style="bold")
    id_text.append(f" {display.id}", style="dim")
    lines.append(id_text)

    with console.capture() as capture:
        for line in lines:
            console.print(line)

    return capture.get().rstrip()


def _format_metadata_section_display(section: MetadataSection) -> list[Text]:
    """Format a metadata section display model."""
    if not section.entries:
        return []

    lines = []
    lines.append(_create_horizontal_separator(section.name, section.color))

    for entry in section.entries:
        if entry.is_url:
            field_text = Text(f"{entry.display_name}:", style="bold")
            field_text.append(f" {entry.value}", style="blue")
            lines.append(field_text)
        else:
            field_text = Text(f"{entry.display_name}:", style="bold")
            field_text.append(f" {entry.value}")
            lines.append(field_text)

        lines.append(Text(f"       ({entry.label})", style="dim"))

    lines.append(Text(""))
    return lines


def _format_asset_display_as_markdown(display: AssetDisplay) -> str:
    """Format asset display model as markdown."""
    lines = [f"# Asset: {display.asset_key}"]

    if display.group_name:
        lines.append(f"**Group:** {display.group_name}")

    if display.kinds:
        lines.append(f"**Kinds:** {', '.join(display.kinds)}")

    lines.append("")

    if display.description:
        lines.extend(["## Description", "", display.description, ""])

    for section in display.metadata_sections:
        if section.name == "Metadata":
            lines.extend(["## Metadata", ""])
        else:
            lines.extend([f"## {section.name} Information", ""])

        for entry in section.entries:
            lines.append(f"- **{entry.display_name}:** {entry.value}")
            lines.append(f"  - _({entry.label})_")
        lines.append("")

    lines.extend(["## Technical Details", "", f"**ID:** {display.id}"])

    return "\n".join(lines)
