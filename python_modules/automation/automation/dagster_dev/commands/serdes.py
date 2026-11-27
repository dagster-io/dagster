"""Inspect registered serdes types."""

import tempfile
import webbrowser

import click
from dagster_shared.serdes.serdes import _WHITELIST_MAP

from automation.serdes.format_html import format_html
from automation.serdes.format_json import format_json
from automation.serdes.format_text import format_detail, format_details, format_simple_list
from automation.serdes.registry import list_descendants, scan_registry
from automation.serdes.scanner import discover_and_import_serdes_modules


@click.group(name="serdes")
@click.option(
    "--scan",
    multiple=True,
    metavar="PACKAGE",
    help="Scan and import serdes types from package (can be specified multiple times)",
)
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output during scanning")
@click.pass_context
def serdes(ctx, scan, verbose):
    """Inspect registered serdes types."""
    ctx.ensure_object(dict)
    ctx.obj["scan"] = scan
    ctx.obj["verbose"] = verbose


@serdes.command(name="list")
@click.option("--detailed", is_flag=True, help="Show detailed information")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--html", is_flag=True, help="Output as HTML")
@click.pass_context
def list_types(ctx, detailed, output_json, html):
    """List all registered types.

    Examples:
      dagster-dev serdes --scan dagster list
      dagster-dev serdes --scan dagster list --detailed
      dagster-dev serdes --scan dagster list --json
    """
    scan_packages = ctx.obj["scan"]
    verbose = ctx.obj["verbose"]

    for package_name in scan_packages:
        discover_and_import_serdes_modules(package_name, verbose=verbose)

    registry = scan_registry(_WHITELIST_MAP)

    if output_json:
        click.echo(format_json(registry))
    elif html:
        html_content = format_html(registry)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            f.write(html_content)
            html_path = f.name
        click.echo(f"Opening {html_path} in browser...", err=True)
        webbrowser.open(f"file://{html_path}")
    elif detailed:
        all_items = (
            list(registry.types.values())
            + list(registry.enums.values())
            + list(registry.unions.values())
        )
        click.echo(format_details(all_items))
    else:
        all_items = (
            list(registry.types.values())
            + list(registry.enums.values())
            + list(registry.unions.values())
        )
        click.echo(format_simple_list(all_items))


@serdes.command()
@click.argument("typename")
@click.pass_context
def show(ctx, typename):
    """Show detailed info for a specific type.

    Examples:
      dagster-dev serdes --scan dagster show AssetKey
      dagster-dev serdes --scan dagster show DagsterRunStatus
    """
    scan_packages = ctx.obj["scan"]
    verbose = ctx.obj["verbose"]

    for package_name in scan_packages:
        discover_and_import_serdes_modules(package_name, verbose=verbose)

    registry = scan_registry(_WHITELIST_MAP)
    defn = registry.get(typename)
    if defn is None:
        raise click.ClickException(f"{typename} not found")
    click.echo(format_detail(defn))


@serdes.command()
@click.argument("typename")
@click.option("--html", is_flag=True, help="Output as HTML")
@click.pass_context
def tree(ctx, typename, html):
    """Show type and all types it references recursively.

    Examples:
      dagster-dev serdes --scan dagster tree AssetKey
      dagster-dev serdes --scan dagster_cloud tree AgentHeartbeat
    """
    scan_packages = ctx.obj["scan"]
    verbose = ctx.obj["verbose"]

    for package_name in scan_packages:
        discover_and_import_serdes_modules(package_name, verbose=verbose)

    registry = scan_registry(_WHITELIST_MAP)
    defn = registry.get(typename)
    if defn is None:
        raise click.ClickException(f"{typename} not found")

    tree_registry = list_descendants(defn.typename, registry)

    if html:
        html_content = format_html(tree_registry)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as f:
            f.write(html_content)
            html_path = f.name
        click.echo(f"Opening {html_path} in browser...", err=True)
        webbrowser.open(f"file://{html_path}")
    else:
        all_items = (
            list(tree_registry.types.values())
            + list(tree_registry.enums.values())
            + list(tree_registry.unions.values())
        )
        click.echo(format_details(all_items))
