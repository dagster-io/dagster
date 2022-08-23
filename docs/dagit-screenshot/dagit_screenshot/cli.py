from typing import Optional
import click

from dagit_screenshot.commands.audit import audit as _audit
from dagit_screenshot.commands.capture import capture as _capture
from dagit_screenshot.commands.show import show as _show
from dagit_screenshot.utils import load_spec, normalize_output_path, spec_id_to_relative_path
from dagit_screenshot.defaults import DEFAULT_OUTPUT_ROOT, DEFAULT_SPEC_DB, DEFAULT_WORKSPACE_ROOT


@click.group(
    help="CLI tools for capturing and managing Dagit screenshots.",
    context_settings={"max_content_width": 120},
)
@click.option(
    "--output-root",
    type=click.Path(exists=True),
    default=DEFAULT_OUTPUT_ROOT,
    help="Path to root directory where generated screenshots are written.",
)
@click.option(
    "--spec-db",
    type=click.Path(exists=True),
    default=DEFAULT_SPEC_DB,
    help="Path to YAML file containing array of screenshot specs.",
)
@click.option(
    "--workspace-root",
    type=click.Path(exists=True),
    default=DEFAULT_WORKSPACE_ROOT,
    help="Path to root directory against which relative spec workspaces are resolved.",
)
@click.pass_context
def dagit_screenshot(ctx, output_root: str, spec_db: str, workspace_root: str) -> None:
    ctx.obj["output_root"] = output_root
    ctx.obj["spec_db"] = spec_db
    ctx.obj["workspace_root"] = workspace_root


@dagit_screenshot.command(
    help="""
    Audit a screenshot spec database. Verifies that screenshot specs are valid and that referenced
    workspace files exist. Optionally verify that corresponding output files exist.
    """
)
@click.option("--verify-outputs/--no-verify-outputs", type=click.BOOL, default=False, help="If set, then the existence of output screenshots in the output root will also be checked.")
@click.pass_context
def audit(ctx, verify_outputs) -> None:
    output_root = ctx.obj["output_root"]
    spec_db = ctx.obj["spec_db"]
    workspace_root = ctx.obj["workspace_root"]
    _audit(spec_db, output_root, workspace_root, verify_outputs=verify_outputs)


@dagit_screenshot.command(help="Reads a screenshot spec and captures a screenshot")
@click.argument("spec_id", nargs=1)
@click.option(
    "--output-path",
    help="""
    Path where screenshot will be written. If path is relative, it is resolved relative to
    the `output_root`. Defaults to the `spec_id` argument, with `.png` appended if the
    `spec_id` does not end in a file extension.
    """,
)
@click.pass_context
def capture(ctx, spec_id: str, output_path: str) -> None:
    """SPEC_ID: ID of screenshot. Typically relative output path of spec."""
    output_path = normalize_output_path(
        output_path or spec_id_to_relative_path(spec_id), ctx.obj["output_root"]
    )
    spec = load_spec(spec_id, ctx.obj["spec_db"])
    _capture(spec, output_path)

@dagit_screenshot.command(help="Dump the contents of a screenshot DB to the terminal as YAML.")
@click.option('--prefix', help="If provided, only specs with ids starting with the passed value will be dumped.")
@click.pass_context
def show(ctx, prefix: Optional[str]):
    _show(ctx.obj['spec_db'], prefix)

def main():
    dagit_screenshot(obj={})
