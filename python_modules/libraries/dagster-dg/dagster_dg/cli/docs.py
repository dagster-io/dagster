import json
import re
import shutil
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Optional

import click
from yaspin import yaspin

from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.component import LibraryObjectKey, RemoteLibraryObjectRegistry
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.docs import json_for_all_components
from dagster_dg.utils import DgClickCommand, DgClickGroup, exit_with_error, pushd
from dagster_dg.utils.telemetry import cli_telemetry_wrapper

# from pathlib import Path
DEV_DOCS_DIR = (
    Path(__file__).parent.parent.parent.parent.parent.parent
    / "js_modules"
    / "dagster-ui"
    / "packages"
    / "dg-docs-site"
)
DOCS_DIR = Path(__file__).parent.parent / "docs" / "packages" / "dg-docs-site"
ACTIVE_DOCS_DIR = DOCS_DIR if DOCS_DIR.exists() else DEV_DOCS_DIR

DOCS_JSON_PATH = ACTIVE_DOCS_DIR / "contents" / "generated.json"

SHOULD_DOCS_EXIT = False


@click.group(name="docs", cls=DgClickGroup)
def docs_group():
    """Commands for generating docs from your Dagster code."""


LOCALHOST_URL_REGEX = re.compile(b".*(http://localhost.*)\n")


@docs_group.command(name="serve", cls=DgClickCommand)
@click.argument("component_type", type=str, default="")
@click.option("--port", type=int, default=3004)
@dg_global_options
@cli_telemetry_wrapper
def serve_docs_command(
    component_type: Optional[str],
    port: int,
    **global_options: object,
) -> None:
    """Serve the Dagster components docs, to be viewed in a browser."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_defined_registry_environment(Path.cwd(), cli_config)
    registry = RemoteLibraryObjectRegistry.from_dg_context(dg_context)

    component_key = None
    if component_type:
        component_key = LibraryObjectKey.from_typename(component_type)
        if not component_key or not registry.has(component_key):
            exit_with_error(f"Component type `{component_type}` not found.")

    with pushd(ACTIVE_DOCS_DIR):
        DOCS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        DOCS_JSON_PATH.write_text(json.dumps(json_for_all_components(registry), indent=2))
        with yaspin(text="Verifying docs dependencies", color="blue") as spinner:
            yes = subprocess.Popen(["yes", "y"], stdout=subprocess.PIPE)
            try:
                subprocess.check_output(["yarn", "install"], stdin=yes.stdout)
            finally:
                yes.terminate()
            spinner.ok("✓")

        spinner = yaspin(text="Starting docs server", color="blue")
        try:
            yarn_dev = subprocess.Popen(
                ["yarn", "dev", "--port", str(port)], stdout=subprocess.PIPE
            )
            assert yarn_dev.stdout is not None
            base_url = None
            for line in iter(yarn_dev.stdout.readline, b""):
                url_match = LOCALHOST_URL_REGEX.match(line)
                if url_match:
                    base_url = url_match.group(1).decode("utf-8")
                if b"Ready" in line:
                    spinner.text = "Docs server ready"
                    spinner.ok("✓")
                    # open browser

                    if base_url:
                        url_suffix_from_component_key = (
                            f"/packages/{component_key.namespace.split('.')[0]}/{component_key.namespace}.{component_key.name}"
                            if component_key
                            else ""
                        )
                        url = f"{base_url}{url_suffix_from_component_key}"
                        click.echo(f"Opening docs in browser: {url}")
                        webbrowser.open(url)

                        while not SHOULD_DOCS_EXIT:
                            time.sleep(0.5)

        finally:
            yarn_dev.terminate()  # pyright: ignore[reportPossiblyUnboundVariable]


@docs_group.command(name="build", cls=DgClickCommand)
@click.argument("output_dir", type=click.Path(exists=False))
@dg_global_options
@cli_telemetry_wrapper
def build_docs_command(
    output_dir: str,
    **global_options: object,
) -> None:
    """Build a static version of the Dagster components docs, to be served by a static file server."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_defined_registry_environment(Path.cwd(), cli_config)
    registry = RemoteLibraryObjectRegistry.from_dg_context(dg_context)

    with pushd(ACTIVE_DOCS_DIR):
        DOCS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        DOCS_JSON_PATH.write_text(json.dumps(json_for_all_components(registry), indent=2))
        with yaspin(text="Verifying docs dependencies", color="blue") as spinner:
            yes = subprocess.Popen(["yes", "y"], stdout=subprocess.PIPE)
            try:
                subprocess.check_output(["yarn", "install"], stdin=yes.stdout)
            finally:
                yes.terminate()
            spinner.ok("✓")

        spinner = yaspin(text="Building docs", color="blue")
        subprocess.check_output(["yarn", "build"])
        spinner.ok("✓")

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        shutil.copytree(ACTIVE_DOCS_DIR / "out", output_dir, dirs_exist_ok=True)
