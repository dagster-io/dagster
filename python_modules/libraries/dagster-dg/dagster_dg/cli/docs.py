import json
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional

import click
from yaspin import yaspin

from dagster_dg.component import ComponentKey, RemoteComponentRegistry
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.docs import json_for_all_components
from dagster_dg.utils import DgClickCommand, exit_with_error, pushd

# from pathlib import Path
DOCS_DIR = Path(__file__).parent.parent.parent / "docs"
DOCS_JSON_PATH = DOCS_DIR / "contents" / "generated.json"


@click.command(name="docs", cls=DgClickCommand)
@click.argument("component_type", type=str, default="")
def docs_command(
    component_type: Optional[str] = None,
    **global_options: object,
) -> None:
    """Get detailed information on a registered Dagster component type."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_defined_registry_environment(Path.cwd(), cli_config)
    registry = RemoteComponentRegistry.from_dg_context(dg_context)

    component_key = None
    if component_type:
        component_key = ComponentKey.from_typename(component_type)
        if not registry.has(component_key):
            exit_with_error(f"Component type `{component_type}` not found.")

    with pushd(DOCS_DIR):
        DOCS_JSON_PATH.write_text(json.dumps(json_for_all_components(registry), indent=2))
        with yaspin(text="Installing first-time docs dependencies", color="blue") as spinner:
            yes = subprocess.Popen(["yes", "y"], stdout=subprocess.PIPE)
            subprocess.check_output(["yarn", "install"], stdin=yes.stdout)

        spinner = yaspin(text="Starting docs server", color="blue")
        yarn_dev = subprocess.Popen(["yarn", "dev"], stdout=subprocess.PIPE)
        assert yarn_dev.stdout is not None
        for line in iter(yarn_dev.stdout.readline, b""):
            if b"Ready" in line:
                spinner.text = "Docs server ready"
                spinner.ok("✓")
                # open browser

                url_suffix_from_component_key = (
                    f"/packages/{component_key.namespace.split('.')[0]}/{component_key.namespace}.{component_key.name}"
                    if component_key
                    else ""
                )
                url = f"http://localhost:3000{url_suffix_from_component_key}"
                click.echo(f"Opening docs in browser: {url}")
                webbrowser.open(url)


# # ########################
# # ##### COMPONENT TYPE
# # ########################


# @docs_group.command(name="component-type", cls=DgClickCommand)
# @click.argument("component_type", type=str)
# @click.option("--output", type=click.Choice(["browser", "cli"]), default="browser")
# @dg_global_options
# def component_type_docs_command(
#     component_type: str,
#     output: str,
#     **global_options: object,
# ) -> None:
#     """Get detailed information on a registered Dagster component type."""
#     cli_config = normalize_cli_config(global_options, click.get_current_context())
#     dg_context = DgContext.for_defined_registry_environment(Path.cwd(), cli_config)
#     registry = RemoteComponentRegistry.from_dg_context(dg_context)
#     component_key = ComponentKey.from_typename(component_type)
#     if not registry.has(component_key):
#         exit_with_error(f"Component type `{component_type}` not found.")

#     markdown = markdown_for_component_type(registry.get(component_key))
#     if output == "browser":
#         open_html_in_browser(html_from_markdown(markdown))
#     else:
#         click.echo(html_from_markdown(markdown))
