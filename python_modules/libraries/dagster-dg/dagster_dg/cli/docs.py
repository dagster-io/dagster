from pathlib import Path

import click

from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.component_key import GlobalComponentKey
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.docs import html_from_markdown, markdown_for_component_type, open_html_in_browser
from dagster_dg.utils import DgClickCommand, DgClickGroup, exit_with_error


@click.group(name="docs", cls=DgClickGroup)
def docs_group():
    """Commands for generating docs from your Dagster code."""


# ########################
# ##### COMPONENT TYPE
# ########################


@docs_group.command(name="component-type", cls=DgClickCommand)
@click.argument("component_type", type=str)
@click.option("--output", type=click.Choice(["browser", "cli"]), default="browser")
@dg_global_options
@click.pass_context
def component_type_docs_command(
    context: click.Context,
    component_type: str,
    output: str,
    **global_options: object,
) -> None:
    """Get detailed information on a registered Dagster component type."""
    cli_config = normalize_cli_config(global_options, context)
    dg_context = DgContext.for_defined_registry_environment(Path.cwd(), cli_config)
    registry = RemoteComponentRegistry.from_dg_context(dg_context)
    component_key = GlobalComponentKey.from_typename(component_type)
    if not registry.has_global(component_key):
        exit_with_error(f"Component type `{component_type}` not found.")

    markdown = markdown_for_component_type(registry.get_global(component_key))
    if output == "browser":
        open_html_in_browser(html_from_markdown(markdown))
    else:
        click.echo(html_from_markdown(markdown))
