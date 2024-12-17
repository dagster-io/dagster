import click
from dagster.version import __version__

from dagster_components.cli.generate import generate_cli
from dagster_components.cli.list import list_cli
from dagster_components.core.component import BUILTIN_PUBLISHED_COMPONENT_ENTRY_POINT
from dagster_components.utils import CLI_BUILTIN_COMPONENT_LIB_KEY


def create_dagster_components_cli():
    commands = {
        "generate": generate_cli,
        "list": list_cli,
    }

    @click.group(
        commands=commands,
        context_settings={"max_content_width": 120, "help_option_names": ["-h", "--help"]},
    )
    @click.option(
        "--builtin-component-lib",
        type=str,
        default=BUILTIN_PUBLISHED_COMPONENT_ENTRY_POINT,
        help="Specify the builitin component library to load.",
    )
    @click.version_option(__version__, "--version", "-v")
    @click.pass_context
    def group(ctx: click.Context, builtin_component_lib: str):
        """CLI tools for working with Dagster."""
        ctx.ensure_object(dict)
        ctx.obj[CLI_BUILTIN_COMPONENT_LIB_KEY] = builtin_component_lib

    return group


ENV_PREFIX = "DG_CLI"
cli = create_dagster_components_cli()


def main():
    cli(auto_envvar_prefix=ENV_PREFIX)
